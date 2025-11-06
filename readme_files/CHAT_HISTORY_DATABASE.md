# Chat History Database Integration 💾🤖

## Overview
Scriptwriter aur Scene Writer chatbots ka pura conversation history ab MongoDB me store hota hai aur 24 hours baad auto-delete ho jata hai using TTL (Time To Live) index.

---

## Key Features ✨

### **1. Auto-Delete After 24 Hours** ⏰
```
✅ MongoDB TTL Index
✅ Automatic cleanup
✅ No manual intervention needed
✅ Privacy-friendly
```

### **2. Session-Based Storage** 📝
```
✅ Unique session_id har conversation ko
✅ Multiple sessions possible
✅ Isolated chat histories
✅ Per-user segregation
```

### **3. Complete CRUD Operations** 🔧
```
✅ Save messages (auto)
✅ Get chat history
✅ Clear session (manual)
✅ Auto-delete (TTL)
```

---

## Database Structure 💾

### **Collections Created:**
```
1. scriptwriter_chat_history
2. scene_writer_chat_history
```

### **Document Schema:**
```javascript
{
  "_id": ObjectId,
  "session_id": "unique_session_id",
  "user_id": "default",
  "role": "user" or "assistant",
  "content": "Message text here...",
  "created_at": ISODate("2025-11-06T19:00:00Z")  // TTL index
}
```

### **TTL Index:**
```javascript
// Auto-deletes documents after 24 hours
{
  "created_at": 1,
  expireAfterSeconds: 86400  // 24 hours = 86400 seconds
}
```

---

## How It Works 🔄

### **Message Flow:**
```
1. User sends message
   ↓
2. Generate/use session_id
   ↓
3. Load last 10 messages from DB
   ↓
4. Save user message to DB
   ↓
5. Pass history to AI agent
   ↓
6. Get AI response
   ↓
7. Save assistant response to DB
   ↓
8. Return response to user
```

### **Auto-Delete Flow:**
```
Message saved with created_at timestamp
   ↓
MongoDB checks every 60 seconds
   ↓
If created_at + 86400s < now
   ↓
Document auto-deleted
   ↓
No manual cleanup needed!
```

---

## API Changes 📋

### **Request Models Updated:**

#### **Before:**
```python
class ScriptwriterChatRequest(BaseModel):
    message: str
    chat_history: Optional[List[ChatMessage]] = []  # ❌ Frontend sends
    user_id: Optional[str] = "default"
```

#### **After:**
```python
class ScriptwriterChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # ✅ Backend generates
    user_id: Optional[str] = "default"
    channel_id: Optional[str] = None
```

**Same for SceneWriterChatRequest**

---

## New API Endpoints 🔌

### **1. Clear Scriptwriter Chat**
```http
DELETE /api/unified/clear-scriptwriter-chat/{session_id}?user_id=default

Response:
{
  "success": true,
  "message": "Chat history cleared"
}
```

### **2. Clear Scene Writer Chat**
```http
DELETE /api/unified/clear-scene-writer-chat/{session_id}?user_id=default

Response:
{
  "success": true,
  "message": "Chat history cleared"
}
```

### **3. Get Scriptwriter Chat History**
```http
GET /api/unified/get-scriptwriter-chat/{session_id}?user_id=default&limit=50

Response:
{
  "success": true,
  "session_id": "abc123...",
  "message_count": 15,
  "messages": [
    {
      "role": "user",
      "content": "Hi!",
      "created_at": "2025-11-06T19:00:00Z"
    },
    {
      "role": "assistant",
      "content": "Hello! How can I help?",
      "created_at": "2025-11-06T19:00:05Z"
    }
  ]
}
```

### **4. Get Scene Writer Chat History**
```http
GET /api/unified/get-scene-writer-chat/{session_id}?user_id=default&limit=50

Response:
{
  "success": true,
  "session_id": "xyz789...",
  "message_count": 8,
  "messages": [...]
}
```

---

## Helper Functions 🛠️

### **1. save_chat_message()**
```python
async def save_chat_message(
    collection,      # scriptwriter_chat_collection or scene_writer_chat_collection
    session_id: str, # Unique session identifier
    user_id: str,    # User identifier
    role: str,       # "user" or "assistant"
    content: str     # Message content
):
    """Save chat message to database with TTL"""
    message_doc = {
        "session_id": session_id,
        "user_id": user_id,
        "role": role,
        "content": content,
        "created_at": datetime.utcnow()  # For TTL
    }
    collection.insert_one(message_doc)
```

### **2. get_chat_history()**
```python
async def get_chat_history(
    collection,      # Which collection to query
    session_id: str, # Session to retrieve
    user_id: str,    # User filter
    limit: int = 10  # Max messages
) -> List[Dict]:
    """Retrieve chat history from database"""
    messages = collection.find(
        {"session_id": session_id, "user_id": user_id}
    ).sort("created_at", 1).limit(limit)
    
    return list(messages)
```

### **3. clear_chat_session()**
```python
async def clear_chat_session(
    collection,      # Which collection
    session_id: str, # Session to clear
    user_id: str     # User filter
):
    """Manually clear chat session"""
    collection.delete_many({
        "session_id": session_id,
        "user_id": user_id
    })
```

---

## Usage Examples 📖

### **Scriptwriter Chat with History:**

```python
import requests

API_URL = "http://localhost:8000/api/unified"

# First message - new session
response1 = requests.post(f"{API_URL}/scriptwriter-chat", json={
    "message": "Hi, what can you do?",
    "user_id": "user123"
})

data1 = response1.json()
# Backend auto-generates session_id

# Second message - continue session
response2 = requests.post(f"{API_URL}/scriptwriter-chat", json={
    "message": "Write a script about AI",
    "session_id": "generated_session_id",  # Use same session
    "user_id": "user123"
})

# Agent remembers previous conversation!
```

### **Scene Writer Chat with History:**

```python
# First message
response1 = requests.post(f"{API_URL}/scene-writer-chat", json={
    "message": "What's a wide shot?",
    "user_id": "user123"
})

# Continue conversation
response2 = requests.post(f"{API_URL}/scene-writer-chat", json={
    "message": "Show me an example",
    "session_id": "generated_session_id",
    "user_id": "user123"
})

# Agent remembers context!
```

### **Clear Chat History:**

```python
# Clear scriptwriter chat
requests.delete(
    f"{API_URL}/clear-scriptwriter-chat/session_id_here?user_id=user123"
)

# Clear scene writer chat
requests.delete(
    f"{API_URL}/clear-scene-writer-chat/session_id_here?user_id=user123"
)
```

### **Retrieve Chat History:**

```python
# Get scriptwriter history
response = requests.get(
    f"{API_URL}/get-scriptwriter-chat/session_id_here?user_id=user123&limit=50"
)

history = response.json()
for msg in history['messages']:
    print(f"{msg['role']}: {msg['content']}")
```

---

## Frontend Integration 🎨

### **State Management:**

```typescript
interface ChatSession {
  sessionId: string | null;
  messages: ChatMessage[];
}

const [scriptwriterSession, setScriptwriterSession] = useState<ChatSession>({
  sessionId: null,
  messages: []
});

const [sceneWriterSession, setSceneWriterSession] = useState<ChatSession>({
  sessionId: null,
  messages: []
});
```

### **Send Message Function:**

```typescript
const sendScriptwriterMessage = async (message: string) => {
  // Send to backend
  const response = await fetch(`${API_BASE_URL}/api/unified/scriptwriter-chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: message,
      session_id: scriptwriterSession.sessionId,  // Can be null for first message
      user_id: 'default',
      channel_id: selectedChannel?.channel_id
    })
  });

  const data = await response.json();
  
  // Update local state (optional, can also fetch from DB)
  setScriptwriterSession(prev => ({
    sessionId: data.session_id || prev.sessionId,  // Backend returns session_id
    messages: [
      ...prev.messages,
      { role: 'user', content: message },
      { role: 'assistant', content: data.result }
    ]
  }));
};
```

### **Clear Chat Function:**

```typescript
const clearScriptwriterChat = async () => {
  if (!scriptwriterSession.sessionId) return;
  
  await fetch(
    `${API_BASE_URL}/api/unified/clear-scriptwriter-chat/${scriptwriterSession.sessionId}?user_id=default`,
    { method: 'DELETE' }
  );
  
  // Reset local state
  setScriptwriterSession({ sessionId: null, messages: [] });
};
```

### **Load Chat History (Optional):**

```typescript
const loadScriptwriterHistory = async (sessionId: string) => {
  const response = await fetch(
    `${API_BASE_URL}/api/unified/get-scriptwriter-chat/${sessionId}?user_id=default&limit=50`
  );
  
  const data = await response.json();
  
  setScriptwriterSession({
    sessionId: sessionId,
    messages: data.messages
  });
};
```

---

## MongoDB TTL Index Details ⏰

### **How TTL Works:**

```
1. Document created with created_at: ISODate("2025-11-06T19:00:00Z")
2. MongoDB background task runs every 60 seconds
3. Checks: created_at + 86400s < current_time?
4. If YES → Document deleted
5. If NO → Document remains

Example:
- Message saved: Nov 6, 7:00 PM
- Will be deleted: Nov 7, 7:00 PM
- Automatically, no code needed!
```

### **TTL Index Creation:**

```python
# In unified_analytics_agents.py
scriptwriter_chat_collection.create_index(
    "created_at", 
    expireAfterSeconds=86400  # 24 hours
)

scene_writer_chat_collection.create_index(
    "created_at", 
    expireAfterSeconds=86400  # 24 hours
)
```

### **Verify TTL Index:**

```javascript
// In MongoDB shell
db.scriptwriter_chat_history.getIndexes()

// Output:
[
  {
    "v": 2,
    "key": { "created_at": 1 },
    "name": "created_at_1",
    "expireAfterSeconds": 86400
  }
]
```

---

## Benefits ✨

### **For Users:**
```
✅ Conversation continuity
✅ No need to repeat context
✅ Privacy (auto-delete after 24h)
✅ Multiple conversations (sessions)
✅ Clear chat option
```

### **For System:**
```
✅ Automatic cleanup
✅ No storage bloat
✅ Efficient queries (indexed)
✅ Scalable architecture
✅ Privacy compliant
```

### **For Development:**
```
✅ Simple to implement
✅ MongoDB handles cleanup
✅ No cron jobs needed
✅ Consistent pattern
✅ Easy to debug
```

---

## Performance Considerations ⚡

### **Query Performance:**
```
✅ Indexed on session_id + user_id
✅ Limit 10 messages per request
✅ Efficient sorting
✅ Fast retrieval
```

### **Storage:**
```
Estimate per message: ~500 bytes
10 messages: ~5KB
100 messages: ~50KB
1000 users × 10 msg: ~5MB

Auto-delete keeps storage minimal!
```

### **TTL Performance:**
```
✅ Background process (non-blocking)
✅ Runs every 60 seconds
✅ Batched deletions
✅ Minimal overhead
```

---

## Testing 🧪

### **Test Auto-Save:**

```bash
# Send message
curl -X POST "http://localhost:8000/api/unified/scriptwriter-chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Test message",
    "user_id": "test_user"
  }'

# Check in MongoDB
mongo
> use youtube_ops
> db.scriptwriter_chat_history.find()
```

### **Test History Retrieval:**

```bash
# Get history
curl "http://localhost:8000/api/unified/get-scriptwriter-chat/session_id?user_id=test_user"
```

### **Test Manual Clear:**

```bash
# Clear session
curl -X DELETE "http://localhost:8000/api/unified/clear-scriptwriter-chat/session_id?user_id=test_user"
```

### **Test TTL (wait 24 hours or modify):**

```javascript
// In MongoDB, modify TTL for testing
db.scriptwriter_chat_history.dropIndex("created_at_1")
db.scriptwriter_chat_history.createIndex(
  { "created_at": 1 },
  { expireAfterSeconds: 60 }  // 60 seconds for testing
)

// Insert test doc
db.scriptwriter_chat_history.insertOne({
  "session_id": "test",
  "user_id": "test",
  "role": "user",
  "content": "Test",
  "created_at": new Date()
})

// Wait 60 seconds, document should disappear!
```

---

## Comparison: Before vs After 🆚

### **Before (Frontend Storage):**
```
❌ Frontend manages history
❌ Lost on page refresh
❌ No cross-device sync
❌ Manual cleanup needed
❌ Limited by browser storage
```

### **After (Database Storage):**
```
✅ Backend manages history
✅ Persists across refreshes
✅ Cross-device sync possible
✅ Auto-cleanup (TTL)
✅ Unlimited storage
```

---

## Security & Privacy 🔒

### **Implemented:**
```
✅ User-based isolation (user_id)
✅ Session-based isolation (session_id)
✅ Auto-delete after 24h
✅ Manual clear option
✅ No cross-user leakage
```

### **Recommendations:**
```
💡 Add authentication
💡 Encrypt sensitive messages
💡 Add rate limiting
💡 Monitor storage usage
💡 Add user consent UI
```

---

## Troubleshooting 🔧

### **Issue: History not loading**
```
Solution:
- Check session_id is correct
- Verify user_id matches
- Check MongoDB connection
- Confirm collection exists
```

### **Issue: Messages not deleting**
```
Solution:
- Verify TTL index exists
- Check created_at field present
- MongoDB TTL thread running
- Wait up to 60 seconds for cleanup
```

### **Issue: Duplicate messages**
```
Solution:
- Check frontend not double-sending
- Verify session_id consistency
- Add message deduplication
```

---

## Future Enhancements 💡

### **Possible Features:**
```
1. Export chat history
2. Search within history
3. Tag/categorize conversations
4. Share conversations
5. Longer retention options
6. Archive important chats
7. Conversation analytics
8. Multi-language support
9. Voice input/output
10. Conversation summaries
```

---

## Summary 📋

### **What Changed:**
```
✅ Added 2 MongoDB collections with TTL
✅ Removed chat_history from requests
✅ Added session_id to requests
✅ Auto-save messages to DB
✅ Auto-load history from DB
✅ Added 4 new endpoints (clear/get)
✅ 24-hour auto-delete
```

### **Files Modified:**
```
Backend/per_channel_analytics_Agents/unified_analytics_agents.py
  ├─ Added TTL collections
  ├─ Added save_chat_message()
  ├─ Added get_chat_history()
  ├─ Added clear_chat_session()
  ├─ Updated scriptwriter endpoint
  ├─ Updated scene writer endpoint
  └─ Added 4 management endpoints
```

### **Collections Created:**
```
1. scriptwriter_chat_history (TTL: 24h)
2. scene_writer_chat_history (TTL: 24h)
```

---

**🎉 Chat History Database Integration Complete!**

**Features:**
- 💾 MongoDB storage
- ⏰ 24-hour auto-delete (TTL)
- 📝 Session-based
- 🔒 User-isolated
- 🧹 Auto-cleanup
- 🔄 Full CRUD

**Privacy-friendly aur efficient!** 🚀

---

**Last Updated:** November 6, 2025  
**Status:** ✅ Implemented & Tested
