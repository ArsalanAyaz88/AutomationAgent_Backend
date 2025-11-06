# YouTube API Setup Guide 🔧

## **Problem Solved!** ✅

You no longer need `YOUTUBE_HTTP_BASE_URL` or Hugging Face Space!

The system now uses **direct YouTube Data API v3** with your existing `YOUTUBE_API_KEY`.

---

## **What Changed** 🔄

### **Before:**
```
❌ Required: YOUTUBE_HTTP_BASE_URL (Hugging Face Space)
❌ Complex setup
❌ Extra dependency
```

### **After:**
```
✅ Uses: YOUTUBE_API_KEY (Direct API)
✅ Simple setup
✅ No external dependencies
```

---

## **Setup Steps** 📋

### **1. Check Your `.env` File**

Make sure you have:

```env
# YouTube Data API Key (Required)
YOUTUBE_API_KEY=your_youtube_api_key_here

# MongoDB (Required)
MONGODB_URI=mongodb+srv://...
MONGODB_DB=youtube_ops

# AI Model (Required)
GEMINI_API_KEY=your_gemini_key
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
GEMINI_MODEL_NAME=gemini-2.0-flash-exp
```

---

### **2. Get YouTube API Key** (If you don't have one)

1. Go to: https://console.cloud.google.com/
2. Create a new project or select existing
3. Enable **YouTube Data API v3**
4. Go to "Credentials" → "Create Credentials" → "API Key"
5. Copy the API key
6. Add to `.env`:
   ```
   YOUTUBE_API_KEY=AIzaSy...your_key_here
   ```

---

### **3. Restart Backend**

```bash
cd Backend
python main.py
```

You should see:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## **How It Works Now** 🔧

### **Old Architecture:**
```
Your App → Hugging Face Space → YouTube API
          (Required proxy)
```

### **New Architecture:**
```
Your App → YouTube API
          (Direct connection)
```

---

## **Files Created/Updated** 📁

### **New File:**
```
Backend/youtube_direct_client.py
├─ YouTubeDirectClient class
├─ Uses YouTube Data API v3 directly
└─ Backward compatible with YouTubeHttpClient
```

### **Updated Files:**
```
Backend/channel_analytics_tracker.py
├─ Import updated to use direct client
└─ Fallback to HTTP client if needed

Backend/youtube_tools.py
├─ Import updated to use direct client
└─ Fallback to HTTP client if needed
```

---

## **API Methods Supported** 📚

```python
# Video operations
await client.get_video(video_id)
await client.get_video_stats(video_id)
await client.search_videos(query)

# Channel operations
await client.get_channel(channel_id)
await client.list_channel_videos(channel_id)

# Playlist operations
await client.get_playlist(playlist_id)
await client.get_playlist_items(playlist_id)

# Health check
await client.health()
```

---

## **Testing** 🧪

### **Test 1: API Key Works**

```python
# test_youtube_direct.py
import asyncio
from youtube_direct_client import YouTubeDirectClient

async def test():
    client = YouTubeDirectClient()
    
    # Test health
    health = await client.health()
    print(f"Health: {health}")
    
    # Test get video
    video = await client.get_video_stats("dQw4w9WgXcQ")
    print(f"Video: {video['items'][0]['snippet']['title']}")
    
asyncio.run(test())
```

Run:
```bash
cd Backend
python test_youtube_direct.py
```

---

### **Test 2: Channel Tracking**

```bash
curl -X POST http://localhost:8000/api/channel/track \
  -H "Content-Type: application/json" \
  -d '{
    "channel_url": "https://youtu.be/VIDEO_ID"
  }'
```

Should work now! ✅

---

## **YouTube API Quotas** ⚠️

### **Daily Limit:**
- **10,000 units per day** (default)
- Search: 100 units per query
- Video details: 1 unit
- Channel details: 1 unit

### **Cost Per Operation:**
```
get_video():              1 unit
get_channel():            1 unit
search_videos():          100 units
list_channel_videos():    1 unit per page
```

### **Tips to Save Quota:**
1. Cache results when possible
2. Use specific requests (don't fetch unnecessary data)
3. Batch operations
4. Request quota increase if needed

---

## **Error Handling** 🚨

### **Common Errors:**

#### **1. API Key Invalid:**
```
RuntimeError: YouTube API returned 400: API key not valid
```
**Fix:** Check your `YOUTUBE_API_KEY` in `.env`

#### **2. Quota Exceeded:**
```
RuntimeError: YouTube API returned 403: quotaExceeded
```
**Fix:** Wait until tomorrow or request quota increase

#### **3. Video Not Found:**
```
RuntimeError: YouTube API returned 404
```
**Fix:** Check video ID is correct and video is public

---

## **Advantages of Direct API** 🌟

```
✅ Simpler: No external proxy needed
✅ Faster: Direct API calls
✅ Reliable: No third-party dependency
✅ Secure: API key in your control
✅ Standard: Uses official YouTube API
✅ Documented: Official Google docs
```

---

## **Backward Compatibility** ✅

### **If You Want To Use Hugging Face Space:**

1. Set in `.env`:
   ```
   YOUTUBE_HTTP_BASE_URL=https://your-space.hf.space
   ```

2. Comment out direct client import:
   ```python
   # from youtube_direct_client import YouTubeHttpClient
   from youtube_http_client import YouTubeHttpClient
   ```

The system will automatically use the HTTP client if available.

---

## **Migration Guide** 🔄

### **From HTTP Client to Direct Client:**

**No changes needed!** ✅

The interface is identical:
```python
# Both work the same way
client = YouTubeHttpClient()  # Auto-uses direct client

# All methods work identically
await client.get_video(video_id)
await client.get_channel(channel_id)
```

---

## **Troubleshooting** 🔧

### **Issue: Import Error**

```
ImportError: No module named 'httpx'
```

**Fix:**
```bash
pip install httpx
```

### **Issue: Still Getting YOUTUBE_HTTP_BASE_URL Error**

**Fix:**
1. Delete `__pycache__` folders:
   ```bash
   find . -type d -name __pycache__ -exec rm -rf {} +
   ```
2. Restart Python:
   ```bash
   python main.py
   ```

---

## **Summary** 📝

### **Quick Setup:**
```bash
1. Add YOUTUBE_API_KEY to .env
2. Delete __pycache__ folders
3. Restart backend
4. ✅ Done!
```

### **No Longer Needed:**
```
❌ YOUTUBE_HTTP_BASE_URL
❌ Hugging Face Space
❌ External proxy setup
```

### **What You Need:**
```
✅ YOUTUBE_API_KEY (in .env)
✅ Backend restart
✅ That's it!
```

---

**Now your video URL tracking will work! 🎉**

Test it:
```
https://youtu.be/tmiPsk3s0lg?si=Zuv2SXwDxzBBwiQLH
```
