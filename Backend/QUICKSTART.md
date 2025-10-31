# 🚀 Quick Start Guide

Get your YouTube Automation API running in 5 minutes!

## Step 1: Install Dependencies

```bash
cd d:\Mission\youtube\Backend
uv sync
```

## Step 2: Configure API Keys

Edit `.env` file with your API keys:

```env
# Required for all agents
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
YOUTUBE_API_KEY=your_youtube_api_key_here
```

**Get your API keys:**
- **Gemini**: https://ai.google.dev/
- **Groq**: https://console.groq.com/keys
- **YouTube Data API**: https://console.cloud.google.com/apis/

## Step 3: Build YouTube MCP Server (First time only)

```bash
cd channel_auditor_agent_1/youtube-mcp-server
npm install
npm run build
cd ../..
```

## Step 4: Start the API Server

```bash
uv run main.py
```

The server will start on `http://localhost:8000`

## Step 5: Test the API

Open in browser: `http://localhost:8000/docs`

Or run the test script:
```bash
uv run test_api.py
```

---

## 📋 Example Workflow

### 1. Audit Channels (Agent 1)
```bash
curl -X POST http://localhost:8000/api/agent1/audit-channel \
  -H "Content-Type: application/json" \
  -d '{
    "channel_urls": ["https://www.youtube.com/@YourCompetitor"]
  }'
```

### 2. Analyze Winning Videos (Agent 2)
```bash
curl -X POST http://localhost:8000/api/agent2/audit-titles \
  -H "Content-Type: application/json" \
  -d '{
    "video_urls": ["https://www.youtube.com/watch?v=VIDEO_ID"]
  }'
```

### 3. Generate Script (Agent 3)
```bash
curl -X POST http://localhost:8000/api/agent3/generate-script \
  -H "Content-Type: application/json" \
  -d '{
    "title_audit_data": "Your analysis from Agent 2",
    "topic": "Your video topic"
  }'
```

### 4. Create Visual Prompts (Agent 4)
```bash
curl -X POST http://localhost:8000/api/agent4/script-to-prompts \
  -H "Content-Type: application/json" \
  -d '{
    "script": "Your script from Agent 3"
  }'
```

### 5. Generate Title Ideas (Agent 5)
```bash
curl -X POST http://localhost:8000/api/agent5/generate-ideas \
  -H "Content-Type: application/json" \
  -d '{
    "winning_videos_data": "Data from successful videos"
  }'
```

### 6. Create Content Roadmap (Agent 6)
```bash
curl -X POST http://localhost:8000/api/agent6/generate-roadmap \
  -H "Content-Type: application/json" \
  -d '{
    "niche": "Your niche here"
  }'
```

---

## 🎯 Pro Tips

1. **Start with Agent 1 & 2**: Analyze competitors before creating content
2. **Chain agents**: Use output from one agent as input to the next
3. **Experiment with queries**: Custom `user_query` field for specific needs
4. **Monitor quotas**: Watch your Gemini and Groq API usage
5. **Use Swagger UI**: `http://localhost:8000/docs` for interactive testing

---

## ⚡ Common Issues

### Port Already in Use
```bash
# Change port in main.py (line 423) or kill existing process
uvicorn main:app --port 8001
```

### API Key Errors
- Check `.env` file has correct keys
- Verify no extra spaces or quotes around keys
- Ensure keys are active and have quota

### YouTube MCP Not Working
```bash
# Rebuild the server
cd channel_auditor_agent_1/youtube-mcp-server
npm run build
```

---

## 📊 API Response Format

All agents return:
```json
{
  "success": true,
  "result": "Agent output here...",
  "error": null
}
```

---

## 🔥 Next Steps

1. ✅ Set up API keys
2. ✅ Start the server
3. ✅ Test with sample requests
4. 🚀 Build your YouTube automation workflow
5. 📈 Scale your content creation

Happy automating! 🎬
