# YouTube Analytics Features

## ✅ Newly Added Analytics Tools

The MCP server now includes three powerful analytics tools for channel analysis:

### 1. **Average Video Duration** 
**Tool:** `analytics_getAverageVideoDuration`

Calculates the average duration of videos from a channel by analyzing recent uploads.

**Parameters:**
- `channelId` (required): The YouTube channel ID
- `maxResults` (optional): Number of recent videos to analyze (default: 50)

**Returns:**
```json
{
  "channelId": "UC...",
  "videosAnalyzed": 50,
  "averageDurationSeconds": 1239,
  "averageDurationFormatted": "20:39",
  "averageDurationMinutes": "20.65"
}
```

**Example Prompts:**
- "What's the average video duration for channel UC8butISFwT-Wl7EV0hUK0BQ?"
- "Calculate the average video length for this channel"
- "How long are videos typically on this channel?"

---

### 2. **Upload Frequency**
**Tool:** `analytics_getUploadFrequency`

Calculates how often a channel uploads videos (videos per week/month).

**Parameters:**
- `channelId` (required): The YouTube channel ID
- `maxResults` (optional): Number of recent videos to analyze (default: 50)

**Returns:**
```json
{
  "channelId": "UC...",
  "videosAnalyzed": 50,
  "timeRangeDays": 180,
  "timeRangeWeeks": "25.71",
  "videosPerWeek": "1.95",
  "videosPerMonth": "8.44",
  "oldestVideoDate": "2024-04-01T10:30:00Z",
  "newestVideoDate": "2024-10-29T14:44:37Z"
}
```

**Example Prompts:**
- "How often does channel UC8butISFwT-Wl7EV0hUK0BQ upload videos?"
- "What's the upload frequency for this channel?"
- "How many videos per week does this channel post?"

---

### 3. **Average Views Per Video**
**Tool:** `analytics_getAverageViewsPerVideo`

Calculates the average number of views per video for a channel.

**Parameters:**
- `channelId` (required): The YouTube channel ID
- `maxResults` (optional): Number of recent videos to analyze (default: 50)

**Returns:**
```json
{
  "channelId": "UC...",
  "recentVideosAnalyzed": 50,
  "averageViewsPerVideo": 125430,
  "totalViewsAnalyzed": 6271500,
  "channelOverallStats": {
    "totalVideos": 7347,
    "totalViews": 1000274353,
    "overallAverageViews": 136147
  }
}
```

**Example Prompts:**
- "What's the average views per video for channel UC8butISFwT-Wl7EV0hUK0BQ?"
- "How many views does this channel typically get per video?"
- "Calculate average video performance for this channel"

---

## 🎯 How These Analytics Are Calculated

### Average Duration
1. Fetches recent videos from the channel
2. Gets full video details including `contentDetails.duration`
3. Parses ISO 8601 duration format (PT#H#M#S)
4. Calculates arithmetic mean of all durations
5. Returns in both seconds and formatted (MM:SS)

### Upload Frequency
1. Fetches recent videos with publish dates
2. Finds oldest and newest video in the sample
3. Calculates time span in days/weeks
4. Divides number of videos by time span
5. Returns videos per week and per month

### Average Views
1. Fetches recent videos from the channel
2. Gets full video details including `statistics.viewCount`
3. Calculates arithmetic mean of view counts
4. Also provides overall channel statistics for comparison
5. Shows both recent average and lifetime average

---

## 📊 Use Cases

### Content Strategy Analysis
```
"What's the average video duration and upload frequency for channel UC8butISFwT-Wl7EV0hUK0BQ?"
```

### Performance Benchmarking
```
"Compare the average views per video for channels UC1234 and UC5678"
```

### Channel Insights
```
"Analyze channel UC8butISFwT-Wl7EV0hUK0BQ: show me upload frequency, average duration, and average views"
```

### Competitive Analysis
```
"For the top 3 Python tutorial channels, show me their upload frequency and average views"
```

---

## 🔧 Technical Details

### Implementation
- Built directly into the MCP server (`src/server.ts`)
- Uses YouTube Data API v3 for data retrieval
- Combines `search.list` and `videos.list` endpoints
- Handles edge cases (no videos, insufficient data, etc.)

### Data Quality
- Default sample size: 50 recent videos
- Can be adjusted with `maxResults` parameter
- Larger samples = more accurate but slower
- Minimum 2 videos required for upload frequency

### Performance
- Efficient API usage with batch video detail requests
- Single API call for video IDs, one for details
- Typical response time: 2-3 seconds per analytics call

---

## 🚀 Quick Start

### Test the Analytics
```bash
uv run youtubeAgent.py
```

Then try:
```
You: What's the average video duration for channel UC8butISFwT-Wl7EV0hUK0BQ?
```

### Or use these complete analysis prompts:
```
"Analyze channel UC8butISFwT-Wl7EV0hUK0BQ and give me all analytics: average duration, upload frequency, and average views"
```

---

## ✨ Benefits

**Before:** Had to manually calculate or couldn't get:
- ❌ Average video duration
- ❌ Upload frequency (videos/week)
- ❌ Average views per video

**Now:** Automatically calculated with:
- ✅ One simple prompt
- ✅ Recent data analysis
- ✅ Statistical insights
- ✅ Formatted results

---

## 📝 Notes

- All analytics use recent videos by default (last 50)
- **🆕 Pagination Support:** You can now request 100+ videos for better accuracy!
- Examples: "analyze last 100 videos", "use 150 recent videos"
- Results include metadata like number of videos analyzed
- Upload frequency excludes Shorts by default (can be configured)
- View counts are current at time of request, not historical

---

## 🆕 Pagination Support (NEW!)

### Now Supports 100+ Videos!

All analytics tools now support analyzing more than 50 videos using automatic pagination:

**How to Use:**
```
"Calculate average video duration for the last 100 videos"
"Analyze upload frequency using 150 recent videos"
"What's the average views for 100 videos from this channel?"
```

**Technical Details:**
- Automatic pagination in the background
- Efficient batching of API requests
- No change in user experience
- Slightly slower for larger datasets (100 videos ≈ 4-5 seconds)

**Accuracy Improvements:**
- 50 videos: Good baseline
- 100 videos: Better statistical accuracy
- 150+ videos: Most accurate representation

See [PAGINATION_SUPPORT.md](PAGINATION_SUPPORT.md) for complete technical details.
