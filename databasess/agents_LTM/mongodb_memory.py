"""
Long-Term Memory (LTM) - MongoDB Implementation
Persistent storage for high-value experiences and learned patterns
"""

from pymongo import MongoClient, DESCENDING, ASCENDING
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import os
from bson import ObjectId
import certifi
import ssl


class AgentLTM:
    """Long-Term Memory using MongoDB for persistent high-value experiences"""
    
    def __init__(self, agent_id: str, mongo_uri: str = None):
        self.agent_id = agent_id
        
        # Use environment variable or provided URI
        if mongo_uri is None:
            mongo_uri = os.getenv('LTM_DATABASE_URL', 'mongodb://localhost:27017')
        
        # Configure MongoDB client with SSL/TLS settings for Atlas
        try:
            # Check if this is a MongoDB Atlas connection
            is_atlas = 'mongodb+srv://' in mongo_uri or 'mongodb.net' in mongo_uri
            
            if is_atlas:
                # Atlas requires SSL/TLS configuration
                self.client = MongoClient(
                    mongo_uri,
                    tls=True,
                    tlsAllowInvalidCertificates=False,
                    tlsCAFile=certifi.where(),
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=10000,
                    socketTimeoutMS=10000,
                    retryWrites=True,
                    retryReads=True
                )
            else:
                # Local MongoDB without SSL
                self.client = MongoClient(
                    mongo_uri,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=10000
                )
            
            # Extract database name from URI or use default
            if 'mongodb+srv://' in mongo_uri or 'mongodb://' in mongo_uri:
                # For Atlas URIs, use a default database name
                database = "youtube_agents_ltm"
            else:
                database = "youtube_agents_ltm"
                
            self.db = self.client[database]
            self.experiences_collection = self.db[f"agent_{agent_id}_experiences"]
            self.patterns_collection = self.db[f"agent_{agent_id}_patterns"]
            self.strategies_collection = self.db[f"agent_{agent_id}_strategies"]
            
            # Create indexes for efficient queries
            self._create_indexes()
            
        except Exception as e:
            print(f"⚠️  Warning: MongoDB LTM initialization failed for agent {agent_id}: {str(e)}")
            print(f"   Connection will be retried on first use.")
            self.client = None
            self.db = None
    
    def _check_connection(self) -> bool:
        """Check if database connection is available"""
        return self.db is not None and self.client is not None
    
    def _create_indexes(self):
        """Create MongoDB indexes for optimal query performance"""
        if self.db is None:
            return  # Skip index creation if connection failed
            
        try:
            # Experiences indexes
            self.experiences_collection.create_index([("q_value", DESCENDING)])
            self.experiences_collection.create_index([("reward", DESCENDING)])
            self.experiences_collection.create_index([("timestamp", DESCENDING)])
            self.experiences_collection.create_index([("action", ASCENDING)])
            self.experiences_collection.create_index([
                ("q_value", DESCENDING), ("timestamp", DESCENDING)
            ])
            
            # Patterns indexes
            self.patterns_collection.create_index([("confidence", DESCENDING)])
            self.patterns_collection.create_index([("pattern_type", ASCENDING)])
            
            print(f"✅ MongoDB LTM indexes created for agent {self.agent_id}")
        except Exception as e:
            print(f"⚠️  Warning: Failed to create MongoDB LTM indexes for agent {self.agent_id}: {str(e)}")
            print(f"   Indexes will be created automatically on first use.")
        
    def store_high_value_experience(self, experience: Dict[str, Any]) -> str:
        """Store high-value experience from STM to LTM"""
        if not self._check_connection():
            print(f"⚠️  Cannot store experience for agent {self.agent_id}: Database connection unavailable")
            return "connection_failed"
        
        ltm_experience = {
            '_id': ObjectId(),
            'agent_id': self.agent_id,
            'stm_id': experience.get('id', ''),
            'timestamp': datetime.now(),
            'q_value': experience.get('q_value', 0.0),
            'reward': experience.get('reward', 0.0),
            'action': experience.get('action', ''),
            'state': experience.get('state', {}),
            'next_state': experience.get('next_state', {}),
            'action_type': experience.get('action_type', 'unknown'),
            'context': experience.get('context', {}),
            'youtube_metrics_before': experience.get('youtube_metrics_before', {}),
            'youtube_metrics_after': experience.get('youtube_metrics_after', {}),
            'success_indicators': experience.get('success_indicators', []),
            'tags': experience.get('tags', [])
        }
        
        result = self.experiences_collection.insert_one(ltm_experience)
        return str(result.inserted_id)
    
    def get_best_experiences(self, limit: int = 100, q_threshold: float = 0.8) -> List[Dict[str, Any]]:
        """Get best experiences with high Q-values and rewards"""
        if not self._check_connection():
            return []  # Return empty list if no connection
        
        query = {"q_value": {"$gte": q_threshold}}
        
        experiences = list(self.experiences_collection.find(query)
                          .sort([("q_value", DESCENDING), ("reward", DESCENDING)])
                          .limit(limit))
        
        # Convert ObjectId to string for JSON serialization
        for exp in experiences:
            exp['_id'] = str(exp['_id'])
            if isinstance(exp['timestamp'], datetime):
                exp['timestamp'] = exp['timestamp'].isoformat()
                
        return experiences
    
    def find_similar_experiences(self, current_state: Dict[str, Any], action: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find experiences with similar states and actions"""
        if not self._check_connection():
            return []  # Return empty list if no connection
        
        query = {
            "action": action,
            "q_value": {"$gte": 0.5}  # Only consider decent experiences
        }
        
        # Add state similarity matching (simplified - could be enhanced with vector similarity)
        if 'video_category' in current_state:
            query['state.video_category'] = current_state['video_category']
        if 'time_of_day' in current_state:
            query['state.time_of_day'] = current_state['time_of_day']
            
        similar_experiences = list(self.experiences_collection.find(query)
                                  .sort("q_value", DESCENDING)
                                  .limit(limit))
        
        for exp in similar_experiences:
            exp['_id'] = str(exp['_id'])
            if isinstance(exp['timestamp'], datetime):
                exp['timestamp'] = exp['timestamp'].isoformat()
                
        return similar_experiences
    
    def learn_pattern(self, pattern_data: Dict[str, Any]) -> str:
        """Store learned patterns for future decision making"""
        if not self._check_connection():
            return "connection_failed"
        pattern = {
            '_id': ObjectId(),
            'agent_id': self.agent_id,
            'timestamp': datetime.now(),
            'pattern_type': pattern_data.get('type', 'unknown'),
            'description': pattern_data.get('description', ''),
            'conditions': pattern_data.get('conditions', {}),
            'expected_outcome': pattern_data.get('expected_outcome', {}),
            'confidence': pattern_data.get('confidence', 0.0),
            'supporting_experiences': pattern_data.get('supporting_experiences', []),
            'success_rate': pattern_data.get('success_rate', 0.0),
            'tags': pattern_data.get('tags', [])
        }
        
        result = self.patterns_collection.insert_one(pattern)
        return str(result.inserted_id)
    
    def get_relevant_patterns(self, current_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get patterns relevant to current context"""
        query = {"confidence": {"$gte": 0.6}}
        
        # Add context matching
        if 'video_type' in current_context:
            query['conditions.video_type'] = current_context['video_type']
        if 'audience_segment' in current_context:
            query['conditions.audience_segment'] = current_context['audience_segment']
            
        patterns = list(self.patterns_collection.find(query)
                       .sort("confidence", DESCENDING)
                       .limit(20))
        
        for pattern in patterns:
            pattern['_id'] = str(pattern['_id'])
            if isinstance(pattern['timestamp'], datetime):
                pattern['timestamp'] = pattern['timestamp'].isoformat()
                
        return patterns
    
    def update_strategy(self, strategy_name: str, performance_data: Dict[str, Any]) -> str:
        """Update or create strategy based on performance"""
        strategy = {
            'agent_id': self.agent_id,
            'strategy_name': strategy_name,
            'last_updated': datetime.now(),
            'performance_metrics': performance_data,
            'success_rate': performance_data.get('success_rate', 0.0),
            'avg_reward': performance_data.get('avg_reward', 0.0),
            'usage_count': performance_data.get('usage_count', 0),
            'recent_results': performance_data.get('recent_results', [])
        }
        
        result = self.strategies_collection.replace_one(
            {'agent_id': self.agent_id, 'strategy_name': strategy_name},
            strategy,
            upsert=True
        )
        
        return str(result.upserted_id) if result.upserted_id else "updated"
    
    def get_best_strategies(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get best performing strategies"""
        strategies = list(self.strategies_collection.find({'agent_id': self.agent_id})
                         .sort([("success_rate", DESCENDING), ("avg_reward", DESCENDING)])
                         .limit(limit))
        
        for strategy in strategies:
            if '_id' in strategy:
                strategy['_id'] = str(strategy['_id'])
            if isinstance(strategy.get('last_updated'), datetime):
                strategy['last_updated'] = strategy['last_updated'].isoformat()
                
        return strategies
    
    def get_agent_learning_stats(self) -> Dict[str, Any]:
        """Get comprehensive learning statistics for the agent"""
        total_experiences = self.experiences_collection.count_documents({'agent_id': self.agent_id})
        
        # High-value experiences
        high_value_count = self.experiences_collection.count_documents({
            'agent_id': self.agent_id,
            'q_value': {'$gte': 0.8}
        })
        
        # Average metrics
        pipeline = [
            {'$match': {'agent_id': self.agent_id}},
            {'$group': {
                '_id': None,
                'avg_q_value': {'$avg': '$q_value'},
                'avg_reward': {'$avg': '$reward'},
                'max_q_value': {'$max': '$q_value'},
                'min_q_value': {'$min': '$q_value'}
            }}
        ]
        
        agg_result = list(self.experiences_collection.aggregate(pipeline))
        avg_stats = agg_result[0] if agg_result else {}
        
        # Pattern and strategy counts
        pattern_count = self.patterns_collection.count_documents({'agent_id': self.agent_id})
        strategy_count = self.strategies_collection.count_documents({'agent_id': self.agent_id})
        
        return {
            'total_experiences': total_experiences,
            'high_value_experiences': high_value_count,
            'avg_q_value': avg_stats.get('avg_q_value', 0.0),
            'avg_reward': avg_stats.get('avg_reward', 0.0),
            'max_q_value': avg_stats.get('max_q_value', 0.0),
            'min_q_value': avg_stats.get('min_q_value', 0.0),
            'learned_patterns': pattern_count,
            'active_strategies': strategy_count
        }
    
    def cleanup_old_data(self, days_old: int = 30) -> int:
        """Clean up old, low-value experiences to maintain performance"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        # Delete old experiences with low Q-values
        result = self.experiences_collection.delete_many({
            'agent_id': self.agent_id,
            'timestamp': {'$lt': cutoff_date},
            'q_value': {'$lt': 0.3}
        })
        
        return result.deleted_count
