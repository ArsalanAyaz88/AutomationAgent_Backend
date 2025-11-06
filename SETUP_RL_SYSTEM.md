# YouTube Agents Reinforcement Learning System

## 🎯 System Overview

This system implements a sophisticated RL architecture where each agent learns locally and shares knowledge globally:

```
[Agent] → [STM - Redis] → Filter High Q-Values → [LTM - MongoDB] → [Central CPU Database]
```

## 🚀 Quick Start

### Prerequisites
1. **Redis Cloud** or local Redis Server (for STM - Short-Term Memory)
2. **MongoDB Atlas** or local MongoDB (for LTM - Long-Term Memory & Central Memory)  
3. **Python 3.8+**

### Installation

1. **Install Dependencies:**
```bash
cd Backend
pip install -r requirements.txt
```

2. **Setup Environment Variables:**
Create a `.env` file in the Backend folder with your database URLs:
```bash
# Cloud Database Connections
LTM_DATABASE_URL=mongodb+srv://username:password@cluster.mongodb.net/
STM_DATABASE_URL=redis://username:password@host:port
CENTRALMEMORY_DATABASE_URL=mongodb+srv://username:password@cluster.mongodb.net/
```

3. **Test Cloud Connections:**
```bash
python test_cloud_connections.py
```

4. **Run the System:**
```bash
cd agents_ReinforcementLearning
python main_orchestrator.py
```

### Cloud Database Setup

#### Redis Cloud (STM)
1. Create account at [Redis Cloud](https://redis.com/cloud/)
2. Create a database and get connection URL
3. Add to `.env` as `STM_DATABASE_URL`

#### MongoDB Atlas (LTM & Central Memory)
1. Create account at [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Create 2 clusters:
   - One for LTM (Long-Term Memory)
   - One for Central Memory 
3. Get connection strings and add to `.env`

## 🧠 Architecture Components

### 1. Short-Term Memory (STM) - Redis
- **File:** `databasess/agents_STM/redis_memory.py`
- **Purpose:** Fast, temporary storage of recent experiences
- **Features:**
  - Auto-expiring experiences (24h TTL)
  - Real-time metrics tracking
  - High Q-value filtering

### 2. Long-Term Memory (LTM) - MongoDB
- **File:** `databasess/agents_LTM/mongodb_memory.py`
- **Purpose:** Persistent storage of high-value experiences
- **Features:**
  - Pattern learning and recognition
  - Strategy optimization
  - Similar experience matching

### 3. Central Memory Database - MongoDB
- **File:** `databasess/agents_CentralMemory/central_memory.py`
- **Purpose:** Global knowledge sharing across all agents
- **Features:**
  - Cross-agent pattern detection
  - Collective strategy development
  - Performance leaderboards

### 4. RL Engine
- **File:** `agents_ReinforcementLearning/rl_engine.py`
- **Purpose:** Q-Learning implementation with YouTube-specific rewards
- **Features:**
  - State-action-reward loops
  - YouTube metrics-based reward calculation
  - Epsilon-greedy exploration

### 5. Memory Integration Loop
- **File:** `agents_ReinforcementLearning/memory_integration.py`
- **Purpose:** Orchestrates the entire memory flow
- **Features:**
  - STM → LTM promotion
  - Central memory synchronization
  - Global insight broadcasting

## 🔄 Learning Flow

```
1. Agent observes YouTube environment
2. RL engine decides action based on Q-values
3. Action results stored in STM (Redis)
4. High Q-value experiences promoted to LTM (MongoDB)  
5. LTM syncs with Central Memory every 30 minutes
6. Global insights redistributed to all agents
7. Cycle repeats with improved decision making
```

## 📊 Monitoring & Analytics

The system provides comprehensive monitoring:

- **Agent Performance:** Individual Q-values, rewards, success rates
- **Global Statistics:** Cross-agent patterns, collective performance
- **Memory Usage:** STM/LTM storage statistics
- **Learning Progress:** Experience accumulation, strategy evolution

## 🎮 Demo Mode

Run the demo to see the system in action:

```bash
python main_orchestrator.py
```

This will:
1. Initialize 7 YouTube agents
2. Simulate YouTube data interactions
3. Demonstrate RL learning process
4. Show collective intelligence in action
5. Generate comprehensive reports

## 🔧 Configuration

Edit `system_config.json` to customize:

```json
{
  "stm_to_ltm_threshold": 0.7,
  "sync_interval_minutes": 30,
  "max_stm_experiences": 1000,
  "redis_host": "localhost",
  "redis_port": 6379,
  "mongodb_uri": "mongodb://localhost:27017"
}
```

## 🎯 Agent Types

The system includes 7 specialized agents:

1. **fifty_videos_fetcher** - Content collection and analysis
2. **trend_analyzer** - Trend detection and timing optimization  
3. **engagement_optimizer** - Title/thumbnail/CTR optimization
4. **audience_analyzer** - Demographic and behavior analysis
5. **content_strategist** - Content planning and series development
6. **performance_tracker** - Analytics and ROI calculation
7. **monetization_optimizer** - Revenue and sponsorship optimization

## 📈 Expected Results

After running the system:

- **Individual Learning:** Each agent improves its YouTube strategies
- **Collective Intelligence:** Agents share successful patterns
- **Performance Gains:** Measurable improvements in YouTube metrics
- **Adaptive Behavior:** System responds to YouTube algorithm changes
- **Knowledge Retention:** Important insights preserved long-term

## 🔍 Troubleshooting

**Redis Connection Issues:**
```bash
# Check Redis status
redis-cli ping
# Expected response: PONG
```

**MongoDB Connection Issues:**
```bash
# Check MongoDB status
mongosh
# Should connect without errors
```

**Import Errors:**
```bash
# Ensure all dependencies installed
pip install -r requirements.txt --upgrade
```

## 📝 Next Steps

1. **Integration:** Connect to real YouTube Data API
2. **Scaling:** Add more agent types for specific niches
3. **Advanced RL:** Implement deep Q-networks or policy gradients
4. **Real-time:** Add webhooks for immediate YouTube data updates
5. **Dashboard:** Build web interface for monitoring and control

## 🚨 Important Notes

- This is a **learning system** - performance improves over time
- **Rewards are based on YouTube metrics** - ensure accurate data
- **Memory grows over time** - monitor database sizes
- **Collective learning** - more agents = better performance
- **Continuous operation** recommended for best results
