"""
Quick test to verify .env file is loading correctly
"""

import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

print("=" * 60)
print("Environment Variables Test")
print("=" * 60)

# Check critical variables
variables = [
    "YOUTUBE_API_KEY",
    "YOUTUBE_HTTP_BASE_URL",
    "GEMINI_API_KEY",
    "MONGODB_URI"
]

for var in variables:
    value = os.getenv(var)
    if value:
        # Show first 20 chars only for security
        masked = value[:20] + "..." if len(value) > 20 else value
        print(f"✅ {var}: {masked}")
    else:
        print(f"❌ {var}: NOT FOUND")

print("=" * 60)

# Test YouTube client import
try:
    from youtube_direct_client import YouTubeDirectClient
    print("✅ YouTubeDirectClient imported successfully")
    
    # Try to create instance
    client = YouTubeDirectClient()
    print(f"✅ Client created with API key: {client.api_key[:20]}...")
    
except Exception as e:
    print(f"❌ Error: {e}")

print("=" * 60)
