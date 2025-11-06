import os
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class YouTubeHttpClient:
    """Lightweight client for the Hugging Face-hosted YouTube MCP HTTP wrapper."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 20.0) -> None:
        self.base_url = (base_url or os.getenv("YOUTUBE_HTTP_BASE_URL") or "").rstrip("/")
        if not self.base_url:
            raise ValueError(
                "Missing YOUTUBE_HTTP_BASE_URL. Set it to your Hugging Face Space base URL."
            )
        self.timeout = timeout

    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            # Surface API error details for easier debugging.
            content = exc.response.text
            raise RuntimeError(
                f"YouTube HTTP wrapper returned {exc.response.status_code}: {content}"
            ) from exc
        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Failed to contact YouTube HTTP wrapper at {url}: {exc}"
            ) from exc

        payload = response.json()
        return payload.get("data", payload)

    async def health(self) -> Dict[str, Any]:
        return await self._get("/health")

    async def get_video(self, video_id: str, parts: Optional[List[str]] = None) -> Any:
        params: Dict[str, Any] = {}
        if parts:
            params["parts"] = ",".join(parts)
        return await self._get(f"/videos/{video_id}", params=params)

    async def get_video_stats(self, video_id: str) -> Any:
        return await self._get(f"/videos/{video_id}/stats")

    async def search_videos(self, query: str, max_results: Optional[int] = None) -> Any:
        params: Dict[str, Any] = {"q": query}
        if max_results:
            params["maxResults"] = max_results
        return await self._get("/videos", params=params)

    async def get_transcript(self, video_id: str, language: Optional[str] = None) -> Any:
        params: Dict[str, Any] = {}
        if language:
            params["language"] = language
        return await self._get(f"/videos/{video_id}/transcript", params=params)

    async def get_channel(self, channel_id: str) -> Any:
        return await self._get(f"/channels/{channel_id}")

    async def list_channel_videos(
        self, channel_id: str, max_results: Optional[int] = None
    ) -> Any:
        params: Dict[str, Any] = {}
        if max_results:
            params["maxResults"] = max_results
        return await self._get(f"/channels/{channel_id}/videos", params=params)

    async def get_playlist(self, playlist_id: str) -> Any:
        return await self._get(f"/playlists/{playlist_id}")

    async def get_playlist_items(
        self, playlist_id: str, max_results: Optional[int] = None
    ) -> Any:
        params: Dict[str, Any] = {}
        if max_results:
            params["maxResults"] = max_results
        return await self._get(f"/playlists/{playlist_id}/items", params=params)
