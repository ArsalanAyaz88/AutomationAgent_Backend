import json
from typing import Annotated, Optional, List

from agents import function_tool

try:
    # Try direct API client first (uses YOUTUBE_API_KEY)
    from youtube_direct_client import YouTubeHttpClient
except ImportError:
    # Fallback to HTTP client (uses YOUTUBE_HTTP_BASE_URL)
    from youtube_http_client import YouTubeHttpClient

_client: YouTubeHttpClient | None = None


def _get_client() -> YouTubeHttpClient:
    global _client
    if _client is None:
        _client = YouTubeHttpClient()
    return _client


def _to_text(payload: object) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False)


@function_tool
async def videos_getVideo(
    videoId: Annotated[str, "The YouTube video ID"],
    parts: Annotated[Optional[List[str]], "Optional list of YouTube API parts to request"] = None,
) -> str:
    client = _get_client()
    data = await client.get_video(videoId, parts)
    return _to_text(data)


@function_tool
async def videos_getVideoStats(
    videoId: Annotated[str, "The YouTube video ID"],
) -> str:
    client = _get_client()
    data = await client.get_video_stats(videoId)
    return _to_text(data)


@function_tool
async def videos_searchVideos(
    query: Annotated[str, "Search query string"],
    maxResults: Annotated[Optional[int], "Maximum number of results"] = None,
) -> str:
    client = _get_client()
    data = await client.search_videos(query, max_results=maxResults)
    return _to_text(data)


@function_tool
async def transcripts_getTranscript(
    videoId: Annotated[str, "The YouTube video ID"],
    language: Annotated[Optional[str], "Preferred language code"] = None,
) -> str:
    client = _get_client()
    data = await client.get_transcript(videoId, language)
    return _to_text(data)


@function_tool
async def channels_getChannel(
    channelId: Annotated[str, "The YouTube channel ID"],
) -> str:
    client = _get_client()
    data = await client.get_channel(channelId)
    return _to_text(data)


@function_tool
async def channels_listVideos(
    channelId: Annotated[str, "The YouTube channel ID"],
    maxResults: Annotated[Optional[int], "Maximum number of videos to return"] = None,
) -> str:
    client = _get_client()
    data = await client.list_channel_videos(channelId, max_results=maxResults)
    return _to_text(data)


@function_tool
async def playlists_getPlaylist(
    playlistId: Annotated[str, "The YouTube playlist ID"],
) -> str:
    client = _get_client()
    data = await client.get_playlist(playlistId)
    return _to_text(data)


@function_tool
async def playlists_getPlaylistItems(
    playlistId: Annotated[str, "The YouTube playlist ID"],
    maxResults: Annotated[Optional[int], "Maximum number of items to return"] = None,
) -> str:
    client = _get_client()
    data = await client.get_playlist_items(playlistId, max_results=maxResults)
    return _to_text(data)


YOUTUBE_TOOLS = [
    videos_getVideo,
    videos_getVideoStats,
    videos_searchVideos,
    transcripts_getTranscript,
    channels_getChannel,
    channels_listVideos,
    playlists_getPlaylist,
    playlists_getPlaylistItems,
]

