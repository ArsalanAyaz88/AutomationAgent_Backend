# YouTube Agent - Test Prompts

## How to Run
```bash
uv run youtubeAgent.py
```

## Built-in Commands
- Type `samples` - Show sample prompts
- Type `exit`, `quit`, or `bye` - Exit the agent
- Press `Ctrl+C` - Force quit

---

## 📝 Sample Test Prompts

### 1. Get Video Information
```
Get information about video dQw4w9WgXcQ
```
```
Tell me about the video with ID dQw4w9WgXcQ
```
```
Show me details for YouTube video jNQXAC9IVRw
```

### 2. Search for Videos
```
Search for Python tutorial videos
```
```
Find videos about machine learning
```
```
Search for cooking recipes on YouTube
```
```
Find the latest AI news videos
```

### 3. Get Video Transcripts
```
Get the transcript for video dQw4w9WgXcQ
```
```
Show me the transcript of video jNQXAC9IVRw
```
```
Get transcript in English for video dQw4w9WgXcQ
```

### 4. Channel Information
```
Get information about channel UC8butISFwT-Wl7EV0hUK0BQ
```
```
Tell me about the YouTube channel UC8butISFwT-Wl7EV0hUK0BQ
```
```
Show channel details for UC_x5XG1OV2P6uZZ5FSM9Ttw
```

### 5. List Videos from Channel
```
List recent videos from channel UC8butISFwT-Wl7EV0hUK0BQ
```
```
Show me the latest 5 videos from channel UC_x5XG1OV2P6uZZ5FSM9Ttw
```
```
Get videos from channel UC8butISFwT-Wl7EV0hUK0BQ
```

### 6. Get Playlist Information
```
Get playlist PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf
```
```
Show me videos in playlist PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf
```
```
Tell me about playlist PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf
```

### 7. Channel Analytics - Average Video Duration
```
What's the average video duration for channel UC8butISFwT-Wl7EV0hUK0BQ?
```
```
Calculate average duration for channel @mansooralikhanlive
```
```
Get average video length for this channel
```

### 8. Channel Analytics - Upload Frequency
```
How often does channel UC8butISFwT-Wl7EV0hUK0BQ upload videos?
```
```
Calculate upload frequency for channel @mansooralikhanlive (videos per week)
```
```
What's the upload schedule for this channel?
```

### 9. Channel Analytics - Average Views Per Video
```
What's the average views per video for channel UC8butISFwT-Wl7EV0hUK0BQ?
```
```
Calculate average views for channel @mansooralikhanlive
```
```
How many views does this channel typically get per video?
```

### 10. 🆕 Bulk Operations (50+ Videos)
```
Give me details of the latest 100 videos from channel UC8butISFwT-Wl7EV0hUK0BQ
```
```
List 150 recent videos from this channel
```
```
Get information about the last 75 videos
```

### 11. 🆕 Analytics with Large Samples
```
Calculate average video duration for the last 100 videos from channel UC8butISFwT-Wl7EV0hUK0BQ
```
```
Analyze upload frequency using 150 recent videos
```
```
What's the average views for the last 100 videos of this channel?
```

### 12. 🔥 Comprehensive Video Analysis (ALL DETAILS!)
```
Get comprehensive analysis of 10 videos from channel UC8butISFwT-Wl7EV0hUK0BQ
```
```
video: https://youtu.be/ZfBN_dgxSTA - analyze latest 10 videos with complete details
```
```
Show me complete analysis of 20 recent videos including engagement metrics and title patterns
```

---

## 🔍 Complex Queries

### Analysis Questions
```
What are the most popular videos about Python programming?
```
```
Find videos about React and tell me their view counts
```
```
Search for cooking videos and summarize the top 3
```

### Multi-step Queries
```
Search for AI tutorials, then get the transcript of the first result
```
```
Find videos about web development and show me the channel info for the first result
```

### Comparison Queries
```
Compare the subscriber count of channels UC8butISFwT-Wl7EV0hUK0BQ and UC_x5XG1OV2P6uZZ5FSM9Ttw
```

---

## 💡 Tips

1. **Real Video IDs**: Replace example video IDs with real ones:
   - Popular: `dQw4w9WgXcQ` (Rick Astley - Never Gonna Give You Up)
   - Popular: `jNQXAC9IVRw` (Me at the zoo - First YouTube video)

2. **Real Channel IDs**: Find channel IDs from:
   - YouTube channel URL: `youtube.com/channel/[CHANNEL_ID]`
   - Or from YouTube channel → About section

3. **Real Playlist IDs**: From playlist URLs:
   - `youtube.com/playlist?list=[PLAYLIST_ID]`

4. **Natural Language**: The agent understands natural language, so ask questions naturally!

---

## ⚠️ Troubleshooting

### If you get API errors:
- Check that `YOUTUBE_API_KEY` is set in `.env`
- Verify the API key is valid at: https://console.cloud.google.com/apis/credentials
- Ensure YouTube Data API v3 is enabled

### If the agent doesn't respond:
- Wait a moment - LLM responses can take time
- Check your internet connection
- Verify the MCP server compiled successfully: `cd youtube-mcp-server && npm run build`

### If you get "JSONRPC" errors:
- Make sure you rebuilt the MCP server after the latest changes
- The server should only log to stderr, not stdout
