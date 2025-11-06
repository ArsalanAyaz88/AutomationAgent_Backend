"""
Channel Analytics Tracker & Video Idea Generator
Tracks YouTube channel analytics and provides AI-powered video ideas
"""

import os
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pymongo import MongoClient
from bson import ObjectId
import certifi

from youtube_http_client import YouTubeHttpClient
from agents import Agent, Runner, set_default_openai_client
from openai import AsyncOpenAI


class ChannelAnalyticsTracker:
    """Tracks channel analytics and generates video ideas"""
    
    def __init__(self):
        self.youtube_client = YouTubeHttpClient()
        self.mongo_client = None
        self.db = None
        self.channels_collection = None
        self.analytics_collection = None
        self._init_mongodb()
    
    def _init_mongodb(self):
        """Initialize MongoDB connection"""
        mongodb_uri = os.getenv("MONGODB_URI")
        if not mongodb_uri:
            raise Exception("MONGODB_URI not set")
        
        ca_file = os.getenv("MONGODB_CA_FILE") or certifi.where()
        self.mongo_client = MongoClient(mongodb_uri, tlsCAFile=ca_file)
        
        db_name = os.getenv("MONGODB_DB", "youtube_ops")
        self.db = self.mongo_client[db_name]
        self.channels_collection = self.db["tracked_channels"]
        self.analytics_collection = self.db["channel_analytics"]
    
    def extract_video_id(self, video_url: str) -> Optional[str]:
        """Extract video ID from various YouTube video URL formats"""
        # Format 1: youtube.com/watch?v=VIDEO_ID
        match = re.search(r'[?&]v=([^&]+)', video_url)
        if match:
            return match.group(1)
        
        # Format 2: youtu.be/VIDEO_ID
        match = re.search(r'youtu\.be/([^?]+)', video_url)
        if match:
            return match.group(1)
        
        # Format 3: youtube.com/embed/VIDEO_ID
        match = re.search(r'youtube\.com/embed/([^?]+)', video_url)
        if match:
            return match.group(1)
        
        # Format 4: youtube.com/v/VIDEO_ID
        match = re.search(r'youtube\.com/v/([^?]+)', video_url)
        if match:
            return match.group(1)
        
        return None
    
    def extract_channel_id(self, channel_url: str) -> Optional[str]:
        """Extract channel ID from various YouTube URL formats (channels and videos)"""
        # Check if it's a video URL first
        video_id = self.extract_video_id(channel_url)
        if video_id:
            # Return special marker to indicate we need to fetch channel from video
            return f"video:{video_id}"
        
        # Format 1: youtube.com/channel/UC...
        match = re.search(r'youtube\.com/channel/([^/?]+)', channel_url)
        if match:
            return match.group(1)
        
        # Format 2: youtube.com/@username
        match = re.search(r'youtube\.com/@([^/?]+)', channel_url)
        if match:
            username = match.group(1)
            # Will need to fetch channel ID via API
            return f"@{username}"
        
        # Format 3: youtube.com/c/customname
        match = re.search(r'youtube\.com/c/([^/?]+)', channel_url)
        if match:
            return f"c/{match.group(1)}"
        
        # If just channel ID provided
        if channel_url.startswith("UC"):
            return channel_url
        
        return None
    
    async def save_channel(self, channel_url: str, user_id: str = "default") -> Dict[str, Any]:
        """Save channel for tracking (supports both channel URLs and video URLs)"""
        channel_id = self.extract_channel_id(channel_url)
        if not channel_id:
            raise ValueError("Invalid YouTube channel or video URL")
        
        # Check if we need to get channel ID from video
        if channel_id.startswith("video:"):
            video_id = channel_id.replace("video:", "")
            # Get video details to extract channel ID
            video_data = await self.youtube_client.get_video_stats(video_id)
            
            if not video_data or 'items' not in video_data or len(video_data['items']) == 0:
                raise ValueError("Video not found or invalid video URL")
            
            # Extract channel ID from video data
            channel_id = video_data['items'][0]['snippet']['channelId']
        
        # Fetch channel data
        channel_data = await self.youtube_client.get_channel(channel_id)
        
        if not channel_data or 'items' not in channel_data or len(channel_data['items']) == 0:
            raise ValueError("Channel not found")
        
        channel_info = channel_data['items'][0]
        channel_id = channel_info['id']
        
        # Check if already tracked
        existing = self.channels_collection.find_one({
            "channel_id": channel_id,
            "user_id": user_id
        })
        
        if existing:
            # Update last accessed
            self.channels_collection.update_one(
                {"_id": existing["_id"]},
                {"$set": {"last_accessed": datetime.now(timezone.utc)}}
            )
            return {
                "status": "already_tracked",
                "channel_id": channel_id,
                "channel_title": existing.get("channel_title"),
                "message": "Channel already being tracked"
            }
        
        # Save new channel
        channel_record = {
            "user_id": user_id,
            "channel_id": channel_id,
            "channel_url": channel_url,
            "channel_title": channel_info['snippet']['title'],
            "channel_description": channel_info['snippet'].get('description', ''),
            "subscriber_count": int(channel_info['statistics'].get('subscriberCount', 0)),
            "video_count": int(channel_info['statistics'].get('videoCount', 0)),
            "view_count": int(channel_info['statistics'].get('viewCount', 0)),
            "thumbnail": channel_info['snippet']['thumbnails']['default']['url'],
            "created_at": datetime.now(timezone.utc),
            "last_accessed": datetime.now(timezone.utc),
            "tracking_enabled": True
        }
        
        result = self.channels_collection.insert_one(channel_record)
        
        # Fetch initial analytics
        await self.fetch_analytics(channel_id, user_id)
        
        return {
            "status": "success",
            "channel_id": channel_id,
            "channel_title": channel_record["channel_title"],
            "subscriber_count": channel_record["subscriber_count"],
            "video_count": channel_record["video_count"],
            "message": "Channel added for tracking"
        }
    
    async def fetch_analytics(self, channel_id: str, user_id: str = "default") -> Dict[str, Any]:
        """Fetch and store current analytics"""
        # Get channel stats
        channel_data = await self.youtube_client.get_channel(channel_id)
        
        if not channel_data or 'items' not in channel_data:
            raise ValueError("Failed to fetch channel data")
        
        channel_info = channel_data['items'][0]
        stats = channel_info['statistics']
        
        # Get recent videos (last 50)
        videos_data = await self.youtube_client.list_channel_videos(channel_id, maxResults=50)
        
        videos = []
        total_views = 0
        total_likes = 0
        total_comments = 0
        
        if videos_data and 'items' in videos_data:
            for video_item in videos_data['items']:
                video_id = video_item['id']['videoId'] if 'id' in video_item and 'videoId' in video_item['id'] else video_item.get('snippet', {}).get('resourceId', {}).get('videoId')
                
                if video_id:
                    # Get detailed stats for each video
                    video_stats = await self.youtube_client.get_video_stats(video_id)
                    
                    if video_stats and 'items' in video_stats and len(video_stats['items']) > 0:
                        v_stats = video_stats['items'][0]['statistics']
                        views = int(v_stats.get('viewCount', 0))
                        likes = int(v_stats.get('likeCount', 0))
                        comments = int(v_stats.get('commentCount', 0))
                        
                        total_views += views
                        total_likes += likes
                        total_comments += comments
                        
                        videos.append({
                            "video_id": video_id,
                            "title": video_item['snippet']['title'],
                            "published_at": video_item['snippet']['publishedAt'],
                            "views": views,
                            "likes": likes,
                            "comments": comments,
                            "engagement_rate": (likes + comments) / views if views > 0 else 0
                        })
        
        # Calculate averages
        video_count = len(videos)
        avg_views = total_views / video_count if video_count > 0 else 0
        avg_engagement = (total_likes + total_comments) / total_views if total_views > 0 else 0
        
        # Store analytics snapshot
        analytics_record = {
            "user_id": user_id,
            "channel_id": channel_id,
            "timestamp": datetime.now(timezone.utc),
            "subscriber_count": int(stats.get('subscriberCount', 0)),
            "total_views": int(stats.get('viewCount', 0)),
            "video_count": int(stats.get('videoCount', 0)),
            "recent_videos": videos,
            "avg_views_per_video": avg_views,
            "avg_engagement_rate": avg_engagement,
            "total_recent_views": total_views,
            "total_recent_likes": total_likes,
            "total_recent_comments": total_comments
        }
        
        self.analytics_collection.insert_one(analytics_record)
        
        return analytics_record
    
    async def generate_video_idea(self, channel_id: str, user_id: str = "default") -> Dict[str, Any]:
        """Generate AI-powered video idea based on analytics"""
        # Get channel info
        channel = self.channels_collection.find_one({
            "channel_id": channel_id,
            "user_id": user_id
        })
        
        if not channel:
            raise ValueError("Channel not found. Please add channel first.")
        
        # Get latest analytics
        latest_analytics = self.analytics_collection.find_one(
            {"channel_id": channel_id, "user_id": user_id},
            sort=[("timestamp", -1)]
        )
        
        if not latest_analytics:
            # Fetch analytics first
            latest_analytics = await self.fetch_analytics(channel_id, user_id)
        
        # Prepare context for AI
        recent_videos = latest_analytics.get('recent_videos', [])[:10]
        
        top_performing = sorted(recent_videos, key=lambda x: x.get('views', 0), reverse=True)[:3]
        high_engagement = sorted(recent_videos, key=lambda x: x.get('engagement_rate', 0), reverse=True)[:3]
        
        context = f"""
Channel: {channel['channel_title']}
Description: {channel.get('channel_description', 'N/A')}
Subscribers: {channel['subscriber_count']:,}
Total Videos: {channel['video_count']}

Recent Performance:
- Average Views: {latest_analytics['avg_views_per_video']:,.0f}
- Average Engagement: {latest_analytics['avg_engagement_rate']:.2%}

Top Performing Videos:
{chr(10).join([f"- {v['title']} ({v['views']:,} views)" for v in top_performing])}

High Engagement Videos:
{chr(10).join([f"- {v['title']} ({v['engagement_rate']:.2%} engagement)" for v in high_engagement])}
"""
        
        # Create AI agent for idea generation
        openai_client = AsyncOpenAI(
            api_key=os.getenv("GEMINI_API_KEY"),
            base_url=os.getenv("GEMINI_BASE_URL")
        )
        
        set_default_openai_client(openai_client)
        
        agent = Agent(
            model=os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash-exp"),
            instructions="""You are a YouTube content strategist expert. 
            Analyze the channel's performance data and generate 3 viral video ideas.
            
            For each idea provide:
            1. Catchy title (with year/numbers for SEO)
            2. Brief description (2-3 lines)
            3. Why it will perform well (based on data)
            4. Target keywords
            5. Best upload time suggestion
            
            Be specific, actionable, and data-driven."""
        )
        
        runner = Runner(agent=agent, client=openai_client)
        
        result = await runner.run(
            context_variables={},
            messages=[{
                "role": "user",
                "content": f"Based on this channel's analytics, suggest 3 high-performing video ideas:\n\n{context}"
            }]
        )
        
        # Parse AI response
        ai_suggestions = result.messages[-1].get('content', '') if result.messages else "No suggestions generated"
        
        # Store the recommendation
        recommendation_record = {
            "user_id": user_id,
            "channel_id": channel_id,
            "timestamp": datetime.now(timezone.utc),
            "analytics_snapshot": {
                "avg_views": latest_analytics['avg_views_per_video'],
                "avg_engagement": latest_analytics['avg_engagement_rate'],
                "subscriber_count": channel['subscriber_count']
            },
            "video_ideas": ai_suggestions,
            "context_used": context
        }
        
        self.db["video_recommendations"].insert_one(recommendation_record)
        
        return {
            "status": "success",
            "channel_title": channel['channel_title'],
            "analytics": {
                "subscribers": channel['subscriber_count'],
                "avg_views": latest_analytics['avg_views_per_video'],
                "avg_engagement": latest_analytics['avg_engagement_rate'],
                "video_count": channel['video_count']
            },
            "video_ideas": ai_suggestions,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_tracked_channels(self, user_id: str = "default") -> List[Dict[str, Any]]:
        """Get all tracked channels for a user"""
        channels = list(self.channels_collection.find(
            {"user_id": user_id},
            sort=[("last_accessed", -1)]
        ))
        
        # Convert ObjectId to string
        for channel in channels:
            channel['_id'] = str(channel['_id'])
            if 'created_at' in channel:
                channel['created_at'] = channel['created_at'].isoformat()
            if 'last_accessed' in channel:
                channel['last_accessed'] = channel['last_accessed'].isoformat()
        
        return channels
