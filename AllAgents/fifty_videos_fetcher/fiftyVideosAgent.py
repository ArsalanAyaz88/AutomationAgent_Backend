"""
Agent: 50 Videos Fetcher - "The Link Collector"
Fetches the latest 50 video links from a YouTube channel.
"""

from typing import Optional
from fastapi import HTTPException
from agents import Agent, Runner
from pydantic import BaseModel
import re


# Request Models
class FiftyVideosRequest(BaseModel):
    input: str  # Can be channel ID, channel URL, or video URL
    user_query: str = "Get the latest 50 video links from this channel"


class AgentResponse(BaseModel):
    success: bool
    result: str
    error: Optional[str] = None


def extract_channel_id_from_url(url: str) -> Optional[str]:
    """Extract channel ID from various YouTube URL formats"""
    # Pattern for /channel/UC... URLs
    channel_match = re.search(r'/channel/(UC[a-zA-Z0-9_-]+)', url)
    if channel_match:
        return channel_match.group(1)
    return None


def register_fifty_videos_routes(app, create_agent_client_func, youtube_tools):
    """Register 50 Videos Fetcher routes with the FastAPI app"""
    
    @app.post("/api/fifty-videos/fetch-links", response_model=AgentResponse)
    async def fetch_fifty_videos(request: FiftyVideosRequest):
        """
        Agent: 50 Videos Fetcher - "The Link Collector"
        Fetches the latest 50 video links from a YouTube channel.
        Accepts channel ID, channel URL (@username or /channel/), or any video URL from that channel.
        """
        try:
            model_name = create_agent_client_func("agent1")
            
            # Agent instructions
            agent_instructions = f"""{request.user_query}

User Input: {request.input}

You are "The Link Collector" — a specialized agent that fetches YouTube video links.

Your mission:
1. Identify the channel from the input (it could be a channel ID, channel URL, or video URL)
2. Use the available YouTube tools to get the channel's latest 50 videos
3. Extract and return ONLY the video links in a clean, formatted list

Output format:
Present the video links as a numbered list with video titles:

### Latest 50 Videos

1. **[Video Title]** - https://youtube.com/watch?v=VIDEO_ID
2. **[Video Title]** - https://youtube.com/watch?v=VIDEO_ID
...

Guidelines:
- Use the channels_listVideos tool with maxResults=50
- If given a video URL, first extract the channel ID from it
- If given a channel handle (@username), convert it to channel ID
- Present links in a clean, copy-friendly format
- Include video titles for context
- Handle errors gracefully with clear messages"""

            agent = Agent(
                name="50 Videos Fetcher",
                instructions=agent_instructions,
                model=model_name,
                tools=youtube_tools,
            )

            result = await Runner.run(
                agent,
                "Fetch and format the video links from the channel."
            )

            return AgentResponse(success=True, result=result.final_output)
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
