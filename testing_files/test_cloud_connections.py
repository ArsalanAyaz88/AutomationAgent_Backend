"""
Test Cloud Database Connections
Verifies Redis Cloud and MongoDB Atlas connections using environment variables
"""

import os
import sys
from dotenv import load_dotenv
import redis
from pymongo import MongoClient
from datetime import datetime

# Load environment variables
load_dotenv()

def test_redis_connection():
    """Test Redis Cloud connection"""
    print("🔧 Testing Redis Cloud (STM) Connection...")
    
    redis_url = os.getenv('STM_DATABASE_URL')
    if not redis_url:
        print("❌ STM_DATABASE_URL not found in environment variables")
        return False
    
    try:
        # Test connection
        client = redis.from_url(redis_url, decode_responses=True)
        
        # Test basic operations
        test_key = "test_connection"
        test_value = f"test_{datetime.now().isoformat()}"
        
        client.set(test_key, test_value, ex=60)  # Expire in 60 seconds
        retrieved_value = client.get(test_key)
        
        if retrieved_value == test_value:
            print("✅ Redis Cloud connection successful!")
            print(f"   - URL: {redis_url[:30]}...")
            print(f"   - Test key/value operation: PASSED")
            
            # Cleanup
            client.delete(test_key)
            return True
        else:
            print("❌ Redis Cloud test failed - value mismatch")
            return False
            
    except Exception as e:
        print(f"❌ Redis Cloud connection failed: {str(e)}")
        return False

def test_ltm_mongodb_connection():
    """Test MongoDB Atlas LTM connection"""
    print("\n🔧 Testing MongoDB Atlas (LTM) Connection...")
    
    mongo_url = os.getenv('LTM_DATABASE_URL')
    if not mongo_url:
        print("❌ LTM_DATABASE_URL not found in environment variables")
        return False
    
    try:
        # Test connection
        client = MongoClient(mongo_url)
        
        # Test database access
        db = client["youtube_agents_ltm"]
        collection = db["connection_test"]
        
        # Test basic operations
        test_doc = {
            "test_type": "connection_test",
            "timestamp": datetime.now(),
            "status": "testing"
        }
        
        result = collection.insert_one(test_doc)
        doc_id = result.inserted_id
        
        # Retrieve and verify
        retrieved_doc = collection.find_one({"_id": doc_id})
        
        if retrieved_doc and retrieved_doc["test_type"] == "connection_test":
            print("✅ MongoDB Atlas (LTM) connection successful!")
            print(f"   - Database: youtube_agents_ltm")
            print(f"   - Collection operations: PASSED")
            
            # Cleanup
            collection.delete_one({"_id": doc_id})
            return True
        else:
            print("❌ MongoDB Atlas (LTM) test failed - document mismatch")
            return False
            
    except Exception as e:
        print(f"❌ MongoDB Atlas (LTM) connection failed: {str(e)}")
        return False

def test_central_mongodb_connection():
    """Test MongoDB Atlas Central Memory connection"""
    print("\n🔧 Testing MongoDB Atlas (Central Memory) Connection...")
    
    mongo_url = os.getenv('CENTRALMEMORY_DATABASE_URL')
    if not mongo_url:
        print("❌ CENTRALMEMORY_DATABASE_URL not found in environment variables")
        return False
    
    try:
        # Test connection
        client = MongoClient(mongo_url)
        
        # Test database access
        db = client["youtube_agents_central"]
        collection = db["connection_test"]
        
        # Test basic operations
        test_doc = {
            "test_type": "central_memory_test", 
            "timestamp": datetime.now(),
            "status": "testing"
        }
        
        result = collection.insert_one(test_doc)
        doc_id = result.inserted_id
        
        # Retrieve and verify
        retrieved_doc = collection.find_one({"_id": doc_id})
        
        if retrieved_doc and retrieved_doc["test_type"] == "central_memory_test":
            print("✅ MongoDB Atlas (Central Memory) connection successful!")
            print(f"   - Database: youtube_agents_central")
            print(f"   - Collection operations: PASSED")
            
            # Cleanup
            collection.delete_one({"_id": doc_id})
            return True
        else:
            print("❌ MongoDB Atlas (Central Memory) test failed - document mismatch")
            return False
            
    except Exception as e:
        print(f"❌ MongoDB Atlas (Central Memory) connection failed: {str(e)}")
        return False

def test_all_connections():
    """Test all cloud database connections"""
    print("🚀 YouTube Agent RL System - Cloud Database Connection Test")
    print("=" * 60)
    
    # Check environment variables exist
    required_vars = ['STM_DATABASE_URL', 'LTM_DATABASE_URL', 'CENTRALMEMORY_DATABASE_URL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please check your .env file")
        return False
    
    # Test each connection
    redis_ok = test_redis_connection()
    ltm_ok = test_ltm_mongodb_connection() 
    central_ok = test_central_mongodb_connection()
    
    print("\n" + "=" * 60)
    print("📊 Connection Test Summary:")
    print(f"   Redis Cloud (STM): {'✅ PASSED' if redis_ok else '❌ FAILED'}")
    print(f"   MongoDB Atlas (LTM): {'✅ PASSED' if ltm_ok else '❌ FAILED'}")
    print(f"   MongoDB Atlas (Central): {'✅ PASSED' if central_ok else '❌ FAILED'}")
    
    all_passed = redis_ok and ltm_ok and central_ok
    
    if all_passed:
        print("\n🎉 All cloud database connections are working!")
        print("Your RL system is ready to use cloud databases.")
    else:
        print("\n⚠️ Some connections failed. Please check your credentials.")
        
    return all_passed

def test_rl_system_initialization():
    """Test if the RL system can initialize with cloud databases"""
    print("\n🔧 Testing RL System Initialization with Cloud Databases...")
    
    try:
        # Import system components
        sys.path.append('databasess')
        from agents_STM.redis_memory import AgentSTM, RealtimeMetrics
        from agents_LTM.mongodb_memory import AgentLTM
        from agents_CentralMemory.central_memory import CentralMemoryDB
        
        # Test STM initialization
        stm = AgentSTM("test_agent")
        print("✅ STM (Redis) initialization: PASSED")
        
        # Test LTM initialization  
        ltm = AgentLTM("test_agent")
        print("✅ LTM (MongoDB) initialization: PASSED")
        
        # Test Central Memory initialization
        central = CentralMemoryDB()
        print("✅ Central Memory initialization: PASSED")
        
        # Test basic operations
        test_experience = {
            'action': 'test_action',
            'reward': 0.8,
            'q_value': 0.9,
            'state': {'test': True}
        }
        
        exp_id = stm.store_experience(test_experience)
        print("✅ STM store operation: PASSED")
        
        # Register agent in central memory
        central.register_agent("test_agent", "test_type", ["testing"])
        print("✅ Central Memory registration: PASSED")
        
        print("\n🎉 RL System cloud initialization successful!")
        return True
        
    except Exception as e:
        print(f"❌ RL System initialization failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Test basic connections
    connections_ok = test_all_connections()
    
    if connections_ok:
        # Test RL system initialization
        test_rl_system_initialization()
    
    print(f"\n{'🎯 Ready to run main_orchestrator.py!' if connections_ok else '❌ Fix connection issues first'}")
