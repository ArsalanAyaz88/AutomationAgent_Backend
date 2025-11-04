"""
Agent 5: CTR Optimizer - "The Click Magnet"
Generates high-CTR titles and thumbnails for YouTube videos.
"""

from typing import Optional
from fastapi import HTTPException
from agents import Agent, Runner
from pydantic import BaseModel


# Request Models
class IdeasGenerationRequest(BaseModel):
    winning_videos_data: Optional[str] = ""
    user_query: str = "Generate 3 high-CTR title-thumbnail combinations"


class AgentResponse(BaseModel):
    success: bool
    result: str
    error: Optional[str] = None


def register_agent5_routes(app, create_agent_client_func, youtube_tools=None):
    """Register Agent 5 routes with the FastAPI app"""
    
    @app.post("/api/agent5/generate-ideas", response_model=AgentResponse)
    async def generate_ideas(request: IdeasGenerationRequest):
        """
        Agent 5: CTR Optimizer - "The Click Magnet"
        Generates high-performing titles and thumbnails that maximize click-through rates.
        Creates 3 optimized title-thumbnail pairs with CTR prediction scores.
        """
        try:
            model_name = create_agent_client_func("agent5")
            
            # Reusable CTR framework (concise)
            base_framework = """You are "The Click Magnet" — a YouTube CTR optimization specialist.

Mission: Generate 3 high-performing title–thumbnail pairs that maximize CTR while staying authentic to content and brand.

Requirements per option:
- Title: 40–70 chars, front-load main keyword, strong hook, not misleading
- Thumbnail: 1–5 words overlay, clear focal point, readable at small size
- Harmony: Title and thumbnail complement (not duplicate) each other
- Include: CTR prediction with brief rationale
"""

            # ========================================
            # PHASE 1: PLANNER AGENT
            # ========================================
            planner_instructions = f"""{request.user_query}

Your task: Propose 3 complete CTR-optimized title–thumbnail options.

Inputs (winning videos data / insights):
{request.winning_videos_data}

{base_framework}

Output an initial set of 3 options with titles, thumbnail concepts, and brief why-it-works notes."""

            planner_agent = Agent(
                name="Planner LLM",
                instructions=planner_instructions,
                model=model_name,
            )

            planner_result = await Runner.run(
                planner_agent,
                "Create 3 initial title–thumbnail options with analysis."
            )
            initial_plan = planner_result.final_output

            # ========================================
            # PHASE 2: CRITIC AGENT
            # ========================================
            critic_instructions = f"""You are a Critic LLM. Review the options and identify:

1. USER COMPLIANCE: Exactly 3 options with full details (title, thumbnail concept, why-it-works, CTR prediction)
2. TITLE QUALITY: Length 40–70, keyword front-loaded, strong hook, authentic
3. THUMBNAIL QUALITY: Clear focal point, 1–5 words, high contrast, readable at small size
4. HARMONY: Title and thumbnail complement, not duplicate
5. BRAND/TONE FIT: Matches likely brand voice (based on inputs)
6. DIVERSITY: Options cover different formulas/emotions/angles
7. ISSUES: Specific problems per option
8. RECOMMENDATIONS: Concrete fixes per issue

Inputs summary:
{request.winning_videos_data}

Options to review:
{initial_plan}

Provide concise critique and actionable recommendations."""

            critic_agent = Agent(
                name="Critic LLM",
                instructions=critic_instructions,
                model=model_name,
            )

            critic_result = await Runner.run(
                critic_agent,
                "Review the 3 options and provide improvements."
            )
            critique = critic_result.final_output

            # ========================================
            # PHASE 3: REFINED PLANNER AGENT
            # ========================================
            refined_planner_instructions = f"""{request.user_query}

{base_framework}

Winning videos data / insights:
{request.winning_videos_data}

Your Initial Options:
{initial_plan}

Critic's Feedback:
{critique}

Task: Produce a REFINED set of exactly 3 options addressing all issues. Each option must include:
- Title (40–70 chars) with main keyword front-loaded
- Thumbnail concept (composition, text 1–5 words, placement, colors, emotion)
- Why this works (2–3 sentences)
- Estimated CTR with brief rationale

Output only the final polished options."""

            refined_planner_agent = Agent(
                name="Refined Planner LLM",
                instructions=refined_planner_instructions,
                model=model_name,
            )

            final_result = await Runner.run(
                refined_planner_agent,
                "Deliver the refined 3 title–thumbnail options."
            )

            return AgentResponse(success=True, result=final_result.final_output)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
