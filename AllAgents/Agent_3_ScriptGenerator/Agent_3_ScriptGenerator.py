"""
Agent 3: Script Generator - "The Storyteller"
Generates ready-to-record video scripts for YouTube.
"""

from typing import Optional
from fastapi import HTTPException
from agents import Agent, Runner
from pydantic import BaseModel


# Request Models
class ScriptGenerationRequest(BaseModel):
    topic: Optional[str] = None
    title_audit_data: Optional[str] = ""
    user_query: Optional[str] = None


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
        Generates ready-to-record video scripts that follow winning formats from viral videos.
        Creates complete scripts with voiceover text, scene breakdowns, and camera cues.
        """
        try:
            model_name = create_agent_client_func("agent3")
            
            # Reusable script framework (concise)
            base_framework = """You are "The Storyteller" — a YouTube script writer focused on retention and clarity.

Mission: Create a ready-to-record script with clear sections, timestamps, voiceover lines, and brief visual/camera cues.

Core requirements:
- Hook under 15 seconds with value promise and curiosity
- Clear structure: Hook → Intro → Main content (sections) → Climax → Conclusion/CTA
- Open loops/pattern interrupts regularly; conversational tone; active voice
- Include timestamps and minimal camera/visual notes per section
"""

            # ========================================
            # PHASE 1: PLANNER AGENT
            # ========================================
            default_prompt = f"Based on the following video analysis data, create a compelling YouTube video script for: {request.topic}" if request.topic else "Create a compelling YouTube video script that maximizes retention."
            planner_instructions = f"""{request.user_query or default_prompt}

Inputs (title/analysis data):
{request.title_audit_data}

{base_framework}

Deliver an initial complete script with:
- Title, target length, tone, arc
- Timestamps per major section
- Voiceover lines (speakable) and brief visual/camera cues
- At least 3 open loops/pattern interrupts throughout
"""

            planner_agent = Agent(
                name="Planner LLM",
                instructions=planner_instructions,
                model=model_name,
            )

            planner_result = await Runner.run(
                planner_agent,
                "Draft a full initial script with timestamps, VO, and cues."
            )
            initial_plan = planner_result.final_output

            # ========================================
            # PHASE 2: CRITIC AGENT
            # ========================================
            critic_instructions = f"""You are a Critic LLM. Review the drafted script and evaluate:

1. USER COMPLIANCE: Does it follow the prompt and core framework?
2. STRUCTURE: Clear sections (hook/intro/main/climax/conclusion) with timestamps?
3. RETENTION: Open loops/pattern interrupts and pacing variety present?
4. VOICE: Conversational, active voice, specific numbers/examples?
5. PRODUCTION NOTES: Visual/camera cues included where helpful?
6. COMPLETENESS: CTA present; climax/payoff clear; no gaps/ambiguities.
7. ISSUES & FIXES: List concrete problems and actionable recommendations.

Original inputs:
Topic: {request.topic}
Title/analysis data: {request.title_audit_data}

Script to review:
{initial_plan}

Provide concise critique and specific improvements."""

            critic_agent = Agent(
                name="Critic LLM",
                instructions=critic_instructions,
                model=model_name,
            )

            critic_result = await Runner.run(
                critic_agent,
                "Review the script and provide actionable feedback."
            )
            critique = critic_result.final_output

            # ========================================
            # PHASE 3: REFINED PLANNER AGENT
            # ========================================
            refined_planner_instructions = f"""{request.user_query or default_prompt}

{base_framework}

Original inputs:
Topic: {request.topic}
Title/analysis data:
{request.title_audit_data}

Initial Script:
{initial_plan}

Critic's Feedback:
{critique}

Task: Produce a REFINED, COMPLETE script addressing all critique points. Ensure:
- Strong hook (<15s), clear timestamps per section
- Open loops/pattern interrupts added where missing
- Conversational, specific, speakable VO
- Include minimal but sufficient visual/camera cues

Output only the final polished script."""

            refined_planner_agent = Agent(
                name="Refined Planner LLM",
                instructions=refined_planner_instructions,
                model=model_name,
            )

            final_result = await Runner.run(
                refined_planner_agent,
                "Deliver the refined, production-ready script."
            )

            return AgentResponse(success=True, result=final_result.final_output)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

