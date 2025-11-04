"""
Agent 1: Channel Deep Auditor - "The Gold Digger"
Finds promising YouTube channels through deep performance analysis.
"""

from typing import Optional, List
from fastapi import HTTPException
from agents import Agent, Runner
from pydantic import BaseModel


# Request Models
class ChannelAuditRequest(BaseModel):
    channel_urls: Optional[List[str]] = []
    user_query: str = "Perform a deep audit on the provided channels"


class AgentResponse(BaseModel):
    success: bool
    result: str
    error: Optional[str] = None


def register_agent1_routes(app, create_agent_client_func, youtube_tools):
    """Register Agent 1 routes with the FastAPI app"""
    
    @app.post("/api/agent1/audit-channel", response_model=AgentResponse)
    async def audit_channel(request: ChannelAuditRequest):
        """
        Agent 1: Channel Auditor
        Deep audit of channels to pick the hottest one for content creation.
        Accepts: channel URLs, video URLs, channel handles (@username), channel names - anything!
        """
        try:
            model_name = create_agent_client_func("agent1")
            
            # Reusable channel audit framework (concise)
            base_framework = """You are "The Gold Digger" — a YouTube channel intelligence analyst.

Mission: Identify the most promising channels/niches via deep audits (engagement, viral patterns, content mix, consistency/growth, competitive positioning) and deliver opportunity scores with actionable recommendations.

Output expectations per channel:
- Opportunity Score (0-100) with category
- Quick stats (subs, avg views, engagement, upload freq, growth)
- Verdict, key strengths, risks, content strategy, actionable insights, bottom line

When multiple channels are provided, include ranking and comparisons.
"""

            channels_list = "\n".join([f"- {url}" for url in request.channel_urls]) if request.channel_urls else "(none provided)"

            # ========================================
            # PHASE 1: PLANNER AGENT (uses tools)
            # ========================================
            planner_instructions = f"""{request.user_query}

User-provided inputs (channels/handles/IDs/names):
{channels_list}

{base_framework}

Task: Perform an initial deep audit for each channel (using available tools as needed) and produce a first-pass comparative report with opportunity scores and recommendations."""

            planner_agent = Agent(
                name="Planner LLM",
                instructions=planner_instructions,
                model=model_name,
                tools=youtube_tools,
            )

            planner_result = await Runner.run(
                planner_agent,
                "Perform the channel audits and produce an initial comparative report."
            )
            initial_report = planner_result.final_output

            # ========================================
            # PHASE 2: CRITIC AGENT
            # ========================================
            critic_instructions = f"""You are a Critic LLM. Review the channel audit for:

1. USER COMPLIANCE: Follows prompt and framework; includes per-channel reports and comparisons when applicable
2. COMPLETENESS: Engagement, viral detection, content classification, consistency/growth, competitive positioning, opportunity scores, and clear recommendations
3. EVIDENCE USE: Specific stats/observations where applicable
4. SCORING CLARITY: Transparent rationale behind Opportunity Scores and categories
5. COMPARATIVE RANKING: Present and justified when multiple channels
6. ISSUES & RECOMMENDATIONS: Specific fixes and additions

Original inputs:
{channels_list}

Audit to review:
{initial_report}

Provide concise critique with actionable recommendations."""

            critic_agent = Agent(
                name="Critic LLM",
                instructions=critic_instructions,
                model=model_name,
            )

            critic_result = await Runner.run(
                critic_agent,
                "Review the channel audit and provide detailed feedback."
            )
            critique = critic_result.final_output

            # ========================================
            # PHASE 3: REFINED PLANNER AGENT
            # ========================================
            refined_planner_instructions = f"""{request.user_query}

{base_framework}

Original inputs:
{channels_list}

Initial Audit:
{initial_report}

Critic's Feedback:
{critique}

Task: Produce a REFINED, COMPLETE channel audit addressing all issues. Ensure per-channel sections are thorough, scores are justified, and comparisons/rankings are clear. Output only the final polished audit."""

            refined_planner_agent = Agent(
                name="Refined Planner LLM",
                instructions=refined_planner_instructions,
                model=model_name,
            )

            final_result = await Runner.run(
                refined_planner_agent,
                "Deliver the refined channel audit with opportunity scores and recommendations."
            )

            return AgentResponse(success=True, result=final_result.final_output)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
