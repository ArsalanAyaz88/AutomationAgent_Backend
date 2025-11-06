"""
Reinforcement Learning Engine
Implements observation-action-reward loop for YouTube agents with Q-Learning
"""

import numpy as np
import json
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import random
from enum import Enum


class ActionType(Enum):
    """Defined action types for YouTube optimization"""
    UPLOAD_TIME_OPTIMIZATION = "upload_time_optimization"
    TITLE_OPTIMIZATION = "title_optimization" 
    THUMBNAIL_OPTIMIZATION = "thumbnail_optimization"
    DESCRIPTION_OPTIMIZATION = "description_optimization"
    TAG_OPTIMIZATION = "tag_optimization"
    CONTENT_STRATEGY = "content_strategy"
    AUDIENCE_ENGAGEMENT = "audience_engagement"


@dataclass
class State:
    """Represents the current state of the YouTube channel"""
    video_metrics: Dict[str, float]  # views, likes, comments, shares, watch_time
    channel_metrics: Dict[str, float]  # subscribers, total_views, engagement_rate
    temporal_context: Dict[str, Any]  # time_of_day, day_of_week, season
    content_context: Dict[str, Any]  # video_category, duration, language
    audience_context: Dict[str, Any]  # demographics, geographic, device_type
    
    def to_vector(self) -> np.ndarray:
        """Convert state to numerical vector for ML processing"""
        features = []
        
        # Video metrics (normalize to 0-1 range)
        video_features = [
            min(self.video_metrics.get('views', 0) / 1000000, 1.0),  # Normalize to millions
            min(self.video_metrics.get('likes', 0) / 10000, 1.0),    # Normalize to 10k
            min(self.video_metrics.get('comments', 0) / 1000, 1.0),  # Normalize to 1k
            min(self.video_metrics.get('watch_time_seconds', 0) / 3600, 1.0),  # Normalize to hours
            self.video_metrics.get('ctr', 0.0),  # Already percentage
            self.video_metrics.get('engagement_rate', 0.0)  # Already percentage
        ]
        features.extend(video_features)
        
        # Channel metrics
        channel_features = [
            min(self.channel_metrics.get('subscribers', 0) / 1000000, 1.0),  # Normalize to millions
            min(self.channel_metrics.get('total_views', 0) / 100000000, 1.0),  # Normalize to 100M
            self.channel_metrics.get('avg_engagement_rate', 0.0)
        ]
        features.extend(channel_features)
        
        # Temporal context (one-hot encoding simplified)
        hour = self.temporal_context.get('hour', 12)
        features.append(hour / 24.0)  # Normalize hour
        
        day_of_week = self.temporal_context.get('day_of_week', 0)
        features.append(day_of_week / 7.0)  # Normalize day
        
        # Content context
        duration = min(self.content_context.get('duration_minutes', 10) / 60, 1.0)  # Normalize to hour
        features.append(duration)
        
        return np.array(features, dtype=np.float32)


@dataclass
class Action:
    """Represents an action the agent can take"""
    action_type: ActionType
    parameters: Dict[str, Any]
    confidence: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.action_type.value,
            'parameters': self.parameters,
            'confidence': self.confidence
        }


class YouTubeRewardCalculator:
    """Calculates rewards based on YouTube performance metrics"""
    
    def __init__(self):
        self.metric_weights = {
            'views': 0.25,
            'likes': 0.15,
            'comments': 0.15,
            'shares': 0.10,
            'watch_time': 0.20,
            'ctr': 0.15
        }
    
    def calculate_reward(self, 
                        metrics_before: Dict[str, float], 
                        metrics_after: Dict[str, float],
                        time_elapsed_hours: float = 24.0) -> float:
        """
        Calculate reward based on metric improvements
        Returns value between -1.0 and +1.0
        """
        total_reward = 0.0
        
        for metric, weight in self.metric_weights.items():
            before = metrics_before.get(metric, 0.0)
            after = metrics_after.get(metric, 0.0)
            
            if before > 0:
                # Calculate percentage improvement
                improvement = (after - before) / before
                
                # Apply time decay for fairness (longer time = less impressive)
                time_factor = max(0.1, 1.0 - (time_elapsed_hours - 24) / 168)  # Decay over week
                
                # Normalize and weight the improvement
                normalized_improvement = np.tanh(improvement * 5)  # Sigmoid-like normalization
                weighted_reward = normalized_improvement * weight * time_factor
                
                total_reward += weighted_reward
            else:
                # If no baseline, reward any positive metrics
                if after > 0:
                    total_reward += weight * 0.1  # Small positive reward
        
        # Clip to valid range
        return np.clip(total_reward, -1.0, 1.0)
    
    def calculate_engagement_bonus(self, metrics: Dict[str, float]) -> float:
        """Calculate bonus reward for high engagement"""
        engagement_rate = metrics.get('engagement_rate', 0.0)
        
        if engagement_rate > 0.05:  # 5%+ engagement is excellent
            return 0.2
        elif engagement_rate > 0.02:  # 2%+ engagement is good
            return 0.1
        elif engagement_rate > 0.01:  # 1%+ engagement is decent
            return 0.05
        
        return 0.0


class QLearningAgent:
    """Q-Learning implementation for YouTube optimization"""
    
    def __init__(self, agent_id: str, state_size: int = 12, learning_rate: float = 0.1, 
                 discount_factor: float = 0.95, epsilon: float = 0.1):
        self.agent_id = agent_id
        self.state_size = state_size
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon  # Exploration rate
        
        # Q-table: state_hash -> {action_type -> q_value}
        self.q_table: Dict[str, Dict[str, float]] = {}
        
        # Action space
        self.action_types = list(ActionType)
        
        # Experience replay buffer
        self.experience_buffer = []
        self.max_buffer_size = 10000
        
        # Performance tracking
        self.episode_rewards = []
        self.learning_stats = {
            'total_actions': 0,
            'successful_actions': 0,
            'avg_reward': 0.0,
            'exploration_actions': 0
        }
    
    def get_state_hash(self, state: State) -> str:
        """Create a hash key for the state (discretize continuous values)"""
        state_vector = state.to_vector()
        
        # Discretize to reduce state space
        discretized = (state_vector * 10).astype(int)  # 10 bins per feature
        return str(hash(tuple(discretized)))
    
    def get_q_value(self, state_hash: str, action_type: ActionType) -> float:
        """Get Q-value for state-action pair"""
        if state_hash not in self.q_table:
            self.q_table[state_hash] = {at.value: 0.0 for at in self.action_types}
        
        return self.q_table[state_hash][action_type.value]
    
    def update_q_value(self, state_hash: str, action_type: ActionType, 
                      reward: float, next_state_hash: str) -> None:
        """Update Q-value using Q-learning formula"""
        current_q = self.get_q_value(state_hash, action_type)
        
        # Find max Q-value for next state
        max_next_q = 0.0
        if next_state_hash in self.q_table:
            max_next_q = max(self.q_table[next_state_hash].values())
        
        # Q-learning update
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )
        
        if state_hash not in self.q_table:
            self.q_table[state_hash] = {at.value: 0.0 for at in self.action_types}
        
        self.q_table[state_hash][action_type.value] = new_q
    
    def choose_action(self, state: State, force_exploration: bool = False) -> Action:
        """Choose action using epsilon-greedy policy"""
        state_hash = self.get_state_hash(state)
        
        # Exploration vs exploitation
        if force_exploration or random.random() < self.epsilon:
            # Explore: random action
            action_type = random.choice(self.action_types)
            self.learning_stats['exploration_actions'] += 1
        else:
            # Exploit: best known action
            q_values = {at: self.get_q_value(state_hash, at) for at in self.action_types}
            action_type = max(q_values, key=q_values.get)
        
        # Generate action parameters based on type
        parameters = self._generate_action_parameters(action_type, state)
        
        # Get confidence from Q-value
        confidence = min(abs(self.get_q_value(state_hash, action_type)), 1.0)
        
        return Action(action_type, parameters, confidence)
    
    def _generate_action_parameters(self, action_type: ActionType, state: State) -> Dict[str, Any]:
        """Generate specific parameters for each action type"""
        current_hour = state.temporal_context.get('hour', 12)
        
        if action_type == ActionType.UPLOAD_TIME_OPTIMIZATION:
            # Suggest optimal upload times based on current performance
            suggested_hours = [8, 12, 16, 20]  # Peak engagement hours
            return {
                'suggested_hour': random.choice(suggested_hours),
                'reason': 'peak_engagement_time'
            }
            
        elif action_type == ActionType.TITLE_OPTIMIZATION:
            return {
                'strategy': random.choice(['emotional_trigger', 'curiosity_gap', 'number_based', 'question_based']),
                'max_length': 60,
                'include_keywords': True
            }
            
        elif action_type == ActionType.THUMBNAIL_OPTIMIZATION:
            return {
                'style': random.choice(['bright_colors', 'contrast_face', 'text_overlay', 'emotional_expression']),
                'face_detection': True,
                'text_size': random.choice(['large', 'medium'])
            }
            
        elif action_type == ActionType.CONTENT_STRATEGY:
            return {
                'content_type': random.choice(['tutorial', 'entertainment', 'educational', 'trending_topic']),
                'duration_target': random.choice([600, 900, 1200]),  # 10, 15, 20 minutes
                'series_potential': random.choice([True, False])
            }
            
        else:
            return {'generic_optimization': True}
    
    def learn_from_experience(self, experience: Dict[str, Any]) -> float:
        """Learn from a single experience and return updated Q-value"""
        state_hash = experience['state_hash']
        action_type = ActionType(experience['action_type'])
        reward = experience['reward']
        next_state_hash = experience['next_state_hash']
        
        # Update Q-value
        self.update_q_value(state_hash, action_type, reward, next_state_hash)
        
        # Update stats
        self.learning_stats['total_actions'] += 1
        if reward > 0:
            self.learning_stats['successful_actions'] += 1
        
        self.episode_rewards.append(reward)
        
        # Calculate rolling average reward
        recent_rewards = self.episode_rewards[-100:]  # Last 100 experiences
        self.learning_stats['avg_reward'] = sum(recent_rewards) / len(recent_rewards)
        
        # Return updated Q-value
        return self.get_q_value(state_hash, action_type)
    
    def get_learning_progress(self) -> Dict[str, Any]:
        """Get current learning progress and statistics"""
        total_actions = self.learning_stats['total_actions']
        success_rate = 0.0
        
        if total_actions > 0:
            success_rate = self.learning_stats['successful_actions'] / total_actions
        
        exploration_rate = 0.0
        if total_actions > 0:
            exploration_rate = self.learning_stats['exploration_actions'] / total_actions
        
        return {
            'agent_id': self.agent_id,
            'total_actions': total_actions,
            'success_rate': success_rate,
            'avg_reward': self.learning_stats['avg_reward'],
            'exploration_rate': exploration_rate,
            'q_table_size': len(self.q_table),
            'epsilon': self.epsilon,
            'recent_episodes': len(self.episode_rewards)
        }
    
    def save_model_state(self) -> Dict[str, Any]:
        """Save current model state for persistence"""
        return {
            'agent_id': self.agent_id,
            'q_table': self.q_table,
            'learning_stats': self.learning_stats,
            'hyperparameters': {
                'learning_rate': self.learning_rate,
                'discount_factor': self.discount_factor,
                'epsilon': self.epsilon
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def load_model_state(self, state_data: Dict[str, Any]) -> None:
        """Load previously saved model state"""
        self.q_table = state_data.get('q_table', {})
        self.learning_stats = state_data.get('learning_stats', self.learning_stats)
        
        hyperparams = state_data.get('hyperparameters', {})
        self.learning_rate = hyperparams.get('learning_rate', self.learning_rate)
        self.discount_factor = hyperparams.get('discount_factor', self.discount_factor)
        self.epsilon = hyperparams.get('epsilon', self.epsilon)


class RLEngine:
    """Main Reinforcement Learning Engine coordinating all components"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.q_agent = QLearningAgent(agent_id)
        self.reward_calculator = YouTubeRewardCalculator()
        
        # Current episode tracking
        self.current_episode = {
            'state': None,
            'action': None,
            'start_time': None,
            'metrics_before': None
        }
    
    def observe_environment(self, youtube_metrics: Dict[str, Any], 
                          context_data: Dict[str, Any]) -> State:
        """Create state observation from environment data"""
        current_time = datetime.now()
        
        state = State(
            video_metrics=youtube_metrics.get('video_metrics', {}),
            channel_metrics=youtube_metrics.get('channel_metrics', {}),
            temporal_context={
                'hour': current_time.hour,
                'day_of_week': current_time.weekday(),
                'month': current_time.month
            },
            content_context=context_data.get('content_context', {}),
            audience_context=context_data.get('audience_context', {})
        )
        
        return state
    
    def decide_action(self, state: State, exploration_mode: bool = False) -> Action:
        """Decide next action based on current state"""
        action = self.q_agent.choose_action(state, exploration_mode)
        
        # Start new episode
        self.current_episode = {
            'state': state,
            'action': action,
            'start_time': datetime.now(),
            'metrics_before': {
                **state.video_metrics,
                **state.channel_metrics
            }
        }
        
        return action
    
    def process_feedback(self, new_metrics: Dict[str, Any]) -> float:
        """Process feedback from environment and learn"""
        if not self.current_episode['state']:
            return 0.0
        
        # Calculate time elapsed
        time_elapsed = datetime.now() - self.current_episode['start_time']
        hours_elapsed = time_elapsed.total_seconds() / 3600
        
        # Calculate reward
        reward = self.reward_calculator.calculate_reward(
            self.current_episode['metrics_before'],
            new_metrics,
            hours_elapsed
        )
        
        # Add engagement bonus
        engagement_bonus = self.reward_calculator.calculate_engagement_bonus(new_metrics)
        reward += engagement_bonus
        
        # Create experience for learning
        experience = {
            'state_hash': self.q_agent.get_state_hash(self.current_episode['state']),
            'action_type': self.current_episode['action'].action_type.value,
            'reward': reward,
            'next_state_hash': '',  # Will be filled when next state is observed
            'timestamp': datetime.now().isoformat(),
            'metrics_before': self.current_episode['metrics_before'],
            'metrics_after': new_metrics,
            'time_elapsed_hours': hours_elapsed
        }
        
        # Learn from experience
        updated_q_value = self.q_agent.learn_from_experience(experience)
        
        # Reset episode
        self.current_episode = {'state': None, 'action': None, 'start_time': None, 'metrics_before': None}
        
        return updated_q_value
    
    def get_engine_status(self) -> Dict[str, Any]:
        """Get comprehensive engine status"""
        learning_progress = self.q_agent.get_learning_progress()
        
        return {
            'agent_id': self.agent_id,
            'learning_progress': learning_progress,
            'current_episode_active': self.current_episode['state'] is not None,
            'reward_calculator_weights': self.reward_calculator.metric_weights,
            'last_updated': datetime.now().isoformat()
        }
