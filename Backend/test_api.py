"""
Test script for YouTube Automation AI Agents API
Run this after starting the main.py server to test all endpoints
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


def print_response(agent_name: str, response: Dict[Any, Any]):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"🤖 {agent_name}")
    print(f"{'='*60}")
    
    if response.get("success"):
        print(f"✅ Success!")
        print(f"\n📝 Result:\n{response['result'][:500]}...")  # First 500 chars
    else:
        print(f"❌ Error: {response.get('error', 'Unknown error')}")
    print(f"{'='*60}\n")


def test_agent1_channel_audit():
    """Test Agent 1: Channel Auditor"""
    endpoint = f"{BASE_URL}/api/agent1/audit-channel"
    
    payload = {
        "channel_urls": [
            "https://www.youtube.com/@MrBeast",
            "https://www.youtube.com/@veritasium"
        ],
        "user_query": "Compare these channels and tell me which has better growth potential"
    }
    
    print("🔄 Testing Agent 1: Channel Auditor...")
    response = requests.post(endpoint, json=payload)
    print_response("Agent 1: Channel Auditor", response.json())


def test_agent2_title_audit():
    """Test Agent 2: Title & Thumbnail Auditor"""
    endpoint = f"{BASE_URL}/api/agent2/audit-titles"
    
    payload = {
        "video_urls": [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=9bZkp7q19f0"
        ],
        "user_query": "Analyze these videos for title patterns and thumbnail strategies"
    }
    
    print("🔄 Testing Agent 2: Title Auditor...")
    response = requests.post(endpoint, json=payload)
    print_response("Agent 2: Title Auditor", response.json())


def test_agent3_script_generation():
    """Test Agent 3: Script Writer"""
    endpoint = f"{BASE_URL}/api/agent3/generate-script"
    
    payload = {
        "title_audit_data": """
        Winning patterns identified:
        - Questions in titles get 30% more clicks
        - Numbers (3, 5, 7) perform well
        - Bold text on thumbnails increases CTR by 25%
        - First 10 seconds must hook with curiosity gap
        """,
        "topic": "How to Grow Your YouTube Channel Fast",
        "user_query": "Create a 5-minute script following these patterns"
    }
    
    print("🔄 Testing Agent 3: Script Writer...")
    response = requests.post(endpoint, json=payload)
    print_response("Agent 3: Script Writer", response.json())


def test_agent4_script_to_prompts():
    """Test Agent 4: Script to Prompts Converter"""
    endpoint = f"{BASE_URL}/api/agent4/script-to-prompts"
    
    sample_script = """
    [INTRO - 0:00-0:10]
    Hook: "What if I told you that you're doing YouTube completely wrong?"
    
    [MAIN CONTENT - 0:10-4:00]
    Point 1: Consistency beats perfection
    Point 2: Thumbnails matter more than you think
    Point 3: The first 10 seconds are everything
    
    [OUTRO - 4:00-4:30]
    Call to action: Subscribe and try these tips
    """
    
    payload = {
        "script": sample_script,
        "user_query": "Convert to detailed scene-by-scene prompts with camera angles"
    }
    
    print("🔄 Testing Agent 4: Script to Prompts...")
    response = requests.post(endpoint, json=payload)
    print_response("Agent 4: Script to Prompts Converter", response.json())


def test_agent5_ideas_generation():
    """Test Agent 5: Ideas Generator"""
    endpoint = f"{BASE_URL}/api/agent5/generate-ideas"
    
    payload = {
        "winning_videos_data": """
        Top performing videos:
        1. "I Tried X for 30 Days" - 5M views, 12% CTR
        2. "Why Everyone is Wrong About Y" - 3M views, 10% CTR
        3. "The Truth About Z (Shocking)" - 4M views, 11% CTR
        
        Common patterns: controversy, time-bound challenges, truth reveals
        """,
        "user_query": "Generate 3 title and thumbnail concepts for productivity niche"
    }
    
    print("🔄 Testing Agent 5: Ideas Generator...")
    response = requests.post(endpoint, json=payload)
    print_response("Agent 5: Ideas Generator", response.json())


def test_agent6_roadmap_generation():
    """Test Agent 6: Content Roadmap Generator"""
    endpoint = f"{BASE_URL}/api/agent6/generate-roadmap"
    
    payload = {
        "niche": "AI & Technology",
        "winning_data": "Tutorial-style videos perform best, 8-12 minute format ideal",
        "user_query": "Create a 30-video roadmap for beginners to advanced learners"
    }
    
    print("🔄 Testing Agent 6: Roadmap Generator...")
    response = requests.post(endpoint, json=payload)
    print_response("Agent 6: Content Roadmap Generator", response.json())


def test_health_check():
    """Test health check endpoint"""
    endpoint = f"{BASE_URL}/health"
    
    print("🔄 Testing Health Check...")
    response = requests.get(endpoint)
    print(f"✅ Health Status: {response.json()}")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🚀 YouTube Automation AI Agents API - Test Suite")
    print("="*60)
    print("\n⚠️  Make sure the API server is running on port 8000!")
    print("Run: uv run main.py\n")
    
    input("Press Enter to start tests...")
    
    try:
        # Test health first
        test_health_check()
        
        # Test each agent
        # Note: Some tests may take a while depending on API response times
        
        # Uncomment the agents you want to test:
        
        # test_agent1_channel_audit()  # Requires YouTube MCP server
        # test_agent2_title_audit()    # Requires YouTube MCP server
        test_agent3_script_generation()
        test_agent4_script_to_prompts()
        test_agent5_ideas_generation()
        test_agent6_roadmap_generation()
        
        print("\n✅ All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API server.")
        print("Make sure the server is running: uv run main.py")
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")


if __name__ == "__main__":
    main()
