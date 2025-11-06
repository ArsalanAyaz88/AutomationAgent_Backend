"""
Unified Analytics-Aware Agent Endpoints
All 7 agents now use YOUR channel analytics automatically!
"""

from typing import Optional, Dict, Any, List
from fastapi import HTTPException
from pydantic import BaseModel
from agents import Agent, Runner

from analytics_enhanced_agents import (
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
    tone: Optional[str] = "conversational"
    key_points: Optional[List[str]] = None


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
            
            # Build prompt
            prompt = f"""
{analytics_context_text if analytics_context_text else ""}

TASK: Generate a {request.total_words}-word YouTube script

TOPIC: {request.topic}
TONE: {request.tone}
"""
            
            if request.key_points:
                prompt += f"\nKEY POINTS:\n" + "\n".join([f"- {p}" for p in request.key_points])
            
            prompt += """

OUTPUT: Professional YouTube script with hook, introduction, main content, and call-to-action.
"""
            
            # Create and run agent
            model_name = create_agent_client_func("agent3")
            agent = Agent(model=model_name, instructions=prompt)
            runner = Runner(agent=agent)
            
            result = await runner.run(
                context_variables={},
                messages=[{"role": "user", "content": f"Generate script: {request.topic}"}]
            )
            
            script = result.messages[-1].get('content', '') if result.messages else ""
            
            return UnifiedResponse(
                success=True,
                result=script,
                analytics_used=has_analytics,
                channel_info=channel_info
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
            agent = Agent(model=model_name, instructions=prompt)
            runner = Runner(agent=agent)
            
            result = await runner.run(
                context_variables={},
                messages=[{"role": "user", "content": "Generate video ideas"}]
            )
            
            ideas = result.messages[-1].get('content', '') if result.messages else ""
            
            return UnifiedResponse(
                success=True,
                result=ideas,
                analytics_used=has_analytics,
                channel_info=channel_info
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
            agent = Agent(model=model_name, instructions=prompt)
            runner = Runner(agent=agent)
            
            result = await runner.run(
                context_variables={},
                messages=[{"role": "user", "content": "Generate titles"}]
            )
            
            titles = result.messages[-1].get('content', '') if result.messages else ""
            
            return UnifiedResponse(
                success=True,
                result=titles,
                analytics_used=has_analytics,
                channel_info=channel_info
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
            agent = Agent(model=model_name, instructions=prompt)
            runner = Runner(agent=agent)
            
            result = await runner.run(
                context_variables={},
                messages=[{"role": "user", "content": "Generate content roadmap"}]
            )
            
            roadmap = result.messages[-1].get('content', '') if result.messages else ""
            
            return UnifiedResponse(
                success=True,
                result=roadmap,
                analytics_used=has_analytics,
                channel_info=channel_info
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
