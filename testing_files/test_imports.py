"""
Quick test script to verify all agent imports work correctly
"""

print("Testing agent imports...")
print("="*60)

try:
    from AllAgents.Agent_1_ChannelAuditor.Agent_1_ChannelAuditor import register_agent1_routes
    print("✅ Agent 1 - Channel Auditor imported successfully")
except Exception as e:
    print(f"❌ Agent 1 failed: {e}")

try:
    from AllAgents.Agent_2_TitleAuditor.Agent_2_TitleAuditor import register_agent2_routes
    print("✅ Agent 2 - Title Auditor imported successfully")
except Exception as e:
    print(f"❌ Agent 2 failed: {e}")

try:
    from AllAgents.Agent_3_ScriptGenerator.Agent_3_ScriptGenerator import register_agent3_routes
    print("✅ Agent 3 - Script Generator imported successfully")
except Exception as e:
    print(f"❌ Agent 3 failed: {e}")

try:
    from AllAgents.Agent_4_ScriptToScene.Agent_4_ScriptToScene import register_agent4_routes
    print("✅ Agent 4 - Script to Scene imported successfully")
except Exception as e:
    print(f"❌ Agent 4 failed: {e}")

try:
    from AllAgents.Agent_5_generateIdeas.Agent_5_generateIdeas import register_agent5_routes
    print("✅ Agent 5 - Generate Ideas imported successfully")
except Exception as e:
    print(f"❌ Agent 5 failed: {e}")

try:
    from AllAgents.Agent_6_roadmap.Agent_6_roadmap import register_agent6_routes
    print("✅ Agent 6 - Roadmap imported successfully")
except Exception as e:
    print(f"❌ Agent 6 failed: {e}")

print("="*60)
print("✅ All imports successful! Ready to run main.py")
