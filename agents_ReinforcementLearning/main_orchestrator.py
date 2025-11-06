"""
Main Orchestrator - YouTube Agents Reinforcement Learning System
Initializes and runs the complete RL system with memory hierarchy
"""

import asyncio
import json
import signal
import os
from typing import Dict, List, Any
from datetime import datetime
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from memory_integration import CollectiveIntelligenceOrchestrator, IntegrationConfig
from rl_engine import RLEngine, State, Action
from agents_STM.redis_memory import RealtimeMetrics
from agents_CentralMemory.central_memory import CentralMemoryDB


class YouTubeAgentSystem:
    """Main system controller for YouTube RL agents"""
    
    def __init__(self, config_file: str = None):
        # Load configuration
        self.config = self._load_config(config_file)
        
        # Initialize logging
        self._setup_logging()
        self.logger = logging.getLogger("YouTubeAgentSystem")
        
        # Initialize orchestrator
        integration_config = IntegrationConfig(
            stm_to_ltm_threshold=self.config.get('stm_to_ltm_threshold', 0.7),
            sync_interval_minutes=self.config.get('sync_interval_minutes', 30),
            max_stm_experiences=self.config.get('max_stm_experiences', 1000)
        )
        
        self.orchestrator = CollectiveIntelligenceOrchestrator(integration_config)
        self.central_memory = CentralMemoryDB()
        self.realtime_metrics = RealtimeMetrics()
        
        # System state
        self.is_running = False
        self.agent_definitions = self._get_agent_definitions()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _load_config(self, config_file: str = None) -> Dict[str, Any]:
        """Load system configuration"""
        default_config = {
            'stm_to_ltm_threshold': 0.7,
            'sync_interval_minutes': 30,
            'max_stm_experiences': 1000,
            'log_level': 'INFO',
            'youtube_api_key': '',  # To be set by user
            'redis_host': 'localhost',
            'redis_port': 6379,
            'mongodb_uri': 'mongodb://localhost:27017',
            'agents': {
                'fifty_videos_fetcher': {
                    'type': 'content_collector',
                    'capabilities': ['video_fetching', 'link_extraction', 'channel_analysis']
                }
                # Additional agents can be defined here
            }
        }
        
        if config_file and Path(config_file).exists():
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                print(f"Warning: Could not load config file {config_file}: {e}")
        
        return default_config
    
    def _setup_logging(self):
        """Setup system logging"""
        log_level = getattr(logging, self.config.get('log_level', 'INFO'))
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('youtube_agent_system.log'),
                logging.StreamHandler()
            ]
        )
    
    def _get_agent_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Define the 7 YouTube agents and their capabilities"""
        return {
            'fifty_videos_fetcher': {
                'type': 'content_collector',
                'capabilities': ['video_fetching', 'link_extraction', 'channel_analysis'],
                'description': 'Fetches latest video links and analyzes channel content'
            },
            'trend_analyzer': {
                'type': 'trend_detector',
                'capabilities': ['trend_analysis', 'viral_prediction', 'content_timing'],
                'description': 'Analyzes trending topics and optimal content timing'
            },
            'engagement_optimizer': {
                'type': 'engagement_specialist', 
                'capabilities': ['title_optimization', 'thumbnail_analysis', 'ctr_improvement'],
                'description': 'Optimizes titles, thumbnails, and engagement metrics'
            },
            'audience_analyzer': {
                'type': 'audience_specialist',
                'capabilities': ['demographic_analysis', 'behavior_tracking', 'retention_optimization'],
                'description': 'Analyzes audience behavior and optimizes retention'
            },
            'content_strategist': {
                'type': 'strategy_planner',
                'capabilities': ['content_planning', 'series_development', 'topic_research'],
                'description': 'Plans content strategy and develops video series'
            },
            'performance_tracker': {
                'type': 'analytics_specialist',
                'capabilities': ['metrics_tracking', 'performance_analysis', 'roi_calculation'],
                'description': 'Tracks performance metrics and calculates ROI'
            },
            'monetization_optimizer': {
                'type': 'revenue_specialist',
                'capabilities': ['ad_optimization', 'sponsorship_analysis', 'revenue_maximization'],
                'description': 'Optimizes monetization and revenue strategies'
            }
        }
    
    async def initialize_agents(self) -> Dict[str, Any]:
        """Initialize all 7 agents in the system"""
        initialization_results = {}
        
        self.logger.info("Initializing YouTube RL Agent System...")
        
        for agent_id, agent_config in self.agent_definitions.items():
            try:
                self.logger.info(f"Initializing agent: {agent_id}")
                
                # Register agent with orchestrator
                integrator = self.orchestrator.register_agent(
                    agent_id=agent_id,
                    agent_type=agent_config['type'],
                    capabilities=agent_config['capabilities']
                )
                
                # Initialize RL engine for the agent
                rl_engine = RLEngine(agent_id)
                
                initialization_results[agent_id] = {
                    'status': 'initialized',
                    'type': agent_config['type'],
                    'capabilities': agent_config['capabilities'],
                    'integrator': integrator,
                    'rl_engine': rl_engine,
                    'timestamp': datetime.now().isoformat()
                }
                
                self.logger.info(f"Agent {agent_id} initialized successfully")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize agent {agent_id}: {str(e)}")
                initialization_results[agent_id] = {
                    'status': 'failed',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
        
        successful_agents = len([r for r in initialization_results.values() if r['status'] == 'initialized'])
        self.logger.info(f"System initialization complete: {successful_agents}/{len(self.agent_definitions)} agents initialized")
        
        return initialization_results
    
    async def simulate_agent_action(self, agent_id: str, youtube_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate an agent taking action based on YouTube data"""
        
        if agent_id not in self.agent_definitions:
            return {'error': f'Agent {agent_id} not found'}
        
        try:
            # Get agent's integrator
            integrator = self.orchestrator.agent_integrators.get(agent_id)
            if not integrator:
                return {'error': f'Agent {agent_id} not initialized'}
            
            # Create state from YouTube data
            state = integrator.rl_engine.observe_environment(
                youtube_metrics=youtube_data.get('metrics', {}),
                context_data=youtube_data.get('context', {})
            )
            
            # Decide action
            action = integrator.rl_engine.decide_action(state)
            
            # Simulate action execution (in real system, this would call YouTube API)
            simulated_results = self._simulate_action_results(action, youtube_data)
            
            # Process feedback
            updated_q_value = integrator.rl_engine.process_feedback(simulated_results)
            
            # Store experience in STM
            experience_id = integrator.stm.store_experience({
                'action': action.action_type.value,
                'action_params': action.parameters,
                'q_value': updated_q_value,
                'reward': simulated_results.get('reward', 0.0),
                'state': state.__dict__,
                'youtube_metrics_before': youtube_data.get('metrics', {}),
                'youtube_metrics_after': simulated_results
            })
            
            return {
                'agent_id': agent_id,
                'action': action.to_dict(),
                'state_summary': {
                    'video_views': state.video_metrics.get('views', 0),
                    'channel_subscribers': state.channel_metrics.get('subscribers', 0),
                    'engagement_rate': state.video_metrics.get('engagement_rate', 0.0)
                },
                'results': simulated_results,
                'q_value': updated_q_value,
                'experience_id': experience_id,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in agent action simulation: {str(e)}")
            return {'error': str(e)}
    
    def _simulate_action_results(self, action: Action, original_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate results of an action (placeholder for real YouTube API integration)"""
        
        # Simulate improved metrics based on action type
        base_metrics = original_data.get('metrics', {}).get('video_metrics', {})
        
        improvement_factors = {
            'upload_time_optimization': {'views': 1.1, 'engagement_rate': 1.05},
            'title_optimization': {'views': 1.15, 'ctr': 1.2},
            'thumbnail_optimization': {'ctr': 1.3, 'views': 1.2},
            'content_strategy': {'views': 1.25, 'watch_time': 1.15},
            'audience_engagement': {'likes': 1.4, 'comments': 1.3, 'engagement_rate': 1.2}
        }
        
        action_type = action.action_type.value
        factors = improvement_factors.get(action_type, {'views': 1.0})
        
        # Apply improvements with some randomness
        import random
        simulated_metrics = {}
        
        for metric, base_value in base_metrics.items():
            if metric in factors:
                # Apply improvement with ±20% randomness
                improvement = factors[metric]
                randomness = random.uniform(0.8, 1.2)
                new_value = base_value * improvement * randomness
            else:
                # Small random change
                new_value = base_value * random.uniform(0.95, 1.05)
            
            simulated_metrics[metric] = max(0, new_value)
        
        # Calculate reward based on improvement
        reward = 0.0
        for metric, new_value in simulated_metrics.items():
            old_value = base_metrics.get(metric, 0)
            if old_value > 0:
                improvement = (new_value - old_value) / old_value
                reward += improvement * 0.2  # Weight each metric improvement
        
        return {
            **simulated_metrics,
            'reward': min(max(reward, -1.0), 1.0),  # Clip reward to [-1, 1]
            'simulation': True,
            'action_confidence': action.confidence
        }
    
    async def run_system_demo(self) -> Dict[str, Any]:
        """Run a demonstration of the complete system"""
        
        self.logger.info("Starting YouTube RL Agent System Demo...")
        
        # Step 1: Initialize agents
        init_results = await self.initialize_agents()
        
        # Step 2: Simulate some YouTube data
        sample_youtube_data = {
            'metrics': {
                'video_metrics': {
                    'views': 10000,
                    'likes': 500,
                    'comments': 50,
                    'shares': 25,
                    'watch_time_seconds': 120000,
                    'ctr': 0.05,
                    'engagement_rate': 0.055
                },
                'channel_metrics': {
                    'subscribers': 50000,
                    'total_views': 1000000,
                    'avg_engagement_rate': 0.04
                }
            },
            'context': {
                'content_context': {
                    'video_category': 'education',
                    'duration_minutes': 15,
                    'language': 'en'
                },
                'audience_context': {
                    'primary_demographic': '25-34',
                    'geographic_region': 'US',
                    'device_type': 'mobile'
                }
            }
        }
        
        # Step 3: Run agent actions
        agent_actions = {}
        for agent_id in list(self.agent_definitions.keys())[:3]:  # Demo with first 3 agents
            action_result = await self.simulate_agent_action(agent_id, sample_youtube_data)
            agent_actions[agent_id] = action_result
            
            # Small delay between actions
            await asyncio.sleep(1)
        
        # Step 4: Run collective intelligence cycle
        self.logger.info("Running collective intelligence cycle...")
        collective_results = await self.orchestrator.run_collective_cycle()
        
        # Step 5: Get system status
        system_status = await self.get_system_status()
        
        demo_results = {
            'initialization': init_results,
            'agent_actions': agent_actions,
            'collective_intelligence': collective_results,
            'system_status': system_status,
            'demo_completed': datetime.now().isoformat()
        }
        
        self.logger.info("Demo completed successfully!")
        return demo_results
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        
        # Get global statistics
        global_stats = self.central_memory.get_global_statistics()
        
        # Get agent statuses
        agent_statuses = {}
        for agent_id, integrator in self.orchestrator.agent_integrators.items():
            try:
                status = integrator.get_integration_status()
                agent_statuses[agent_id] = status
            except Exception as e:
                agent_statuses[agent_id] = {'error': str(e)}
        
        # Get orchestrator stats
        orchestrator_stats = self.orchestrator.orchestrator_stats
        
        return {
            'system_info': {
                'total_agents': len(self.agent_definitions),
                'active_agents': len(self.orchestrator.agent_integrators),
                'system_uptime': datetime.now().isoformat(),
                'configuration': {
                    'stm_to_ltm_threshold': self.orchestrator.config.stm_to_ltm_threshold,
                    'sync_interval_minutes': self.orchestrator.config.sync_interval_minutes
                }
            },
            'global_statistics': global_stats,
            'agent_statuses': agent_statuses,
            'orchestrator_stats': orchestrator_stats,
            'last_updated': datetime.now().isoformat()
        }
    
    async def start_continuous_operation(self):
        """Start continuous system operation"""
        self.is_running = True
        self.logger.info("Starting continuous YouTube RL Agent System operation...")
        
        # Initialize agents
        await self.initialize_agents()
        
        # Start continuous integration
        await self.orchestrator.start_continuous_integration()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.is_running = False
    
    def save_system_config(self, filename: str = "system_config.json"):
        """Save current system configuration"""
        config_data = {
            'config': self.config,
            'agent_definitions': self.agent_definitions,
            'saved_at': datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        self.logger.info(f"System configuration saved to {filename}")


async def main():
    """Main entry point"""
    
    print("🚀 YouTube Agent Reinforcement Learning System")
    print("=" * 50)
    
    # Create system instance
    system = YouTubeAgentSystem()
    
    try:
        # Run demonstration
        demo_results = await system.run_system_demo()
        
        # Print demo results summary
        print("\n📊 Demo Results Summary:")
        print(f"Agents Initialized: {len(demo_results['initialization'])}")
        print(f"Actions Executed: {len(demo_results['agent_actions'])}")
        
        collective_info = demo_results['collective_intelligence'].get('cycle_info', {})
        print(f"Collective Intelligence Cycle: {'✅ Success' if collective_info.get('success') else '❌ Failed'}")
        print(f"Cycle Duration: {collective_info.get('duration_seconds', 0):.2f}s")
        
        # Save results
        with open('demo_results.json', 'w') as f:
            json.dump(demo_results, f, indent=2, default=str)
        
        print(f"\n💾 Full results saved to demo_results.json")
        print(f"📋 System logs saved to youtube_agent_system.log")
        
        # Ask if user wants to continue with live operation
        print(f"\n🔄 Demo completed! Would you like to start continuous operation? (y/n)")
        
        # For demo purposes, we'll just show the status
        system_status = demo_results['system_status']
        print(f"\n📈 System Status:")
        print(f"Total Agents: {system_status['system_info']['total_agents']}")
        print(f"Active Agents: {system_status['system_info']['active_agents']}")
        print(f"Global Insights: {system_status['global_statistics']['system_overview']['total_global_insights']}")
        
    except Exception as e:
        print(f"❌ System error: {str(e)}")
        logging.error(f"System error: {str(e)}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
