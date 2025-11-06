"""
RL Integration Layer
Connects existing FastAPI agents with the RL learning system
"""

import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager

# Import our RL system components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents_ReinforcementLearning'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'databasess'))

from agents_ReinforcementLearning.rl_engine import RLEngine, State, Action, YouTubeRewardCalculator
from databasess.agents_STM.redis_memory import AgentSTM, RealtimeMetrics
from databasess.agents_LTM.mongodb_memory import AgentLTM
from databasess.agents_CentralMemory.central_memory import CentralMemoryDB


class RLEnhancedAgent:
    """Wrapper that adds RL capabilities to existing agents"""
    
    def __init__(self, agent_name: str, agent_type: str, capabilities: list):
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.capabilities = capabilities
        
        # Initialize RL components
        self.stm = AgentSTM(agent_name)
        self.ltm = AgentLTM(agent_name)
        self.rl_engine = RLEngine(agent_name)
        self.reward_calculator = YouTubeRewardCalculator()
        self.realtime_metrics = RealtimeMetrics()
        
        # Current session tracking
        self.current_session = {}
    
    async def start_session(self, user_request: str, input_data: Dict[str, Any]) -> str:
        """Start a new learning session"""
        session_id = f"{self.agent_name}_{int(datetime.now().timestamp())}"
        
        # Create state from input data
        state = self._create_state_from_input(input_data)
        
        # Get action recommendation from RL engine
        recommended_action = self.rl_engine.decide_action(state)
        
        self.current_session = {
            'session_id': session_id,
            'user_request': user_request,
            'input_data': input_data,
            'state': state,
            'recommended_action': recommended_action,
            'start_time': datetime.now(),
            'baseline_metrics': input_data.get('current_metrics', {})
        }
        
        return session_id
    
    def _create_state_from_input(self, input_data: Dict[str, Any]) -> State:
        """Convert API input to RL state"""
        # Extract YouTube metrics if available
        video_metrics = input_data.get('video_metrics', {
            'views': input_data.get('views', 0),
            'likes': input_data.get('likes', 0),
            'comments': input_data.get('comments', 0),
            'ctr': input_data.get('ctr', 0.0),
            'engagement_rate': input_data.get('engagement_rate', 0.0)
        })
        
        channel_metrics = input_data.get('channel_metrics', {
            'subscribers': input_data.get('subscribers', 0),
            'total_views': input_data.get('total_views', 0)
        })
        
        # Create temporal context
        now = datetime.now()
        temporal_context = {
            'hour': now.hour,
            'day_of_week': now.weekday(),
            'month': now.month
        }
        
        # Extract content context
        content_context = {
            'input_type': input_data.get('input_type', 'unknown'),
            'channel_id': input_data.get('channel_id', ''),
            'video_url': input_data.get('video_url', ''),
            'user_query': input_data.get('user_query', '')
        }
        
        return State(
            video_metrics=video_metrics,
            channel_metrics=channel_metrics,
            temporal_context=temporal_context,
            content_context=content_context,
            audience_context={}
        )
    
    async def process_result(self, agent_response: str, success: bool = True) -> Dict[str, Any]:
        """Process agent result and update RL system"""
        if not self.current_session:
            return {'error': 'No active session'}
        
        # Calculate performance metrics from response
        performance_metrics = self._analyze_response_quality(agent_response, success)
        
        # Calculate reward
        reward = self._calculate_reward(performance_metrics, success)
        
        # Store experience in STM
        experience = {
            'session_id': self.current_session['session_id'],
            'agent_name': self.agent_name,
            'user_request': self.current_session['user_request'],
            'action': self.current_session['recommended_action'].to_dict(),
            'reward': reward,
            'q_value': 0.0,  # Will be updated by RL engine
            'state': self.current_session['state'].__dict__,
            'response_quality': performance_metrics,
            'success': success,
            'response_length': len(agent_response),
            'processing_time': (datetime.now() - self.current_session['start_time']).total_seconds()
        }
        
        # Store in STM
        exp_id = self.stm.store_experience(experience)
        
        # Update RL engine
        updated_q_value = self.rl_engine.process_feedback(performance_metrics)
        
        # Update Q-value in STM
        self.stm.update_q_value(exp_id, updated_q_value)
        
        # Clear session
        session_summary = {
            'session_id': self.current_session['session_id'],
            'experience_id': exp_id,
            'reward': reward,
            'q_value': updated_q_value,
            'learning_progress': self.rl_engine.get_engine_status()
        }
        
        self.current_session = {}
        
        return session_summary
    
    def _analyze_response_quality(self, response: str, success: bool) -> Dict[str, float]:
        """Analyze quality of agent response"""
        metrics = {
            'success': 1.0 if success else 0.0,
            'response_length_score': min(len(response) / 1000, 1.0),  # Normalize to 1000 chars
            'structure_score': 0.8 if '###' in response or '**' in response else 0.5,  # Has formatting
            'completeness_score': 0.9 if len(response) > 100 else 0.3,  # Substantial response
        }
        
        # Agent-specific quality metrics
        if self.agent_name == 'fifty_videos_fetcher':
            metrics['link_count_score'] = min(response.count('youtube.com/watch') / 50, 1.0)
        elif self.agent_name == 'channel_auditor':
            metrics['analysis_depth'] = 0.9 if 'analysis' in response.lower() else 0.5
        elif self.agent_name == 'title_auditor':
            metrics['title_suggestions'] = min(response.count('Title:') / 3, 1.0)
        
        return metrics
    
    def _calculate_reward(self, performance_metrics: Dict[str, float], success: bool) -> float:
        """Calculate reward for the learning system"""
        if not success:
            return -0.5
        
        # Base reward from performance metrics
        base_reward = sum(performance_metrics.values()) / len(performance_metrics)
        
        # Time-based bonus (faster = better)
        time_taken = (datetime.now() - self.current_session['start_time']).total_seconds()
        time_bonus = max(0, 1.0 - (time_taken / 60))  # Bonus for responses under 1 minute
        
        total_reward = (base_reward * 0.8) + (time_bonus * 0.2)
        
        return min(max(total_reward, -1.0), 1.0)  # Clip to [-1, 1]
    
    async def get_learning_insights(self) -> Dict[str, Any]:
        """Get current learning insights for this agent"""
        try:
            stm_stats = self.stm.get_agent_stats()
            ltm_stats = self.ltm.get_agent_learning_stats()
            rl_status = self.rl_engine.get_engine_status()
            
            return {
                'agent_name': self.agent_name,
                'agent_type': self.agent_type,
                'capabilities': self.capabilities,
                'stm_stats': stm_stats,
                'ltm_stats': ltm_stats,
                'rl_status': rl_status,
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'agent_name': self.agent_name,
                'error': str(e),
                'last_updated': datetime.now().isoformat()
            }


class RLAgentRegistry:
    """Registry to manage RL-enhanced agents"""
    
    def __init__(self):
        self.agents: Dict[str, RLEnhancedAgent] = {}
        self.central_memory = CentralMemoryDB()
        
        # Define agent configurations
        self.agent_configs = {
            'agent1_channel_auditor': {
                'type': 'channel_analyst',
                'capabilities': ['channel_analysis', 'performance_audit', 'competitive_analysis']
            },
            'agent2_title_auditor': {
                'type': 'content_optimizer',
                'capabilities': ['title_optimization', 'thumbnail_analysis', 'hook_creation']
            },
            'agent3_script_generator': {
                'type': 'content_creator',
                'capabilities': ['script_writing', 'content_structure', 'narrative_flow']
            },
            'agent4_script_to_scene': {
                'type': 'visual_processor',
                'capabilities': ['scene_generation', 'visual_prompts', 'storyboarding']
            },
            'agent5_ideas_generator': {
                'type': 'creative_strategist',
                'capabilities': ['idea_generation', 'trend_analysis', 'concept_development']
            },
            'agent6_roadmap': {
                'type': 'strategic_planner',
                'capabilities': ['content_planning', 'roadmap_creation', 'series_development']
            },
            'fifty_videos_fetcher': {
                'type': 'data_collector',
                'capabilities': ['video_fetching', 'link_extraction', 'channel_crawling']
            }
        }
    
    def initialize_agent(self, agent_name: str) -> RLEnhancedAgent:
        """Initialize an RL-enhanced agent"""
        if agent_name in self.agents:
            return self.agents[agent_name]
        
        config = self.agent_configs.get(agent_name, {
            'type': 'generic_agent',
            'capabilities': ['general_processing']
        })
        
        agent = RLEnhancedAgent(
            agent_name=agent_name,
            agent_type=config['type'],
            capabilities=config['capabilities']
        )
        
        self.agents[agent_name] = agent
        
        # Register with central memory (graceful failure if MongoDB unavailable)
        try:
            self.central_memory.register_agent(
                agent_name, 
                config['type'], 
                config['capabilities']
            )
        except Exception as e:
            print(f"⚠️  Could not register {agent_name} with Central Memory: {str(e)[:100]}")
            print(f"   Agent will still work, but collective intelligence features disabled.")
        
        return agent
    
    def get_agent(self, agent_name: str) -> Optional[RLEnhancedAgent]:
        """Get an RL-enhanced agent"""
        return self.agents.get(agent_name)
    
    async def sync_all_agents(self) -> Dict[str, Any]:
        """Sync all agents with central memory"""
        sync_results = {}
        
        for agent_name, agent in self.agents.items():
            try:
                # Get agent learning insights and register with central memory
                insights = await agent.get_learning_insights()
                
                # Register agent with central memory
                try:
                    self.central_memory.register_agent(
                        agent_name, 
                        agent.agent_type, 
                        agent.capabilities
                    )
                except Exception:
                    pass  # Already warned during initialization
                
                sync_results[agent_name] = {
                    'status': 'synced',
                    'insights': insights,
                    'timestamp': datetime.now().isoformat()
                }
            except Exception as e:
                sync_results[agent_name] = {'error': str(e)}
        
        return sync_results
    
    async def get_global_insights(self) -> Dict[str, Any]:
        """Get global insights from central memory"""
        return self.central_memory.get_global_statistics()


# Global registry instance
rl_registry = RLAgentRegistry()


# Decorator to enhance existing agent functions with RL
def rl_enhanced(agent_name: str):
    """Decorator to add RL capabilities to agent functions"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get or create RL agent
            rl_agent = rl_registry.initialize_agent(agent_name)
            
            # Extract request data (assuming first arg is request object)
            request_data = args[0] if args else {}
            if hasattr(request_data, 'dict'):
                input_data = request_data.dict()
            else:
                input_data = kwargs
            
            # Start learning session
            session_id = await rl_agent.start_session(
                user_request=str(input_data),
                input_data=input_data
            )
            
            try:
                # Execute original function
                result = await func(*args, **kwargs)
                
                # Process result for learning
                learning_summary = await rl_agent.process_result(
                    agent_response=str(result),
                    success=True
                )
                
                # Add learning info to response if it's a dict
                if isinstance(result, dict):
                    result['rl_learning'] = {
                        'session_id': session_id,
                        'learning_summary': learning_summary,
                        'agent_insights': await rl_agent.get_learning_insights()
                    }
                
                return result
                
            except Exception as e:
                # Process error for learning
                await rl_agent.process_result(
                    agent_response=str(e),
                    success=False
                )
                raise e
        
        return wrapper
    return decorator


# Helper function to get RL insights
async def get_rl_system_status() -> Dict[str, Any]:
    """Get comprehensive RL system status"""
    global_insights = await rl_registry.get_global_insights()
    
    agent_statuses = {}
    for agent_name, agent in rl_registry.agents.items():
        agent_statuses[agent_name] = await agent.get_learning_insights()
    
    return {
        'global_insights': global_insights,
        'agent_statuses': agent_statuses,
        'total_agents': len(rl_registry.agents),
        'last_updated': datetime.now().isoformat()
    }
