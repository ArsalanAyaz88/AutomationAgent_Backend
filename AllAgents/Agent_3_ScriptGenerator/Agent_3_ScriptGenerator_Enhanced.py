"""
Agent 3: Analytics-Enhanced Script Generator
Now uses YOUR channel's analytics to generate personalized scripts!
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException
from agents import Agent, Runner
from pydantic import BaseModel

# Import RL and Analytics integration
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from agents_ReinforcementLearning.rl_integration import rl_enhanced
from analytics_enhanced_agents import (
    analytics_context,
    enhance_prompt_with_analytics,
    get_channel_context_for_script
)


# Request Models
class ScriptGenerationRequest(BaseModel):
    topic: str
    total_words: Optional[int] = 1500
    tone: Optional[str] = "conversational"
    target_audience: Optional[str] = "general"
    video_duration: Optional[int] = None
    include_hook: Optional[bool] = True
    include_cta: Optional[bool] = True
    script_structure: Optional[str] = "standard"
    key_points: Optional[list[str]] = None
    additional_instructions: Optional[str] = None
    
    # NEW: Analytics integration
    channel_id: Optional[str] = None  # Your YouTube channel ID
    user_id: Optional[str] = "default"
    use_analytics: Optional[bool] = True  # Auto-use analytics if available


class AgentResponse(BaseModel):
    success: bool
    result: str
    error: Optional[str] = None
    rl_learning: Optional[Dict[str, Any]] = None
    analytics_used: Optional[bool] = False  # Indicates if analytics were used
    channel_context: Optional[str] = None  # Analytics summary used


def register_agent3_enhanced_routes(app, create_agent_client_func, youtube_tools=None):
    """Register Analytics-Enhanced Agent 3 routes"""
    
    @app.post("/api/agent3/generate-script-enhanced", response_model=AgentResponse)
    @rl_enhanced("agent3_script_generator")
    async def generate_script_enhanced(request: ScriptGenerationRequest):
        """
        🎯 Analytics-Enhanced Script Generator
        
        NEW FEATURE: Automatically uses your channel's analytics to:
        - Match your successful video style
        - Optimize script length based on what works
        - Use tone that resonates with your audience
        - Structure content like your top performers
        
        If you've tracked your channel, this agent will reference your actual data!
        """
        try:
            model_name = create_agent_client_func("agent3")
            
            # Get analytics context if available
            analytics_data = ""
            channel_used = None
            
            if request.use_analytics:
                # If no channel_id provided, try to get most recent tracked channel
                if not request.channel_id:
                    tracked = await analytics_context.get_tracked_channel(request.user_id)
                    if tracked:
                        request.channel_id = tracked.get('channel_id')
                        channel_used = tracked.get('channel_title')
                
                # Get analytics context
                if request.channel_id:
                    analytics_data = get_channel_context_for_script(
                        request.channel_id,
                        request.topic,
                        request.user_id
                    )
            
            # Base instructions
            base_instructions = f"""You are an expert YouTube script writer.

TASK: Generate a {request.total_words}-word script about: "{request.topic}"

REQUIREMENTS:
- Tone: {request.tone}
- Target Audience: {request.target_audience}
- Structure: {request.script_structure}
- Include Hook: {request.include_hook}
- Include CTA: {request.include_cta}
"""
            
            if request.video_duration:
                base_instructions += f"- Target Duration: ~{request.video_duration} minutes\n"
            
            if request.key_points:
                base_instructions += f"\nKEY POINTS TO COVER:\n"
                for point in request.key_points:
                    base_instructions += f"- {point}\n"
            
            if request.additional_instructions:
                base_instructions += f"\nADDITIONAL INSTRUCTIONS:\n{request.additional_instructions}\n"
            
            # Enhance with analytics if available
            if analytics_data:
                final_instructions = enhance_prompt_with_analytics(
                    base_instructions,
                    analytics_data
                )
                analytics_used = True
            else:
                final_instructions = base_instructions
                analytics_used = False
            
            final_instructions += """

OUTPUT FORMAT:
[HOOK - First 10 seconds]
<Attention-grabbing opening>

[INTRODUCTION]
<Set context and promise value>

[MAIN CONTENT]
<Deliver on the promise with clear sections>

[CONCLUSION]
<Summarize key takeaways>

[CALL TO ACTION]
<Engage viewers: like, subscribe, comment>

Generate ONLY the script content. No meta-commentary or production notes.
"""
            
            # Create agent
            agent = Agent(
                name="enhanced_script_generator",
                model=model_name,
                instructions=final_instructions
            )
            
            # Run agent
            result = await Runner.run(
                agent,
                f"Generate a script about: {request.topic}"
            )
            
            # Extract result
            final_response = result.final_output if hasattr(result, 'final_output') else "No response generated"
            
            # Return with analytics info
            response = AgentResponse(
                success=True,
                result=final_response,
                analytics_used=analytics_used,
                channel_context=channel_used if channel_used else None
            )
            
            return response
            
        except Exception as e:
            return AgentResponse(
                success=False,
                result="",
                error=str(e)
            )
