# YouTube Auditor Agent

A powerful AI agent for YouTube analytics and data retrieval using the Model Context Protocol (MCP).

## 🚀 Features

### Video Operations
- ✅ Get detailed video information
- ✅ Search for videos by query
- ✅ Retrieve video transcripts
- ✅ Extract video metadata (title, description, views, likes, etc.)

### Channel Operations
- ✅ Get channel information and statistics
- ✅ List videos from any channel
- ✅ Retrieve channel metadata

### Playlist Operations
- ✅ Get playlist information
- ✅ List videos in a playlist

### 🆕 Advanced Analytics
- ✅ **Average Video Duration** - Calculate average video length for a channel
- ✅ **Upload Frequency** - Analyze how often a channel posts (videos/week, videos/month)
- ✅ **Average Views Per Video** - Calculate typical video performance
- ✅ **Pagination Support** - Analyze 100+ videos for better accuracy
- 🔥 **Comprehensive Video Analysis** - Get ALL details in ONE call (NEW!)
  - Complete metadata, statistics, thumbnails
  - Auto-calculated engagement rates
  - Title pattern analysis
  - Primary & secondary keywords
  - NO "Not directly retrievable" - Everything included!

## 📋 Prerequisites

- Python 3.12+
- Node.js 18+
- YouTube Data API v3 Key
- Gemini API Key (or any OpenAI-compatible LLM API)
- uv (Python package manager)

## 🔧 Setup

### 1. Clone the Repository
```bash
cd d:\Mission\youtube_auditor
```

### 2. Install Dependencies

#### Python Dependencies
```bash
uv sync
```

#### MCP Server Dependencies
```bash
cd youtube-mcp-server
npm install
npm run build
```

### 3. Environment Configuration

Create a `.env` file in the root directory:

```env
# YouTube API
YOUTUBE_API_KEY=your_youtube_api_key_here

# Gemini API (or your preferred LLM)
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL_NAME=gemini-1.5-flash
```

### 4. Get API Keys

#### YouTube Data API Key
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "YouTube Data API v3"
4. Create credentials (API Key)
5. Copy the API key to `.env`

#### Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Get API key
3. Copy to `.env`

## 🎮 Usage

### Start the Agent
```bash
uv run youtubeAgent.py
```

### Interactive Commands
- Type `samples` - View example prompts
- Type `exit`, `quit`, or `bye` - Exit the agent
- Press `Ctrl+C` - Force quit

### Example Prompts

#### Video Analysis
```
Get information about video dQw4w9WgXcQ
Search for Python tutorial videos
Get the transcript for video jNQXAC9IVRw
```

#### Channel Analysis
```
Get information about channel UC8butISFwT-Wl7EV0hUK0BQ
List recent videos from channel UC8butISFwT-Wl7EV0hUK0BQ
```

#### Analytics
```
What's the average video duration for channel UC8butISFwT-Wl7EV0hUK0BQ?
How often does channel UC8butISFwT-Wl7EV0hUK0BQ upload videos?
What's the average views per video for this channel?
```

#### Complex Queries
```
Analyze channel UC8butISFwT-Wl7EV0hUK0BQ: show me upload frequency, average duration, and average views
Compare the performance of these two channels: UC1234 and UC5678
Find the top Python tutorial videos and calculate their average views
```

#### Bulk Operations (100+ Videos)
```
Give me details of the latest 100 videos from channel UC8butISFwT-Wl7EV0hUK0BQ
Calculate average video duration for the last 100 videos
Analyze upload frequency using 150 recent videos
```

#### 🔥 Comprehensive Analysis (Complete Details in One Call) - NEW!
```
Get comprehensive analysis of 10 videos from channel UC8butISFwT-Wl7EV0hUK0BQ
video: https://youtu.be/ZfBN_dgxSTA - analyze latest 10 videos with ALL details
Show complete analysis of 20 videos including engagement, title patterns, and keywords
```
**Returns:** Channel info, complete video details, engagement rates, title analysis, keywords - NO missing data!

## 📚 Documentation

- **[TEST_PROMPTS.md](TEST_PROMPTS.md)** - Complete testing guide with examples
- **[ANALYTICS_FEATURES.md](ANALYTICS_FEATURES.md)** - Detailed analytics documentation
- **[PAGINATION_SUPPORT.md](PAGINATION_SUPPORT.md)** - 100+ videos support documentation
- 🔥 **[COMPREHENSIVE_ANALYSIS_TOOL.md](COMPREHENSIVE_ANALYSIS_TOOL.md)** - Complete video analysis in one call (NEW!)
- **[MCP Specification](https://modelcontextprotocol.io/)** - Official MCP docs

## 🏗️ Architecture

```
youtube_auditor/
├── youtubeAgent.py              # Main agent file
├── youtube-mcp-server/          # MCP server implementation
│   ├── src/
│   │   ├── server.ts           # Main server with tools
│   │   ├── cli.ts              # CLI entry point
│   │   ├── services/           # YouTube API services
│   │   │   ├── video.ts
│   │   │   ├── channel.ts
│   │   │   ├── playlist.ts
│   │   │   └── transcript.ts
│   │   └── types.ts            # TypeScript types
│   └── dist/                   # Compiled JavaScript
├── .env                        # Environment configuration
└── README.md                   # This file
```

## 🛠️ MCP Server Tools

The server exposes the following tools via MCP:

### Core Tools
1. `videos_getVideo` - Get video details
2. `videos_searchVideos` - Search for videos
3. `transcripts_getTranscript` - Get video transcript
4. `channels_getChannel` - Get channel information
5. `channels_listVideos` - List channel videos
6. `playlists_getPlaylist` - Get playlist details
7. `playlists_getPlaylistItems` - Get playlist videos

### Analytics Tools
8. `analytics_getAverageVideoDuration` - Calculate average video duration
9. `analytics_getUploadFrequency` - Calculate upload frequency
10. `analytics_getAverageViewsPerVideo` - Calculate average views per video
11. 🔥 `analytics_getComprehensiveVideoAnalysis` - Complete video analysis in ONE call (NEW!)
   - Fetches ALL data automatically
   - Calculates engagement metrics
   - Analyzes title patterns
   - Extracts keywords
   - Returns structured, complete data

## 🔍 Troubleshooting

### JSONRPC Parsing Errors
If you see "Failed to parse JSONRPC message", make sure:
- You rebuilt the MCP server after changes: `npm run build`
- The server only logs to stderr, not stdout

### API Quota Errors
If you hit YouTube API quota limits:
- Default quota is 10,000 units/day
- Each search costs ~100 units
- Consider caching results or upgrading quota

### Connection Issues
If the agent can't connect to MCP server:
- Check that Node.js is installed: `node --version`
- Verify the server builds: `cd youtube-mcp-server && npm run build`
- Check the path in `youtubeAgent.py` is correct

## 📈 Performance

- **Startup Time:** ~2-3 seconds
- **Query Response:** 2-5 seconds (depends on LLM)
- **Analytics Calculation:** 2-3 seconds per metric
- **API Rate Limits:** YouTube Data API v3 quotas apply

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Built with [OpenAI Agents SDK](https://github.com/openai/openai-agents-python)
- Uses [Model Context Protocol](https://modelcontextprotocol.io/)
- Powered by [YouTube Data API v3](https://developers.google.com/youtube/v3)

## 📞 Support

For issues, questions, or feature requests:
1. Check [TEST_PROMPTS.md](TEST_PROMPTS.md) for examples
2. Review [ANALYTICS_FEATURES.md](ANALYTICS_FEATURES.md) for analytics docs
3. Open an issue on GitHub

---

**Made with ❤️ for YouTube Analytics**
