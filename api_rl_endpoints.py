"""
RL System API Endpoints
Provides frontend with RL system status, agent stats, and central memory insights
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any
from datetime import datetime
from rl_integration import rl_registry
from databasess.agents_CentralMemory.central_memory import CentralMemoryDB

router = APIRouter(prefix="/api/rl", tags=["RL System"])


@router.get("/system-status")
async def get_rl_system_status():
    """Get overall RL system status including all agents"""
    try:
        agents_status = []
        operational_count = 0
        
        # Get all initialized agents
        for agent_name, agent in rl_registry.agents.items():
            try:
                # Check STM connection
                stm_connected = False
                storage_type = "memory"
                try:
                    agent.stm.redis_client.ping()
                    stm_connected = True
                    storage_type = "redis"
                except:
                    pass
                
                # Check LTM connection
                ltm_connected = agent.ltm._check_connection()
                ltm_collections = []
                if ltm_connected:
                    ltm_collections = [
                        f"{agent.ltm.experiences_collection.name}",
                        f"{agent.ltm.patterns_collection.name}",
                        f"{agent.ltm.strategies_collection.name}"
                    ]
                
                # Get RL Engine stats
                rl_active = hasattr(agent.rl_engine, 'q_agent')
                rl_stats = {
                    'active': rl_active,
                    'learning_rate': 0.1,
                    'discount_factor': 0.95,
                    'epsilon': 0.1,
                    'total_actions': 0,
                    'avg_reward': 0.0
                }
                
                if rl_active:
                    rl_stats = {
                        'active': True,
                        'learning_rate': agent.rl_engine.q_agent.learning_rate,
                        'discount_factor': agent.rl_engine.q_agent.discount_factor,
                        'epsilon': agent.rl_engine.q_agent.epsilon,
                        'total_actions': agent.rl_engine.q_agent.learning_stats.get('total_actions', 0),
                        'avg_reward': agent.rl_engine.q_agent.learning_stats.get('avg_reward', 0.0)
                    }
                
                if rl_active:
                    operational_count += 1
                
                agents_status.append({
                    'agent_name': agent_name,
                    'agent_type': agent.agent_type,
                    'capabilities': agent.capabilities,
                    'stm_status': {
                        'connected': stm_connected,
                        'key_prefix': agent.stm.key_prefix,
                        'storage_type': storage_type
                    },
                    'ltm_status': {
                        'connected': ltm_connected,
                        'collections': ltm_collections,
                        'database': 'youtube_agents_ltm'
                    },
                    'rl_engine_status': rl_stats,
                    'last_updated': datetime.now().isoformat()
                })
            except Exception as e:
                print(f"Error getting status for {agent_name}: {str(e)}")
                continue
        
        # Check central memory
        central_connected = rl_registry.central_memory._check_connection()
        
        # Determine system health
        total_agents = len(agents_status)
        if operational_count == total_agents and total_agents > 0:
            system_health = "fully_operational"
        elif operational_count > 0:
            system_health = "partially_operational"
        else:
            system_health = "offline"
        
        return {
            'total_agents': total_agents,
            'operational_agents': operational_count,
            'central_memory_connected': central_connected,
            'agents': agents_status,
            'system_health': system_health
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get RL system status: {str(e)}")


@router.get("/agent/{agent_name}/stats")
async def get_agent_learning_stats(agent_name: str):
    """Get detailed learning statistics for a specific agent"""
    try:
        agent = rl_registry.get_agent(agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
        
        # Get STM experiences count
        stm_count = 0
        try:
            stm_experiences = agent.stm.get_recent_experiences(limit=100)
            stm_count = len(stm_experiences)
        except:
            pass
        
        # Get LTM experiences count
        ltm_count = 0
        try:
            if agent.ltm._check_connection():
                ltm_experiences = agent.ltm.get_best_experiences(limit=100)
                ltm_count = len(ltm_experiences)
        except:
            pass
        
        # Get recent rewards (mock data for now)
        recent_rewards = [0.5, 0.6, 0.7, 0.8, 0.75]
        
        # Get best actions
        best_actions = []
        try:
            if hasattr(agent.rl_engine, 'q_agent'):
                q_table = agent.rl_engine.q_agent.q_table
                # Get top 3 actions by Q-value
                for state_hash, actions in list(q_table.items())[:3]:
                    for action_type, q_value in actions.items():
                        if q_value > 0.5:
                            best_actions.append({
                                'action_type': action_type,
                                'q_value': q_value,
                                'confidence': min(abs(q_value), 1.0)
                            })
                
                # Sort by Q-value and limit to top 5
                best_actions.sort(key=lambda x: x['q_value'], reverse=True)
                best_actions = best_actions[:5]
        except:
            pass
        
        # Learning progress stats
        epsilon = agent.rl_engine.q_agent.epsilon if hasattr(agent.rl_engine, 'q_agent') else 0.1
        learning_progress = {
            'exploration_rate': epsilon,
            'exploitation_rate': 1.0 - epsilon,
            'avg_q_value': 0.5  # Placeholder
        }
        
        return {
            'agent_name': agent_name,
            'stm_experiences': stm_count,
            'ltm_experiences': ltm_count,
            'recent_rewards': recent_rewards,
            'best_actions': best_actions,
            'learning_progress': learning_progress
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent stats: {str(e)}")


@router.get("/central-memory/insights")
async def get_central_memory_insights():
    """Get insights from central memory database"""
    try:
        if not rl_registry.central_memory._check_connection():
            return {
                'total_global_insights': 0,
                'top_insights': [],
                'cross_agent_patterns': 0,
                'performance_leaderboard': []
            }
        
        # Get global statistics
        stats = rl_registry.central_memory.get_global_statistics()
        
        # Get top insights
        top_insights = []
        try:
            insights = rl_registry.central_memory.global_insights.find({}).sort('confidence', -1).limit(5)
            for insight in insights:
                top_insights.append({
                    'insight_type': insight.get('insight_type', 'unknown'),
                    'confidence': insight.get('confidence', 0.0),
                    'applicable_agents': insight.get('applicable_agents', 'unknown')
                })
        except:
            pass
        
        # Get performance leaderboard
        leaderboard = []
        try:
            performances = rl_registry.central_memory.performance_leaderboard.find({}).sort('overall_score', -1).limit(7)
            for perf in performances:
                leaderboard.append({
                    'agent_id': perf.get('agent_id', 'unknown'),
                    'overall_score': perf.get('overall_score', 0.0),
                    'rank': perf.get('rank', 0)
                })
        except:
            pass
        
        return {
            'total_global_insights': stats['system_overview'].get('total_global_insights', 0),
            'top_insights': top_insights,
            'cross_agent_patterns': stats['system_overview'].get('cross_agent_patterns', 0),
            'performance_leaderboard': leaderboard
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get central memory insights: {str(e)}")
