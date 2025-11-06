"""
Unified Analytics-Aware Agent Endpoints
All 7 agents now use YOUR channel analytics automatically!
"""

from typing import Optional, Dict, Any, List
from fastapi import HTTPException
from pydantic import BaseModel
from agents import Agent, Runner

from per_channel_analytics_Agents.analytics_enhanced_agents import (
    analytics_context,
    get_channel_context_for_script,
    get_channel_context_for_ideas,
    get_channel_context_for_title,
    get_channel_context_for_roadmap,
    get_channel_summary
)


# ============================================
# REQUEST MODELS
# ============================================

class AnalyticsAwareRequest(BaseModel):
    """Base model with analytics support"""
    channel_id: Optional[str] = None
    user_id: Optional[str] = "default"
    use_analytics: Optional[bool] = True


class UnifiedScriptRequest(AnalyticsAwareRequest):
    topic: str
    total_words: Optional[int] = 1500
    tone: Optional[str] = "conversational"  # conversational, professional, casual, energetic
    target_audience: Optional[str] = "general"  # beginners, professionals, tech enthusiasts
    video_duration: Optional[int] = None  # Target video duration in minutes
    include_hook: Optional[bool] = True  # Whether to include attention-grabbing hook
    include_cta: Optional[bool] = True  # Whether to include call-to-action
    script_structure: Optional[str] = "standard"  # standard, story-based, tutorial, listicle
    key_points: Optional[List[str]] = None
    additional_instructions: Optional[str] = None  # Extra custom instructions


class UnifiedVideoIdeasRequest(AnalyticsAwareRequest):
    niche: Optional[str] = None
    video_count: Optional[int] = 5
    style: Optional[str] = "viral"  # viral, educational, entertaining


class UnifiedTitleRequest(AnalyticsAwareRequest):
    video_description: str
    keywords: Optional[List[str]] = None
    title_count: Optional[int] = 5


class UnifiedRoadmapRequest(AnalyticsAwareRequest):
    video_count: Optional[int] = 30
    timeframe_days: Optional[int] = 90
    focus_area: Optional[str] = None


class UnifiedResponse(BaseModel):
    success: bool
    result: str
    error: Optional[str] = None
    analytics_used: bool = False
    channel_info: Optional[Dict[str, Any]] = None
    video_analytics: Optional[Dict[str, Any]] = None  # Top 30 videos data for frontend display


# ============================================
# UNIFIED AGENT FUNCTIONS
# ============================================

def register_unified_analytics_routes(app, create_agent_client_func, youtube_tools):
    """Register all unified analytics-aware endpoints"""
    
    async def get_channel_context(request: AnalyticsAwareRequest) -> tuple[str, bool, Optional[Dict]]:
        """Helper to get analytics context for any request"""
        if not request.use_analytics:
            return "", False, None
        
        # Get channel_id if not provided
        channel_id = request.channel_id
        if not channel_id:
            tracked = await analytics_context.get_tracked_channel(request.user_id)
            if tracked:
                channel_id = tracked.get('channel_id')
        
        if not channel_id:
            return "", False, None
        
        # Get channel summary
        summary = get_channel_summary(channel_id, request.user_id)
        
        return channel_id, True, summary
    
    
    async def get_video_analytics_data(channel_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed video analytics for frontend display
        
        Shows up to 30 videos, or all available if channel has fewer than 30
        """
        try:
            # Get latest analytics from MongoDB
            analytics = analytics_context.tracker.analytics_collection.find_one(
                {"channel_id": channel_id, "user_id": user_id},
                sort=[("timestamp", -1)]
            )
            
            if not analytics:
                return None
            
            recent_videos = analytics.get('recent_videos', [])
            total_videos = len(recent_videos)
            
            # If channel has fewer than 30 videos, show all; otherwise show top 30
            max_videos = min(30, total_videos)
            
            # Calculate combined scores: recency + performance
            from datetime import datetime
            if recent_videos:
                # Parse dates and calculate days ago
                for video in recent_videos:
                    try:
                        pub_date = datetime.fromisoformat(video['published_at'].replace('Z', '+00:00'))
                        days_ago = (datetime.now(pub_date.tzinfo) - pub_date).days
                        # Recency score: newer videos get higher scores (0-1 range)
                        video['recency_score'] = max(0, 1 - (days_ago / 365))
                    except:
                        video['recency_score'] = 0.5
                
                # Normalize metrics for scoring
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
            
            # Get top videos by combined score (recency + performance)
            top_performing = sorted(
                recent_videos, 
                key=lambda x: x.get('combined_score', 0), 
                reverse=True
            )[:max_videos]
            
            # Get high engagement videos (also considering recency)
            high_engagement = sorted(
                recent_videos,
                key=lambda x: (0.5 * x.get('engagement_score', 0) + 0.5 * x.get('recency_score', 0)),
                reverse=True
            )[:max_videos]
            
            return {
                "total_videos_analyzed": total_videos,
                "videos_shown": max_videos,  # Actual count of videos in lists
                "showing_all": total_videos <= 30,  # True if showing all available videos
                "avg_views": analytics.get('avg_views_per_video', 0),
                "avg_engagement": analytics.get('avg_engagement_rate', 0),
                "top_performing_videos": [
                    {
                        "rank": i + 1,
                        "title": video['title'],
                        "views": video['views'],
                        "likes": video['likes'],
                        "comments": video['comments'],
                        "engagement_rate": video['engagement_rate'],
                        "published_at": video['published_at']
                    }
                    for i, video in enumerate(top_performing)
                ],
                "high_engagement_videos": [
                    {
                        "rank": i + 1,
                        "title": video['title'],
                        "views": video['views'],
                        "likes": video['likes'],
                        "comments": video['comments'],
                        "engagement_rate": video['engagement_rate'],
                        "published_at": video['published_at']
                    }
                    for i, video in enumerate(high_engagement)
                ]
            }
        except Exception as e:
            print(f"Error getting video analytics: {e}")
            return None
    
    
    # ============================================
    # 1. UNIFIED SCRIPT GENERATOR
    # ============================================
    @app.post("/api/unified/generate-script", response_model=UnifiedResponse)
    async def unified_generate_script(request: UnifiedScriptRequest):
        """
        📝 Analytics-Aware Script Generator
        
        Generates scripts optimized for YOUR channel based on:
        - Your top-performing video styles
        - Optimal script length for your audience
        - Tone that resonates with your viewers
        - Content structure that drives engagement
        
        Just provide the topic - analytics are automatically applied!
        """
        try:
            channel_id, has_analytics, channel_info = await get_channel_context(request)
            
            # Get analytics context
            if has_analytics:
                analytics_context_text = get_channel_context_for_script(
                    channel_id, request.topic, request.user_id
                )
            else:
                analytics_context_text = ""
            
            # Calculate targets for instructions
            target_paragraphs = request.total_words // 150  # ~150 words per paragraph
            min_chars = request.total_words * 4  # Conservative estimate
            
            # Build structure guidance
            structure_guides = {
                "standard": "Hook → Introduction → Main Content (3-5 sections) → Climax → Conclusion/CTA",
                "story-based": "Opening Hook → Story Setup → Conflict/Challenge → Journey → Resolution → Lesson/CTA",
                "tutorial": "Hook → Problem Statement → Overview → Step-by-Step Instructions → Common Mistakes → Summary/CTA",
                "listicle": "Hook → Introduction → List Items (with explanations) → Bonus Point → Conclusion/CTA"
            }
            structure_guide = structure_guides.get(request.script_structure, structure_guides["standard"])
            
            # Build key points section
            key_points_section = ""
            if request.key_points and len(request.key_points) > 0:
                key_points_section = "\nKey Points to Cover:\n" + "\n".join([f"- {point}" for point in request.key_points])
            
            # Hook and CTA requirements
            hook_requirement = "- Start with a strong hook (under 15 seconds) that grabs attention and creates curiosity" if request.include_hook else ""
            cta_requirement = "- End with a clear and compelling call-to-action (subscribe, comment, like, etc.)" if request.include_cta else ""
            
            # Additional instructions
            extra_instructions = f"\n\nAdditional Requirements:\n{request.additional_instructions}" if request.additional_instructions else ""
            
            # Duration info
            duration_info = f"Target video duration: {request.video_duration} minutes" if request.video_duration else ""
            
            # Build comprehensive prompt
            prompt = f"""
{analytics_context_text}

You are "The Storyteller" — a YouTube script writer focused on creating engaging video scripts.

SCRIPT SPECIFICATIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Topic: {request.topic}
Tone: {request.tone}
Target Audience: {request.target_audience}
Target Word Count: {request.total_words} WORDS (not characters, ~{request.total_words * 5} characters)
{duration_info}
Script Structure: {request.script_structure}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚨 ABSOLUTE REQUIREMENT - WORD COUNT 🚨
You MUST write EXACTLY {request.total_words} WORDS or MORE. This is NON-NEGOTIABLE!

UNDERSTANDING WORDS vs CHARACTERS:
- 1 word = "Hello" or "Python" or "video" (each counts as 1)
- {request.total_words} WORDS ≈ {request.total_words * 5} CHARACTERS minimum
- Example: "I love making YouTube videos for beginners" = 7 WORDS (not 7 characters!)

MANDATORY LENGTH GUIDELINES:
- For 1500 words: Write approximately 10-12 paragraphs with 150-200 words each
- For 5000 words: Write approximately 30-35 paragraphs with 150-200 words each
- DO NOT stop until you reach the word count
- Each section should be EXTREMELY detailed with examples, stories, explanations
- Add personal anecdotes, step-by-step breakdowns, case studies
- Include multiple examples for each point
- Elaborate on every concept thoroughly

EXPANSION STRATEGY:
- Opening Hook: 200-300 words
- Introduction: 400-500 words
- Each main point/section: 800-1200 words minimum
- Add sub-sections with detailed explanations
- Include "why this matters" for each point
- Add "common mistakes" sections
- Include "pro tips" and "advanced techniques"
- Conclusion: 300-400 words

THIS IS YOUR PRIMARY GOAL: Reach {request.total_words} WORDS (not characters)!

STRUCTURE TO FOLLOW:
{structure_guide}
{key_points_section}

CORE REQUIREMENTS:
{hook_requirement}
- Use {request.tone} tone throughout the script
- Write for {request.target_audience} audience
- Maintain viewer interest with pattern interrupts and open loops
- Use active voice and engaging storytelling
- Natural flow and pacing appropriate for YouTube
- Keep it conversational and relatable
{cta_requirement}

⚠️ LENGTH IS PRIORITY #1:
- Write LONG, DETAILED sections - not short summaries
- Every point needs 200-300 words of explanation minimum
- Add real examples, not just concepts
- Include specific details, numbers, statistics when possible
- Tell stories and create scenarios to illustrate points
- Never rush - take time to explain everything thoroughly
- REMEMBER: {request.total_words} WORDS is your target (approximately {target_paragraphs} paragraphs)

IMPORTANT - DO NOT INCLUDE:
- Visual suggestions or descriptions
- Camera cues or directions
- Voiceover notes or annotations
- Production notes or technical directions
- Timestamps or time markers
- Section headers (like "Hook:", "Introduction:", etc.)
{extra_instructions}

OUTPUT: Pure script text only - exactly what should be said in the video, nothing else. Write as if you're speaking directly to the viewer.
"""
            
            # Create and run agent
            model_name = create_agent_client_func("agent3")
            agent = Agent(name="script_generator", model=model_name, instructions=prompt)
            
            result = await Runner.run(
                agent,
                f"Generate a {request.total_words}-word YouTube script about: {request.topic}"
            )
            
            print(f"[DEBUG] Script result: {result}")
            
            script = result.final_output if hasattr(result, 'final_output') else ""
            print(f"[DEBUG] Script content length: {len(script)}")
            
            # If still empty, provide error message
            if not script or script.strip() == "":
                script = "⚠️ Failed to generate script. Please try again or check backend logs."
            
            # Get video analytics data for frontend display
            video_analytics = None
            if has_analytics and channel_id:
                video_analytics = await get_video_analytics_data(channel_id, request.user_id)
            
            return UnifiedResponse(
                success=True,
                result=script,
                analytics_used=has_analytics,
                channel_info=channel_info,
                video_analytics=video_analytics
            )
            
        except Exception as e:
            return UnifiedResponse(success=False, result="", error=str(e))
    
    
    # ============================================
    # 2. UNIFIED VIDEO IDEAS GENERATOR
    # ============================================
    @app.post("/api/unified/generate-video-ideas", response_model=UnifiedResponse)
    async def unified_generate_ideas(request: UnifiedVideoIdeasRequest):
        """
        💡 Analytics-Aware Video Ideas Generator
        
        Generates video ideas based on YOUR channel's:
        - Top-performing content themes
        - High-engagement topics
        - Successful content patterns
        - Audience preferences
        
        Ideas are personalized to match what works for YOUR channel!
        """
        try:
            channel_id, has_analytics, channel_info = await get_channel_context(request)
            
            # Get analytics context
            if has_analytics:
                analytics_context_text = get_channel_context_for_ideas(channel_id, request.user_id)
            else:
                analytics_context_text = f"Generate {request.video_count} video ideas for a {request.niche or 'general'} YouTube channel."
            
            prompt = f"""
{analytics_context_text}

TASK: Generate {request.video_count} viral video ideas
STYLE: {request.style}
{f"NICHE: {request.niche}" if request.niche else ""}

For each idea provide:
1. Catchy title
2. Brief description (2-3 sentences)
3. Why it will perform well
4. Target keywords

Format as a numbered list.
"""
            
            # Create and run agent
            model_name = create_agent_client_func("agent5")
            agent = Agent(name="video_ideas_generator", model=model_name, instructions=prompt)
            
            result = await Runner.run(
                agent,
                f"Generate {request.video_count} {request.style} video ideas"
            )
            
            print(f"[DEBUG] Ideas result: {result}")
            
            ideas = result.final_output if hasattr(result, 'final_output') else ""
            print(f"[DEBUG] Ideas content length: {len(ideas)}")
            
            # If still empty, provide error message
            if not ideas or ideas.strip() == "":
                ideas = "⚠️ Failed to generate ideas. Please try again or check backend logs."
            
            # Get video analytics data for frontend display
            video_analytics = None
            if has_analytics and channel_id:
                video_analytics = await get_video_analytics_data(channel_id, request.user_id)
            
            return UnifiedResponse(
                success=True,
                result=ideas,
                analytics_used=has_analytics,
                channel_info=channel_info,
                video_analytics=video_analytics
            )
            
        except Exception as e:
            return UnifiedResponse(success=False, result="", error=str(e))
    
    
    # ============================================
    # 3. UNIFIED TITLE GENERATOR
    # ============================================
    @app.post("/api/unified/generate-titles", response_model=UnifiedResponse)
    async def unified_generate_titles(request: UnifiedTitleRequest):
        """
        📌 Analytics-Aware Title Generator
        
        Generates titles based on YOUR channel's:
        - Top-performing title patterns
        - Click-through rate optimization
        - Successful keywords and phrases
        - Audience engagement triggers
        
        Titles follow YOUR channel's proven success formula!
        """
        try:
            channel_id, has_analytics, channel_info = await get_channel_context(request)
            
            # Get analytics context
            if has_analytics:
                analytics_context_text = get_channel_context_for_title(
                    channel_id, request.video_description, request.user_id
                )
            else:
                analytics_context_text = ""
            
            keywords_text = f"Target keywords: {', '.join(request.keywords)}" if request.keywords else ""
            
            prompt = f"""
{analytics_context_text}

TASK: Generate {request.title_count} viral YouTube titles

VIDEO CONTEXT: {request.video_description}
{keywords_text}

REQUIREMENTS:
- Maximum 70 characters (YouTube optimal)
- Include power words and numbers where appropriate
- Optimize for CTR
- Make it curiosity-driven

OUTPUT: Numbered list of titles only.
"""
            
            # Create and run agent
            model_name = create_agent_client_func("agent2")
            agent = Agent(name="title_generator", model=model_name, instructions=prompt)
            
            result = await Runner.run(
                agent,
                f"Generate {request.title_count} titles for: {request.video_description}"
            )
            
            print(f"[DEBUG] Titles result: {result}")
            
            titles = result.final_output if hasattr(result, 'final_output') else ""
            print(f"[DEBUG] Titles content length: {len(titles)}")
            
            # If still empty, provide error message
            if not titles or titles.strip() == "":
                titles = "⚠️ Failed to generate titles. Please try again or check backend logs."
            
            # Get video analytics data for frontend display
            video_analytics = None
            if has_analytics and channel_id:
                video_analytics = await get_video_analytics_data(channel_id, request.user_id)
            
            return UnifiedResponse(
                success=True,
                result=titles,
                analytics_used=has_analytics,
                channel_info=channel_info,
                video_analytics=video_analytics
            )
            
        except Exception as e:
            return UnifiedResponse(success=False, result="", error=str(e))
    
    
    # ============================================
    # 4. UNIFIED CONTENT ROADMAP
    # ============================================
    @app.post("/api/unified/generate-roadmap", response_model=UnifiedResponse)
    async def unified_generate_roadmap(request: UnifiedRoadmapRequest):
        """
        🗺️ Analytics-Aware Content Roadmap
        
        Creates a roadmap based on YOUR channel's:
        - Proven content pillars
        - Optimal posting frequency
        - Seasonal trends in your niche
        - Growth opportunities
        
        Roadmap builds on what's already working for YOU!
        """
        try:
            channel_id, has_analytics, channel_info = await get_channel_context(request)
            
            # Get analytics context
            if has_analytics:
                analytics_context_text = get_channel_context_for_roadmap(channel_id, request.user_id)
            else:
                analytics_context_text = ""
            
            prompt = f"""
{analytics_context_text}

TASK: Create a {request.video_count}-video content roadmap
TIMEFRAME: {request.timeframe_days} days
{f"FOCUS: {request.focus_area}" if request.focus_area else ""}

For each video provide:
1. Week number
2. Video topic
3. Brief description
4. Strategic rationale
5. Expected performance

Format as a structured roadmap.
"""
            
            # Create and run agent
            model_name = create_agent_client_func("agent6")
            agent = Agent(name="roadmap_generator", model=model_name, instructions=prompt)
            
            result = await Runner.run(
                agent,
                f"Create a {request.video_count}-video roadmap for {request.timeframe_days} days"
            )
            
            print(f"[DEBUG] Roadmap result: {result}")
            
            roadmap = result.final_output if hasattr(result, 'final_output') else ""
            print(f"[DEBUG] Roadmap content length: {len(roadmap)}")
            
            # If still empty, provide error message
            if not roadmap or roadmap.strip() == "":
                roadmap = "⚠️ Failed to generate roadmap. Please try again or check backend logs."
            
            # Get video analytics data for frontend display
            video_analytics = None
            if has_analytics and channel_id:
                video_analytics = await get_video_analytics_data(channel_id, request.user_id)
            
            return UnifiedResponse(
                success=True,
                result=roadmap,
                analytics_used=has_analytics,
                channel_info=channel_info,
                video_analytics=video_analytics
            )
            
        except Exception as e:
            return UnifiedResponse(success=False, result="", error=str(e))
    
    
    # ============================================
    # 5. QUICK ANALYTICS STATUS
    # ============================================
    @app.get("/api/unified/analytics-status")
    async def get_analytics_status(user_id: str = "default"):
        """
        Check if user has tracked channels and analytics available
        """
        try:
            channels = await analytics_context.tracker.get_tracked_channels(user_id)
            
            if not channels:
                return {
                    "has_analytics": False,
                    "tracked_channels": 0,
                    "message": "No channels tracked. Add your channel to enable analytics-aware agents!"
                }
            
            most_recent = channels[0] if channels else None
            
            return {
                "has_analytics": True,
                "tracked_channels": len(channels),
                "most_recent_channel": {
                    "title": most_recent.get('channel_title'),
                    "channel_id": most_recent.get('channel_id'),
                    "subscribers": most_recent.get('subscriber_count')
                } if most_recent else None,
                "message": f"✅ {len(channels)} channel(s) tracked! All agents will use your analytics automatically."
            }
            
        except Exception as e:
            return {"error": str(e)}
