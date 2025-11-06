"""
Agent 2: Video-Level Auditor - "The Content Detective" with RL Learning
Deconstructs high-performing videos to identify success patterns and learns from feedback.
"""

from typing import Optional, List, Dict, Any
from fastapi import HTTPException
from agents import Agent, Runner
from pydantic import BaseModel

# Import RL integration
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from rl_integration import rl_enhanced

# Request Models
class TitleAuditRequest(BaseModel):
    video_urls: List[str]
    user_query: str = "Analyze these videos and extract winning patterns"

class AgentResponse(BaseModel):
    success: bool
    result: str
    error: Optional[str] = None
    rl_learning: Optional[Dict[str, Any]] = None

def register_agent2_routes(app, create_agent_client_func, youtube_tools):
    """Register Agent 2 routes with the FastAPI app"""
    
    @app.post("/api/agent2/audit-titles", response_model=AgentResponse)
    @rl_enhanced("agent2_title_auditor")
    async def audit_titles(request: TitleAuditRequest):
        """
        Agent 2: Video-Level Auditor - "The Content Detective"
        Deconstructs high-performing videos to identify what makes them work.
        Analyzes titles, thumbnails, hooks, storytelling structure, and content patterns.
        """
        try:
            model_name = create_agent_client_func("agent2")
            # Reusable audit framework (concise)
            base_framework = """You are "The Content Detective" — a YouTube video forensics analyst.

Mission: Perform deep audits of videos to extract winning patterns across titles, thumbnails, hooks, storytelling, engagement, and SEO; then synthesize repeatable formulas.

Output expectations:
- Per-video structured findings (metadata, title/thumbnail forensics, hook analysis, storytelling arc, engagement patterns, format classification, keywords, winning elements, verdict)
- Cross-video pattern summary with reusable templates and recommendations
"""

            videos_list = "\n".join([f"- {url}" for url in request.video_urls])

            # ========================================
            # PHASE 1: PLANNER AGENT (uses tools)
            # ========================================
            planner_instructions = f"""{request.user_query}

Videos to analyze:
{videos_list}

{base_framework}

Task: Run an initial comprehensive audit for each video (using available tools as needed) and produce a first-pass synthesis of cross-video patterns and templates."""

            planner_agent = Agent(
                name="Planner LLM",
                instructions=planner_instructions,
                model=model_name,
                tools=youtube_tools,
            )

            planner_result = await Runner.run(
                planner_agent,
                "Perform the audit and produce a structured initial report."
            )
            initial_report = planner_result.final_output

            # ========================================
            # PHASE 2: CRITIC AGENT
            # ========================================
            critic_instructions = f"""You are a Critic LLM. Review the audit for:

1. USER COMPLIANCE: Follows prompt and framework; one structured report per video + pattern summary
2. COMPLETENESS: Metadata, title/thumbnail forensics, hook analysis, storytelling arc, engagement patterns, format, keywords, winning elements, verdict
3. EVIDENCE USE: Specific observations, quotes, and data where applicable
4. SYNTHESIS: Clear cross-video patterns, repeatable templates, and practical recommendations
5. CLARITY: Actionable, unambiguous, minimal fluff
6. ISSUES & RECOMMENDATIONS: Specific fixes and additions

Original inputs (videos):
{videos_list}

Audit to review:
{initial_report}

Provide concise critique plus actionable recommendations."""

            critic_agent = Agent(
                name="Critic LLM",
                instructions=critic_instructions,
                model=model_name,
            )

            critic_result = await Runner.run(
                critic_agent,
                "Review the audit and provide detailed feedback."
            )
            critique = critic_result.final_output

            # ========================================
            # PHASE 3: REFINED PLANNER AGENT
            # ========================================
            refined_planner_instructions = f"""{request.user_query}

{base_framework}

Videos to analyze:
{videos_list}

Initial Audit:
{initial_report}

Critic's Feedback:
{critique}

Task: Produce a REFINED, COMPLETE audit that addresses all issues. Ensure per-video reports are thorough and the cross-video synthesis includes clear templates and prioritized recommendations. Output only the final polished audit."""

            refined_planner_agent = Agent(
                name="Refined Planner LLM",
                instructions=refined_planner_instructions,
                model=model_name,
            )

            final_result = await Runner.run(
                refined_planner_agent,
                "Deliver the refined comprehensive audit."
            )

            return AgentResponse(success=True, result=final_result.final_output)
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))