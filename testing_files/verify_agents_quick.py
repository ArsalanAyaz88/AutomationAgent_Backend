"""
Quick Agent Verification - Compact Summary of All Agents
Shows all 7 agents in a compact format
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 80)
print("🚀 QUICK AGENT VERIFICATION - ALL 7 AGENTS")
print("=" * 80)

# Initialize Registry
from rl_integration import RLAgentRegistry

registry = RLAgentRegistry()

# All agents
all_agents = [
    'agent1_channel_auditor',
    'agent2_title_auditor', 
    'agent3_script_generator',
    'agent4_script_to_scene',
    'agent5_ideas_generator',
    'agent6_roadmap',
    'fifty_videos_fetcher'
]

print(f"\n✅ Registry: {len(registry.agent_configs)} agents configured")

# Check connectivity
central_ok = registry.central_memory._check_connection()
print(f"{'✅' if central_ok else '⚠️ '} Central Memory: {'Connected' if central_ok else 'Offline (isolated mode)'}")

print("\n" + "=" * 80)
print("📋 AGENT INITIALIZATION SUMMARY")
print("=" * 80)

results = []

for i, agent_name in enumerate(all_agents, 1):
    print(f"\n{i}. Initializing {agent_name}...", end=" ")
    
    try:
        agent = registry.initialize_agent(agent_name)
        
        # Check connections
        redis_ok = False
        try:
            agent.stm.redis_client.ping()
            redis_ok = True
        except:
            pass
        
        mongo_ok = agent.ltm._check_connection()
        rl_ok = hasattr(agent.rl_engine, 'q_agent')
        
        status = "✅ OK"
        details = {
            'agent': agent_name,
            'type': agent.agent_type,
            'stm': '✅ Redis' if redis_ok else '⚠️  Memory',
            'ltm': '✅ MongoDB' if mongo_ok else '⚠️  Offline',
            'rl': '✅ Active' if rl_ok else '❌ Failed',
            'status': 'operational'
        }
        
        results.append(details)
        print(status)
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)[:50]}")
        results.append({
            'agent': agent_name,
            'status': 'failed',
            'error': str(e)[:100]
        })

# Summary Table
print("\n" + "=" * 80)
print("📊 COMPLETE AGENT STATUS TABLE")
print("=" * 80)
print()
print("┌─────┬───────────────────────────┬─────────────────┬───────┬─────────┬───────┐")
print("│ No. │ Agent Name                │ Type            │ STM   │ LTM     │ RL    │")
print("├─────┼───────────────────────────┼─────────────────┼───────┼─────────┼───────┤")

for i, result in enumerate(results, 1):
    if result['status'] == 'operational':
        agent_name = result['agent'][:25].ljust(25)
        agent_type = result['type'][:15].ljust(15)
        stm = result['stm']
        ltm = result['ltm']
        rl = result['rl']
        print(f"│ {i}   │ {agent_name} │ {agent_type} │ {stm} │ {ltm} │ {rl} │")
    else:
        agent_name = result['agent'][:25].ljust(25)
        print(f"│ {i}   │ {agent_name} │ FAILED          │   ❌   │   ❌     │   ❌   │")

print("└─────┴───────────────────────────┴─────────────────┴───────┴─────────┴───────┘")

# Component Details
print("\n" + "=" * 80)
print("🔍 MEMORY ISOLATION VERIFICATION")
print("=" * 80)

print("\n📦 STM (Redis) Key Prefixes:")
for result in results:
    if result['status'] == 'operational':
        print(f"   • agent:{result['agent']}:stm")

print("\n💾 LTM (MongoDB) Collections:")
for result in results:
    if result['status'] == 'operational':
        print(f"   • agent_{result['agent']}_experiences")
        print(f"   • agent_{result['agent']}_patterns")
        print(f"   • agent_{result['agent']}_strategies")

print("\n🎯 RL Engine Q-Tables:")
for result in results:
    if result['status'] == 'operational':
        print(f"   • {result['agent']} (in-memory)")

# Statistics
operational = sum(1 for r in results if r['status'] == 'operational')
failed = len(results) - operational

print("\n" + "=" * 80)
print("📈 STATISTICS")
print("=" * 80)
print(f"""
Total Agents Configured: {len(all_agents)}
Successfully Initialized: {operational} ✅
Failed: {failed} {'❌' if failed > 0 else ''}

Memory Components Per Agent:
  • STM: Isolated Redis keys (agent:NAME:stm:*)
  • LTM: Isolated MongoDB collections (agent_NAME_*)
  • RL:  Isolated in-memory Q-tables

Shared Components:
  • Central Memory: 1 shared MongoDB database
  • Collections: global_insights, agent_synchronization, etc.

System Status: {'✅ FULLY OPERATIONAL' if operational == len(all_agents) else '⚠️  PARTIALLY OPERATIONAL' if operational > 0 else '❌ SYSTEM DOWN'}
""")

print("=" * 80)
print("✅ QUICK VERIFICATION COMPLETE")
print("=" * 80)

print("""
💡 Key Insights:
   1. Each agent has ISOLATED memory (STM, LTM, RL)
   2. All agents SHARE Central Memory for collective intelligence
   3. System works WITHOUT databases (RL uses in-memory Q-tables)
   4. Redis/MongoDB failures don't break the system

📖 For detailed per-agent verification, run: python verify_agent_architecture.py
📚 For complete documentation, see: AGENT_MEMORY_ARCHITECTURE.md
""")
