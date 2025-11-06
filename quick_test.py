#!/usr/bin/env python3
"""
Quick test to check if all imports work
"""

try:
    print("🧪 Testing imports...")
    
    print("1. Testing RL integration...")
    from rl_integration import rl_registry, get_rl_system_status
    print("✅ RL integration imported successfully")
    
    print("2. Testing main app...")
    from main import app
    print("✅ Main app imported successfully")
    
    print("3. Testing FastAPI startup...")
    import uvicorn
    print("✅ All imports successful - ready to start server!")
    
    print("\n🚀 You can now start the server with:")
    print("uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
    
except Exception as e:
    print(f"❌ Import error: {str(e)}")
    import traceback
    traceback.print_exc()
