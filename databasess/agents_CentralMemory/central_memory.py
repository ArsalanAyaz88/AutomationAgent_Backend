"""
Central Memory Database - The "Brain Hub"
Aggregates knowledge from all 7 agents and enables collective intelligence
"""

from pymongo import MongoClient, DESCENDING, ASCENDING
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
import json
import os
from bson import ObjectId
import numpy as np
from collections import defaultdict
import statistics
import certifi
import ssl


class CentralMemoryDB:
    """Central Memory Database coordinating knowledge across all agents"""
    
    def __init__(self, mongo_uri: str = None):
        # Use environment variable or provided URI
        if mongo_uri is None:
            mongo_uri = os.getenv('CENTRALMEMORY_DATABASE_URL', 'mongodb://localhost:27017')
        
        # Store connection params but don't connect yet (lazy connection)
        self.mongo_uri = mongo_uri
        self.client = None
        self.db = None
        
        # Collections will be initialized on first use
        self.global_insights = None
        self.agent_synchronization = None
        self.collective_strategies = None
        self.cross_agent_patterns = None
        self.performance_leaderboard = None
        self.shared_experiences = None
        self.active_agents = None
        
        self._connected = False
        self._connection_attempted = False
    
    def _ensure_connection(self):
        """Establish connection if not already connected (lazy initialization)"""
        if self._connected or self._connection_attempted:
            return self._connected
        
        self._connection_attempted = True
        
        try:
            # Check if this is a MongoDB Atlas connection
            is_atlas = 'mongodb+srv://' in self.mongo_uri or 'mongodb.net' in self.mongo_uri
            
            if is_atlas:
                # Atlas requires SSL/TLS configuration
                self.client = MongoClient(
                    self.mongo_uri,
                    tls=True,
                    tlsAllowInvalidCertificates=False,
                    tlsCAFile=certifi.where(),
                    serverSelectionTimeoutMS=2000,  # Reduced timeout
                    connectTimeoutMS=5000,
                    socketTimeoutMS=5000,
                    retryWrites=True,
                    retryReads=True
                )
            else:
                # Local MongoDB without SSL
                self.client = MongoClient(
                    self.mongo_uri,
                    serverSelectionTimeoutMS=2000,
                    connectTimeoutMS=5000
                )
            
            # Extract database name from URI or use default  
            database = "youtube_agents_central"
            self.db = self.client[database]
            
            # Initialize collections
            self.global_insights = self.db["global_insights"]
            self.agent_synchronization = self.db["agent_synchronization"] 
            self.collective_strategies = self.db["collective_strategies"]
            self.cross_agent_patterns = self.db["cross_agent_patterns"]
            self.performance_leaderboard = self.db["performance_leaderboard"]
            self.shared_experiences = self.db["shared_experiences"]
            self.active_agents = self.db["active_agents"]
            
            # Create indexes with error handling
            self._create_indexes()
            
            self._connected = True
            print("✅ MongoDB Central Memory connected successfully")
            return True
            
        except Exception as e:
            print(f"⚠️  Warning: MongoDB Central Memory connection failed: {str(e)}")
            print(f"   Connection will be retried on next use.")
            self.client = None
            self.db = None
            return False
        
    def _check_connection(self) -> bool:
        """Check if database connection is available"""
        return self.db is not None and self.client is not None
    
    def _create_indexes(self):
        """Create indexes for optimal query performance"""
        if not self._check_connection():
            return  # Skip index creation if connection failed
            
        try:
            # Global insights
            self.global_insights.create_index([("confidence", DESCENDING)])
            self.global_insights.create_index([("insight_type", ASCENDING)])
            self.global_insights.create_index([("last_updated", DESCENDING)])
            
            # Agent sync
            self.agent_synchronization.create_index([("agent_id", ASCENDING)])
            self.agent_synchronization.create_index([("last_sync", DESCENDING)])
            
            # Strategies
            self.collective_strategies.create_index([("success_rate", DESCENDING)])
            self.collective_strategies.create_index([("usage_count", DESCENDING)])
            
            # Patterns
            self.cross_agent_patterns.create_index([("pattern_strength", DESCENDING)])
            self.cross_agent_patterns.create_index([("supporting_agents", ASCENDING)])
            
            # Performance
            self.performance_leaderboard.create_index([("overall_score", DESCENDING)])
            self.performance_leaderboard.create_index([("last_updated", DESCENDING)])
            
            print("✅ MongoDB Central Memory indexes created successfully")
        except Exception as e:
            print(f"⚠️  Warning: Failed to create MongoDB indexes: {str(e)}")
            print(f"   Indexes will be created automatically on first use.")
        
    def register_agent(self, agent_id: str, agent_type: str, capabilities: List[str]) -> str:
        """Register an agent in the central system"""
        self._ensure_connection()
        if not self._check_connection():
            print(f"⚠️  Cannot register agent {agent_id}: Database connection unavailable")
            return "connection_failed"
        
        agent_doc = {
            'agent_id': agent_id,
            'agent_type': agent_type,
            'capabilities': capabilities,
            'registered_at': datetime.now(),
            'last_active': datetime.now(),
            'status': 'active',
            'total_contributions': 0,
            'quality_score': 0.5  # Start with neutral score
        }
        
        result = self.active_agents.replace_one(
            {'agent_id': agent_id},
            agent_doc,
            upsert=True
        )
        
        return str(result.upserted_id) if result.upserted_id else "updated"
    
    def sync_agent_data(self, agent_id: str, ltm_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync agent's LTM data with central memory and return global insights"""
        self._ensure_connection()
        if not self._check_connection():
            print(f"⚠️  Cannot sync agent {agent_id}: Database connection unavailable")
            return {'insights': [], 'strategies': [], 'error': 'connection_failed'}
        
        # Update agent's last sync time
        self.agent_synchronization.replace_one(
            {'agent_id': agent_id},
            {
                'agent_id': agent_id,
                'last_sync': datetime.now(),
                'ltm_summary': ltm_data,
                'contribution_count': ltm_data.get('total_experiences', 0)
            },
            upsert=True
        )
        
        # Process agent's experiences for global insights
        self._process_agent_experiences(agent_id, ltm_data)
        
        # Update agent activity
        self.active_agents.update_one(
            {'agent_id': agent_id},
            {
                '$set': {'last_active': datetime.now()},
                '$inc': {'total_contributions': 1}
            }
        )
        
        # Return relevant global insights for this agent
        return self.get_relevant_insights_for_agent(agent_id)
    
    def _process_agent_experiences(self, agent_id: str, ltm_data: Dict[str, Any]) -> None:
        """Process agent's experiences to extract global insights"""
        
        best_experiences = ltm_data.get('best_experiences', [])
        if not best_experiences:
            return
            
        # Analyze patterns in successful actions
        action_performance = defaultdict(list)
        timing_patterns = defaultdict(list)
        content_patterns = defaultdict(list)
        
        for exp in best_experiences:
            if exp.get('q_value', 0) >= 0.8:  # High-quality experiences only
                action_type = exp.get('action', '')
                reward = exp.get('reward', 0)
                
                action_performance[action_type].append(reward)
                
                # Extract timing patterns
                state = exp.get('state', {})
                if 'hour' in str(state):
                    timing_patterns[action_type].append(state)
                    
                # Extract content patterns
                if 'video_category' in str(state):
                    content_patterns[action_type].append(state)
        
        # Generate insights from patterns
        self._generate_global_insights(agent_id, action_performance, timing_patterns, content_patterns)
    
    def _generate_global_insights(self, 
                                agent_id: str, 
                                action_performance: Dict[str, List[float]],
                                timing_patterns: Dict[str, List[Dict]],
                                content_patterns: Dict[str, List[Dict]]) -> None:
        """Generate global insights from agent data"""
        
        current_time = datetime.now()
        
        # Insight 1: Best performing actions globally
        for action, rewards in action_performance.items():
            if len(rewards) >= 3:  # Need minimum samples
                avg_reward = statistics.mean(rewards)
                std_dev = statistics.stdev(rewards) if len(rewards) > 1 else 0
                
                insight = {
                    'insight_type': 'action_performance',
                    'action_type': action,
                    'average_reward': avg_reward,
                    'confidence': min(len(rewards) / 10, 1.0),  # More samples = higher confidence
                    'std_deviation': std_dev,
                    'sample_size': len(rewards),
                    'contributing_agent': agent_id,
                    'last_updated': current_time,
                    'applicable_agents': 'all'  # This insight applies to all agents
                }
                
                # Upsert insight
                self.global_insights.replace_one(
                    {
                        'insight_type': 'action_performance',
                        'action_type': action
                    },
                    insight,
                    upsert=True
                )
        
        # Insight 2: Optimal timing patterns
        for action, timing_data in timing_patterns.items():
            if len(timing_data) >= 5:  # Need sufficient data
                # Extract hour patterns (simplified analysis)
                hours = [data.get('hour', 12) for data in timing_data if 'hour' in str(data)]
                if hours:
                    optimal_hour = statistics.mode(hours) if len(set(hours)) < len(hours) else statistics.median(hours)
                    
                    timing_insight = {
                        'insight_type': 'timing_optimization',
                        'action_type': action,
                        'optimal_hour': optimal_hour,
                        'confidence': len(hours) / 20,  # Normalize confidence
                        'sample_size': len(hours),
                        'contributing_agent': agent_id,
                        'last_updated': current_time,
                        'applicable_agents': 'all'
                    }
                    
                    self.global_insights.replace_one(
                        {
                            'insight_type': 'timing_optimization',
                            'action_type': action
                        },
                        timing_insight,
                        upsert=True
                    )
    
    def get_relevant_insights_for_agent(self, agent_id: str) -> Dict[str, Any]:
        """Get insights relevant to a specific agent"""
        self._ensure_connection()
        if not self._check_connection():
            return {}
        
        # Get agent's capabilities
        agent_info = self.active_agents.find_one({'agent_id': agent_id})
        if not agent_info:
            return {'insights': [], 'strategies': []}
        
        capabilities = agent_info.get('capabilities', [])
        
        # Query relevant insights
        insights_query = {
            '$or': [
                {'applicable_agents': 'all'},
                {'applicable_agents': {'$in': capabilities}}
            ],
            'confidence': {'$gte': 0.3}  # Only reasonably confident insights
        }
        
        insights = list(self.global_insights.find(insights_query)
                       .sort('confidence', DESCENDING)
                       .limit(10))
        
        # Get relevant strategies
        strategies = list(self.collective_strategies.find({'success_rate': {'$gte': 0.6}})
                         .sort('success_rate', DESCENDING)
                         .limit(5))
        
        # Clean up ObjectIds for JSON serialization
        for item in insights + strategies:
            if '_id' in item:
                item['_id'] = str(item['_id'])
            if 'last_updated' in item and isinstance(item['last_updated'], datetime):
                item['last_updated'] = item['last_updated'].isoformat()
        
        return {
            'insights': insights,
            'strategies': strategies,
            'sync_timestamp': datetime.now().isoformat(),
            'total_insights_available': self.global_insights.count_documents(insights_query)
        }
    
    def update_collective_strategy(self, strategy_data: Dict[str, Any]) -> str:
        """Update or create a collective strategy based on multi-agent data"""
        
        strategy = {
            'strategy_name': strategy_data['name'],
            'description': strategy_data.get('description', ''),
            'action_sequence': strategy_data.get('action_sequence', []),
            'success_rate': strategy_data.get('success_rate', 0.0),
            'usage_count': strategy_data.get('usage_count', 0),
            'contributing_agents': strategy_data.get('contributing_agents', []),
            'applicable_scenarios': strategy_data.get('applicable_scenarios', []),
            'average_reward': strategy_data.get('average_reward', 0.0),
            'last_updated': datetime.now(),
            'confidence': strategy_data.get('confidence', 0.5)
        }
        
        result = self.collective_strategies.replace_one(
            {'strategy_name': strategy_data['name']},
            strategy,
            upsert=True
        )
        
        return str(result.upserted_id) if result.upserted_id else "updated"
    
    def detect_cross_agent_patterns(self) -> List[Dict[str, Any]]:
        """Detect patterns that emerge across multiple agents"""
        
        # Get recent sync data from all agents
        recent_syncs = list(self.agent_synchronization.find({
            'last_sync': {'$gte': datetime.now() - timedelta(hours=24)}
        }))
        
        if len(recent_syncs) < 2:
            return []
        
        cross_patterns = []
        
        # Pattern 1: Common successful actions across agents
        common_actions = defaultdict(list)
        
        for sync in recent_syncs:
            ltm_summary = sync.get('ltm_summary', {})
            best_experiences = ltm_summary.get('best_experiences', [])
            
            for exp in best_experiences:
                if exp.get('q_value', 0) >= 0.8:
                    action = exp.get('action', '')
                    if action:
                        common_actions[action].append({
                            'agent_id': sync['agent_id'],
                            'reward': exp.get('reward', 0),
                            'q_value': exp.get('q_value', 0)
                        })
        
        # Find actions successful across multiple agents
        for action, agent_results in common_actions.items():
            if len(agent_results) >= 3:  # At least 3 agents found this successful
                avg_reward = statistics.mean([r['reward'] for r in agent_results])
                avg_q_value = statistics.mean([r['q_value'] for r in agent_results])
                
                pattern = {
                    'pattern_type': 'cross_agent_success',
                    'action_type': action,
                    'supporting_agents': [r['agent_id'] for r in agent_results],
                    'pattern_strength': len(agent_results) / len(recent_syncs),
                    'avg_reward': avg_reward,
                    'avg_q_value': avg_q_value,
                    'confidence': min(len(agent_results) / 5, 1.0),
                    'discovered_at': datetime.now()
                }
                
                cross_patterns.append(pattern)
                
                # Store in database
                self.cross_agent_patterns.replace_one(
                    {
                        'pattern_type': 'cross_agent_success',
                        'action_type': action
                    },
                    pattern,
                    upsert=True
                )
        
        return cross_patterns
    
    def update_performance_leaderboard(self) -> Dict[str, Any]:
        """Update agent performance leaderboard based on recent contributions"""
        
        leaderboard_data = []
        
        # Get all active agents
        active_agents = list(self.active_agents.find({'status': 'active'}))
        
        for agent in active_agents:
            agent_id = agent['agent_id']
            
            # Get recent sync data
            recent_sync = self.agent_synchronization.find_one({'agent_id': agent_id})
            
            if recent_sync:
                ltm_summary = recent_sync.get('ltm_summary', {})
                
                # Calculate performance metrics
                total_experiences = ltm_summary.get('total_experiences', 0)
                avg_q_value = ltm_summary.get('avg_q_value', 0.0)
                avg_reward = ltm_summary.get('avg_reward', 0.0)
                high_value_experiences = ltm_summary.get('high_value_experiences', 0)
                
                # Calculate overall score
                experience_score = min(total_experiences / 1000, 1.0)  # Normalize to 1000 experiences
                quality_score = (avg_q_value + avg_reward) / 2
                consistency_score = min(high_value_experiences / max(total_experiences, 1), 1.0)
                
                overall_score = (experience_score * 0.3 + quality_score * 0.5 + consistency_score * 0.2)
                
                performance_entry = {
                    'agent_id': agent_id,
                    'agent_type': agent.get('agent_type', 'unknown'),
                    'overall_score': overall_score,
                    'total_experiences': total_experiences,
                    'avg_q_value': avg_q_value,
                    'avg_reward': avg_reward,
                    'high_value_experiences': high_value_experiences,
                    'last_updated': datetime.now(),
                    'rank': 0  # Will be calculated after sorting
                }
                
                leaderboard_data.append(performance_entry)
        
        # Sort by overall score and assign ranks
        leaderboard_data.sort(key=lambda x: x['overall_score'], reverse=True)
        
        for i, entry in enumerate(leaderboard_data):
            entry['rank'] = i + 1
            
            # Update in database
            self.performance_leaderboard.replace_one(
                {'agent_id': entry['agent_id']},
                entry,
                upsert=True
            )
        
        return {
            'leaderboard': leaderboard_data,
            'last_updated': datetime.now().isoformat(),
            'total_agents': len(leaderboard_data)
        }
    
    def get_global_statistics(self) -> Dict[str, Any]:
        """Get comprehensive global statistics across all agents"""
        self._ensure_connection()
        if not self._check_connection():
            return {'error': 'Database connection unavailable'}
        
        total_agents = self.active_agents.count_documents({'status': 'active'})
        total_insights = self.global_insights.count_documents({})
        total_strategies = self.collective_strategies.count_documents({})
        total_patterns = self.cross_agent_patterns.count_documents({})
        
        # Recent activity (last 24 hours)
        recent_syncs = self.agent_synchronization.count_documents({
            'last_sync': {'$gte': datetime.now() - timedelta(hours=24)}
        })
        
        # Average performance metrics
        recent_performance = list(self.performance_leaderboard.find({}).sort('overall_score', DESCENDING))
        
        avg_performance = 0.0
        if recent_performance:
            avg_performance = statistics.mean([p['overall_score'] for p in recent_performance])
        
        # Top insights
        top_insights = list(self.global_insights.find({})
                           .sort('confidence', DESCENDING)
                           .limit(3))
        
        for insight in top_insights:
            insight['_id'] = str(insight['_id'])
            if isinstance(insight.get('last_updated'), datetime):
                insight['last_updated'] = insight['last_updated'].isoformat()
        
        return {
            'system_overview': {
                'total_active_agents': total_agents,
                'total_global_insights': total_insights,
                'collective_strategies': total_strategies,
                'cross_agent_patterns': total_patterns,
                'recent_syncs_24h': recent_syncs,
                'average_agent_performance': avg_performance
            },
            'top_insights': top_insights,
            'last_updated': datetime.now().isoformat()
        }
    
    def broadcast_urgent_insight(self, insight: Dict[str, Any], target_agents: List[str] = None) -> int:
        """Broadcast urgent insight to specific agents or all agents"""
        
        if target_agents is None:
            # Get all active agents
            target_agents = [agent['agent_id'] for agent in self.active_agents.find({'status': 'active'})]
        
        urgent_insight = {
            **insight,
            'priority': 'urgent',
            'broadcast_time': datetime.now(),
            'target_agents': target_agents,
            'acknowledged_by': []
        }
        
        # Store urgent insight
        result = self.global_insights.insert_one(urgent_insight)
        
        return len(target_agents)
