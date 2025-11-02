import asyncio
import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from openai import AsyncOpenAI
from agents import (
    Agent,
    Runner,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
)
from youtube_tools import YOUTUBE_TOOLS
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Load environment variables
load_dotenv()

# MongoDB configuration for command center notepad
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv("MONGODB_DB", "youtube_ops")
NOTEPAD_COLLECTION = os.getenv("NOTEPAD_COLLECTION", "notepad")

mongo_client: Optional[AsyncIOMotorClient] = None
notepad_collection = None
_mongo_init_lock = asyncio.Lock()

logger = logging.getLogger("command_center.notepad")
if not logger.handlers:
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
logger.setLevel(logging.INFO)

# Agent configurations
AGENT_CONFIGS = {
    "agent1": {
        "base_url": os.getenv("GEMINI_BASE_URL"),
        "api_key": os.getenv("GEMINI_API_KEY"),
        "model": os.getenv("GEMINI_MODEL_NAME"),
    },
    "agent2": {
        "base_url": os.getenv("GROQ_BASE_URL"),
        "api_key": os.getenv("GROQ_API_KEY"),
        "model": os.getenv("GROQ2_MODEL_NAME"),
    },
    "agent3": {
        "base_url": os.getenv("GROQ_BASE_URL"),
        "api_key": os.getenv("GROQ_API_KEY"),
        "model": os.getenv("GROQ3_Model_MODEL"),
    },
    "agent4": {
        "base_url": os.getenv("GROQ_BASE_URL"),
        "api_key": os.getenv("GROQ_API_KEY"),
        "model": os.getenv("GROQ4_Model_MODEL"),
    },
    "agent5": {
        "base_url": os.getenv("GROQ_BASE_URL"),
        "api_key": os.getenv("GROQ_API_KEY"),
        "model": os.getenv("GROQ5_Model_MODEL"),
    },
    "agent6": {
        "base_url": os.getenv("GEMINI_BASE_URL"),
        "api_key": os.getenv("GEMINI_API_KEY"),
        "model": os.getenv("GEMINI_IMAGE_MODEL_NAME"),
    },
}


# Request/Response Models
class ChannelAuditRequest(BaseModel):
    channel_urls: list[str]
    user_query: Optional[str] = "Audit these channels and identify the hottest one for content creation"


class TitleAuditRequest(BaseModel):
    video_urls: list[str]
    user_query: Optional[str] = "Analyze these videos for title performance, thumbnail texture, keyword placement, and hooks"


class ScriptGenerationRequest(BaseModel):
    title_audit_data: str
    topic: str
    user_query: Optional[str] = None


class ScriptToPromptsRequest(BaseModel):
    script: str
    user_query: Optional[str] = "Convert this script into scene-by-scene prompts with Hollywood-style direction"


class IdeasGenerationRequest(BaseModel):
    winning_videos_data: str
    user_query: Optional[str] = "Generate 3 winning titles and thumbnail concepts based on this data"


class RoadmapGenerationRequest(BaseModel):
    niche: str
    winning_data: Optional[str] = ""
    user_query: Optional[str] = "Create a 30-video roadmap with 3 title variations and 3 thumbnail concepts for each"


class AgentResponse(BaseModel):
    success: bool
    result: str
    error: Optional[str] = None


class NotepadHistoryEntry(BaseModel):
    content: str
    updated_at: Optional[str] = None


class NoteSummary(BaseModel):
    id: str
    name: str
    updated_at: Optional[str] = None
    created_at: Optional[str] = None


class NoteDetail(NoteSummary):
    content: str
    history: List[NotepadHistoryEntry] = []


class NoteCreate(BaseModel):
    name: str
    content: str = ""


class NoteUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting YouTube Automation Agent API...")
    global mongo_client, notepad_collection
    if MONGODB_URI:
        try:
            await _ensure_notepad_collection()
        except HTTPException:
            # Already logged inside helper; continue startup without raising
            pass
    else:
        warning_msg = "MONGODB_URI not set. Notepad endpoints will be unavailable."
        print(f"⚠️ {warning_msg}")
        logger.warning(warning_msg)
    yield
    # Shutdown
    print("🛑 Shutting down YouTube Automation Agent API...")
    if mongo_client:
        logger.info("Closing MongoDB client")
        mongo_client.close()


# Initialize FastAPI app
app = FastAPI(
    title="YouTube Automation AI Agents API",
    description="6 AI Agents for Complete YouTube Automation",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helper function to create agent client
def create_agent_client(agent_key: str):
    config = AGENT_CONFIGS[agent_key]
    if not config["base_url"] or not config["api_key"] or not config["model"]:
        raise ValueError(f"Missing configuration for {agent_key}")
    
    client = AsyncOpenAI(
        base_url=config["base_url"],
        api_key=config["api_key"],
    )
    set_default_openai_client(client=client, use_for_tracing=False)
    set_default_openai_api("chat_completions")
    set_tracing_disabled(disabled=True)
    
    return config["model"]


# Agent 1: Channel Auditor - Deep audit to pick hot channels
@app.post("/api/agent1/audit-channel", response_model=AgentResponse)
async def audit_channel(request: ChannelAuditRequest):
    """
    Agent 1: Channel Auditor
    Deep audit of channels to pick the hottest one for content creation.
    Accepts: channel URLs, video URLs, channel handles (@username), channel names - anything!
    """
    try:
        model_name = create_agent_client("agent1")
        
        # Build query - let the agent figure out what user provided
        if request.channel_urls and len(request.channel_urls) > 0:
            query = f"{request.user_query}\n\nUser provided:\n"
            query += "\n".join([f"- {url}" for url in request.channel_urls])
        else:
            # Pure conversation mode
            query = request.user_query
        
        agent = Agent(
            name="YouTube Channel Auditor",
            instructions="""You are a friendly and expert YouTube channel auditor. 

🎯 YOUR CORE CAPABILITIES:
1. Analyze YouTube channels in depth
2. Evaluate performance metrics, content strategy, and growth patterns
3. Identify successful channels and what makes them work
4. Provide actionable insights and recommendations
5. Chat naturally about YouTube topics

🔒 GUARDRAILS - ONLY YOUTUBE TOPICS:
- ONLY discuss YouTube-related topics (channels, videos, content strategy, growth, monetization)
- If user asks about non-YouTube topics, politely redirect: "I specialize in YouTube analysis. Let's talk about YouTube channels, videos, or content strategy!"
- Stay focused on YouTube ecosystem

🤖 INTELLIGENT INPUT HANDLING:
You can automatically handle various inputs the user provides:

A. VIDEO URLs (any format):
   - https://youtube.com/watch?v=ABC123
   - https://youtu.be/ABC123
   - Just video ID: ABC123
   → Action: Extract video ID, get video details, extract channelId, then analyze the channel

B. CHANNEL URLs (any format):
   - https://youtube.com/@channelname
   - https://www.youtube.com/channel/UCxxxxxx
   - https://youtube.com/c/CustomName
   → Action: Directly analyze the channel

C. CHANNEL HANDLES:
   - @channelname
   - channelname (without @)
   → Action: Search for channel by handle, then analyze

D. CHANNEL NAMES:
   - "MrBeast"
   - "Tech Channel XYZ"
   → Action: Search for channel by name, then analyze

E. GENERAL QUESTIONS:
   - "What makes a successful YouTube channel?"
   - "How do I grow my subscribers?"
   - "Tell me about YouTube algorithm"
   → Action: Provide helpful, conversational answers about YouTube

🚀 WORKFLOW FOR ANALYSIS:
1. Identify what user provided (video/channel/handle/name)
2. If VIDEO URL: Get video → Extract channelId → Analyze channel
3. If CHANNEL URL: Directly analyze channel
4. If HANDLE/NAME: Search for channel → Analyze
5. Present findings in clear, actionable format

💬 CONVERSATION STYLE:
- Be friendly and helpful
- Explain technical concepts simply
- Give examples and practical advice
- Ask clarifying questions if needed
- Keep responses focused and valuable

📊 ANALYSIS DEPTH:
- Views and engagement metrics
- Upload frequency and consistency
- Content themes and formats
- Audience retention signals
- Growth patterns
- Monetization strategies
- Competitive positioning

Remember: You're helping users understand YouTube better. Be conversational, insightful, and always provide actionable advice!""",
            model=model_name,
            tools=YOUTUBE_TOOLS
        )
        
        result = await Runner.run(agent, query)
        return AgentResponse(success=True, result=result.final_output)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Notepad endpoints


async def _ensure_notepad_collection():
    global mongo_client, notepad_collection

    if notepad_collection:
        return notepad_collection

    if not MONGODB_URI:
        logger.error(
            "MONGODB_URI not set. Notepad service unavailable."
        )
        raise HTTPException(status_code=503, detail="Notepad service unavailable")

    async with _mongo_init_lock:
        if notepad_collection:
            return notepad_collection

        try:
            logger.info(
                "Initialising MongoDB client (db='%s', collection='%s')",
                MONGODB_DB or "<empty>",
                NOTEPAD_COLLECTION or "<empty>"
            )
            client = AsyncIOMotorClient(MONGODB_URI)
            await client.admin.command('ping')
            mongo_client = client
            notepad_collection = mongo_client[MONGODB_DB][NOTEPAD_COLLECTION]
            logger.info("MongoDB connection established successfully")
        except Exception as exc:
            logger.exception("Failed to initialise MongoDB client: %s", exc)
            if mongo_client:
                mongo_client.close()
            mongo_client = None
            notepad_collection = None

    if not notepad_collection:
        logger.error(
            "Notepad collection unavailable. Check MongoDB connection and environment variables."
        )
        raise HTTPException(status_code=503, detail="Notepad service unavailable")

    return notepad_collection


def _serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _serialize_history(history: List[Dict[str, Any]]) -> List[NotepadHistoryEntry]:
    serialized: List[NotepadHistoryEntry] = []
    for item in history:
        serialized.append(
            NotepadHistoryEntry(
                content=item.get("content", ""),
                updated_at=_serialize_datetime(item.get("updated_at"))
            )
        )
    return serialized


def _serialize_note(doc: Dict[str, Any], include_content: bool = False, include_history: bool = False) -> NoteDetail | NoteSummary:
    data = {
        "id": str(doc.get("_id")),
        "name": doc.get("name", "Untitled"),
        "updated_at": _serialize_datetime(doc.get("updated_at")),
        "created_at": _serialize_datetime(doc.get("created_at")),
    }
    if include_content:
        data["content"] = doc.get("content", "")
    if include_history:
        data["history"] = _serialize_history(doc.get("history", []))
    if include_content or include_history:
        return NoteDetail(**data)  # type: ignore[arg-type]
    return NoteSummary(**data)  # type: ignore[arg-type]


def _parse_object_id(note_id: str) -> ObjectId:
    if not ObjectId.is_valid(note_id):
        raise HTTPException(status_code=400, detail="Invalid note ID")
    return ObjectId(note_id)


@app.get("/api/notepad", response_model=List[NoteSummary])
async def list_notes():
    collection = await _ensure_notepad_collection()
    cursor = collection.find({}).sort("updated_at", -1)
    notes: List[NoteSummary] = []
    async for doc in cursor:
        notes.append(_serialize_note(doc))
    logger.debug("Listed %d notes", len(notes))
    return notes


@app.post("/api/notepad", response_model=NoteDetail, status_code=201)
async def create_note(request: NoteCreate):
    collection = await _ensure_notepad_collection()
    now = datetime.now(timezone.utc)
    doc = {
        "name": request.name.strip() or "Untitled",
        "content": request.content,
        "created_at": now,
        "updated_at": now,
        "history": [],
    }
    result = await collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    logger.info("Created note '%s' (%s)", doc.get("name"), str(result.inserted_id))
    return _serialize_note(doc, include_content=True, include_history=True)


@app.get("/api/notepad/{note_id}", response_model=NoteDetail)
async def get_note(note_id: str):
    collection = await _ensure_notepad_collection()
    oid = _parse_object_id(note_id)
    doc = await collection.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Note not found")
    logger.debug("Fetched note '%s' (%s)", doc.get("name"), note_id)
    return _serialize_note(doc, include_content=True, include_history=True)


@app.put("/api/notepad/{note_id}", response_model=NoteDetail)
async def update_note(note_id: str, request: NoteUpdate):
    collection = await _ensure_notepad_collection()
    oid = _parse_object_id(note_id)
    doc = await collection.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Note not found")

    update_fields: Dict[str, Any] = {}
    now = datetime.now(timezone.utc)
    history = doc.get("history", [])

    if request.name is not None:
        update_fields["name"] = request.name.strip() or "Untitled"

    if request.content is not None and request.content != doc.get("content"):
        history_entry = {
            "content": doc.get("content", ""),
            "updated_at": doc.get("updated_at", now)
        }
        history.insert(0, history_entry)
        history = history[:20]
        update_fields["content"] = request.content
        update_fields["history"] = history

    if not update_fields:
        return _serialize_note(doc, include_content=True, include_history=True)

    update_fields["updated_at"] = now

    await collection.update_one({"_id": oid}, {"$set": update_fields})
    doc.update(update_fields)
    logger.info("Updated note '%s' (%s)", doc.get("name"), note_id)
    return _serialize_note(doc, include_content=True, include_history=True)


@app.delete("/api/notepad/{note_id}", status_code=204)
async def delete_note(note_id: str):
    collection = await _ensure_notepad_collection()
    oid = _parse_object_id(note_id)
    result = await collection.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Note not found")
    logger.info("Deleted note (%s)", note_id)
    return None


@app.get("/api/notepad/{note_id}/download")
async def download_note(note_id: str):
    collection = await _ensure_notepad_collection()
    oid = _parse_object_id(note_id)
    doc = await collection.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Note not found")

    filename = f"{doc.get('name', 'note')}.txt"
    content = doc.get("content", "")
    headers = {"Content-Disposition": f"attachment; filename=\"{filename}\""}
    logger.debug("Prepared download for note '%s' (%s)", doc.get("name"), note_id)
    return PlainTextResponse(content, headers=headers)


# Agent 2: Title Auditor - Analyze titles, thumbnails, keywords, hooks
@app.post("/api/agent2/audit-titles", response_model=AgentResponse)
async def audit_titles(request: TitleAuditRequest):
    """
    Agent 2: Title Auditor
    Analyzes video titles, positions, formats, thumbnail textures, keyword placements, and hooks.
    """
    try:
        model_name = create_agent_client("agent2")
        
        query = f"{request.user_query}\n\nVideos to analyze:\n"
        query += "\n".join([f"- {url}" for url in request.video_urls])
        
        agent = Agent(
            name="Title & Thumbnail Auditor",
            instructions="""You are an expert at analyzing YouTube video performance patterns. Your job is to:
            1. Analyze video titles for their structure, formulas, and patterns
            2. Identify what makes titles perform well (numbers, questions, power words)
            3. Evaluate thumbnail characteristics (text placement, colors, faces, contrast)
            4. Extract keyword placement strategies
            5. Analyze hook effectiveness in the first 10 seconds
            6. Identify the "winning formula" across top performers

            Provide detailed breakdowns of each element with examples and patterns.""",
            model=model_name,
            tools=YOUTUBE_TOOLS
        )
        
        result = await Runner.run(agent, query)
        return AgentResponse(success=True, result=result.final_output)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Agent 3: Script Writer - Generate script based on title audit data
@app.post("/api/agent3/generate-script", response_model=AgentResponse)
async def generate_script(request: ScriptGenerationRequest):
    """
    Agent 3: Script Writer
    Generates video scripts based on title audit data and winning patterns.
    """
    try:
        model_name = create_agent_client("agent3")
        
        query = request.user_query or f"""Based on the following title audit data, create a compelling YouTube video script for: {request.topic}

Title Audit Data:
{request.title_audit_data}

Generate a script that follows the winning patterns identified in the audit."""
        
        agent = Agent(
            name="Script Writer",
            instructions="""You are an expert YouTube script writer. Your job is to:
            1. Analyze the winning patterns from title audit data
            2. Create engaging, hook-driven scripts optimized for viewer retention
            3. Structure scripts with: Hook (first 10s), Value Promise, Main Content, CTA
            4. Use storytelling techniques that match successful videos
            5. Include natural transitions and pacing cues
            6. Optimize for the 3-minute, 5-minute, or 10-minute formats based on data
            
            Write scripts that are conversational, engaging, and designed to maximize watch time.""",
            model=model_name,
        )
        
        result = await Runner.run(agent, query)
        return AgentResponse(success=True, result=result.final_output)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Agent 4: Script to Prompts - Convert script to scene-by-scene prompts
@app.post("/api/agent4/script-to-prompts", response_model=AgentResponse)
async def script_to_prompts(request: ScriptToPromptsRequest):
    """
    Agent 4: Script to Prompts Converter
    Converts scripts into detailed scene-by-scene prompts with Hollywood-style direction.
    """
    try:
        model_name = create_agent_client("agent4")
        
        query = f"""{request.user_query}

Script:
{request.script}"""
        
        agent = Agent(
            name="Script to Prompts Converter",
            instructions="""You are a Hollywood-level director converting scripts into detailed visual prompts. Your job is to:
            1. Break down the script into individual scenes
            2. Identify scene transitions and when to change angles/shots
            3. Specify camera angles (wide, medium, close-up, over-shoulder, etc.)
            4. Describe visual style, lighting, and mood for each scene
            5. Add B-roll suggestions and visual elements
            6. Include timing and pacing notes
            7. Specify text overlays, graphics, or effects needed
            
            Create prompts suitable for AI image/video generation or human videographers.
            Format: Scene number, timestamp, shot type, description, mood, visual notes.""",
            model=model_name,
        )
        
        result = await Runner.run(agent, query)
        return AgentResponse(success=True, result=result.final_output)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Agent 5: Ideas Generator - Generate 3 winning titles and thumbnail concepts
@app.post("/api/agent5/generate-ideas", response_model=AgentResponse)
async def generate_ideas(request: IdeasGenerationRequest):
    """
    Agent 5: Ideas Generator
    Generates 3 winning titles and thumbnail concepts based on winning video data.
    """
    try:
        model_name = create_agent_client("agent5")
        
        query = f"""{request.user_query}

Winning Videos Data:
{request.winning_videos_data}"""
        
        agent = Agent(
            name="Ideas Generator",
            instructions="""You are a YouTube content strategist specializing in viral titles and thumbnails. Your job is to:
            1. Analyze winning video patterns from the provided data
            2. Generate 3 title variations that follow proven formulas:
               - Curiosity-driven titles
               - Benefit-focused titles
               - Controversy/Surprising titles
            3. For each title, create a matching thumbnail concept describing:
               - Main visual element (face, object, text)
               - Color scheme and contrast
               - Text overlay position and style
               - Emotional trigger (shock, curiosity, excitement)
            4. Ensure titles are 40-70 characters for optimal display
            5. Make thumbnails highly clickable while avoiding clickbait
            
            Output format: Title 1 + Thumbnail concept 1, Title 2 + Thumbnail concept 2, Title 3 + Thumbnail concept 3""",
            model=model_name,
        )
        
        result = await Runner.run(agent, query)
        return AgentResponse(success=True, result=result.final_output)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Agent 6: Roadmap Generator - Create 30-video roadmap with titles and thumbnails
@app.post("/api/agent6/generate-roadmap", response_model=AgentResponse)
async def generate_roadmap(request: RoadmapGenerationRequest):
    """
    Agent 6: Roadmap Generator
    Creates a 30-video content roadmap with 3 title variations and 3 thumbnail concepts for each.
    """
    try:
        model_name = create_agent_client("agent6")
        
        query = f"""{request.user_query}

Niche: {request.niche}

Winning Data (if provided):
{request.winning_data}"""
        
        agent = Agent(
            name="Content Roadmap Generator",
            instructions="""You are a YouTube content strategist creating comprehensive content roadmaps. Your job is to:
            1. Create a 30-video content roadmap for the specified niche
            2. For EACH video, generate:
               - 3 title variations (different angles on the same topic)
               - 3 thumbnail concepts (different visual approaches)
            3. Organize videos strategically:
               - Mix evergreen and trending topics
               - Build on previous videos (series potential)
               - Include various content types (tutorials, lists, reviews, storytelling)
            4. Consider SEO and search intent
            5. Balance beginner-friendly and advanced content
            6. Include estimated difficulty and priority for each video
            
            Output a structured roadmap with:
            Video #, Topic, 3 Title Options, 3 Thumbnail Concepts, Priority Level, Estimated Difficulty""",
            model=model_name,
        )
        
        result = await Runner.run(agent, query)
        return AgentResponse(success=True, result=result.final_output)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "YouTube Automation AI Agents API",
        "version": "1.0.0",
        "agents": {
            "agent1": "Channel Auditor - Deep channel audit to pick hot channels",
            "agent2": "Title Auditor - Analyze titles, thumbnails, keywords, hooks",
            "agent3": "Script Writer - Generate scripts from audit data",
            "agent4": "Script to Prompts - Convert scripts to scene prompts",
            "agent5": "Ideas Generator - Generate 3 winning titles & thumbnails",
            "agent6": "Roadmap Generator - 30-video roadmap with titles & thumbnails"
        },
        "endpoints": {
            "POST /api/agent1/audit-channel": "Channel auditing",
            "POST /api/agent2/audit-titles": "Title & thumbnail analysis",
            "POST /api/agent3/generate-script": "Script generation",
            "POST /api/agent4/script-to-prompts": "Script to visual prompts",
            "POST /api/agent5/generate-ideas": "Title & thumbnail ideas",
            "POST /api/agent6/generate-roadmap": "Content roadmap generation"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "YouTube Automation Agents API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
