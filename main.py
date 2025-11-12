import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

import certifi
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId

from openai import AsyncOpenAI
from openai.types.responses import ResponseTextDeltaEvent
from agents import (
    Agent,
    Runner,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
)
from all_youtube_tools.youtube_tools import YOUTUBE_TOOLS
from per_channel_analytics_Agents.channel_analytics_tracker import ChannelAnalyticsTracker
from per_channel_analytics_Agents.unified_analytics_agents import register_unified_analytics_routes

# Load environment variables
load_dotenv()

# MongoDB configuration for saved responses
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv("MONGODB_DB", "youtube_ops")
SAVED_RESPONSES_COLLECTION = os.getenv("SAVED_RESPONSES_COLLECTION", "saved_responses")
MONGODB_CA_FILE = os.getenv("MONGODB_CA_FILE")

mongo_client: Optional[MongoClient] = None
saved_responses_collection = None

logger = logging.getLogger("command_center.saved_responses")
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
        "base_url": os.getenv("GEMINI_BASE_URL"),
        "api_key": os.getenv("GEMINI2_API_KEY"),
        "model": os.getenv("GEMINI2_MODEL_NAME"),
    },
    "agent3": {
        "base_url": os.getenv("GEMINI_BASE_URL"),
        "api_key": os.getenv("GEMINI2_API_KEY"),
        "model": os.getenv("GEMINI2_MODEL_NAME"),
    },
    "agent4": {
        "base_url": os.getenv("GEMINI_BASE_URL"),
        "api_key": os.getenv("GEMINI2_API_KEY"),
        "model": os.getenv("GEMINI2_MODEL_NAME"),
    },
    "agent5": {
        "base_url": os.getenv("GEMINI_BASE_URL"),
        "api_key": os.getenv("GEMINI2_API_KEY"),
        "model": os.getenv("GEMINI2_MODEL_NAME"),
    },
    "agent6": {
        "base_url": os.getenv("GEMINI_BASE_URL"),
        "api_key": os.getenv("GEMINI_API_KEY"),
        "model": os.getenv("GEMINI_MODEL_NAME"),
    },
    # Added chatbot configs used by unified_analytics_agents
    "scriptwriter_chat": {
        "base_url": os.getenv("GEMINI_BASE_URL"),
        "api_key": os.getenv("GEMINI_API_KEY"),
        "model": os.getenv("GEMINI_MODEL_NAME"),
    },
    "scene_writer_chat": {
        "base_url": os.getenv("GEMINI_BASE_URL"),
        "api_key": os.getenv("GEMINI_API_KEY"),
        "model": os.getenv("GEMINI_MODEL_NAME"),
    },
}


# Note: Agent request/response models are now defined in their respective agent files
# Only keeping shared models here that are used by multiple agents or the API


class SavedResponseHistoryEntry(BaseModel):
    content: str
    updated_at: Optional[str] = None


class SavedResponseSummary(BaseModel):
    id: str
    title: str
    agent_id: int
    agent_name: str
    agent_codename: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SavedResponseDetail(SavedResponseSummary):
    content: str


class SavedResponseCreate(BaseModel):
    title: str
    content: str
    agent_id: int
    agent_name: str
    agent_codename: str


class SavedResponseUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


# Initialize MongoDB client and saved responses collection
def _ensure_saved_responses_collection():
    """Ensure MongoDB client and saved responses collection are initialized.
    Uses env vars: MONGODB_URI, MONGODB_DB, SAVED_RESPONSES_COLLECTION, MONGODB_CA_FILE.
    Sets globals: mongo_client, saved_responses_collection.
    """
    global mongo_client, saved_responses_collection
    if saved_responses_collection is not None and mongo_client is not None:
        return
    if not MONGODB_URI:
        raise HTTPException(status_code=500, detail="MONGODB_URI not set")

    try:
        ca_file = MONGODB_CA_FILE or certifi.where()
        mongo_client = MongoClient(MONGODB_URI, tlsCAFile=ca_file)
        db = mongo_client[MONGODB_DB]
        saved_responses_collection = db[SAVED_RESPONSES_COLLECTION]
        # simple ping to ensure connection works
        mongo_client.admin.command("ping")
        logger.info(
            f"MongoDB connected. DB='{MONGODB_DB}', Collection='{SAVED_RESPONSES_COLLECTION}'"
        )
    except Exception as e:
        # Reset globals on failure
        mongo_client = None
        saved_responses_collection = None
        raise HTTPException(status_code=500, detail=f"Failed to init MongoDB: {str(e)}")


# Lifespan context manager
@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup
    print("🚀 Starting YouTube Automation Agent API...")
    if MONGODB_URI:
        try:
            _ensure_saved_responses_collection()
        except HTTPException:
            pass
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


# Import RL integration system
from agents_ReinforcementLearning.rl_integration import rl_registry, get_rl_system_status

# Import and register all agent routes
from AllAgents.Agent_1_ChannelAuditor.Agent_1_ChannelAuditor import register_agent1_routes
from AllAgents.Agent_2_TitleAuditor.Agent_2_TitleAuditor import register_agent2_routes
from AllAgents.Agent_3_ScriptGenerator.Agent_3_ScriptGenerator import register_agent3_routes
from AllAgents.Agent_4_ScriptToScene.Agent_4_ScriptToScene import register_agent4_routes
from AllAgents.Agent_5_generateIdeas.Agent_5_generateIdeas import register_agent5_routes
from AllAgents.Agent_6_roadmap.Agent_6_roadmap import register_agent6_routes
from AllAgents.fifty_videos_fetcher.fiftyVideosAgent import register_fifty_videos_routes

# Register all agent routes with the app
# register_agent1_routes(app, create_agent_client, YOUTUBE_TOOLS)
# register_agent2_routes(app, create_agent_client, YOUTUBE_TOOLS)
# register_agent3_routes(app, create_agent_client, YOUTUBE_TOOLS)
# register_agent4_routes(app, create_agent_client, YOUTUBE_TOOLS)
# register_agent5_routes(app, create_agent_client, YOUTUBE_TOOLS)
# register_agent6_routes(app, create_agent_client, YOUTUBE_TOOLS)
# register_fifty_videos_routes(app, create_agent_client, YOUTUBE_TOOLS)

# Register RL System API endpoints
from agents_ReinforcementLearning.api_rl_endpoints import router as rl_router
app.include_router(rl_router)

# Register Unified Analytics-Aware Agent Routes
register_unified_analytics_routes(app, create_agent_client, YOUTUBE_TOOLS)


# Streaming request model
class StreamRunRequest(BaseModel):
    agent_key: str  # e.g., "scriptwriter_chat", "scene_writer_chat", or "agent3"/"agent4"
    prompt: str
    agent_name: Optional[str] = "stream_agent"
    instructions: Optional[str] = "You are a helpful assistant."


@app.post("/api/stream/run")
async def stream_run(req: StreamRunRequest):
    """Run an agent and stream incremental deltas as Server-Sent Events (SSE)."""
    try:
        model_name = create_agent_client(req.agent_key)
        agent = Agent(
            name=req.agent_name or "stream_agent",
            instructions=req.instructions or "You are a helpful assistant.",
            model=model_name,
        )

        async def event_generator():
            try:
                result = Runner.run_streamed(agent, input=req.prompt)
                # Optional start event
                yield "event: start\n" + "data: {}\n\n"
                async for event in result.stream_events():
                    if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                        text = event.data.delta or ""
                        if text:
                            yield f"data: {text}\n\n"
                # Optional end event
                yield "event: end\n" + "data: {}\n\n"
            except Exception as e:
                # Stream an error event
                err = str(e).replace("\n", " ")
                yield f"event: error\ndata: {err}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Streaming failed: {str(e)}")


# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "YouTube Automation AI Agents API",
        "version": "1.0.0",
        "agents": {
            "agent1": "Channel Auditor - Deep channel audit to pick hot channels [RL Enhanced]",
            "agent2": "Title Auditor - Analyze titles, thumbnails, keywords, hooks [RL Enhanced]", 
            "agent3": "Script Writer - Generate scripts from audit data [RL Enhanced]",
            "agent4": "Script to Prompts - Convert scripts to scene prompts [RL Enhanced]",
            "agent5": "Ideas Generator - Generate 3 winning titles & thumbnails [RL Enhanced]",
            "agent6": "Roadmap Generator - 30-video roadmap with titles & thumbnails [RL Enhanced]",
            "fifty_videos": "50 Videos Fetcher - Get latest 50 video links from a channel [RL Enhanced]"
        },
        "rl_system": {
            "status": "✅ ACTIVE - All agents enhanced with reinforcement learning",
            "features": [
                "Automatic learning from each interaction",
                "Cross-agent knowledge sharing",
                "Performance improvement over time", 
                "Cloud-based memory hierarchy (STM/LTM/Central)"
            ],
            "memory_systems": {
                "STM": "Redis Cloud - Fast temporary learning",
                "LTM": "MongoDB Atlas - Persistent pattern storage", 
                "Central": "MongoDB Atlas - Global collective intelligence"
            }
        },
        "endpoints": {
            "POST /api/agent1/audit-channel": "Channel auditing [RL Enhanced]",
            "POST /api/agent2/audit-titles": "Title & thumbnail analysis [RL Enhanced]",
            "POST /api/agent3/generate-script": "Script generation [RL Enhanced]",
            "POST /api/agent4/script-to-prompts": "Script to visual prompts [RL Enhanced]",
            "POST /api/agent5/generate-ideas": "Title & thumbnail ideas [RL Enhanced]",
            "POST /api/agent6/generate-roadmap": "Content roadmap generation [RL Enhanced]",
            "POST /api/fifty-videos/fetch-links": "Fetch 50 video links from channel [RL Enhanced]"
        },
        "rl_endpoints": {
            "GET /api/rl/status": "Overall RL system status and learning progress",
            "GET /api/rl/global-insights": "Collective intelligence insights",
            "POST /api/rl/sync": "Manual agent synchronization trigger", 
            "GET /api/rl/agents/{agent}/insights": "Individual agent learning progress"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "YouTube Automation Agents API"}


# RL System Endpoints
@app.get("/api/rl/status")
async def get_rl_status():
    """Get comprehensive RL system status and learning progress"""
    return await get_rl_system_status()


@app.post("/api/rl/sync")
async def sync_rl_agents():
    """Manually trigger RL agent synchronization with central memory"""
    try:
        sync_results = await rl_registry.sync_all_agents()
        return {
            "success": True,
            "sync_results": sync_results,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RL sync failed: {str(e)}")


@app.get("/api/rl/agents/{agent_name}/insights")
async def get_agent_insights(agent_name: str):
    """Get learning insights for a specific agent"""
    agent = rl_registry.get_agent(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
    
    return await agent.get_learning_insights()


@app.get("/api/rl/global-insights")
async def get_global_rl_insights():
    """Get global insights from central memory"""
    return await rl_registry.get_global_insights()


# Channel Analytics & Video Ideas Endpoints
analytics_tracker = ChannelAnalyticsTracker()


class ChannelSubmitRequest(BaseModel):
    channel_url: str
    user_id: Optional[str] = "default"


class VideoIdeaRequest(BaseModel):
    channel_id: str
    user_id: Optional[str] = "default"


@app.post("/api/channel/track")
async def track_channel(request: ChannelSubmitRequest):
    """
    Save YouTube channel for tracking and analytics
    
    Example:
    {
        "channel_url": "https://www.youtube.com/@MrBeast",
        "user_id": "user123"
    }
    """
    try:
        result = await analytics_tracker.save_channel(
            channel_url=request.channel_url,
            user_id=request.user_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track channel: {str(e)}")


@app.post("/api/channel/video-ideas")
async def generate_video_ideas(request: VideoIdeaRequest):
    """
    Generate AI-powered video ideas based on channel analytics
    
    Example:
    {
        "channel_id": "UCX6OQ3DkcsbYNE6H8uQQuVA",
        "user_id": "user123"
    }
    """
    try:
        result = await analytics_tracker.generate_video_idea(
            channel_id=request.channel_id,
            user_id=request.user_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate ideas: {str(e)}")


@app.get("/api/channel/tracked")
async def get_tracked_channels(user_id: str = "default"):
    """Get all tracked channels for a user"""
    try:
        channels = await analytics_tracker.get_tracked_channels(user_id=user_id)
        return {
            "status": "success",
            "count": len(channels),
            "channels": channels
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch channels: {str(e)}")


@app.delete("/api/channel/tracked/{channel_id}")
async def delete_tracked_channel(channel_id: str, user_id: str = "default"):
    """Delete a tracked channel and its analytics data
    
    Note: channel_id parameter is actually the MongoDB _id, not the YouTube channel ID
    """
    try:
        # Get MongoDB collection
        collection = analytics_tracker.channels_collection
        
        # First, get the channel to retrieve the actual YouTube channel_id
        try:
            channel_doc = collection.find_one({
                "_id": ObjectId(channel_id),
                "user_id": user_id
            })
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid channel ID format")
        
        if not channel_doc:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        youtube_channel_id = channel_doc.get("channel_id")
        
        # Delete the channel document by _id
        result = collection.delete_one({
            "_id": ObjectId(channel_id),
            "user_id": user_id
        })
        
        # Also delete analytics data using the YouTube channel ID
        if youtube_channel_id:
            analytics_collection = analytics_tracker.analytics_collection
            analytics_collection.delete_many({
                "channel_id": youtube_channel_id,
                "user_id": user_id
            })
        
        return {
            "status": "success",
            "message": f"Channel and its analytics deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete channel: {str(e)}")


@app.post("/api/channel/refresh-analytics/{channel_id}")
async def refresh_channel_analytics(channel_id: str, user_id: str = "default"):
    """Manually refresh analytics for a channel"""
    try:
        analytics = await analytics_tracker.fetch_analytics(
            channel_id=channel_id,
            user_id=user_id
        )
        
        # Remove MongoDB-specific fields for JSON response
        analytics.pop('_id', None)
        if 'timestamp' in analytics:
            analytics['timestamp'] = analytics['timestamp'].isoformat()
        
        return {
            "status": "success",
            "analytics": analytics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh analytics: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
