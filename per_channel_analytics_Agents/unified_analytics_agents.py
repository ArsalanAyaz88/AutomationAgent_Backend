"""
Unified Analytics-Aware Agent Endpoints
All 7 agents now use YOUR channel analytics automatically!
"""

from typing import Optional, Dict, Any, List
from fastapi import HTTPException, UploadFile, File
from pydantic import BaseModel
from agents import Agent, Runner
from datetime import datetime
import re
import PyPDF2
import io

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


class ScriptUploadRequest(BaseModel):
    """Request model for uploading scripts"""
    script_title: str
    script_content: str  # Text extracted from PDF or direct text input
    user_id: Optional[str] = "default"


class ScriptToSceneRequest(BaseModel):
    """Request model for converting script to scene prompts"""
    script_id: str
    user_id: Optional[str] = "default"
    user_query: Optional[str] = "Convert this script into detailed scene-by-scene prompts"


class ChatMessage(BaseModel):
    """Chat message model"""
    role: str  # 'user' or 'assistant'
    content: str


class ScriptwriterChatRequest(BaseModel):
    """Request model for scriptwriter chatbot"""
    message: str
    session_id: Optional[str] = None  # To identify chat session
    user_id: Optional[str] = "default"
    channel_id: Optional[str] = None


class SceneWriterChatRequest(BaseModel):
    """Request model for scene writer chatbot"""
    message: str
    session_id: Optional[str] = None  # To identify chat session
    user_id: Optional[str] = "default"
    script_context: Optional[str] = None  # If user has uploaded a script


class UnifiedResponse(BaseModel):
    success: bool
    result: str
    error: Optional[str] = None
    analytics_used: bool = False
    channel_info: Optional[Dict[str, Any]] = None
    video_analytics: Optional[Dict[str, Any]] = None  # Top 30 videos data for frontend display


class ScriptResponse(BaseModel):
    """Response model for script operations"""
    success: bool
    script_id: Optional[str] = None
    script_title: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None


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
    # SCRIPT DATABASE & HELPERS
    # ============================================
    
    # Initialize chat history collections with TTL index (24 hours auto-delete)
    scriptwriter_chat_collection = analytics_context.tracker.db["scriptwriter_chat_history"]
    scene_writer_chat_collection = analytics_context.tracker.db["scene_writer_chat_history"]
    
    # Create TTL indexes (auto-delete after 24 hours)
    try:
        scriptwriter_chat_collection.create_index(
            "created_at", 
            expireAfterSeconds=86400  # 24 hours = 86400 seconds
        )
        scene_writer_chat_collection.create_index(
            "created_at", 
            expireAfterSeconds=86400  # 24 hours = 86400 seconds
        )
    except Exception as e:
        print(f"TTL index creation (may already exist): {e}")
    
    
    async def save_chat_message(
        collection, 
        session_id: str, 
        user_id: str, 
        role: str, 
        content: str
    ):
        """Save chat message to database with TTL"""
        try:
            message_doc = {
                "session_id": session_id,
                "user_id": user_id,
                "role": role,
                "content": content,
                "created_at": datetime.utcnow()  # TTL index uses this
            }
            collection.insert_one(message_doc)
        except Exception as e:
            print(f"Error saving chat message: {e}")
    
    
    async def get_chat_history(collection, session_id: str, user_id: str, limit: int = 10) -> List[Dict]:
        """Retrieve chat history from database (last N messages)"""
        try:
            messages = list(collection.find(
                {"session_id": session_id, "user_id": user_id},
                {"_id": 0, "role": 1, "content": 1, "created_at": 1}
            ).sort("created_at", 1).limit(limit))
            return messages
        except Exception as e:
            print(f"Error getting chat history: {e}")
            return []
    
    
    async def clear_chat_session(collection, session_id: str, user_id: str):
        """Manually clear chat session (in addition to auto TTL)"""
        try:
            collection.delete_many({"session_id": session_id, "user_id": user_id})
        except Exception as e:
            print(f"Error clearing chat session: {e}")
    
    
    def _sanitize_for_veo(text: str) -> str:
        """Sanitize content for Veo v3 compliance"""
        if not isinstance(text, str):
            return text
        out = text
        # Soften or remove explicit mentions of human remains/graphic injury
        replacements = {
            r"\b(lifeless\s+bodies|bodies|corpse|corpses|dead\s+bodies)\b": "sensitive elements",
            r"\b(remains)\b": "sensitive elements",
            r"\b(blood|bloody|gore|gory|severed|mutilated)\b": "damage",
            r"\b(killed|dead|death)\b": "serious incident",
        }
        for pat, repl in replacements.items():
            out = re.sub(pat, repl, out, flags=re.IGNORECASE)

        # Anonymize private individual names in the JSON character field if present
        def _anon_char(match: re.Match) -> str:
            original = match.group(1)
            generic_roles = {"narrator", "host", "speaker", "subject", "the subject", "the host", "the narrator", "the survivor"}
            if original.strip().lower() in generic_roles:
                return f'"character": "{original}"'
            # Heuristic: if it looks like a proper name (contains a space and starts with uppercase)
            if re.match(r"^[A-Z][a-z]+(\s+[A-Z][a-z\-]+)+$", original):
                return '"character": "the subject"'
            return f'"character": "{original}"'

        out = re.sub(r'"character"\s*:\s*"([^"]+)"', _anon_char, out)
        return out
    
    
    async def extract_text_from_pdf(file_content: bytes) -> str:
        """Extract text from PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to extract text from PDF: {str(e)}")
    
    
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
            
            # Script generator is topic-based, doesn't analyze specific videos
            # So we don't send video_analytics data
            return UnifiedResponse(
                success=True,
                result=script,
                analytics_used=has_analytics,
                channel_info=channel_info,
                video_analytics=None  # Script generator doesn't use video analytics
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
    # 5. SCRIPT UPLOAD & MANAGEMENT (CRUD)
    # ============================================
    
    @app.post("/api/unified/upload-script-pdf")
    async def upload_script_pdf(file: UploadFile = File(...), user_id: str = "default"):
        """
        📄 Upload PDF script for scene conversion
        Extracts text from PDF and stores in database
        """
        try:
            if not file.filename.endswith('.pdf'):
                raise HTTPException(status_code=400, detail="Only PDF files are allowed")
            
            # Read PDF content
            pdf_content = await file.read()
            
            # Extract text from PDF
            script_text = await extract_text_from_pdf(pdf_content)
            
            if not script_text:
                raise HTTPException(status_code=400, detail="No text found in PDF")
            
            # Generate script ID
            from bson.objectid import ObjectId
            script_id = str(ObjectId())
            
            # Store in database
            script_doc = {
                "script_id": script_id,
                "script_title": file.filename.replace('.pdf', ''),
                "script_content": script_text,
                "user_id": user_id,
                "uploaded_at": datetime.utcnow(),
                "file_type": "pdf"
            }
            
            analytics_context.tracker.db["uploaded_scripts"].insert_one(script_doc)
            
            return ScriptResponse(
                success=True,
                script_id=script_id,
                script_title=script_doc["script_title"],
                message=f"✅ Script uploaded successfully! {len(script_text)} characters extracted."
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    
    
    @app.post("/api/unified/upload-script-text", response_model=ScriptResponse)
    async def upload_script_text(request: ScriptUploadRequest):
        """
        📝 Upload text script for scene conversion
        Stores text directly in database
        """
        try:
            from bson.objectid import ObjectId
            script_id = str(ObjectId())
            
            # Store in database
            script_doc = {
                "script_id": script_id,
                "script_title": request.script_title,
                "script_content": request.script_content,
                "user_id": request.user_id,
                "uploaded_at": datetime.utcnow(),
                "file_type": "text"
            }
            
            analytics_context.tracker.db["uploaded_scripts"].insert_one(script_doc)
            
            return ScriptResponse(
                success=True,
                script_id=script_id,
                script_title=request.script_title,
                message=f"✅ Script uploaded successfully! {len(request.script_content)} characters."
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    
    
    @app.get("/api/unified/get-scripts")
    async def get_scripts(user_id: str = "default"):
        """
        📚 Get all uploaded scripts for user
        """
        try:
            scripts = list(analytics_context.tracker.db["uploaded_scripts"].find(
                {"user_id": user_id},
                {"_id": 0}
            ).sort("uploaded_at", -1))
            
            return {
                "success": True,
                "count": len(scripts),
                "scripts": scripts
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    
    @app.get("/api/unified/get-script/{script_id}")
    async def get_script(script_id: str, user_id: str = "default"):
        """
        📄 Get specific script by ID
        """
        try:
            script = analytics_context.tracker.db["uploaded_scripts"].find_one(
                {"script_id": script_id, "user_id": user_id},
                {"_id": 0}
            )
            
            if not script:
                raise HTTPException(status_code=404, detail="Script not found")
            
            return {
                "success": True,
                "script": script
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    
    @app.delete("/api/unified/delete-script/{script_id}")
    async def delete_script(script_id: str, user_id: str = "default"):
        """
        🗑️ Delete uploaded script
        """
        try:
            result = analytics_context.tracker.db["uploaded_scripts"].delete_one({
                "script_id": script_id,
                "user_id": user_id
            })
            
            if result.deleted_count == 0:
                raise HTTPException(status_code=404, detail="Script not found")
            
            return {
                "success": True,
                "message": "Script deleted successfully"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    
    # ============================================
    # 6. SCRIPT-TO-SCENE CONVERTER (Single Agent)
    # ============================================
    
    @app.post("/api/unified/script-to-scene", response_model=UnifiedResponse)
    async def script_to_scene(request: ScriptToSceneRequest):
        """
        🎬 Script-to-Scene Converter - "The Director"
        
        Converts uploaded script into detailed scene-by-scene video generation prompts.
        Uses single simplified agent (no planner-critic complexity).
        
        Features:
        - Reads complete script from database for full context
        - Converts each line/beat to video generation prompt
        - 8-second scenes with detailed visual descriptions
        - Veo v3 compliant and safety-focused
        - JSON output for easy integration
        """
        try:
            # Get script from database
            script = analytics_context.tracker.db["uploaded_scripts"].find_one(
                {"script_id": request.script_id, "user_id": request.user_id},
                {"_id": 0}
            )
            
            if not script:
                raise HTTPException(status_code=404, detail="Script not found")
            
            script_content = script.get("script_content", "")
            script_title = script.get("script_title", "Untitled")
            
            if not script_content:
                raise HTTPException(status_code=400, detail="Script content is empty")
            
            # Create agent model
            model_name = create_agent_client_func("agent4")
            
            # Comprehensive instructions (copied from Agent_4_ScriptToScene)
            agent_instructions = f"""{request.user_query}

SCRIPT TITLE: {script_title}

Your task: Break down the provided script into detailed scene-by-scene visual prompts for video generation.

SCENE BREAKDOWN FRAMEWORK:

Priority order:
- User-provided instructions, constraints, or preferences take absolute precedence over defaults.
- Only fall back to the guidelines below when the user prompt is silent on a requirement.

Tone & scope guidelines:
- Communicate in a warm, encouraging, YouTube-savvy voice (think collaborative creative partner).
- Keep discussion anchored to YouTube video production, storytelling, or visual execution. Avoid unrelated topics.

Safety & compliance (Veo v3):
- Strictly avoid disallowed content: sexual content or nudity (including minors), graphic violence or gore, hate or harassment, extremist or terrorist content, self-harm, illegal activities, weapons instruction, scams or malware, personal data collection, medical or legal advice, political persuasion, or any content violating local laws.
- Do not depict or identify real private individuals or request biometric identification. If the user provides a real name, anonymize to a neutral role (e.g., "the host", "the narrator", "the survivor"). Avoid using celebrity likenesses or trademarks without permission.
- Use brand-agnostic, generic descriptions. Do not include copyrighted text or logos; describe them generically instead.
- Keep content safe-for-work, non-graphic, and respectful. Do not depict human remains, death, or graphic injury. For traumatic events or accidents, focus on environment and respectful implication (e.g., cutaways, abstract visuals) instead of explicit depiction.
- If the user requests disallowed or sensitive content, briefly state it's not possible and provide a safe alternative within the filmmaking context.
- Never bypass platform safety filters or provide instructions to do so.

Scene segmentation guidelines:
- Analyze the script's narrative shifts, locations, emotions, or beat changes.
- Create as many scenes as required based on the script (one scene if appropriate, otherwise multiple scenes).
- Maintain a continuous timeline. Each scene must span exactly 8 seconds (no more, no less) from its start to end timestamp.

For each scene provide (within its own Markdown ```json code block):
1. "scene": Clear label with scene number and descriptive title.
2. "duration": Start-end time (e.g., "0:00-0:08") — must equal 8 seconds.
3. "character": Primary speaker or focus (e.g., narrator name, subject).
4. "segments": Nested object covering the full 0-8 second range (e.g., "0-2s", "2-5s", "5-8s") describing visual beats.
5. "sound": Ambience or SFX.
6. "voiceover": Spoken line for the scene.
7. Optional fields (e.g., "camera", "notes") are allowed if helpful.

Shot Types: EWS, WS, MS, MCU, CU, ECU
Angles: Eye level, High, Low, Dutch, Bird's eye, Worm's eye
Movement: Static, Pan, Tilt, Dolly, Tracking, Crane, Handheld, Gimbal
Lighting: Three-point, Natural, High key, Low key, Silhouette
Pacing: Fast (3-8s), Balanced (8-15s), Cinematic (15-30s)

Final Output Requirement:
- Present each scene as a separate ```json code block so it can be copied easily.
- Ensure scene objects are valid JSON (double quotes, comma-separated pairs, etc.).

COMPLETE SCRIPT TO ANALYZE:
{script_content}

Now, create a complete scene-by-scene breakdown covering the entire script. Each scene should be 8 seconds with detailed visual descriptions, camera work, lighting, sound, and voiceover. Output each scene in its own JSON code block."""
            
            # Create and run agent
            agent = Agent(
                name="ScriptToScene Director",
                instructions=agent_instructions,
                model=model_name,
            )
            
            # Execute agent
            result = await Runner.run(
                agent,
                f"Create detailed scene-by-scene video generation prompts for: {script_title}"
            )
            
            # Get result and sanitize
            scene_breakdown = result.final_output if hasattr(result, 'final_output') else ""
            
            if not scene_breakdown or scene_breakdown.strip() == "":
                scene_breakdown = "⚠️ Failed to generate scene breakdown. Please try again."
            
            # Sanitize for Veo v3 compliance
            sanitized_result = _sanitize_for_veo(scene_breakdown)
            
            return UnifiedResponse(
                success=True,
                result=sanitized_result,
                analytics_used=False,  # Script-to-scene doesn't use channel analytics
                channel_info=None,
                video_analytics=None
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Scene conversion failed: {str(e)}")
    
    
    # ============================================
    # 7. SCRIPTWRITER CHATBOT (Gemini-like)
    # ============================================
    
    @app.post("/api/unified/scriptwriter-chat", response_model=UnifiedResponse)
    async def scriptwriter_chatbot(request: ScriptwriterChatRequest):
        """
        💬 Scriptwriter Chatbot - Gemini-like Conversational Agent
        
        Can do:
        - General conversation about scriptwriting
        - Answer questions about YouTube content
        - Generate scripts when asked
        - Give tips and suggestions
        - Understand context from chat history
        
        Example prompts:
        - "Write a script about AI"
        - "How do I make engaging intros?"
        - "What's a good hook for tech videos?"
        """
        try:
            # Generate session_id if not provided
            from bson.objectid import ObjectId
            session_id = request.session_id or str(ObjectId())
            
            # Get channel context if available
            channel_context = ""
            channel_info = None
            if request.channel_id:
                summary = get_channel_summary(request.channel_id, request.user_id)
                if summary:
                    channel_info = summary
                    channel_context = f"""
📊 YOUR CHANNEL ANALYTICS:
- Channel: {summary.get('channel_title', 'N/A')}
- Subscribers: {summary.get('subscriber_count', 'N/A'):,}
- Avg Views: {summary.get('avg_views', 'N/A'):,}
- Top Style: {summary.get('top_style', 'N/A')}
"""
            
            # Get chat history from database
            chat_history = await get_chat_history(
                scriptwriter_chat_collection, 
                session_id, 
                request.user_id, 
                limit=10
            )
            
            # Build chat history context
            history_context = ""
            if chat_history:
                history_context = "\n\nCONVERSATION HISTORY:\n"
                for msg in chat_history:
                    history_context += f"{msg['role'].upper()}: {msg['content']}\n"
            
            # Save user message to database
            await save_chat_message(
                scriptwriter_chat_collection,
                session_id,
                request.user_id,
                "user",
                request.message
            )
            
            # Create chatbot agent with conversational instructions
            model_name = create_agent_client_func("scriptwriter_chat")
            
            agent_instructions = f"""You are "The Storyteller" — a friendly and expert YouTube scriptwriting assistant with Gemini-like conversational abilities.

🎯 YOUR PERSONALITY:
- Warm, helpful, and encouraging
- Expert in YouTube content creation
- Can chat casually or get serious about work
- Remember context from conversation
- Understand when user wants to chat vs. get work done

🔧 YOUR CAPABILITIES:
1. **General Conversation**: Answer questions, give tips, discuss ideas
2. **Script Writing**: Generate full scripts when asked
3. **Advice & Tips**: Share best practices for YouTube success
4. **Analysis**: Review and improve existing scripts
5. **Brainstorming**: Help develop video ideas

📝 WHEN TO WRITE SCRIPTS:
Only write full scripts when user explicitly asks:
- "Write a script about..."
- "Generate a script for..."
- "Create a video script on..."
- "I need a script about..."

Otherwise, engage conversationally and provide guidance.

{channel_context}
{history_context}

🎬 SCRIPTWRITING GUIDELINES (when asked):
- Hook in first 15 seconds
- Clear structure (Hook → Content → CTA)
- Conversational tone (like talking to a friend)
- Natural transitions
- Strong call-to-action
- Aim for 1500-2000 words for 10-minute video

💡 BEST PRACTICES:
- Keep sentences short and punchy
- Use storytelling techniques
- Address viewer directly ("you")
- Create curiosity loops
- End with clear next steps

Current User Message: "{request.message}"

Respond naturally. If they want a script, write it. If they want to chat, chat!"""

            agent = Agent(
                name="Scriptwriter Chatbot",
                instructions=agent_instructions,
                model=model_name,
            )
            
            # Run agent
            result = await Runner.run(agent, request.message)
            response_text = result.final_output if hasattr(result, 'final_output') else str(result)
            
            # Save assistant response to database
            await save_chat_message(
                scriptwriter_chat_collection,
                session_id,
                request.user_id,
                "assistant",
                response_text
            )
            
            return UnifiedResponse(
                success=True,
                result=response_text,
                analytics_used=bool(request.channel_id),
                channel_info=channel_info,
                video_analytics=None
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Chatbot error: {str(e)}")
    
    
    # ============================================
    # 8. SCENE WRITER CHATBOT (Gemini-like)
    # ============================================
    
    @app.post("/api/unified/scene-writer-chat", response_model=UnifiedResponse)
    async def scene_writer_chatbot(request: SceneWriterChatRequest):
        """
        🎬 Scene Writer Chatbot - Gemini-like Conversational Agent
        
        Can do:
        - General conversation about video production
        - Answer questions about scene creation
        - Convert scripts to scenes when asked
        - Give cinematography tips
        - Discuss shot types, angles, lighting
        
        Example prompts:
        - "Convert my script to scenes"
        - "What's a good shot for dramatic moment?"
        - "Explain wide shots vs close-ups"
        - "How do I create tension in scenes?"
        """
        try:
            # Generate session_id if not provided
            from bson.objectid import ObjectId
            session_id = request.session_id or str(ObjectId())
            
            # Build script context if available
            script_context_text = ""
            if request.script_context:
                script_context_text = f"""
📄 UPLOADED SCRIPT CONTEXT:
{request.script_context[:500]}...
(User has a script ready to convert)
"""
            
            # Get chat history from database
            chat_history = await get_chat_history(
                scene_writer_chat_collection, 
                session_id, 
                request.user_id, 
                limit=10
            )
            
            # Build chat history context
            history_context = ""
            if chat_history:
                history_context = "\n\nCONVERSATION HISTORY:\n"
                for msg in chat_history:
                    history_context += f"{msg['role'].upper()}: {msg['content']}\n"
            
            # Save user message to database
            await save_chat_message(
                scene_writer_chat_collection,
                session_id,
                request.user_id,
                "user",
                request.message
            )
            
            # Create chatbot agent
            model_name = create_agent_client_func("scene_writer_chat")
            
            agent_instructions = f"""You are "The Director" — a friendly and expert video scene designer with Gemini-like conversational abilities.

🎯 YOUR PERSONALITY:
- Friendly cinematography expert
- Passionate about visual storytelling
- Can chat casually or dive deep into technical details
- Remember context from conversation
- Understand when user wants advice vs. actual scene breakdowns

🔧 YOUR CAPABILITIES:
1. **General Conversation**: Discuss filmmaking, cinematography, visual storytelling
2. **Scene Generation**: Convert scripts to detailed 8-second scene breakdowns (JSON format)
3. **Technical Advice**: Explain shot types, angles, lighting, camera movements
4. **Creative Guidance**: Help visualize stories cinematically
5. **Best Practices**: Share Veo v3 compliant video generation tips

📝 WHEN TO GENERATE SCENES:
Only create full scene breakdowns when user explicitly asks:
- "Convert to scenes"
- "Generate scene breakdown"
- "Break this into scenes"
- "Create video scenes"

Otherwise, engage conversationally and provide guidance.

{script_context_text}
{history_context}

🎬 SCENE GENERATION GUIDELINES (when asked):
- Each scene exactly 8 seconds
- JSON format with: scene, duration, character, segments, sound, voiceover
- Shot types: EWS, WS, MS, MCU, CU, ECU
- Angles: Eye level, High, Low, Dutch, Bird's eye, Worm's eye
- Movement: Static, Pan, Tilt, Dolly, Tracking, Crane, Handheld
- Lighting: Three-point, Natural, High key, Low key

🛡️ VEO V3 SAFETY:
- No graphic violence or gore
- No sexual content
- Anonymize real individuals
- Safe-for-work content only
- Generic brand descriptions

💡 CINEMATOGRAPHY TIPS:
- Wide shots establish context
- Close-ups show emotion
- Movement adds energy
- Lighting sets mood
- Sound enhances immersion

Current User Message: "{request.message}"

Respond naturally. If they want scenes, generate them. If they want to learn, teach!"""

            agent = Agent(
                name="Scene Writer Chatbot",
                instructions=agent_instructions,
                model=model_name,
            )
            
            # Run agent
            result = await Runner.run(agent, request.message)
            response_text = result.final_output if hasattr(result, 'final_output') else str(result)
            
            # Sanitize for Veo compliance
            sanitized_response = _sanitize_for_veo(response_text)
            
            # Save assistant response to database
            await save_chat_message(
                scene_writer_chat_collection,
                session_id,
                request.user_id,
                "assistant",
                sanitized_response
            )
            
            return UnifiedResponse(
                success=True,
                result=sanitized_response,
                analytics_used=False,
                channel_info=None,
                video_analytics=None
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Chatbot error: {str(e)}")
    
    
    # ============================================
    # 9. CHAT HISTORY MANAGEMENT
    # ============================================
    
    @app.delete("/api/unified/clear-scriptwriter-chat/{session_id}")
    async def clear_scriptwriter_chat(session_id: str, user_id: str = "default"):
        """
        🗑️ Clear Scriptwriter Chat Session
        Manually delete chat history (in addition to 24-hour auto-delete)
        """
        try:
            await clear_chat_session(scriptwriter_chat_collection, session_id, user_id)
            return {"success": True, "message": "Chat history cleared"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    
    @app.delete("/api/unified/clear-scene-writer-chat/{session_id}")
    async def clear_scene_writer_chat(session_id: str, user_id: str = "default"):
        """
        🗑️ Clear Scene Writer Chat Session
        Manually delete chat history (in addition to 24-hour auto-delete)
        """
        try:
            await clear_chat_session(scene_writer_chat_collection, session_id, user_id)
            return {"success": True, "message": "Chat history cleared"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    
    @app.get("/api/unified/get-scriptwriter-chat/{session_id}")
    async def get_scriptwriter_chat(session_id: str, user_id: str = "default", limit: int = 50):
        """
        📜 Get Scriptwriter Chat History
        Retrieve chat messages for a session
        """
        try:
            messages = await get_chat_history(scriptwriter_chat_collection, session_id, user_id, limit)
            return {
                "success": True,
                "session_id": session_id,
                "message_count": len(messages),
                "messages": messages
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    
    @app.get("/api/unified/get-scene-writer-chat/{session_id}")
    async def get_scene_writer_chat(session_id: str, user_id: str = "default", limit: int = 50):
        """
        📜 Get Scene Writer Chat History
        Retrieve chat messages for a session
        """
        try:
            messages = await get_chat_history(scene_writer_chat_collection, session_id, user_id, limit)
            return {
                "success": True,
                "session_id": session_id,
                "message_count": len(messages),
                "messages": messages
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    
    # ============================================
    # 10. ANALYTICS STATUS
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
