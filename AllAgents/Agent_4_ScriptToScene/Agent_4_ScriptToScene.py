"""
Agent 4: Script-to-Scene Synchronizer - "The Director"
Uses Planner-Critic multi-agent pattern for intelligent task decomposition.
"""

from typing import Optional
import re
import json
import logging
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


logger = logging.getLogger("agent4.script_to_scene")


def register_agent4_routes(app, create_agent_client_func, youtube_tools=None):
    """Register Agent 4 routes with Planner-Critic multi-agent system"""
    # Simple utility to safely get text output from model response object
    def _safe_get_text(model_response):
        """Safely extract text from model response, with fallbacks."""
        try:
            # Most common case - object with final_output attribute
            if hasattr(model_response, 'final_output'):
                return str(model_response.final_output)
            # Second most common - dictionary with 'final_output' key
            elif isinstance(model_response, dict) and 'final_output' in model_response:
                return str(model_response['final_output'])
            # Just convert whatever we got to string
            return str(model_response) if model_response is not None else ""
        except Exception as e:
            logger.exception("Error extracting text from model response")
            return "Error processing response"
    
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

Priority order:
- User-provided instructions, constraints, or preferences take absolute precedence over defaults.
- Only fall back to the guidelines below when the user prompt is silent on a requirement.

Tone & scope guidelines:
- Communicate in a warm, encouraging, YouTube-savvy voice (think collaborative creative partner).
- Keep discussion anchored to YouTube video production, storytelling, or visual execution. Avoid unrelated topics.

Safety & compliance (Veo v3):
- Strictly avoid disallowed content: sexual content or nudity (including minors), graphic violence or gore, hate or harassment, extremist or terrorist content, self-harm, illegal activities, weapons instruction, scams or malware, personal data collection, medical or legal advice, political persuasion, or any content violating local laws.
- Do not depict or identify real private individuals or request biometric identification. If the user provides a real name, anonymize to a neutral role (e.g., "the host", "the narrator", "the survivor"). Avoid using celebrity likenesses or trademarks without permission.
- Use brand-agnostic, generic descriptions. Do not include copyrighted text or logos; describe them generically instead.
- Keep content safe-for-work, non-graphic, and respectful. Do not depict human remains, death, or graphic injury. For traumatic events or accidents, focus on environment and respectful implication (e.g., cutaways, abstract visuals) instead of explicit depiction.
- If the user requests disallowed or sensitive content, briefly state it's not possible and provide a safe alternative within the filmmaking context.
- Never bypass platform safety filters or provide instructions to do so.

Scene segmentation guidelines:
- Analyze the script's narrative shifts, locations, emotions, or beat changes.
- Create as many scenes as required based on the script (one scene if appropriate, otherwise multiple scenes).
- Maintain a continuous timeline. Each scene must span exactly 8 seconds (no more, no less) from its start to end timestamp.

For each scene provide (within its own Markdown ```json code block):
1. "scene": Clear label with scene number and descriptive title.
2. "duration": Start-end time (e.g., "0:00-0:08") — must equal 8 seconds.
3. "character": Primary speaker or focus (use generic roles like "narrator", "host", "the subject" - NEVER use real names of private individuals).
4. "segments": Nested object covering the full 0-8 second range (e.g., "0-2s", "2-5s", "5-8s") describing visual beats.
5. "sound": Ambience or SFX.
6. "voiceover": Spoken line for the scene.
7. Optional fields (e.g., "camera", "notes") are allowed if helpful. Add a "notes" field with safety information.

Shot Types: EWS, WS, MS, MCU, CU, ECU
Angles: Eye level, High, Low, Dutch, Bird's eye, Worm's eye
Movement: Static, Pan, Tilt, Dolly, Tracking, Crane, Handheld, Gimbal
Lighting: Three-point, Natural, High key, Low key, Silhouette
Pacing: Fast (3-8s), Balanced (8-15s), Cinematic (15-30s)

Final Output Requirement:
- Present each scene as a separate ```json code block so it can be copied easily.
- Ensure scene objects are valid JSON (double quotes, comma-separated pairs, etc.)."""
            
            # ========================================
            # PHASE 1: PLANNER AGENT
            # ========================================
            planner_instructions = f"""You are a professional scene director. Your job is to immediately convert the script below into detailed visual scene prompts.

DO NOT explain what you can do. DO NOT ask questions. START IMMEDIATELY with the scene breakdown.

{base_framework}

Script to convert:
{request.script}

IMPORTANT: Output the scene-by-scene breakdown NOW. Each scene should be in its own ```json code block."""
            
            planner_agent = Agent(
                name="Planner LLM",
                instructions=planner_instructions,
                model=model_name,
            )
            
            # Execute Planner
            planner_result = await Runner.run(
                planner_agent, 
                "Output the complete scene breakdown NOW in the required format. Start with Scene 1."
            )
            initial_plan = planner_result.final_output
            
            # ========================================
            # PHASE 2: CRITIC AGENT
            # ========================================
            critic_instructions = f"""You are a Critic LLM. Review the scene breakdown plan below and identify:

1. USER COMPLIANCE: Does the plan follow every explicit instruction from the user prompt (formatting, focus, counts, tone, etc.)?
2. VEO V3 COMPLIANCE: Does every scene and description comply with the Safety & Compliance rules (no sexual content, graphic violence, hate, self-harm, illegal activity, political persuasion, medical/legal advice, personal data, copyrighted logos, or attempts to bypass safety)? If any risk is found, propose a safe rewrite.
   - Check specifically for: identification of real private individuals (names, likenesses) and any depiction of human remains, death, or graphic injury. Require anonymization and non-explicit treatment.
3. FRIENDLY YOUTUBE TONE: Is the narration/supportive language warm, collaborative, and clearly tied to YouTube filmmaking?
4. COMPLETENESS: Are ALL parts of the script covered with the right number of scenes?
5. TIMING ACCURACY: Does every scene span exactly 8 seconds between start and end timestamps?
6. SEGMENT COVERAGE: Do the "segments" keys cover the entire 0-8 second window with no gaps/overlap?
7. JSON FORMAT: Is each scene provided as a standalone ```json code block with valid JSON structure and required keys?
8. CONSISTENCY: Is visual style coherent across scenes when needed?
9. MISSING ELEMENTS: Any missing shots, lighting, sound, or voiceover details?
10. TECHNICAL QUALITY: Are details production-ready and unambiguous?
11. ISSUES FOUND: List specific problems
12. RECOMMENDATIONS: How to improve the plan safely

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
            refined_planner_instructions = f"""You are refining your scene breakdown. Output the final, complete scene-by-scene breakdown immediately.

{base_framework}

Original Script:
{request.script}

Your Initial Plan:
{initial_plan}

Critic's Feedback:
{critique}

Task: Create a REFINED, COMPLETE scene breakdown that addresses all issues raised by the Critic.
Follow every explicit user directive before applying defaults. Maintain a friendly, YouTube-focused tone. Ensure every scene is exactly 8 seconds long, uses valid JSON structure inside its own ```json code block, and includes complete details (duration, character, segments, sound, voiceover, plus any supporting notes).
Strictly enforce Veo v3 Safety & Compliance: if the script implies unsafe content, reframe with safe, generic, non-graphic alternatives and clearly state the changes in "notes". Do not identify real private individuals; anonymize roles. Do not depict human remains, death, or graphic injury; use respectful cutaways or abstract visuals instead.

Output format requirements (mandatory):
- Output each scene separately, never inside a single JSON array.
- For each scene, first write a short heading like: Scene X — Title
- Immediately follow the heading with a fenced code block using exactly this syntax:

```json
{
  "scene": "Scene X - Title",
  "duration": "0:00-0:08",
  "character": "the narrator", 
  "segments": [{"time": "0-4s", "visual": "Safe description"}, {"time": "4-8s", "visual": "Safe description"}],
  "sound": "Description",
  "voiceover": "Text",
  "notes": "Safety information" 
}
```

- Do not include any other prose between scenes, other than the heading and its JSON block.
- Ensure JSON is valid (double quotes, commas) and copyable.
"""
            
            refined_planner_agent = Agent(
                name="Refined Planner LLM",
                instructions=refined_planner_instructions,
                model=model_name,
            )
            
            # Execute Refined Planner
            final_result = await Runner.run(
                refined_planner_agent, 
                "Output the final scene breakdown NOW. Start with Scene 1 in a ```json code block."
            )
            # Use our safe helper to get text
            result_text = _safe_get_text(final_result)
            return AgentResponse(success=True, result=result_text)
            
        except Exception as e:
            logger.exception("Agent 4 script_to_prompts execution failed")
            raise HTTPException(status_code=500, detail=str(e))
