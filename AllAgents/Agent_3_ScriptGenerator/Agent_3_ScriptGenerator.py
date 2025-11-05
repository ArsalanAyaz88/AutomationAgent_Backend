"""
Agent 3: Script Generator - "The Storyteller"
Generates pure YouTube video scripts based on topic input.
Creates script content only - no visuals, voiceover notes, or production cues.
"""

from typing import Optional
from fastapi import HTTPException
from agents import Agent, Runner
from pydantic import BaseModel


# Request Models
class ScriptGenerationRequest(BaseModel):
    topic: str


class AgentResponse(BaseModel):
    success: bool
    result: str
    error: Optional[str] = None


def register_agent3_routes(app, create_agent_client_func, youtube_tools=None):
    """Register Agent 3 routes with the FastAPI app"""
    
    @app.post("/api/agent3/generate-script", response_model=AgentResponse)
    async def generate_script(request: ScriptGenerationRequest):
        """
        Agent 3: Script Generator - "The Storyteller"
        Generates YouTube video scripts based on topic input only.
        Creates pure script content without visuals or voiceover notes.
        """
        try:
            model_name = create_agent_client_func("agent3")
            
            # Script generation instructions
            script_instructions = f"""You are "The Storyteller" — a YouTube script writer focused on creating engaging video scripts.

Topic: {request.topic}

Mission: Create a compelling YouTube video script ONLY. Do not include:
- Visual suggestions
- Camera cues
- Voiceover notes
- Production notes
- Timestamps

Core requirements:
- Start with a strong hook (under 15 seconds) that grabs attention
- Clear structure: Hook → Introduction → Main Content → Climax → Conclusion/Call-to-Action
- Conversational tone with active voice
- Engaging storytelling that maintains viewer interest
- Natural flow and pacing
- Include pattern interrupts and open loops to maintain retention
- End with a clear call-to-action

Output: Pure script text only - what should be said in the video, nothing else."""

            # Generate the script
            script_agent = Agent(
                name="Script Generator",
                instructions=script_instructions,
                model=model_name,
            )

            result = await Runner.run(
                script_agent,
                f"Generate a complete YouTube video script for the topic: {request.topic}"
            )

            return AgentResponse(success=True, result=result.final_output)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

