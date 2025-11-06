# Channel Analytics & Video Ideas System 📊

## Overview
Complete system to track YouTube channel analytics and generate AI-powered video ideas based on performance data.

---

## 🎯 Features

### 1. **Channel Tracking**
- Save any YouTube channel for monitoring
- Automatic analytics collection
- Support for multiple URL formats

### 2. **Analytics Collection**
- Subscriber count
- Total views
- Video performance metrics
- Engagement rates
- Recent video analysis (last 50 videos)

### 3. **AI Video Ideas**
- Analyzes top-performing content
- Identifies patterns in high-engagement videos
- Generates 3 data-driven video suggestions
- Includes title, description, keywords, and timing

### 4. **RL Integration**
- Learns from channel performance
- Improves recommendations over time
- Pattern recognition across videos

---

## 🔌 API Endpoints

### **1. Track Channel**
```http
POST /api/channel/track
Content-Type: application/json

{
  "channel_url": "https://www.youtube.com/@MrBeast",
  "user_id": "user123"  // optional, default: "default"
}
```

**Response:**
```json
{
  "status": "success",
  "channel_id": "UCX6OQ3DkcsbYNE6H8uQQuVA",
  "channel_title": "MrBeast",
  "subscriber_count": 123000000,
  "video_count": 741,
  "message": "Channel added for tracking"
}
```

**Supported URL Formats:**
- `https://www.youtube.com/@username`
- `https://www.youtube.com/channel/UCxxxxxxxxxx`
- `https://www.youtube.com/c/customname`
- `UCxxxxxxxxxx` (just the ID)

---

### **2. Generate Video Ideas**
```http
POST /api/channel/video-ideas
Content-Type: application/json

{
  "channel_id": "UCX6OQ3DkcsbYNE6H8uQQuVA",
  "user_id": "user123"  // optional
}
```

**Response:**
```json
{
  "status": "success",
  "channel_title": "MrBeast",
  "analytics": {
    "subscribers": 123000000,
    "avg_views": 50000000,
    "avg_engagement": 0.045,
    "video_count": 741
  },
  "video_ideas": "1. **$1,000,000 Island Challenge 2024**\n   Description: Create massive survival challenge...\n   Why: Your challenge videos get 80M+ views...\n   Keywords: challenge, survival, money\n   Upload: Saturday 2 PM EST\n\n2. **I Built The World's Largest...** [etc]",
  "generated_at": "2024-11-06T09:20:00Z"
}
```

---

### **3. Get Tracked Channels**
```http
GET /api/channel/tracked?user_id=user123
```

**Response:**
```json
{
  "status": "success",
  "count": 3,
  "channels": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "channel_id": "UCX6OQ3DkcsbYNE6H8uQQuVA",
      "channel_title": "MrBeast",
      "channel_url": "https://youtube.com/@MrBeast",
      "subscriber_count": 123000000,
      "video_count": 741,
      "view_count": 20000000000,
      "thumbnail": "https://...",
      "created_at": "2024-11-06T08:00:00Z",
      "last_accessed": "2024-11-06T09:20:00Z",
      "tracking_enabled": true
    }
  ]
}
```

---

### **4. Refresh Analytics**
```http
POST /api/channel/refresh-analytics/{channel_id}?user_id=user123
```

Manually triggers analytics update for a channel.

---

## 💻 Frontend Integration

### **1. Install & Import**
```typescript
import {
  trackChannel,
  generateVideoIdeas,
  getTrackedChannels
} from '@/services/channelAnalytics';
```

### **2. Track Channel**
```typescript
const result = await trackChannel(
  'https://youtube.com/@MrBeast',
  'user123'
);

console.log(result.channel_title); // "MrBeast"
console.log(result.subscriber_count); // 123000000
```

### **3. Generate Ideas**
```typescript
const ideas = await generateVideoIdeas(
  'UCX6OQ3DkcsbYNE6H8uQQuVA',
  'user123'
);

console.log(ideas.video_ideas); // AI-generated suggestions
```

### **4. Use Component**
```tsx
import ChannelAnalytics from '@/components/ChannelAnalytics';

export default function Page() {
  return <ChannelAnalytics />;
}
```

---

## 🗄️ Database Collections

### **1. tracked_channels**
Stores tracked channel information:
```json
{
  "user_id": "user123",
  "channel_id": "UCxxxxxxx",
  "channel_url": "https://...",
  "channel_title": "Channel Name",
  "subscriber_count": 100000,
  "video_count": 250,
  "view_count": 50000000,
  "tracking_enabled": true,
  "created_at": "2024-11-06T08:00:00Z"
}
```

### **2. channel_analytics**
Analytics snapshots over time:
```json
{
  "channel_id": "UCxxxxxxx",
  "timestamp": "2024-11-06T09:00:00Z",
  "subscriber_count": 100000,
  "total_views": 50000000,
  "recent_videos": [
    {
      "video_id": "xyz123",
      "title": "Video Title",
      "views": 500000,
      "likes": 25000,
      "engagement_rate": 0.05
    }
  ],
  "avg_views_per_video": 200000,
  "avg_engagement_rate": 0.04
}
```

### **3. video_recommendations**
AI-generated ideas history:
```json
{
  "channel_id": "UCxxxxxxx",
  "timestamp": "2024-11-06T09:20:00Z",
  "analytics_snapshot": {
    "avg_views": 200000,
    "avg_engagement": 0.04
  },
  "video_ideas": "1. Title...\n2. Title...",
  "context_used": "Channel: ..."
}
```

---

## 🎨 How It Works

### **Step-by-Step Flow:**

```
1. User submits channel URL
   ↓
2. System extracts channel ID
   ↓
3. Fetch channel data via YouTube API
   ↓
4. Save to tracked_channels collection
   ↓
5. Fetch recent 50 videos
   ↓
6. Analyze performance metrics
   ↓
7. Store in channel_analytics
   ↓
8. AI analyzes patterns
   ↓
9. Generate 3 video ideas
   ↓
10. Save recommendations
   ↓
11. Return to user
```

### **Analytics Analysis:**

```python
For each video:
  - Views count
  - Likes count
  - Comments count
  - Engagement rate = (likes + comments) / views
  
Calculate:
  - Average views per video
  - Average engagement rate
  - Top performing videos (by views)
  - High engagement videos (by rate)
  
Identify patterns:
  - What titles work best?
  - What content gets most engagement?
  - When to upload?
  - What topics are trending?
```

### **AI Idea Generation:**

```
Input Context:
- Channel description
- Subscriber count
- Top 3 performing videos
- High engagement videos
- Average metrics

AI Agent analyzes:
- Successful patterns
- Trending topics
- Audience preferences
- Content gaps

Generates:
1. Video Title (SEO optimized)
2. Description (2-3 lines)
3. Why it will work (data-backed)
4. Target keywords
5. Best upload time
```

---

## 🚀 Usage Examples

### **Example 1: Track & Get Ideas (Python)**
```python
import requests

# Track channel
response = requests.post(
    'http://localhost:8000/api/channel/track',
    json={
        'channel_url': 'https://youtube.com/@TechChannel',
        'user_id': 'user123'
    }
)
result = response.json()
channel_id = result['channel_id']

# Generate ideas
ideas_response = requests.post(
    'http://localhost:8000/api/channel/video-ideas',
    json={
        'channel_id': channel_id,
        'user_id': 'user123'
    }
)
ideas = ideas_response.json()
print(ideas['video_ideas'])
```

### **Example 2: Track & Get Ideas (JavaScript)**
```javascript
// Track channel
const trackResult = await fetch('/api/channel/track', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    channel_url: 'https://youtube.com/@TechChannel',
    user_id: 'user123'
  })
});
const channel = await trackResult.json();

// Generate ideas
const ideasResult = await fetch('/api/channel/video-ideas', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    channel_id: channel.channel_id,
    user_id: 'user123'
  })
});
const ideas = await ideasResult.json();
console.log(ideas.video_ideas);
```

### **Example 3: React Component Usage**
```tsx
'use client';
import { useState } from 'react';
import { trackAndGenerateIdeas } from '@/services/channelAnalytics';

export default function MyComponent() {
  const [channelUrl, setChannelUrl] = useState('');
  const [ideas, setIdeas] = useState(null);

  const handleSubmit = async () => {
    const result = await trackAndGenerateIdeas(channelUrl);
    setIdeas(result.ideas);
  };

  return (
    <div>
      <input 
        value={channelUrl}
        onChange={e => setChannelUrl(e.target.value)}
        placeholder="YouTube channel URL"
      />
      <button onClick={handleSubmit}>Get Ideas</button>
      {ideas && <pre>{ideas.video_ideas}</pre>}
    </div>
  );
}
```

---

## 📈 Sample AI Output

```markdown
Based on your channel's analytics, here are 3 high-performing video ideas:

### 1. **"Best Budget Tech Under $50 in 2024 - Actually Worth It!"**

**Description:**
Review 10 affordable tech products under $50 that actually deliver value.
Include hands-on tests, pros/cons, and where to buy.

**Why This Will Perform Well:**
- Your "budget tech" videos average 80k views (2x channel average)
- Price-point titles get 35% higher CTR
- "2024" keyword trending in your niche

**Target Keywords:**
- budget tech 2024
- cheap tech worth buying
- affordable gadgets
- tech under 50 dollars

**Best Upload Time:** Tuesday or Thursday, 2 PM EST
(Your tech review videos perform 40% better mid-week)

---

### 2. **"I Tested 5 Viral TikTok Tech Gadgets - Truth Revealed"**

**Description:**
Purchase and thoroughly test popular TikTok tech products to see if
they live up to the hype. Honest reviews with side-by-side comparisons.

**Why This Will Perform Well:**
- Your "testing" videos have 4.8% engagement (highest on channel)
- TikTok crossover content gaining traction
- "Truth Revealed" format matches your top video structure

**Target Keywords:**
- viral tiktok tech
- testing viral products
- tiktok gadgets review
- is it worth it

**Best Upload Time:** Saturday, 10 AM EST
(Weekend uploads get 25% more shares)

---

### 3. **"Setup Wars: $500 vs $5000 Gaming Setup Comparison"**

**Description:**
Build and compare budget vs premium gaming setups. Performance tests,
aesthetics, and value analysis. Let viewers decide which is better.

**Why This Will Perform Well:**
- Comparison videos are your 2nd best performing category
- Gaming content up 60% in your audience demographics
- "Wars" format encourages comments (engagement boost)

**Target Keywords:**
- budget gaming setup
- gaming setup comparison
- cheap vs expensive setup
- setup wars 2024

**Best Upload Time:** Friday, 6 PM EST
(Gaming content peaks on Friday evenings)
```

---

## 🔐 Environment Variables

Add to `.env`:
```env
# MongoDB for storing channel data
MONGODB_URI=mongodb+srv://...
MONGODB_DB=youtube_ops

# YouTube API (for fetching analytics)
YOUTUBE_API_KEY=your_api_key

# AI Model (for generating ideas)
GEMINI_API_KEY=your_gemini_key
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
GEMINI_MODEL_NAME=gemini-2.0-flash-exp
```

---

## 🎯 Access the Feature

### **Backend API:**
- Local: `http://localhost:8000/api/channel/track`
- Vercel: `https://your-project.vercel.app/api/channel/track`

### **Frontend Page:**
- Local: `http://localhost:3000/channel-analytics`
- Production: `https://your-site.com/channel-analytics`

---

## 🐛 Troubleshooting

### **Issue: "Channel not found"**
- Check URL format
- Ensure channel is public
- Try using channel ID directly

### **Issue: "Failed to fetch analytics"**
- Verify YouTube API key is valid
- Check API quota (YouTube API has daily limits)
- Ensure channel has videos

### **Issue: "AI ideas not generating"**
- Check Gemini API key
- Verify model name is correct
- Ensure analytics data exists

---

## 📊 Performance Tips

1. **Cache Results:** Analytics refresh every 24 hours
2. **Batch Requests:** Use tracked channels list for bulk operations
3. **Monitor Quota:** YouTube API has daily limits (10,000 units/day)
4. **Store Ideas:** Save AI responses to avoid regenerating

---

## 🎉 Success!

You now have a complete system to:
✅ Track YouTube channels
✅ Analyze performance data
✅ Generate AI-powered video ideas
✅ Learn from analytics patterns
✅ Improve over time with RL

**Frontend Route:** `/channel-analytics`
**API Base:** `/api/channel/`

Happy video creating! 🚀📹
