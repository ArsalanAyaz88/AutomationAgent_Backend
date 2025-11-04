"""
Agent 6: Video Roadmap Planner - "The Strategist"
Creates 30-video content roadmaps for YouTube channel growth.
"""

from typing import Optional
from fastapi import HTTPException
from agents import Agent, Runner
from pydantic import BaseModel


# Request Models
class RoadmapGenerationRequest(BaseModel):
    niche: str
    winning_data: Optional[str] = ""
    user_query: Optional[str] = "Create a 30-video roadmap with 3 title variations and 3 thumbnail concepts for each"


class AgentResponse(BaseModel):
    success: bool
    result: str
    error: Optional[str] = None


def register_agent6_routes(app, create_agent_client_func, youtube_tools=None):
    """Register Agent 6 routes with the FastAPI app"""
    
    @app.post("/api/agent6/generate-roadmap", response_model=AgentResponse)
    async def generate_roadmap(request: RoadmapGenerationRequest):
        """
        Agent 6: Video Roadmap Planner - "The Strategist"
        Creates comprehensive 30-video content roadmaps with publishing schedules and growth strategies.
        Synthesizes data from all previous agents to build strategic content calendars.
        """
        try:
            model_name = create_agent_client_func("agent6")
            
            # Reusable strategic framework (base guidelines)
            base_framework = """You're "The Strategist" - architect sustainable YouTube success through intelligent content planning, data-driven decisions, and strategic execution! 🎯📈"""

            # ========================================
            # PHASE 1: PLANNER AGENT
            # ========================================
            planner_instructions = f"""{request.user_query}

Your task: Generate a complete 30-video strategic roadmap for the given niche.

Niche: {request.niche}

Data from Previous Agents (if provided):
{request.winning_data}

{base_framework}

Create an initial execution plan covering all 30 videos with pillars, sequencing, SEO, titles (3 options), thumbnails (3 concepts), schedule, and metrics."""

            planner_agent = Agent(
                name="Planner LLM",
                instructions=planner_instructions,
                model=model_name,
            )

            planner_result = await Runner.run(
                planner_agent,
                "Create an initial 30-video roadmap for this niche."
            )
            initial_plan = planner_result.final_output

            # ========================================
            # PHASE 2: CRITIC AGENT
            # ========================================
            critic_instructions = f"""You are a Critic LLM. Review the roadmap plan below and identify:

1. USER COMPLIANCE: Does it follow the user's directives (format, scope, tone)?
2. COMPLETENESS: Are there 30 videos with 3 title options and 3 thumbnail concepts each?
3. SEQUENCING LOGIC: Does the plan follow Lead-In → Main Story → Follow-Up phases?
4. PILLAR COVERAGE: Balanced content pillars and mix (evergreen/trending/series)?
5. SEO DETAILS: Primary/secondary/long-tail keywords and tags per video?
6. SCHEDULE: Clear publishing cadence, days, times, and timeline?
7. METRICS: Targets for CTR/AVD and feedback loops included?
8. SEASONAL/TREND INTEGRATION: Allocated spots and quick-pivot strategy?
9. CONSISTENCY/QUALITY: Clarity, actionable details, no ambiguities.
10. ISSUES & RECOMMENDATIONS: List specific problems and how to fix them.

Original Inputs:
Niche: {request.niche}
Winning Data: {request.winning_data}

Plan to review:
{initial_plan}

Provide constructive critique with actionable feedback."""

            critic_agent = Agent(
                name="Critic LLM",
                instructions=critic_instructions,
                model=model_name,
            )

            critic_result = await Runner.run(
                critic_agent,
                "Review this 30-video roadmap and provide detailed feedback."
            )
            critique = critic_result.final_output

            # ========================================
            # PHASE 3: REFINED PLANNER AGENT
            # ========================================
            refined_planner_instructions = f"""{request.user_query}

{base_framework}

Original Inputs:
Niche: {request.niche}
Winning Data:
{request.winning_data}

Your Initial Plan:
{initial_plan}

Critic's Feedback:
{critique}

Task: Produce a REFINED, COMPLETE 30-video roadmap that addresses all critic issues. Follow every explicit user directive before defaults. Maintain strategic YouTube-focused tone. Ensure each video includes required elements (phase, pillar, type, titles x3, thumbnails x3, SEO, outline, connections, publishing, metrics, notes). Output only the final polished roadmap."""

            refined_planner_agent = Agent(
                name="Refined Planner LLM",
                instructions=refined_planner_instructions,
                model=model_name,
            )

            final_result = await Runner.run(
                refined_planner_agent,
                "Deliver the complete refined 30-video roadmap."
            )

            return AgentResponse(success=True, result=final_result.final_output)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


