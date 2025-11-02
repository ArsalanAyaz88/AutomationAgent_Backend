import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

import certifi
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId

from openai import AsyncOpenAI
from agents import (
    Agent,
    Runner,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
)
from youtube_tools import YOUTUBE_TOOLS
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


# Import and register all agent routes
from AllAgents.Agent_1_ChannelAuditor.Agent_1_ChannelAuditor import register_agent1_routes
from AllAgents.Agent_2_TitleAuditor.Agent_2_TitleAuditor import register_agent2_routes
from AllAgents.Agent_3_ScriptGenerator.Agent_3_ScriptGenerator import register_agent3_routes
from AllAgents.Agent_4_ScriptToScene.Agent_4_ScriptToScene import register_agent4_routes
from AllAgents.Agent_5_generateIdeas.Agent_5_generateIdeas import register_agent5_routes
from AllAgents.Agent_6_roadmap.Agent_6_roadmap import register_agent6_routes

# Register all agent routes with the app
register_agent1_routes(app, create_agent_client, YOUTUBE_TOOLS)
register_agent2_routes(app, create_agent_client, YOUTUBE_TOOLS)
register_agent3_routes(app, create_agent_client, YOUTUBE_TOOLS)
register_agent4_routes(app, create_agent_client, YOUTUBE_TOOLS)
register_agent5_routes(app, create_agent_client, YOUTUBE_TOOLS)
register_agent6_routes(app, create_agent_client, YOUTUBE_TOOLS)


def _ensure_saved_responses_collection():
    global mongo_client, saved_responses_collection

    if saved_responses_collection is not None:
        return saved_responses_collection

    if not MONGODB_URI:
        logger.error("MONGODB_URI not set. Saved responses unavailable.")
        raise HTTPException(status_code=503, detail="Saved responses service unavailable")

    if saved_responses_collection is not None:
        return saved_responses_collection

    client: Optional[MongoClient] = None
    try:
        logger.info(
            "Initialising MongoDB client for saved responses (db='%s', collection='%s')",
            MONGODB_DB or "<empty>",
            SAVED_RESPONSES_COLLECTION or "<empty>"
        )
        client_kwargs: Dict[str, Any] = {}
        ca_file = MONGODB_CA_FILE
        if not ca_file:
            uri_lower = MONGODB_URI.lower()
            if MONGODB_URI.startswith("mongodb+srv://") or "tls=true" in uri_lower or "ssl=true" in uri_lower:
                ca_file = certifi.where()
        if ca_file:
            client_kwargs["tlsCAFile"] = ca_file

        client = MongoClient(MONGODB_URI, **client_kwargs)
        client.admin.command('ping')
        mongo_client = client
        saved_responses_collection = mongo_client[MONGODB_DB][SAVED_RESPONSES_COLLECTION]
        logger.info("MongoDB connection for saved responses established successfully")
    except Exception as exc:
        logger.exception("Failed to initialise MongoDB client: %s", exc)
        if client:
            client.close()
        if mongo_client and mongo_client is not client:
            mongo_client.close()
        mongo_client = None
        saved_responses_collection = None

    if saved_responses_collection is None:
        logger.error("Saved responses collection unavailable. Check MongoDB configuration.")
        raise HTTPException(status_code=503, detail="Saved responses service unavailable")

    return saved_responses_collection


def _serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _serialize_saved_response(doc: Dict[str, Any], include_content: bool = False) -> SavedResponseDetail | SavedResponseSummary:
    data = {
        "id": str(doc.get("_id")),
        "title": doc.get("title", "Untitled Response"),
        "agent_id": doc.get("agent_id", 0),
        "agent_name": doc.get("agent_name", ""),
        "agent_codename": doc.get("agent_codename", ""),
        "created_at": _serialize_datetime(doc.get("created_at")),
        "updated_at": _serialize_datetime(doc.get("updated_at")),
    }
    if include_content:
        data["content"] = doc.get("content", "")
        return SavedResponseDetail(**data)
    return SavedResponseSummary(**data)


def _parse_saved_response_id(response_id: str) -> ObjectId:
    if not ObjectId.is_valid(response_id):
        raise HTTPException(status_code=400, detail="Invalid saved response ID")
    return ObjectId(response_id)


@app.get("/api/saved-responses", response_model=List[SavedResponseSummary])
async def list_saved_responses():
    collection = _ensure_saved_responses_collection()
    logger.info("Listing saved responses")
    try:
        docs = list(collection.find({}).sort("updated_at", -1))
        responses = [_serialize_saved_response(doc) for doc in docs]
        logger.info("Successfully retrieved %d saved responses", len(responses))
        return responses
    except Exception as exc:
        logger.exception("Failed to list saved responses: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to list saved responses")


@app.post("/api/saved-responses", response_model=SavedResponseDetail, status_code=201)
async def create_saved_response(request: SavedResponseCreate):
    collection = _ensure_saved_responses_collection()
    now = datetime.now(timezone.utc)
    doc = {
        "title": request.title.strip() or "Untitled Response",
        "content": request.content,
        "agent_id": request.agent_id,
        "agent_name": request.agent_name,
        "agent_codename": request.agent_codename,
        "created_at": now,
        "updated_at": now,
    }
    result = collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    logger.info("Saved response '%s' (%s)", doc.get("title"), str(result.inserted_id))
    return _serialize_saved_response(doc, include_content=True)


@app.get("/api/saved-responses/{response_id}", response_model=SavedResponseDetail)
async def get_saved_response(response_id: str):
    collection = _ensure_saved_responses_collection()
    oid = _parse_saved_response_id(response_id)
    doc = collection.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Saved response not found")
    return _serialize_saved_response(doc, include_content=True)


@app.put("/api/saved-responses/{response_id}", response_model=SavedResponseDetail)
async def update_saved_response(response_id: str, request: SavedResponseUpdate):
    collection = _ensure_saved_responses_collection()
    oid = _parse_saved_response_id(response_id)
    doc = collection.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Saved response not found")

    update_fields: Dict[str, Any] = {}
    if request.title is not None:
        update_fields["title"] = request.title.strip() or "Untitled Response"
    if request.content is not None:
        update_fields["content"] = request.content
    if not update_fields:
        return _serialize_saved_response(doc, include_content=True)

    update_fields["updated_at"] = datetime.now(timezone.utc)
    collection.update_one({"_id": oid}, {"$set": update_fields})
    doc.update(update_fields)
    logger.info("Updated saved response '%s' (%s)", doc.get("title"), response_id)
    return _serialize_saved_response(doc, include_content=True)


@app.delete("/api/saved-responses/{response_id}", status_code=204)
async def delete_saved_response(response_id: str):
    collection = _ensure_saved_responses_collection()
    oid = _parse_saved_response_id(response_id)
    result = collection.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Saved response not found")
    logger.info("Deleted saved response (%s)", response_id)
    return None



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
