import asyncio
import os
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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
from agents.mcp import MCPServerStdio

# Load environment variables
load_dotenv()

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


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting YouTube Automation Agent API...")
    yield
    # Shutdown
    print("🛑 Shutting down YouTube Automation Agent API...")


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
    """
    try:
        model_name = create_agent_client("agent1")
        
        # Build query with channel URLs
        query = f"{request.user_query}\n\nChannels to audit:\n"
        query += "\n".join([f"- {url}" for url in request.channel_urls])
        
        async with MCPServerStdio(
            name="youtube",
            params={
                "command": "node",
                "args": ["./channel_auditor_agent_1/youtube-mcp-server/dist/cli.js"],
                "env": {"YOUTUBE_API_KEY": os.getenv("YOUTUBE_API_KEY")},
            },
        ) as youtube_server:
            agent = Agent(
                name="Channel Auditor",
                instructions="""You are an expert YouTube channel auditor. Your job is to:
                1. Analyze multiple YouTube channels in depth
                2. Evaluate their performance metrics, content strategy, and growth patterns
                3. Identify the hottest channel with the best potential for replication
                4. Provide detailed insights on what makes it successful
                5. Recommend strategies based on the winning channel's approach
                
                Analyze: views, engagement rate, upload frequency, content themes, audience retention signals.""",
                model=model_name,
                mcp_servers=[youtube_server]
            )
            
            result = await Runner.run(agent, query)
            return AgentResponse(success=True, result=result.final_output)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        
        async with MCPServerStdio(
            name="youtube",
            params={
                "command": "node",
                "args": ["./channel_auditor_agent_1/youtube-mcp-server/dist/cli.js"],
                "env": {"YOUTUBE_API_KEY": os.getenv("YOUTUBE_API_KEY")},
            },
        ) as youtube_server:
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
                mcp_servers=[youtube_server]
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
