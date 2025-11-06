"""
Analytics-Enhanced Agents Integration
Makes all agents aware of channel analytics for better recommendations
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime
from functools import wraps
from per_channel_analytics_Agents.channel_analytics_tracker import ChannelAnalyticsTracker


class AnalyticsContext:
    """Provides channel analytics context to agents"""
    
    def __init__(self):
        self.tracker = ChannelAnalyticsTracker()
    
    def get_analytics_context(self, channel_id: str, user_id: str = "default") -> str:
        """Get formatted analytics context for agent prompts"""
        try:
            # Get channel info
            channel = self.tracker.channels_collection.find_one({
                "channel_id": channel_id,
                "user_id": user_id
            })
            
            if not channel:
                return ""
            
            # Get latest analytics
            latest_analytics = self.tracker.analytics_collection.find_one(
                {"channel_id": channel_id, "user_id": user_id},
                sort=[("timestamp", -1)]
            )
            
            if not latest_analytics:
                return f"""
🎯 TRACKED CHANNEL: {channel['channel_title']}
📊 Subscribers: {channel['subscriber_count']:,}
📹 Total Videos: {channel['video_count']}
"""
            
            # Get top performing videos (up to 30, or all if fewer than 30)
            # Priority: Latest + Top Performing
            recent_videos = latest_analytics.get('recent_videos', [])
            total_videos = len(recent_videos)
            max_videos = min(30, total_videos)
            showing_all = total_videos <= 30
            
            # Calculate recency score (newer = higher score)
            from datetime import datetime
            if recent_videos:
                # Parse dates and calculate days ago
                for video in recent_videos:
                    try:
                        pub_date = datetime.fromisoformat(video['published_at'].replace('Z', '+00:00'))
                        days_ago = (datetime.now(pub_date.tzinfo) - pub_date).days
                        # Recency score: newer videos get higher scores (0-1 range)
                        # Videos within 30 days = 1.0, after 365 days = 0
                        video['recency_score'] = max(0, 1 - (days_ago / 365))
                    except:
                        video['recency_score'] = 0.5  # Default for parsing errors
                
                # Normalize views for scoring (0-1 range)
                max_views = max(video.get('views', 0) for video in recent_videos) or 1
                max_engagement = max(video.get('engagement_rate', 0) for video in recent_videos) or 1
                
                for video in recent_videos:
                    video['views_score'] = video.get('views', 0) / max_views
                    video['engagement_score'] = video.get('engagement_rate', 0) / max_engagement
                    
                    # Combined score: 40% recency + 40% views + 20% engagement
                    video['combined_score'] = (
                        0.4 * video['recency_score'] + 
                        0.4 * video['views_score'] + 
                        0.2 * video['engagement_score']
                    )
            
            # Get top performers by combined score (recency + performance)
            top_performing = sorted(
                recent_videos, 
                key=lambda x: x.get('combined_score', 0), 
                reverse=True
            )[:max_videos]
            
            # Get high engagement performers (also considering recency)
            high_engagement = sorted(
                recent_videos,
                key=lambda x: (0.5 * x.get('engagement_score', 0) + 0.5 * x.get('recency_score', 0)),
                reverse=True
            )[:max_videos]
            
            context = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 YOUR CHANNEL ANALYTICS (Real-Time Data)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📺 Channel: {channel['channel_title']}
👥 Subscribers: {channel['subscriber_count']:,}
📹 Total Videos: {channel['video_count']}
👁️ Total Views: {channel.get('view_count', 0):,}

📊 RECENT PERFORMANCE (Last {total_videos} Videos):
├─ Average Views: {latest_analytics['avg_views_per_video']:,.0f}
├─ Average Engagement: {latest_analytics['avg_engagement_rate']:.2%}
├─ Total Recent Views: {latest_analytics['total_recent_views']:,}
└─ Total Engagement: {latest_analytics['total_recent_likes'] + latest_analytics['total_recent_comments']:,}

🔥 {'ALL' if showing_all else f'TOP {max_videos} LATEST & BEST'} PERFORMING VIDEOS (Sorted by: Recency 40% + Views 40% + Engagement 20%){' - COMPLETE CHANNEL DATA' if showing_all else ''}:
"""
            for i, video in enumerate(top_performing, 1):
                context += f"""
{i}. "{video['title']}"
   └─ {video['views']:,} views | {video['engagement_rate']:.2%} engagement
"""
            
            context += f"""

💎 {'ALL' if showing_all else f'TOP {max_videos} LATEST & MOST ENGAGING'} VIDEOS (Sorted by: Engagement 50% + Recency 50%){' - COMPLETE CHANNEL DATA' if showing_all else ''}:
"""
            for i, video in enumerate(high_engagement, 1):
                context += f"""
{i}. "{video['title']}"
   └─ {video['views']:,} views | {video['engagement_rate']:.2%} engagement
"""
            
            context += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ INSTRUCTIONS FOR YOU:
Use this data to provide HIGHLY PERSONALIZED recommendations.
Consider what's working, what patterns exist, and suggest ideas
that align with this channel's proven success formula.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            
            return context
            
        except Exception as e:
            print(f"Error getting analytics context: {e}")
            return ""
    
    async def get_tracked_channel(self, user_id: str = "default") -> Optional[Dict[str, Any]]:
        """Get the most recently accessed tracked channel"""
        try:
            channel = self.tracker.channels_collection.find_one(
                {"user_id": user_id, "tracking_enabled": True},
                sort=[("last_accessed", -1)]
            )
            return channel
        except Exception as e:
            print(f"Error getting tracked channel: {e}")
            return None


# Global analytics context instance
analytics_context = AnalyticsContext()


def with_analytics(agent_name: str):
    """
    Decorator to enhance agent functions with channel analytics context
    
    Usage:
    @with_analytics("agent3_script_generator")
    async def generate_script(request):
        # request.analytics_context will contain channel analytics
        ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            # Check if request has channel_id
            channel_id = getattr(request, 'channel_id', None)
            user_id = getattr(request, 'user_id', 'default')
            
            # If no channel_id, try to get most recent tracked channel
            if not channel_id:
                tracked = await analytics_context.get_tracked_channel(user_id)
                if tracked:
                    channel_id = tracked.get('channel_id')
            
            # Get analytics context if channel_id exists
            if channel_id:
                context = analytics_context.get_analytics_context(channel_id, user_id)
                # Add to request object
                if hasattr(request, '__dict__'):
                    request.analytics_context = context
                    request.has_analytics = True
                    request.channel_id = channel_id
            else:
                if hasattr(request, '__dict__'):
                    request.analytics_context = ""
                    request.has_analytics = False
            
            # Call original function
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def enhance_prompt_with_analytics(base_prompt: str, analytics_context: str) -> str:
    """Add analytics context to agent prompt"""
    if not analytics_context:
        return base_prompt
    
    enhanced = f"""
{analytics_context}

{base_prompt}

⚠️ IMPORTANT: The analytics data above is from the user's actual YouTube channel.
Use this data to make your recommendations more relevant and personalized.
Reference specific patterns, successful videos, or performance metrics when applicable.
"""
    return enhanced


# Convenience functions for each agent type

def get_channel_context_for_script(channel_id: str, topic: str, user_id: str = "default") -> str:
    """Get analytics context optimized for script generation"""
    context = analytics_context.get_analytics_context(channel_id, user_id)
    if not context:
        return ""
    
    return f"""
{context}

📝 SCRIPT GENERATION CONTEXT:
You are generating a script about: "{topic}"

Based on the analytics above:
1. What tone/style matches the successful videos?
2. What video length typically performs best?
3. Are there successful patterns to follow?
4. What hooks/styles drive engagement?

Use these insights to craft a script optimized for this specific channel!
"""


def get_channel_context_for_ideas(channel_id: str, user_id: str = "default") -> str:
    """Get analytics context optimized for video ideas"""
    context = analytics_context.get_analytics_context(channel_id, user_id)
    if not context:
        return ""
    
    return f"""
{context}

💡 VIDEO IDEAS GENERATION CONTEXT:

Based on this channel's performance data:
1. Identify content gaps (what's missing but could work?)
2. Suggest variations of top performers
3. Recommend trending topics in this niche
4. Consider upload timing patterns
5. Factor in audience engagement preferences

Generate ideas that have HIGH probability of success based on this data!
"""


def get_channel_context_for_title(channel_id: str, video_context: str, user_id: str = "default") -> str:
    """Get analytics context optimized for title generation"""
    context = analytics_context.get_analytics_context(channel_id, user_id)
    if not context:
        return ""
    
    return f"""
{context}

📌 TITLE GENERATION CONTEXT:
Video context: {video_context}

Analyze the top-performing titles above:
1. What words/phrases appear in successful titles?
2. What's the typical title structure?
3. Do numbers work well? Questions? Emotional words?
4. What CTR patterns can you identify?

Create titles following the proven success formula of this channel!
"""


def get_channel_context_for_roadmap(channel_id: str, user_id: str = "default") -> str:
    """Get analytics context optimized for content roadmap"""
    context = analytics_context.get_analytics_context(channel_id, user_id)
    if not context:
        return ""
    
    return f"""
{context}

🗺️ ROADMAP GENERATION CONTEXT:

Based on this channel's analytics:
1. What content types are proven winners?
2. What's the optimal posting frequency?
3. What topics should be expanded?
4. What seasonal/trending opportunities exist?
5. How to balance proven content vs experimentation?

Create a 30-video roadmap that builds on what's working while exploring growth opportunities!
"""


# Helper to check if user has tracked channels
async def user_has_tracked_channels(user_id: str = "default") -> bool:
    """Check if user has any tracked channels"""
    try:
        count = analytics_context.tracker.channels_collection.count_documents({
            "user_id": user_id,
            "tracking_enabled": True
        })
        return count > 0
    except:
        return False


# Helper to get channel summary
def get_channel_summary(channel_id: str, user_id: str = "default") -> Dict[str, Any]:
    """Get quick channel summary for UI display"""
    try:
        channel = analytics_context.tracker.channels_collection.find_one({
            "channel_id": channel_id,
            "user_id": user_id
        })
        
        if not channel:
            return {}
        
        analytics = analytics_context.tracker.analytics_collection.find_one(
            {"channel_id": channel_id, "user_id": user_id},
            sort=[("timestamp", -1)]
        )
        
        summary = {
            "channel_title": channel['channel_title'],
            "channel_id": channel_id,
            "subscribers": channel['subscriber_count'],
            "video_count": channel['video_count'],
            "has_analytics": analytics is not None
        }
        
        if analytics:
            summary.update({
                "avg_views": analytics['avg_views_per_video'],
                "avg_engagement": analytics['avg_engagement_rate'],
                "last_updated": analytics['timestamp'].isoformat()
            })
        
        return summary
        
    except Exception as e:
        print(f"Error getting channel summary: {e}")
        return {}
