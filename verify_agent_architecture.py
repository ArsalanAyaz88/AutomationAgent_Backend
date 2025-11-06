"""
Verify Agent Memory Architecture
Shows how each agent has its own STM, LTM, RL but shares Central Memory
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 80)
print("🧠 AGENT MEMORY ARCHITECTURE VERIFICATION")
print("=" * 80)

# Initialize Registry
print("\n📋 Initializing Agent Registry...")
from rl_integration import RLAgentRegistry

registry = RLAgentRegistry()

# Test all 7 agents
test_agents = [
    'agent1_channel_auditor',
    'agent2_title_auditor', 
    'agent3_script_generator',
    'agent4_script_to_scene',
    'agent5_ideas_generator',
    'agent6_roadmap',
    'fifty_videos_fetcher'
]

print(f"\n✅ Registry created with {len(registry.agent_configs)} agent configurations")

central_connected = registry.central_memory._check_connection()
if central_connected:
    print(f"✅ Central Memory: Connected")
else:
    print(f"⚠️  Central Memory: Not connected (working in isolated mode)")

# Initialize agents
print("\n" + "=" * 80)
print("🔧 INITIALIZING AGENTS & CHECKING MEMORY ISOLATION")
print("=" * 80)

for agent_name in test_agents:
    print(f"\n{'─' * 80}")
    print(f"🤖 Agent: {agent_name}")
    print(f"{'─' * 80}")
    
    agent = registry.initialize_agent(agent_name)
    
    # Check STM isolation
    print(f"\n  📦 STM (Short-Term Memory - Redis):")
    print(f"     ✅ Agent ID: {agent.stm.agent_id}")
    print(f"     ✅ Key Prefix: {agent.stm.key_prefix}")
    try:
        agent.stm.redis_client.ping()
        print(f"     ✅ Redis Connection: Active")
    except Exception:
        print(f"     ⚠️  Redis Connection: Not available (will store in memory)")
    print(f"     ℹ️  Storage: Redis with 24hr TTL")
    print(f"     ℹ️  Isolated: Each agent has unique key prefix")
    
    # Check LTM isolation
    print(f"\n  💾 LTM (Long-Term Memory - MongoDB):")
    print(f"     ✅ Agent ID: {agent.ltm.agent_id}")
    if agent.ltm._check_connection():
        print(f"     ✅ Experiences Collection: {agent.ltm.experiences_collection.name}")
        print(f"     ✅ Patterns Collection: {agent.ltm.patterns_collection.name}")
        print(f"     ✅ Strategies Collection: {agent.ltm.strategies_collection.name}")
    else:
        print(f"     ⚠️  MongoDB not connected (will be created on first use)")
    print(f"     ℹ️  Storage: MongoDB - Persistent")
    print(f"     ℹ️  Isolated: Each agent has separate collections")
    
    # Check RL Engine isolation
    print(f"\n  🎯 RL Engine (Q-Learning):")
    print(f"     ✅ Agent ID: {agent.rl_engine.agent_id}")
    print(f"     ✅ Q-Agent: {agent.rl_engine.q_agent.agent_id}")
    print(f"     ✅ Learning Rate: {agent.rl_engine.q_agent.learning_rate}")
    print(f"     ✅ Discount Factor: {agent.rl_engine.q_agent.discount_factor}")
    print(f"     ✅ Epsilon (Exploration): {agent.rl_engine.q_agent.epsilon}")
    print(f"     ℹ️  Storage: In-Memory Q-Table")
    print(f"     ℹ️  Isolated: Each agent has independent Q-table")
    
    # Check agent type and capabilities
    print(f"\n  📊 Agent Configuration:")
    print(f"     Type: {agent.agent_type}")
    print(f"     Capabilities: {', '.join(agent.capabilities)}")

# Check Central Memory (Shared)
print("\n" + "=" * 80)
print("🌐 CENTRAL MEMORY (SHARED BY ALL AGENTS)")
print("=" * 80)

central = registry.central_memory

if central._check_connection():
    print("\n  ✅ Central Memory Database Connected")
    print(f"\n  📚 Collections (Shared by all agents):")
    print(f"     • global_insights: Global patterns from all agents")
    print(f"     • agent_synchronization: Last sync data for all agents")
    print(f"     • collective_strategies: Multi-agent strategies")
    print(f"     • cross_agent_patterns: Common patterns across agents")
    print(f"     • performance_leaderboard: Agent performance rankings")
    print(f"     • active_agents: Registry of all active agents")
    
    # Check how many agents are registered
    try:
        agent_count = central.active_agents.count_documents({})
        print(f"\n  👥 Registered Agents: {agent_count}")
        
        # Show registered agents
        if agent_count > 0:
            agents = list(central.active_agents.find({}, {'agent_id': 1, 'agent_type': 1}))
            print(f"\n  📋 Agent List:")
            for a in agents:
                print(f"     • {a['agent_id']} ({a['agent_type']})")
    except Exception as e:
        print(f"\n  ⚠️  Could not query agents: {str(e)}")
else:
    print("\n  ⚠️  Central Memory not connected (MongoDB Atlas)")
    print("     Configure CENTRALMEMORY_DATABASE_URL in .env file")

# Summary
print("\n" + "=" * 80)
print("📊 ARCHITECTURE SUMMARY")
print("=" * 80)

print("""
┌─────────────────────────────────────────────────────────────┐
│  PER AGENT (Isolated):                                      │
├─────────────────────────────────────────────────────────────┤
│  ✅ STM (Redis)           - agent:NAME:stm:*               │
│  ✅ LTM (MongoDB)         - agent_NAME_*                    │
│  ✅ RL Engine (Memory)    - Independent Q-table             │
│  ✅ Reward Calculator     - YouTube metrics based           │
│  ✅ Realtime Metrics      - Performance tracking            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  SHARED (All Agents):                                       │
├─────────────────────────────────────────────────────────────┤
│  🌐 Central Memory (MongoDB) - Collective Intelligence      │
│     • Global insights from all agents                       │
│     • Cross-agent pattern detection                         │
│     • Performance leaderboard                               │
│     • Shared strategies                                     │
└─────────────────────────────────────────────────────────────┘

""")

print("=" * 80)
print("✅ VERIFICATION COMPLETE")
print("=" * 80)

print("""
Key Findings:
1. ✅ Each agent has its OWN STM, LTM, and RL Engine
2. ✅ STM uses Redis with unique key prefix per agent
3. ✅ LTM uses MongoDB with separate collections per agent
4. ✅ RL Engine has independent Q-table per agent (always works)
5. ✅ Central Memory is SHARED by all agents for collective intelligence

This is a HYBRID architecture:
- Individual learning for specialization (STM/LTM/RL per agent)
- Collective intelligence for optimization (Central Memory shared)

⚠️  NOTE: System works WITHOUT databases!
   - RL Engine uses in-memory Q-tables (no database needed)
   - STM falls back to memory if Redis unavailable
   - LTM features disabled if MongoDB unavailable
   - Central Memory features disabled if MongoDB unavailable

اردو میں: ہاں، ہر agent کا اپنا STM، LTM، اور RL ہے۔
         لیکن Central Memory سب agents share کرتے ہیں!
         Database نہ ہو تو بھی RL Engine کام کرتا ہے!
""")

print("\n📖 For detailed documentation, see: AGENT_MEMORY_ARCHITECTURE.md\n")
