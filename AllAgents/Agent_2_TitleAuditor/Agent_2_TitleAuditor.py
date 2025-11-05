"""
Agent 2: Video-Level Auditor - "The Content Detective"
Deconstructs high-performing videos to identify success patterns.
"""

from typing import Optional, List
from fastapi import HTTPException
from agents import Agent, Runner
from pydantic import BaseModel


# Request Models
class TitleAuditRequest(BaseModel):
    video_urls: List[str]
    user_query: str = "Analyze these videos and extract winning patterns"


class VideoAudit(BaseModel):
    video_url: str
    audit_report: str


class AgentResponse(BaseModel):
    success: bool
    individual_audits: List[VideoAudit]
    cross_video_summary: Optional[str] = None
    error: Optional[str] = None


def register_agent2_routes(app, create_agent_client_func, youtube_tools):
    """Register Agent 2 routes with the FastAPI app"""
    
    @app.post("/api/agent2/audit-titles", response_model=AgentResponse)
    async def audit_titles(request: TitleAuditRequest):
        """
        Agent 2: Video-Level Auditor - "The Content Detective"
        Deconstructs high-performing videos to identify what makes them work.
        Analyzes titles, thumbnails, hooks, storytelling structure, and content patterns.
        Each video is audited separately with individual reports.
        """
        try:
            model_name = create_agent_client_func("agent2")
            
            # Reusable audit framework for individual videos
            base_framework = """You are "The Content Detective" — a YouTube video forensics analyst.

Mission: Perform a deep audit of this video to extract winning patterns across titles, thumbnails, hooks, storytelling, engagement, and SEO.

Output expectations:
- Structured findings including:
  * Video metadata (title, views, likes, publish date, channel info)
  * Title/thumbnail forensics (pattern analysis, psychological triggers)
  * Hook analysis (first 30 seconds breakdown)
  * Storytelling arc (structure, pacing, retention tactics)
  * Engagement patterns (CTR indicators, comment themes)
  * Format classification (tutorial, vlog, review, etc.)
  * SEO keywords and tags
  * Winning elements (what makes this video successful)
  * Overall verdict and recommendations
"""

            individual_audits = []
            
            # ========================================
            # AUDIT EACH VIDEO SEPARATELY
            # ========================================
            for video_url in request.video_urls:
                # PHASE 1: Initial Audit with Tools
                planner_instructions = f"""{request.user_query}

Video to analyze: {video_url}

{base_framework}

Task: Perform a comprehensive audit of this single video using available tools. Produce a detailed, structured report."""

                planner_agent = Agent(
                    name="Video Auditor",
                    instructions=planner_instructions,
                    model=model_name,
                    tools=youtube_tools,
                )

                planner_result = await Runner.run(
                    planner_agent,
                    f"Audit the video at {video_url}"
                )
                initial_report = planner_result.final_output

                # PHASE 2: Critic Review
                critic_instructions = f"""You are a Critic LLM. Review this video audit for:

1. COMPLETENESS: All required sections covered (metadata, title/thumbnail, hook, storytelling, engagement, format, keywords, winning elements, verdict)
2. EVIDENCE: Specific observations and data from the video
3. DEPTH: Actionable insights, not surface-level observations
4. CLARITY: Well-structured and easy to understand
5. ISSUES: Missing elements or areas needing improvement

Video: {video_url}

Audit to review:
{initial_report}

Provide concise critique with actionable recommendations."""

                critic_agent = Agent(
                    name="Audit Critic",
                    instructions=critic_instructions,
                    model=model_name,
                )

                critic_result = await Runner.run(
                    critic_agent,
                    "Review and provide feedback on the audit."
                )
                critique = critic_result.final_output

                # PHASE 3: Refined Audit
                refined_instructions = f"""{request.user_query}

Video: {video_url}

{base_framework}

Initial Audit:
{initial_report}

Critic's Feedback:
{critique}

Task: Produce a REFINED, COMPLETE audit addressing all feedback. Output only the final polished audit report."""

                refined_agent = Agent(
                    name="Refined Auditor",
                    instructions=refined_instructions,
                    model=model_name,
                )

                final_result = await Runner.run(
                    refined_agent,
                    "Deliver the refined audit."
                )
                
                individual_audits.append(VideoAudit(
                    video_url=video_url,
                    audit_report=final_result.final_output
                ))

            # ========================================
            # OPTIONAL: CROSS-VIDEO PATTERN SUMMARY
            # ========================================
            cross_video_summary = None
            if len(request.video_urls) > 1:
                all_audits_text = "\n\n".join([
                    f"VIDEO {i+1}: {audit.video_url}\n{audit.audit_report}"
                    for i, audit in enumerate(individual_audits)
                ])
                
                summary_instructions = f"""You are a Pattern Analyst. Review these individual video audits and identify:

1. Common success patterns across all videos
2. Repeatable formulas for titles, thumbnails, hooks
3. Shared storytelling techniques
4. Universal engagement tactics
5. Actionable recommendations for creating similar content

Individual Audits:
{all_audits_text}

Task: Synthesize cross-video patterns into actionable templates and recommendations."""

                summary_agent = Agent(
                    name="Pattern Synthesizer",
                    instructions=summary_instructions,
                    model=model_name,
                )

                summary_result = await Runner.run(
                    summary_agent,
                    "Identify patterns and create reusable templates."
                )
                cross_video_summary = summary_result.final_output

            return AgentResponse(
                success=True,
                individual_audits=individual_audits,
                cross_video_summary=cross_video_summary
            )
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))