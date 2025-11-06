"""
Agent 6: Video Roadmap Planner - "The Strategist"
Creates 30-video content roadmaps for YouTube channel growth.
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException
from agents import Agent, Runner
from pydantic import BaseModel

# Import RL integration
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from agents_ReinforcementLearning.rl_integration import rl_enhanced


# Request Models
class RoadmapGenerationRequest(BaseModel):
    niche: Optional[str] = None
    winning_data: Optional[str] = ""
    channel_input: Optional[str] = None
    user_query: Optional[str] = "Create a 30-video roadmap with 3 title variations and 3 thumbnail concepts for each"


class AgentResponse(BaseModel):
    success: bool
    result: str
    error: Optional[str] = None
    rl_learning: Optional[Dict[str, Any]] = None


def register_agent6_routes(app, create_agent_client_func, youtube_tools=None):
    """Register Agent 6 routes with the FastAPI app"""
    
    @app.post("/api/agent6/generate-roadmap", response_model=AgentResponse)
    @rl_enhanced("agent6_roadmap_generator")
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

            channel_focus = ""
            if request.channel_input:
                channel_focus = f"""
CRITICAL CHANNEL CONTEXT:
- Channel reference provided: {request.channel_input}
- Use YouTube tools (channels_listVideos, videos_getVideoStats, etc.) to fetch the channel's latest 50 videos and identify top performers (view velocity, CTR proxies, engagement metrics).
- Extract at least 10 high-performing videos with stats (title, publish date, views, subs if available, growth signals).
- Base roadmap pillars, themes, and sequencing on proven winners from this channel. Reference the actual videos in your plan (mention titles, performance rationale, how each roadmap video builds on those wins).
- Infer the channel's niche, audience persona, and content pillars directly from the performance patterns you surface.
- Produce a concise "Channel Performance Insights" section summarizing the analyzed videos (table encouraged) and an "Inferred Niche & Audience" summary when the niche was not supplied.
- If tools fail, state the issue briefly and proceed with best-effort strategy, but still note the failure.
"""

            niche_context = request.niche or "INFER THIS: Analyze the channel's high-performing videos to define the niche, content pillars, and target audience persona."
            winning_data_context = request.winning_data if request.winning_data else "No manual winning data provided. Derive performance insights from the channel analysis and summarize them explicitly."
            channel_input_context = request.channel_input or "None provided"

            # ========================================
            # PHASE 1: PLANNER AGENT
            # ========================================
            planner_instructions = f"""{request.user_query}

Your task: Generate a complete 30-video strategic roadmap for the given niche.

Niche Context:
{niche_context}

Data from Previous Agents (if provided):
{winning_data_context}

Channel Input Reference:
{channel_input_context}

{base_framework}
{channel_focus}

Create an initial execution plan covering all 30 videos with pillars, sequencing, SEO, titles (3 options), thumbnails (3 concepts), schedule, and metrics."""

            planner_agent = Agent(
                name="Planner LLM",
                instructions=planner_instructions,
                model=model_name,
                tools=youtube_tools,
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
10. CHANNEL ALIGNMENT: Do roadmap ideas clearly reference and build upon the channel's actual high-performing videos (if channel data was provided)? Are those references accurate and data-backed?
11. ISSUES & RECOMMENDATIONS: List specific problems and how to fix them.

Original Inputs:
Niche Context: {niche_context}
Winning Data / Insights: {winning_data_context}
Channel Input: {channel_input_context}

Plan to review:
{initial_plan}

Provide constructive critique with actionable feedback."""

            critic_agent = Agent(
                name="Critic LLM",
                instructions=critic_instructions,
                model=model_name,
                tools=youtube_tools,
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
Niche Context:
{niche_context}
Winning Data / Insights:
{winning_data_context}
Channel Input:
{channel_input_context}

Your Initial Plan:
{initial_plan}

Critic's Feedback:
{critique}

Task: Produce a REFINED, COMPLETE 30-video roadmap that addresses all critic issues. Follow every explicit user directive before defaults. Maintain strategic YouTube-focused tone. Ensure each video includes required elements (phase, pillar, type, titles x3, thumbnails x3, SEO, outline, connections, publishing, metrics, notes).

When channel_input is provided you MUST:
- Cite specific high-performing videos from the channel (title + performance metrics) when explaining pillars or video ideas.
- Highlight how each roadmap video is inspired by, remixes, or improves upon proven winners.
- Include a reference table summarizing the top channel videos used to inform the roadmap (title, publish date, key metrics, what to learn).
- Present an "Inferred Niche & Audience" summary when the niche was not supplied.
- Deliver a "Channel Performance Insights" section (table or structured list) that captures the analyzed video metrics and takeaways.
- Document any tool failures briefly.

Output only the final polished roadmap."""

            refined_planner_agent = Agent(
                name="Refined Planner LLM",
                instructions=refined_planner_instructions,
                model=model_name,
                tools=youtube_tools,
            )

            final_result = await Runner.run(
                refined_planner_agent,
                "Deliver the complete refined 30-video roadmap."
            )

            return AgentResponse(success=True, result=final_result.final_output)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


