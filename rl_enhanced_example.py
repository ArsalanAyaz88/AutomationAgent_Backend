"""
Example: How to Enhance Existing Agents with RL Learning
This shows the complete integration of Agent 1 (Channel Auditor) with RL capabilities
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException
from agents import Agent, Runner
from pydantic import BaseModel
import json
from datetime import datetime

# Import RL integration
from rl_integration import rl_enhanced, rl_registry


# Enhanced Request Model with RL tracking
class ChannelAuditRequest(BaseModel):
    input: str
    user_query: str = "Deep audit of this YouTube channel to identify hot patterns"
    # Additional RL tracking fields
    channel_metrics: Optional[Dict[str, Any]] = None
    baseline_performance: Optional[Dict[str, Any]] = None
    

class EnhancedAgentResponse(BaseModel):
    success: bool
    result: str
    error: Optional[str] = None
    # RL learning data included in response
    rl_learning: Optional[Dict[str, Any]] = None


def register_enhanced_agent1_routes(app, create_agent_client_func, youtube_tools):
    """Enhanced Agent 1 with RL learning capabilities"""
    
    @app.post("/api/agent1/audit-channel-rl", response_model=EnhancedAgentResponse)
    @rl_enhanced("agent1_channel_auditor")  # This decorator adds RL learning
    async def audit_channel_with_rl(request: ChannelAuditRequest):
        """
        Enhanced Channel Auditor with Reinforcement Learning
        
        This agent now:
        1. Learns from each audit request
        2. Improves audit quality over time  
        3. Shares insights with other agents
        4. Adapts based on user feedback
        """
        try:
            # Get the RL-enhanced agent for additional insights
            rl_agent = rl_registry.get_agent("agent1_channel_auditor")
            
            # Get historical insights if available
            learning_insights = None
            if rl_agent:
                learning_insights = await rl_agent.get_learning_insights()
            
            model_name = create_agent_client_func("agent1")
            
            # Enhanced instructions that incorporate RL learning
            agent_instructions = f"""{request.user_query}

User Input: {request.input}

You are the "Channel Auditor" - an AI agent that performs deep YouTube channel analysis and learns from each interaction.

**RL Learning Context:**
{f"Previous Learning: Based on {learning_insights['stm_stats']['total_experiences']} past audits, with {learning_insights['stm_stats']['avg_reward']:.3f} average performance." if learning_insights else "This is a new learning session."}

**Enhanced Mission with Learning:**
1. **Deep Channel Analysis**: Analyze the channel's content strategy, performance patterns, and growth indicators
2. **Pattern Recognition**: Identify successful video patterns, optimal posting times, and engagement triggers  
3. **Competitive Intelligence**: Compare with similar channels and identify competitive advantages
4. **Growth Opportunities**: Provide actionable recommendations for channel optimization
5. **Learning Integration**: Apply insights from previous successful audits

**Advanced Analysis Framework:**
- Content Performance Matrix (views, engagement, retention)
- Audience Behavior Analysis (demographics, viewing patterns)
- Optimization Recommendations (titles, thumbnails, timing)
- Growth Strategy Roadmap (short-term and long-term)
- Competitive Positioning Analysis

**Output Format:**
```
# 🔍 ENHANCED CHANNEL AUDIT REPORT

## 📊 Channel Performance Overview
[Comprehensive metrics analysis]

## 🎯 Success Pattern Analysis  
[Identify what works best for this channel]

## 🚀 Growth Opportunities
[Specific, actionable recommendations]

## 📈 Optimization Strategy
[Data-driven improvement plan]

## 🧠 RL Insights Applied
[How previous learning enhanced this audit]
```

**Quality Standards:**
- Provide specific, actionable insights
- Include quantitative analysis where possible
- Reference successful patterns from the channel's history
- Suggest concrete next steps
- Explain the reasoning behind recommendations

Apply any relevant patterns from previous successful audits to enhance this analysis."""

            # Create enhanced agent with learning context
            agent = Agent(
                name="Enhanced Channel Auditor with RL",
                instructions=agent_instructions,
                model=model_name,
                tools=youtube_tools,
            )

            # Execute the agent
            result = await Runner.run(
                agent,
                "Perform an enhanced channel audit incorporating RL learning insights."
            )

            # The @rl_enhanced decorator will automatically:
            # 1. Create a learning session
            # 2. Store the experience in STM
            # 3. Update Q-values based on performance  
            # 4. Add rl_learning data to the response
            
            return EnhancedAgentResponse(
                success=True, 
                result=result.final_output,
                # rl_learning will be added by the decorator
            )
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    
    @app.get("/api/agent1/learning-progress")
    async def get_agent1_learning_progress():
        """Get learning progress for Channel Auditor agent"""
        rl_agent = rl_registry.get_agent("agent1_channel_auditor")
        if not rl_agent:
            return {"error": "RL agent not initialized"}
        
        return await rl_agent.get_learning_insights()
    
    
    @app.post("/api/agent1/feedback")
    async def provide_feedback(session_id: str, rating: float, feedback: str):
        """Provide feedback on agent performance for learning"""
        rl_agent = rl_registry.get_agent("agent1_channel_auditor")
        if not rl_agent:
            raise HTTPException(status_code=404, detail="RL agent not found")
        
        # Update the experience with user feedback
        # This helps the RL system learn what users consider high-quality responses
        feedback_reward = (rating - 3) / 2  # Convert 1-5 rating to -1 to 1 reward
        
        # Store feedback as additional experience
        feedback_experience = {
            'session_id': session_id,
            'user_feedback': feedback,
            'user_rating': rating,
            'feedback_reward': feedback_reward,
            'feedback_timestamp': datetime.now().isoformat()
        }
        
        exp_id = rl_agent.stm.store_experience(feedback_experience)
        
        return {
            "success": True,
            "message": "Feedback received and integrated into learning system",
            "experience_id": exp_id
        }


# Example of how the RL system learns and improves:

class RLLearningExample:
    """
    Example showing how the RL system learns and improves over time
    """
    
    def __init__(self):
        self.example_learning_progression = {
            "session_1": {
                "user_request": "Audit MrBeast channel",
                "agent_response": "Basic audit with generic recommendations",
                "user_feedback": "Too generic, needs more specific insights",
                "rating": 2.0,
                "reward": -0.5,
                "q_value": 0.1,
                "learning": "Agent learns that generic responses get low rewards"
            },
            "session_15": {
                "user_request": "Audit PewDiePie channel", 
                "agent_response": "Detailed analysis with specific metrics and actionable insights",
                "user_feedback": "Excellent analysis, very helpful recommendations",
                "rating": 5.0,
                "reward": 1.0,
                "q_value": 0.8,
                "learning": "Agent learns that detailed, specific analysis gets high rewards"
            },
            "session_50": {
                "user_request": "Audit tech review channel",
                "agent_response": "Comprehensive audit applying learned patterns from similar channels",
                "user_feedback": "Perfect audit, applied relevant insights from similar channels",
                "rating": 5.0, 
                "reward": 1.0,
                "q_value": 0.95,
                "learning": "Agent now applies cross-channel insights effectively"
            }
        }
    
    def get_learning_progression(self):
        return self.example_learning_progression


# Integration checklist for existing agents:
INTEGRATION_CHECKLIST = """
✅ RL Integration Checklist for Existing Agents:

1. **Import RL System**
   - Add: from rl_integration import rl_enhanced
   
2. **Enhance Request Models** 
   - Add optional RL tracking fields (metrics, baselines)
   
3. **Add RL Decorator**
   - Add: @rl_enhanced("agent_name") to endpoint functions
   
4. **Update Response Models**
   - Include: rl_learning: Optional[Dict[str, Any]] = None
   
5. **Add Learning Endpoints**
   - GET /api/{agent}/learning-progress
   - POST /api/{agent}/feedback
   
6. **Enhance Instructions**
   - Include learning context in agent instructions
   - Reference previous successful patterns
   
7. **Test Integration**
   - Verify STM storage works
   - Check learning progression over time
   - Validate central memory sync

🔄 **Automatic RL Benefits After Integration:**
- Agents learn from each interaction
- Performance improves over time
- Successful patterns are shared across agents  
- User feedback drives optimization
- Global insights enhance all agents
- Adaptive behavior based on results

📈 **Expected Results:**
- Week 1: Basic learning pattern establishment
- Week 2-4: Noticeable improvement in response quality
- Month 2-3: Sophisticated pattern recognition and application
- Month 6+: Highly optimized, adaptive agent behaviors
"""


if __name__ == "__main__":
    print("RL Enhanced Agent Example")
    print("=" * 50)
    
    example = RLLearningExample()
    progression = example.get_learning_progression()
    
    for session, data in progression.items():
        print(f"\n{session.upper()}:")
        print(f"Request: {data['user_request']}")
        print(f"Response Quality: {data['rating']}/5")
        print(f"Q-Value: {data['q_value']}")
        print(f"Learning: {data['learning']}")
    
    print(f"\n{INTEGRATION_CHECKLIST}")
