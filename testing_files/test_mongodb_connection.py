"""
Test MongoDB connection with SSL/TLS configuration
"""
import os
import sys

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

print("Testing MongoDB connections...")
print("-" * 60)

try:
    # Test Central Memory DB
    print("\n1. Testing Central Memory DB...")
    from databasess.agents_CentralMemory.central_memory import CentralMemoryDB
    
    central_db = CentralMemoryDB()
    if central_db.client is not None:
        print("   ✅ Central Memory DB connection successful!")
    else:
        print("   ⚠️  Central Memory DB connection failed (will retry on use)")
    
except Exception as e:
    print(f"   ❌ Error testing Central Memory: {str(e)}")

try:
    # Test LTM DB
    print("\n2. Testing LTM DB...")
    from databasess.agents_LTM.mongodb_memory import AgentLTM
    
    ltm = AgentLTM(agent_id="test_agent")
    if ltm.client is not None:
        print("   ✅ LTM DB connection successful!")
    else:
        print("   ⚠️  LTM DB connection failed (will retry on use)")
        
except Exception as e:
    print(f"   ❌ Error testing LTM: {str(e)}")

print("\n" + "-" * 60)
print("Test completed! If connections failed, check:")
print("1. MongoDB Atlas credentials are correct")
print("2. IP address is whitelisted in MongoDB Atlas")
print("3. Network connection is stable")
print("4. Environment variables are set: LTM_DATABASE_URL, CENTRALMEMORY_DATABASE_URL")
