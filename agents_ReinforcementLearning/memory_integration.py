"""
Memory Integration Loop - Collective Intelligence Orchestrator
Coordinates STM -> LTM -> Central Memory flow for all agents
"""

import asyncio
import time
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
from enum import Enum
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import memory systems
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'databasess'))

from agents_STM.redis_memory import AgentSTM, RealtimeMetrics
from agents_LTM.mongodb_memory import AgentLTM  
from agents_CentralMemory.central_memory import CentralMemoryDB
from .rl_engine import RLEngine, State, Action, YouTubeRewardCalculator


class IntegrationPhase(Enum):
    """Memory integration phases"""
    STM_COLLECTION = "stm_collection"
    LTM_PROMOTION = "ltm_promotion"
    CENTRAL_SYNC = "central_sync"
    INSIGHT_BROADCAST = "insight_broadcast"
    STRATEGY_UPDATE = "strategy_update"


@dataclass
class IntegrationConfig:
    """Configuration for memory integration"""
    stm_to_ltm_threshold: float = 0.7  # Q-value threshold for LTM promotion
    sync_interval_minutes: int = 30     # How often to sync with central memory
    max_stm_experiences: int = 1000     # Max STM experiences before cleanup
    ltm_cleanup_days: int = 30          # Days to keep low-value LTM data
    insight_confidence_threshold: float = 0.6  # Min confidence for actionable insights
    
    # Performance thresholds
    urgent_reward_threshold: float = 0.9   # Trigger urgent insight sharing
    poor_performance_threshold: float = -0.5  # Trigger intervention


class AgentMemoryIntegrator:
    """Manages memory integration for a single agent"""
    
    def __init__(self, agent_id: str, agent_type: str, capabilities: List[str], config: IntegrationConfig = None):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.config = config or IntegrationConfig()
        
        # Initialize memory systems
        self.stm = AgentSTM(agent_id)
        self.ltm = AgentLTM(agent_id)
        self.central_memory = CentralMemoryDB()
        self.rl_engine = RLEngine(agent_id)
        self.realtime_metrics = RealtimeMetrics()
        
        # Integration state
        self.last_sync_time = datetime.now()
        self.integration_stats = {
            'total_integrations': 0,
            'stm_to_ltm_promotions': 0,
            'central_syncs': 0,
            'insights_received': 0,
            'strategies_updated': 0
        }
        
        # Register agent in central memory
        self.central_memory.register_agent(agent_id, agent_type, capabilities)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(f"MemoryIntegrator-{agent_id}")
    
    async def run_integration_cycle(self) -> Dict[str, Any]:
        """Run complete memory integration cycle"""
        cycle_start = time.time()
        results = {}
        
        try:
            # Phase 1: STM Collection and Analysis
            self.logger.info(f"Starting integration cycle for agent {self.agent_id}")
            stm_results = await self._process_stm_data()
            results['stm_processing'] = stm_results
            
            # Phase 2: LTM Promotion
            ltm_results = await self._promote_to_ltm(stm_results['high_value_experiences'])
            results['ltm_promotion'] = ltm_results
            
            # Phase 3: Central Memory Sync
            central_results = await self._sync_with_central_memory()
            results['central_sync'] = central_results
            
            # Phase 4: Apply Global Insights
            insight_results = await self._apply_global_insights(central_results.get('insights', []))
            results['insight_application'] = insight_results
            
            # Phase 5: Update Learning Strategy
            strategy_results = await self._update_learning_strategy(central_results.get('strategies', []))
            results['strategy_update'] = strategy_results
            
            # Update integration stats
            self.integration_stats['total_integrations'] += 1
            self.last_sync_time = datetime.now()
            
            cycle_duration = time.time() - cycle_start
            results['cycle_performance'] = {
                'duration_seconds': cycle_duration,
                'success': True,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"Integration cycle completed in {cycle_duration:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Integration cycle failed: {str(e)}")
            results['error'] = str(e)
            results['cycle_performance'] = {
                'duration_seconds': time.time() - cycle_start,
                'success': False,
                'timestamp': datetime.now().isoformat()
            }
        
        return results
    
    async def _process_stm_data(self) -> Dict[str, Any]:
        """Process STM data and identify high-value experiences"""
        
        # Get recent experiences from STM
        recent_experiences = self.stm.get_recent_experiences(self.config.max_stm_experiences)
        
        # Get high Q-value experiences for LTM promotion
        high_value_experiences = self.stm.get_high_q_experiences(
            q_threshold=self.config.stm_to_ltm_threshold,
            limit=100
        )
        
        # Get agent stats
        agent_stats = self.stm.get_agent_stats()
        
        return {
            'total_stm_experiences': len(recent_experiences),
            'high_value_experiences': high_value_experiences,
            'agent_stats': agent_stats,
            'promotion_candidates': len(high_value_experiences)
        }
    
    async def _promote_to_ltm(self, high_value_experiences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Promote high-value STM experiences to LTM"""
        
        promoted_count = 0
        promotion_errors = []
        
        for experience in high_value_experiences:
            try:
                # Store in LTM
                ltm_id = self.ltm.store_high_value_experience(experience)
                promoted_count += 1
                
                # Optional: Remove from STM to save memory (keep most recent)
                # This is handled by Redis TTL automatically
                
            except Exception as e:
                promotion_errors.append({
                    'experience_id': experience.get('id', 'unknown'),
                    'error': str(e)
                })
        
        self.integration_stats['stm_to_ltm_promotions'] += promoted_count
        
        return {
            'promoted_count': promoted_count,
            'errors': promotion_errors,
            'success_rate': promoted_count / len(high_value_experiences) if high_value_experiences else 1.0
        }
    
    async def _sync_with_central_memory(self) -> Dict[str, Any]:
        """Sync LTM data with central memory and get global insights"""
        
        # Get LTM summary for central sync
        ltm_stats = self.ltm.get_agent_learning_stats()
        best_experiences = self.ltm.get_best_experiences(limit=50)
        
        ltm_summary = {
            **ltm_stats,
            'best_experiences': best_experiences,
            'sync_timestamp': datetime.now().isoformat()
        }
        
        # Sync with central memory
        global_insights = self.central_memory.sync_agent_data(self.agent_id, ltm_summary)
        
        self.integration_stats['central_syncs'] += 1
        
        return global_insights
    
    async def _apply_global_insights(self, insights: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply global insights to improve agent performance"""
        
        applied_insights = []
        
        for insight in insights:
            try:
                insight_type = insight.get('insight_type', '')
                confidence = insight.get('confidence', 0.0)
                
                if confidence >= self.config.insight_confidence_threshold:
                    
                    if insight_type == 'action_performance':
                        # Update RL engine's action preferences
                        action_type = insight.get('action_type', '')
                        avg_reward = insight.get('average_reward', 0.0)
                        
                        # This could influence exploration strategy
                        if avg_reward > 0.5:
                            # Encourage this action type
                            applied_insights.append({
                                'insight_id': str(insight.get('_id', '')),
                                'action': 'encourage_action',
                                'action_type': action_type,
                                'reason': f'High global reward: {avg_reward:.3f}'
                            })
                    
                    elif insight_type == 'timing_optimization':
                        # Update timing preferences
                        optimal_hour = insight.get('optimal_hour', 12)
                        action_type = insight.get('action_type', '')
                        
                        applied_insights.append({
                            'insight_id': str(insight.get('_id', '')),
                            'action': 'timing_preference',
                            'optimal_hour': optimal_hour,
                            'action_type': action_type,
                            'reason': 'Global timing pattern detected'
                        })
                    
            except Exception as e:
                self.logger.warning(f"Failed to apply insight: {str(e)}")
        
        self.integration_stats['insights_received'] += len(applied_insights)
        
        return {
            'total_insights_received': len(insights),
            'applied_insights': applied_insights,
            'application_rate': len(applied_insights) / len(insights) if insights else 0.0
        }
    
    async def _update_learning_strategy(self, strategies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update agent's learning strategy based on collective intelligence"""
        
        strategy_updates = []
        
        for strategy in strategies:
            success_rate = strategy.get('success_rate', 0.0)
            strategy_name = strategy.get('strategy_name', '')
            
            if success_rate >= 0.7:  # High success rate strategies
                
                # Update agent's strategy in LTM
                self.ltm.update_strategy(strategy_name, {
                    'success_rate': success_rate,
                    'source': 'collective_intelligence',
                    'last_applied': datetime.now().isoformat(),
                    'global_validation': True
                })
                
                strategy_updates.append({
                    'strategy_name': strategy_name,
                    'success_rate': success_rate,
                    'action': 'adopted'
                })
        
        self.integration_stats['strategies_updated'] += len(strategy_updates)
        
        return {
            'available_strategies': len(strategies),
            'adopted_strategies': strategy_updates,
            'adoption_rate': len(strategy_updates) / len(strategies) if strategies else 0.0
        }
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get current integration status and statistics"""
        
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'capabilities': self.capabilities,
            'last_sync_time': self.last_sync_time.isoformat(),
            'integration_stats': self.integration_stats,
            'config': asdict(self.config),
            'memory_status': {
                'stm_stats': self.stm.get_agent_stats(),
                'ltm_stats': self.ltm.get_agent_learning_stats(),
            }
        }


class CollectiveIntelligenceOrchestrator:
    """Orchestrates memory integration across all 7 agents"""
    
    def __init__(self, config: IntegrationConfig = None):
        self.config = config or IntegrationConfig()
        self.central_memory = CentralMemoryDB()
        self.agent_integrators: Dict[str, AgentMemoryIntegrator] = {}
        self.orchestrator_stats = {
            'total_cycles': 0,
            'successful_cycles': 0,
            'cross_agent_patterns_detected': 0,
            'urgent_insights_broadcasted': 0
        }
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("CollectiveIntelligence")
        
    def register_agent(self, agent_id: str, agent_type: str, capabilities: List[str]) -> AgentMemoryIntegrator:
        """Register an agent for collective intelligence"""
        
        integrator = AgentMemoryIntegrator(agent_id, agent_type, capabilities, self.config)
        self.agent_integrators[agent_id] = integrator
        
        self.logger.info(f"Registered agent {agent_id} with capabilities: {capabilities}")
        return integrator
    
    async def run_collective_cycle(self) -> Dict[str, Any]:
        """Run collective intelligence cycle for all agents"""
        cycle_start = time.time()
        
        try:
            # Step 1: Run individual agent integrations in parallel
            integration_tasks = [
                integrator.run_integration_cycle() 
                for integrator in self.agent_integrators.values()
            ]
            
            individual_results = await asyncio.gather(*integration_tasks, return_exceptions=True)
            
            # Step 2: Detect cross-agent patterns
            cross_patterns = self.central_memory.detect_cross_agent_patterns()
            self.orchestrator_stats['cross_agent_patterns_detected'] += len(cross_patterns)
            
            # Step 3: Update performance leaderboard
            leaderboard = self.central_memory.update_performance_leaderboard()
            
            # Step 4: Check for urgent insights to broadcast
            urgent_insights = await self._check_urgent_insights()
            
            # Step 5: Generate collective report
            collective_report = await self._generate_collective_report()
            
            cycle_duration = time.time() - cycle_start
            self.orchestrator_stats['total_cycles'] += 1
            self.orchestrator_stats['successful_cycles'] += 1
            
            return {
                'cycle_info': {
                    'duration_seconds': cycle_duration,
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'participating_agents': len(self.agent_integrators)
                },
                'individual_results': {
                    agent_id: result for agent_id, result in 
                    zip(self.agent_integrators.keys(), individual_results)
                    if not isinstance(result, Exception)
                },
                'cross_agent_patterns': cross_patterns,
                'performance_leaderboard': leaderboard,
                'urgent_insights': urgent_insights,
                'collective_report': collective_report,
                'orchestrator_stats': self.orchestrator_stats
            }
            
        except Exception as e:
            self.logger.error(f"Collective cycle failed: {str(e)}")
            return {
                'cycle_info': {
                    'duration_seconds': time.time() - cycle_start,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': str(e)
                }
            }
    
    async def _check_urgent_insights(self) -> List[Dict[str, Any]]:
        """Check for urgent insights that need immediate broadcasting"""
        
        urgent_insights = []
        
        # Get recent performance data
        recent_performance = self.central_memory.performance_leaderboard.find({}).sort('last_updated', -1).limit(10)
        
        for perf in recent_performance:
            # Check for exceptionally high performance
            if perf.get('avg_reward', 0) >= self.config.urgent_reward_threshold:
                urgent_insight = {
                    'type': 'exceptional_performance',
                    'agent_id': perf['agent_id'],
                    'avg_reward': perf['avg_reward'],
                    'insight': 'This agent achieved exceptional results - analyze their recent strategies',
                    'priority': 'high',
                    'timestamp': datetime.now().isoformat()
                }
                
                # Broadcast to all other agents
                target_agents = [aid for aid in self.agent_integrators.keys() if aid != perf['agent_id']]
                self.central_memory.broadcast_urgent_insight(urgent_insight, target_agents)
                
                urgent_insights.append(urgent_insight)
                self.orchestrator_stats['urgent_insights_broadcasted'] += 1
        
        return urgent_insights
    
    async def _generate_collective_report(self) -> Dict[str, Any]:
        """Generate comprehensive collective intelligence report"""
        
        global_stats = self.central_memory.get_global_statistics()
        
        # Calculate collective performance metrics
        total_experiences = 0
        total_high_value = 0
        avg_performance_scores = []
        
        for integrator in self.agent_integrators.values():
            try:
                status = integrator.get_integration_status()
                ltm_stats = status['memory_status']['ltm_stats']
                
                total_experiences += ltm_stats.get('total_experiences', 0)
                total_high_value += ltm_stats.get('high_value_experiences', 0)
                
                # Calculate individual performance score
                avg_q = ltm_stats.get('avg_q_value', 0.0)
                avg_reward = ltm_stats.get('avg_reward', 0.0)
                performance_score = (avg_q + avg_reward) / 2
                avg_performance_scores.append(performance_score)
                
            except Exception as e:
                self.logger.warning(f"Could not get stats for agent {integrator.agent_id}: {str(e)}")
        
        collective_performance = sum(avg_performance_scores) / len(avg_performance_scores) if avg_performance_scores else 0.0
        
        return {
            'collective_metrics': {
                'total_agents': len(self.agent_integrators),
                'total_experiences_collected': total_experiences,
                'total_high_value_experiences': total_high_value,
                'collective_performance_score': collective_performance,
                'knowledge_quality_ratio': total_high_value / max(total_experiences, 1)
            },
            'global_statistics': global_stats,
            'system_health': {
                'all_agents_active': len(self.agent_integrators) == len(avg_performance_scores),
                'integration_success_rate': self.orchestrator_stats['successful_cycles'] / max(self.orchestrator_stats['total_cycles'], 1),
                'last_updated': datetime.now().isoformat()
            }
        }
    
    async def start_continuous_integration(self, interval_minutes: int = None) -> None:
        """Start continuous integration loop"""
        
        interval = interval_minutes or self.config.sync_interval_minutes
        self.logger.info(f"Starting continuous integration with {interval} minute intervals")
        
        while True:
            try:
                self.logger.info("Running collective intelligence cycle...")
                results = await self.run_collective_cycle()
                
                success = results.get('cycle_info', {}).get('success', False)
                if success:
                    self.logger.info(f"Collective cycle completed successfully")
                else:
                    self.logger.error(f"Collective cycle failed")
                
                # Wait for next cycle
                await asyncio.sleep(interval * 60)
                
            except KeyboardInterrupt:
                self.logger.info("Continuous integration stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Continuous integration error: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
