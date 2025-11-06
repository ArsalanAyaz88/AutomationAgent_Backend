"""
Agent 3: Script Generator - "The Storyteller"
Generates fully customizable YouTube video scripts.

Features:
- Customizable word count, tone, audience, and structure
- Multiple script formats (standard, story-based, tutorial, listicle)
- Flexible key points and additional instructions
- Pure script content - no visuals, voiceover notes, or production cues
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
class ScriptGenerationRequest(BaseModel):
    topic: str
    total_words: Optional[int] = 1500  # Target word count for the script
    tone: Optional[str] = "conversational"  # e.g., conversational, professional, casual, energetic
    target_audience: Optional[str] = "general"  # e.g., beginners, professionals, tech enthusiasts
    video_duration: Optional[int] = None  # Target video duration in minutes
    include_hook: Optional[bool] = True  # Whether to include an attention-grabbing hook
    include_cta: Optional[bool] = True  # Whether to include call-to-action
    script_structure: Optional[str] = "standard"  # standard, story-based, tutorial, listicle
    key_points: Optional[list[str]] = None  # Specific points to cover in the script
    additional_instructions: Optional[str] = None  # Any extra instructions


class AgentResponse(BaseModel):
    success: bool
    result: str
    error: Optional[str] = None
    rl_learning: Optional[Dict[str, Any]] = None


def register_agent3_routes(app, create_agent_client_func, youtube_tools=None):
    """Register Agent 3 routes with the FastAPI app"""
    
    @app.post("/api/agent3/generate-script", response_model=AgentResponse)
    @rl_enhanced("agent3_script_generator")
    async def generate_script(request: ScriptGenerationRequest):
        """
        Agent 3: Script Generator - "The Storyteller"
        Generates fully customizable YouTube video scripts.
        
        Customization Options:
        - Topic (required)
        - Word count target
        - Tone (conversational, professional, casual, energetic)
        - Target audience
        - Video duration
        - Script structure (standard, story-based, tutorial, listicle)
        - Key points to cover
        - Include/exclude hook and CTA
        - Additional custom instructions
        
        Creates pure script content without visuals or voiceover notes.
        """
        try:
            model_name = create_agent_client_func("agent3")
            
            # Build dynamic script instructions based on parameters
            duration_info = f"Target video duration: {request.video_duration} minutes" if request.video_duration else ""
            word_count_info = f"Target word count: {request.total_words} WORDS (not characters, ~{request.total_words * 5} characters)"
            
            # Calculate targets for instructions
            target_paragraphs = request.total_words // 150  # ~150 words per paragraph
            min_chars = request.total_words * 4  # Conservative estimate
            
            # Build structure guidance based on script_structure
            structure_guides = {
                "standard": "Hook → Introduction → Main Content (3-5 sections) → Climax → Conclusion/CTA",
                "story-based": "Opening Hook → Story Setup → Conflict/Challenge → Journey → Resolution → Lesson/CTA",
                "tutorial": "Hook → Problem Statement → Overview → Step-by-Step Instructions → Common Mistakes → Summary/CTA",
                "listicle": "Hook → Introduction → List Items (with explanations) → Bonus Point → Conclusion/CTA"
            }
            structure_guide = structure_guides.get(request.script_structure, structure_guides["standard"])
            
            # Build key points section
            key_points_section = ""
            if request.key_points and len(request.key_points) > 0:
                key_points_section = "\nKey Points to Cover:\n" + "\n".join([f"- {point}" for point in request.key_points])
            
            # Hook and CTA requirements
            hook_requirement = "- Start with a strong hook (under 15 seconds) that grabs attention and creates curiosity" if request.include_hook else ""
            cta_requirement = "- End with a clear and compelling call-to-action (subscribe, comment, like, etc.)" if request.include_cta else ""
            
            # Additional instructions
            extra_instructions = f"\n\nAdditional Requirements:\n{request.additional_instructions}" if request.additional_instructions else ""
            
            # Script generation instructions
            script_instructions = f"""You are "The Storyteller" — a YouTube script writer focused on creating engaging video scripts.

SCRIPT SPECIFICATIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Topic: {request.topic}
Tone: {request.tone}
Target Audience: {request.target_audience}
{word_count_info}
{duration_info}
Script Structure: {request.script_structure}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚨 ABSOLUTE REQUIREMENT - WORD COUNT 🚨
You MUST write EXACTLY {request.total_words} WORDS or MORE. This is NON-NEGOTIABLE!

UNDERSTANDING WORDS vs CHARACTERS:
- 1 word = "Hello" or "Python" or "video" (each counts as 1)
- {request.total_words} WORDS ≈ {request.total_words * 5} CHARACTERS minimum
- Example: "I love making YouTube videos for beginners" = 7 WORDS (not 7 characters!)

MANDATORY LENGTH GUIDELINES:
- For 5000 words: Write approximately 30-35 paragraphs with 150-200 words each
- For 10000 words: Write approximately 60-70 paragraphs with 150-200 words each
- DO NOT stop until you reach the word count
- Each section should be EXTREMELY detailed with examples, stories, explanations
- Add personal anecdotes, step-by-step breakdowns, case studies
- Include multiple examples for each point
- Elaborate on every concept thoroughly

EXPANSION STRATEGY:
- Opening Hook: 200-300 words
- Introduction: 400-500 words
- Each main point/section: 800-1200 words minimum
- Add sub-sections with detailed explanations
- Include "why this matters" for each point
- Add "common mistakes" sections
- Include "pro tips" and "advanced techniques"
- Conclusion: 300-400 words

THIS IS YOUR PRIMARY GOAL: Reach {request.total_words} WORDS (not characters)!

STRUCTURE TO FOLLOW:
{structure_guide}
{key_points_section}

CORE REQUIREMENTS:
{hook_requirement}
- Use {request.tone} tone throughout the script
- Write for {request.target_audience} audience
- Maintain viewer interest with pattern interrupts and open loops
- Use active voice and engaging storytelling
- Natural flow and pacing appropriate for YouTube
- Keep it conversational and relatable
{cta_requirement}

⚠️ LENGTH IS PRIORITY #1:
- Write LONG, DETAILED sections - not short summaries
- Every point needs 200-300 words of explanation minimum
- Add real examples, not just concepts
- Include specific details, numbers, statistics when possible
- Tell stories and create scenarios to illustrate points
- Never rush - take time to explain everything thoroughly
- REMEMBER: {request.total_words} WORDS is your target (approximately {target_paragraphs} paragraphs)

IMPORTANT - DO NOT INCLUDE:
- Visual suggestions or descriptions
- Camera cues or directions
- Voiceover notes or annotations
- Production notes or technical directions
- Timestamps or time markers
- Section headers (like "Hook:", "Introduction:", etc.)
{extra_instructions}

OUTPUT: Pure script text only - exactly what should be said in the video, nothing else. Write as if you're speaking directly to the viewer."""

            # Generate the script
            script_agent = Agent(
                name="Script Generator",
                instructions=script_instructions,
                model=model_name,
            )
            
            result = await Runner.run(
                script_agent,
                f"""CRITICAL MISSION: Write a {request.total_words}-WORD YouTube script for: {request.topic}

VERIFICATION CHECKLIST:
✓ Target: {request.total_words} WORDS (NOT {request.total_words} characters!)
✓ Minimum {min_chars} characters (since average word = 4-5 chars)
✓ Write {target_paragraphs}+ paragraphs of 150-200 words each
✓ DO NOT STOP writing until you have written {request.total_words} words

EXPANSION RULES:
- Never be brief or concise - always elaborate
- Add examples, stories, case studies for every point
- Include "why this matters", "common mistakes", "pro tips"
- Break down complex ideas into detailed explanations
- Add transitional content between sections

START WRITING NOW - Your goal is {request.total_words} WORDS!"""
            )

            return AgentResponse(success=True, result=result.final_output)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

