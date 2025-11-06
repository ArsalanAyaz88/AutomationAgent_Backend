"""
Short-Term Memory (STM) - Redis Cache Implementation
Fast learning storage for temporary agent experiences
"""

import redis
import json
import time
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pickle
from urllib.parse import urlparse


class AgentSTM:
    """Short-Term Memory using Redis for fast access to recent experiences"""
    
    def __init__(self, agent_id: str, redis_url: str = None):
        self.agent_id = agent_id
        
        # Use environment variable or provided URL
        if redis_url is None:
            redis_url = os.getenv('STM_DATABASE_URL', 'redis://localhost:6379/0')
        
        # Parse Redis URL and create connection
        if redis_url.startswith('redis://'):
            self.redis_client = redis.from_url(redis_url, decode_responses=False)
        else:
            # Fallback to localhost if URL parsing fails
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=False)
        
        self.key_prefix = f"agent:{agent_id}:stm"
        
    def store_experience(self, experience_data: Dict[str, Any]) -> str:
        """Store a new experience with timestamp and auto-expiring TTL"""
        experience_id = f"{int(time.time() * 1000)}_{hash(str(experience_data)) % 10000}"
        
        experience = {
            'id': experience_id,
            'agent_id': self.agent_id,
            'timestamp': datetime.now().isoformat(),
            'data': experience_data,
            'q_value': experience_data.get('q_value', 0.0),
            'reward': experience_data.get('reward', 0.0),
            'action': experience_data.get('action', ''),
            'state': experience_data.get('state', {}),
            'next_state': experience_data.get('next_state', {})
        }
        
        key = f"{self.key_prefix}:exp:{experience_id}"
        
        # Store with 24-hour TTL (Redis auto-cleanup)
        self.redis_client.setex(key, 86400, pickle.dumps(experience))
        
        # Add to agent's experience list
        self.redis_client.lpush(f"{self.key_prefix}:list", experience_id)
        self.redis_client.expire(f"{self.key_prefix}:list", 86400)
        
        return experience_id
    
    def get_recent_experiences(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent experiences, sorted by most recent first"""
        experience_ids = self.redis_client.lrange(f"{self.key_prefix}:list", 0, limit - 1)
        experiences = []
        
        for exp_id in experience_ids:
            exp_id_str = exp_id.decode('utf-8') if isinstance(exp_id, bytes) else exp_id
            key = f"{self.key_prefix}:exp:{exp_id_str}"
            exp_data = self.redis_client.get(key)
            
            if exp_data:
                experience = pickle.loads(exp_data)
                experiences.append(experience)
                
        return experiences
    
    def get_high_q_experiences(self, q_threshold: float = 0.7, limit: int = 50) -> List[Dict[str, Any]]:
        """Filter experiences with high Q-values for LTM promotion"""
        all_experiences = self.get_recent_experiences(limit * 2)  # Get more to filter
        
        high_q_experiences = [
            exp for exp in all_experiences 
            if exp.get('q_value', 0.0) >= q_threshold
        ]
        
        # Sort by Q-value (highest first)
        high_q_experiences.sort(key=lambda x: x.get('q_value', 0.0), reverse=True)
        
        return high_q_experiences[:limit]
    
    def update_q_value(self, experience_id: str, new_q_value: float) -> bool:
        """Update Q-value for an existing experience"""
        key = f"{self.key_prefix}:exp:{experience_id}"
        exp_data = self.redis_client.get(key)
        
        if exp_data:
            experience = pickle.loads(exp_data)
            experience['q_value'] = new_q_value
            experience['updated_at'] = datetime.now().isoformat()
            
            ttl = self.redis_client.ttl(key)
            self.redis_client.setex(key, max(ttl, 3600), pickle.dumps(experience))
            return True
            
        return False
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Get agent's STM statistics"""
        total_experiences = self.redis_client.llen(f"{self.key_prefix}:list")
        
        experiences = self.get_recent_experiences(100)
        if not experiences:
            return {
                'total_experiences': 0,
                'avg_q_value': 0.0,
                'avg_reward': 0.0,
                'last_action_time': None
            }
        
        q_values = [exp.get('q_value', 0.0) for exp in experiences]
        rewards = [exp.get('reward', 0.0) for exp in experiences]
        
        return {
            'total_experiences': total_experiences,
            'avg_q_value': sum(q_values) / len(q_values) if q_values else 0.0,
            'avg_reward': sum(rewards) / len(rewards) if rewards else 0.0,
            'last_action_time': experiences[0]['timestamp'] if experiences else None,
            'high_q_count': len([q for q in q_values if q >= 0.7])
        }
    
    def clear_agent_memory(self) -> bool:
        """Clear all STM data for this agent (use with caution)"""
        keys = self.redis_client.keys(f"{self.key_prefix}:*")
        if keys:
            self.redis_client.delete(*keys)
            return True
        return False


class RealtimeMetrics:
    """Real-time metrics tracking in Redis"""
    
    def __init__(self, redis_url: str = None):
        # Use environment variable or provided URL  
        if redis_url is None:
            redis_url = os.getenv('STM_DATABASE_URL', 'redis://localhost:6379/1')
        
        # Parse Redis URL and create connection
        if redis_url.startswith('redis://'):
            # Use database 1 for metrics (modify URL)
            if redis_url.endswith('/0'):
                redis_url = redis_url[:-1] + '1'  # Change db from 0 to 1
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
        else:
            # Fallback to localhost
            self.redis_client = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)
        
    def update_youtube_metrics(self, channel_id: str, metrics: Dict[str, Any]) -> None:
        """Update real-time YouTube metrics"""
        key = f"youtube:metrics:{channel_id}"
        
        metrics_with_timestamp = {
            **metrics,
            'last_updated': datetime.now().isoformat(),
            'timestamp': int(time.time())
        }
        
        self.redis_client.hset(key, mapping=metrics_with_timestamp)
        self.redis_client.expire(key, 7200)  # 2-hour expiry
        
    def get_youtube_metrics(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Get current YouTube metrics"""
        key = f"youtube:metrics:{channel_id}"
        metrics = self.redis_client.hgetall(key)
        
        if metrics:
            # Convert numeric values back
            for k, v in metrics.items():
                if k in ['views', 'subscribers', 'videos', 'timestamp']:
                    try:
                        metrics[k] = int(v)
                    except (ValueError, TypeError):
                        pass
                elif k in ['avg_view_duration', 'ctr', 'engagement_rate']:
                    try:
                        metrics[k] = float(v)
                    except (ValueError, TypeError):
                        pass
                        
        return metrics if metrics else None
    
    def track_agent_performance(self, agent_id: str, action: str, result_metrics: Dict[str, Any]) -> None:
        """Track agent performance in real-time"""
        key = f"agent:performance:{agent_id}"
        
        performance_data = {
            'action': action,
            'timestamp': int(time.time()),
            'metrics': json.dumps(result_metrics),
            'success': result_metrics.get('success', False)
        }
        
        self.redis_client.lpush(key, json.dumps(performance_data))
        self.redis_client.ltrim(key, 0, 99)  # Keep last 100 actions
        self.redis_client.expire(key, 86400)  # 24-hour expiry
