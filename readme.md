# YouTube Automation AI Agents API

Complete backend API for 6 AI agents that automate YouTube content creation workflow.

## 🤖 The 6 AI Agents

### Agent 1: Channel Auditor
Deep audit of YouTube channels to identify the hottest one for content replication.
- **Endpoint**: `POST /api/agent1/audit-channel`
- **Purpose**: Analyze multiple channels, evaluate metrics, growth patterns, and content strategy

### Agent 2: Title Auditor  
Comprehensive analysis of video titles, thumbnails, keywords, and hooks.
- **Endpoint**: `POST /api/agent2/audit-titles`
- **Purpose**: Extract winning formulas from top-performing videos

### Agent 3: Script Writer
Generate video scripts based on winning patterns from title audit data.
- **Endpoint**: `POST /api/agent3/generate-script`
- **Purpose**: Create engaging, retention-optimized scripts

### Agent 4: Script to Prompts Converter
Convert scripts into detailed scene-by-scene visual prompts.
- **Endpoint**: `POST /api/agent4/script-to-prompts`
- **Purpose**: Break down scripts with Hollywood-style direction for video production

### Agent 5: Ideas Generator
Generate 3 winning title variations and thumbnail concepts.
- **Endpoint**: `POST /api/agent5/generate-ideas`
- **Purpose**: Create viral-ready titles and thumbnail concepts based on data

### Agent 6: Content Roadmap Generator
Create a 30-video content roadmap with titles and thumbnail variations.
- **Endpoint**: `POST /api/agent6/generate-roadmap`
- **Purpose**: Strategic content planning with complete title/thumbnail variations

---

## 🚀 Installation

### Prerequisites
- Python 3.12+
- uv (recommended) or pip
- Node.js (for YouTube MCP server)

### Setup

1. **Clone and navigate to Backend directory**
```bash
cd d:\Mission\youtube\Backend
```

2. **Install dependencies**
```bash
uv sync
```

3. **Configure environment variables**
Edit `.env` file with your API keys:
```env
# Gemini Configuration (Agent 1, 6)
GEMINI_API_KEY=your_gemini_key
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
GEMINI_MODEL_NAME=gemini-2.5-flash
GEMINI_IMAGE_MODEL_NAME=gemini-2.0-flash-preview-image-generation

# Groq Configuration (Agent 2, 3, 4, 5)
GROQ_API_KEY=your_groq_key
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ2_MODEL_NAME=llama-3.3-70b-versatile
GROQ3_Model_MODEL=llama-3.1-8b-instant
GROQ4_Model_MODEL=llama-3.1-8b-instant
GROQ5_Model_MODEL=llama-3.3-70b-versatile

# YouTube Data API
YOUTUBE_API_KEY=your_youtube_api_key
```

4. **Build YouTube MCP Server**
```bash
cd channel_auditor_agent_1/youtube-mcp-server
npm install
npm run build
cd ../..
```

---

## 🏃‍♂️ Running the API

### Start the server
```bash
uv run main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

---

## 📚 API Documentation

### Interactive Docs
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Health Check
```bash
GET http://localhost:8000/health
```

---

## 💡 Usage Examples

### Agent 1: Audit Channels
```bash
curl -X POST http://localhost:8000/api/agent1/audit-channel \
  -H "Content-Type: application/json" \
  -d '{
    "channel_urls": [
      "https://www.youtube.com/@channel1",
      "https://www.youtube.com/@channel2"
    ],
    "user_query": "Audit these channels and pick the best one"
  }'
```

### Agent 2: Audit Titles & Thumbnails
```bash
curl -X POST http://localhost:8000/api/agent2/audit-titles \
  -H "Content-Type: application/json" \
  -d '{
    "video_urls": [
      "https://www.youtube.com/watch?v=VIDEO_ID_1",
      "https://www.youtube.com/watch?v=VIDEO_ID_2"
    ]
  }'
```

### Agent 3: Generate Script
```bash
curl -X POST http://localhost:8000/api/agent3/generate-script \
  -H "Content-Type: application/json" \
  -d '{
    "title_audit_data": "Winning patterns: questions in titles, bold text on thumbnails...",
    "topic": "How to Start a YouTube Channel in 2024"
  }'
```

### Agent 4: Convert Script to Prompts
```bash
curl -X POST http://localhost:8000/api/agent4/script-to-prompts \
  -H "Content-Type: application/json" \
  -d '{
    "script": "Your complete video script here..."
  }'
```

### Agent 5: Generate Ideas
```bash
curl -X POST http://localhost:8000/api/agent5/generate-ideas \
  -H "Content-Type: application/json" \
  -d '{
    "winning_videos_data": "Top video data with metrics and patterns..."
  }'
```

### Agent 6: Generate Content Roadmap
```bash
curl -X POST http://localhost:8000/api/agent6/generate-roadmap \
  -H "Content-Type: application/json" \
  -d '{
    "niche": "AI & Technology",
    "winning_data": "Optional data from previous analysis"
  }'
```

---

## 🔄 Complete Workflow

1. **Channel Research** → Use Agent 1 to audit competitor channels
2. **Pattern Analysis** → Use Agent 2 to analyze winning videos  
3. **Script Creation** → Use Agent 3 to generate script based on patterns
4. **Visual Planning** → Use Agent 4 to create scene-by-scene prompts
5. **Content Ideas** → Use Agent 5 to generate title/thumbnail variations
6. **Roadmap** → Use Agent 6 to plan 30-video content calendar

---

## 🛠️ Development

### Project Structure
```
Backend/
├── main.py                          # FastAPI application
├── .env                             # Environment variables
├── pyproject.toml                   # Dependencies
├── channel_auditor_agent_1/         # Agent 1 + YouTube MCP server
├── title_auditor_agent_2/           # Agent 2
├── sriptwriter_agent_3/             # Agent 3
├── script_to_prompts_agent_4/       # Agent 4
├── ideas_generator_5/               # Agent 5
└── thumbnail_agent_6/               # Agent 6
```

### Adding New Features
1. Create new endpoint in `main.py`
2. Define request/response models with Pydantic
3. Initialize agent with proper instructions
4. Test with `/docs` interactive API

---

## ⚠️ Troubleshooting

### Gemini Rate Limit Error
If Agent 6 shows quota errors:
- Enable billing on Google AI Studio
- Switch to different model in `.env`
- Use alternative provider (OpenAI DALL-E, Stability AI)

### YouTube API Errors
- Verify `YOUTUBE_API_KEY` is valid
- Check API quota in Google Cloud Console
- Ensure MCP server is built (`npm run build`)

### GROQ Connection Issues
- Verify `GROQ_API_KEY` is active
- Check model names match available models
- Monitor rate limits

---

## 📝 License

MIT License - Feel free to use for your YouTube automation projects!

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new agents
4. Submit pull request

---

## 📧 Support

For issues or questions:
- Check `/docs` for API documentation
- Review error logs in console
- Verify all environment variables are set

Happy YouTubing! 🎬
