"""
Direct YouTube Data API v3 Client
Uses YOUTUBE_API_KEY directly without Hugging Face Space proxy
"""

import os
from typing import Any, Dict, List, Optional
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class YouTubeDirectClient:
    """Direct client for YouTube Data API v3"""
    
    def __init__(self, api_key: Optional[str] = None, timeout: float = 20.0):
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            raise ValueError("Missing YOUTUBE_API_KEY environment variable")
        
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.timeout = timeout
    
    async def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Make GET request to YouTube API"""
        if params is None:
            params = {}
        
        # Add API key to all requests
        params['key'] = self.api_key
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            content = exc.response.text
            raise RuntimeError(
                f"YouTube API returned {exc.response.status_code}: {content}"
            ) from exc
        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Failed to contact YouTube API: {exc}"
            ) from exc
    
    async def health(self) -> Dict[str, Any]:
        """Health check - verify API key works"""
        try:
            # Try a simple API call
            result = await self._get("search", {
                "part": "snippet",
                "q": "test",
                "maxResults": 1,
                "type": "video"
            })
            return {"status": "ok", "message": "YouTube API accessible"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def get_video(self, video_id: str, parts: Optional[List[str]] = None) -> Any:
        """Get video details"""
        part = ",".join(parts) if parts else "snippet,contentDetails,statistics"
        result = await self._get("videos", {
            "part": part,
            "id": video_id
        })
        return result
    
    async def get_video_stats(self, video_id: str) -> Any:
        """Get video statistics"""
        result = await self._get("videos", {
            "part": "snippet,statistics",
            "id": video_id
        })
        return result
    
    async def search_videos(self, query: str, max_results: Optional[int] = None) -> Any:
        """Search for videos"""
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max_results or 10
        }
        result = await self._get("search", params)
        return result
    
    async def get_transcript(self, video_id: str, language: Optional[str] = None) -> Any:
        """Get video transcript (Note: YouTube API doesn't provide transcripts directly)"""
        # YouTube API v3 doesn't support transcripts
        # This would need youtube-transcript-api library
        raise NotImplementedError(
            "Transcripts not available via YouTube Data API v3. "
            "Use youtube-transcript-api library or caption endpoints."
        )
    
    async def get_channel(self, channel_id: str) -> Any:
        """Get channel details"""
        result = await self._get("channels", {
            "part": "snippet,contentDetails,statistics",
            "id": channel_id
        })
        return result
    
    async def list_channel_videos(
        self, channel_id: str, max_results: Optional[int] = None
    ) -> Any:
        """List videos from a channel"""
        # First get the uploads playlist ID
        channel_data = await self.get_channel(channel_id)
        
        if not channel_data.get('items'):
            return {"items": []}
        
        uploads_playlist = channel_data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        # Get videos from uploads playlist
        result = await self._get("playlistItems", {
            "part": "snippet,contentDetails",
            "playlistId": uploads_playlist,
            "maxResults": max_results or 50
        })
        return result
    
    async def get_playlist(self, playlist_id: str) -> Any:
        """Get playlist details"""
        result = await self._get("playlists", {
            "part": "snippet,contentDetails",
            "id": playlist_id
        })
        return result
    
    async def get_playlist_items(
        self, playlist_id: str, max_results: Optional[int] = None
    ) -> Any:
        """Get items from a playlist"""
        result = await self._get("playlistItems", {
            "part": "snippet,contentDetails",
            "playlistId": playlist_id,
            "maxResults": max_results or 50
        })
        return result


# Alias for backward compatibility
YouTubeHttpClient = YouTubeDirectClient
