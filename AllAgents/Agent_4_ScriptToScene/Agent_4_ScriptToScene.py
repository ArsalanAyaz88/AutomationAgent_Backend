"""
Agent 4: Script-to-Scene Synchronizer - "The Director"
Uses Planner-Critic multi-agent pattern for intelligent task decomposition.
"""

from typing import Optional
from fastapi import HTTPException
from agents import Agent, Runner
from pydantic import BaseModel


# Request Models
class ScriptToPromptsRequest(BaseModel):
    script: str
    user_query: Optional[str] = "Convert this script into detailed scene-by-scene prompts"


class AgentResponse(BaseModel):
    success: bool
    result: str
    error: Optional[str] = None


def register_agent4_routes(app, create_agent_client_func, youtube_tools=None):
    """Register Agent 4 routes with Planner-Critic multi-agent system"""
    
    @app.post("/api/agent4/script-to-prompts", response_model=AgentResponse)
    async def script_to_prompts(request: ScriptToPromptsRequest):
        """
        Agent 4: Script-to-Scene Synchronizer - "The Director"
        Uses Planner-Critic LLM pattern for intelligent task decomposition.
        """
        try:
            model_name = create_agent_client_func("agent4")
            
            # Minimal framework (reusable guidelines)
            base_framework = """
SCENE BREAKDOWN FRAMEWORK:

For each scene provide:
1. TIMESTAMP: Start-end time — each scene must be exactly 8 seconds long (no more, no less)
2. VOICEOVER/DIALOGUE: Script text for this scene
3. SHOT BREAKDOWN: Shot type, camera angle, movement, subject, background
4. LIGHTING SETUP: Style, key/fill/back lights, mood, color temperature
5. VISUAL MOOD: Overall atmosphere and tone
6. VISUAL ELEMENTS: Text overlays, graphics, special elements
7. TRANSITION: How to transition to next scene
8. AI GENERATION PROMPT: Detailed prompt for AI video tools

Shot Types: EWS, WS, MS, MCU, CU, ECU
Angles: Eye level, High, Low, Dutch, Bird's eye, Worm's eye
Movement: Static, Pan, Tilt, Dolly, Tracking, Crane, Handheld, Gimbal
Lighting: Three-point, Natural, High key, Low key, Silhouette
Pacing: Fast (3-8s), Balanced (8-15s), Cinematic (15-30s)"""
            
            # ========================================
            # PHASE 1: PLANNER AGENT
            # ========================================
            planner_instructions = f"""{request.user_query}

Your task: Break down the provided script into detailed scene-by-scene visual prompts.

{base_framework}

Script to analyze:
{request.script}

Create a complete execution plan covering all scenes with timing, shots, lighting, and AI prompts."""
            
            planner_agent = Agent(
                name="Planner LLM",
                instructions=planner_instructions,
                model=model_name,
            )
            
            # Execute Planner
            planner_result = await Runner.run(
                planner_agent, 
                "Create a complete scene-by-scene breakdown for this script."
            )
            initial_plan = planner_result.final_output
            
            # ========================================
            # PHASE 2: CRITIC AGENT
            # ========================================
            critic_instructions = f"""You are a Critic LLM. Review the scene breakdown plan below and identify:

1. COMPLETENESS: Are ALL parts of the script covered?
2. TIMING ACCURACY: Does every scene span exactly 8 seconds between start and end timestamps?
3. CONSISTENCY: Is visual style uniform across scenes?
4. MISSING ELEMENTS: Any missing shots, lighting, transitions, or AI prompts?
5. TECHNICAL QUALITY: Are AI prompts generation-ready?
6. ISSUES FOUND: List specific problems
7. RECOMMENDATIONS: How to improve the plan

Original Script:
{request.script}

Plan to review:
{initial_plan}

Provide constructive critique with specific actionable feedback."""
            
            critic_agent = Agent(
                name="Critic LLM",
                instructions=critic_instructions,
                model=model_name,
            )
            
            # Execute Critic
            critic_result = await Runner.run(
                critic_agent, 
                "Review this plan and provide detailed feedback."
            )
            critique = critic_result.final_output
            
            # ========================================
            # PHASE 3: REFINED PLANNER AGENT
            # ========================================
            refined_planner_instructions = f"""{request.user_query}

{base_framework}

Original Script:
{request.script}

Your Initial Plan:
{initial_plan}

Critic's Feedback:
{critique}

Task: Create a REFINED, COMPLETE scene breakdown that addresses all issues raised by the Critic. 
Ensure every scene is exactly 8 seconds long and has complete details (timestamp, dialogue, shots, lighting, mood, transitions, AI prompts). 
Output only the final polished breakdown."""
            
            refined_planner_agent = Agent(
                name="Refined Planner LLM",
                instructions=refined_planner_instructions,
                model=model_name,
            )
            
            # Execute Refined Planner
            final_result = await Runner.run(
                refined_planner_agent, 
                "Deliver the complete refined scene breakdown."
            )
            
            return AgentResponse(success=True, result=final_result.final_output)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
