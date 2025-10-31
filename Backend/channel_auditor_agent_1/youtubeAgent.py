import asyncio
import os

from openai import AsyncOpenAI
from dotenv import load_dotenv
load_dotenv()

from agents import (
    Agent,
    Runner,
    function_tool,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
)
from agents.mcp import MCPServerStdio

BASE_URL = os.getenv("GEMINI_BASE_URL") or ""
API_KEY = os.getenv("GEMINI_API_KEY") or ""
MODEL_NAME = os.getenv("GEMINI_MODEL_NAME") or ""

if not BASE_URL or not API_KEY or not MODEL_NAME:
    raise ValueError(
        "Please set GEMINI_BASE_URL, GEMINI_API_KEY, GEMINI_MODEL_NAME via env var or code."
    )


"""This example uses a custom provider for all requests by default. We do three things:
1. Create a custom client.
2. Set it as the default OpenAI client, and don't use it for tracing.
3. Set the default API as Chat Completions, as most LLM providers don't yet support Responses API.

Note that in this example, we disable tracing under the assumption that you don't have an API key
from platform.openai.com. If you do have one, you can either set the `OPENAI_API_KEY` env var
or call set_tracing_export_api_key() to set a tracing specific key.
"""

client = AsyncOpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
)
set_default_openai_client(client=client, use_for_tracing=False)
set_default_openai_api("chat_completions")
set_tracing_disabled(disabled=True)


async def main():
    async with MCPServerStdio(
        name="youtube",
        params={
            "command": "node",
            "args": ["./youtube-mcp-server/dist/cli.js"],
            "env": {"YOUTUBE_API_KEY": os.getenv("YOUTUBE_API_KEY")},
        },
    ) as youtube_server:
        agent = Agent(
            name="YouTube Assistant",
            instructions="""You are a helpful YouTube assistant with access to YouTube data.
            You can help users with:
            - Getting video information and details
            - Searching for videos
            - Getting video transcripts
            - Retrieving channel information
            - Listing videos from channels
            - Getting playlist information and videos
            - Calculating channel analytics:
              * Average video duration
              * Upload frequency (videos per week/month)
              * Average views per video
            - 🆕 Comprehensive video analysis (NEW!):
              * Complete metadata for all videos
              * Engagement metrics (likes, comments, views)
              * Title analysis (formula types, patterns)
              * Duration, thumbnails, statistics
              * Primary and secondary keywords
              * All details in one call
            
            For comprehensive analysis of multiple videos, use the analytics_getComprehensiveVideoAnalysis tool.
            
            ⚠️ IMPORTANT WORKFLOW RULES:
            
            1. AUTOMATIC CHANNEL ID EXTRACTION:
               - If user provides a VIDEO URL or VIDEO ID and asks for channel analysis/videos
               - First call video_getVideo to get video details
               - Extract channelId from the response (video.snippet.channelId)
               - Then use that channelId for analytics_getComprehensiveVideoAnalysis
               - NEVER ask user for channel ID if they provided a video link
               - Example flow: Video URL → Get Video → Extract channelId → Get Channel Analysis
            
            2. PRESENTATION RULES FOR COMPREHENSIVE ANALYSIS:
               When user requests "comprehensive analysis" or "complete analysis" or "detailed analysis" of multiple videos:
               a. First show the channel information summary
               b. Then show EACH video's analysis SEPARATELY - DO NOT SUMMARIZE
               c. For each video, present ALL available data including:
                  - Video Title and URL
                  - Upload Date
                  - Duration (formatted)
                  - Statistics: Views, Likes, Comments, Engagement Rate
                  - Title Analysis: Formula Type, Question Type, Numbers in Title
                  - Keywords: Primary, Secondary, and All Tags
                  - Thumbnails: All available sizes
                  - Description preview
               d. Present each video as a distinct section with clear separation
               e. DO NOT create summaries or aggregate patterns unless specifically asked
               f. Present the data in a clear, structured format for each video
            
            3. VIDEO ID/URL PARSING:
               - Accept various formats: full URLs, short URLs (youtu.be), or just video IDs
               - Extract video ID automatically from any YouTube URL format
               - Example: https://youtu.be/ABC123 → videoId: ABC123
               - Example: https://www.youtube.com/watch?v=ABC123 → videoId: ABC123
            
            Always provide detailed and helpful responses with complete information.""",
            model=MODEL_NAME,
            mcp_servers=[youtube_server]
        )

        print("\n=== YouTube Agent ===")
        print("Available commands:")
        print("  - Get video information by video ID")
        print("  - Search for videos")
        print("  - Get video transcripts")
        print("  - Get channel information")
        print("  - List videos from a channel")
        print("  - Get playlist information")
        print("  - Calculate channel analytics (avg duration, upload frequency, avg views)")
        print("\nType 'samples' to see example prompts")
        print("Type 'exit' to quit\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("Goodbye!")
                    break
                
                if user_input.lower() == 'samples':
                    print("\n📝 Sample Prompts:")
                    print("1. Get video details:")
                    print("   'Get information about video dQw4w9WgXcQ'")
                    print("\n2. Search videos:")
                    print("   'Search for Python tutorial videos'")
                    print("\n3. Get transcript:")
                    print("   'Get the transcript for video dQw4w9WgXcQ'")
                    print("\n4. Channel info:")
                    print("   'Get information about channel UC8butISFwT-Wl7EV0hUK0BQ'")
                    print("\n5. List channel videos:")
                    print("   'List recent videos from channel UC8butISFwT-Wl7EV0hUK0BQ'")
                    print("\n6. Playlist info:")
                    print("   'Get playlist PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf'")
                    print("\n7. Analytics - Average Duration:")
                    print("   'What is the average video duration for channel UC8butISFwT-Wl7EV0hUK0BQ?'")
                    print("\n8. Analytics - Upload Frequency:")
                    print("   'How often does channel UC8butISFwT-Wl7EV0hUK0BQ upload videos?'")
                    print("\n9. Analytics - Average Views:")
                    print("   'What is the average views per video for channel UC8butISFwT-Wl7EV0hUK0BQ?'")
                    print("\nType 'exit' to quit\n")
                    continue
                
                print("\n🤔 Thinking...")
                result = await Runner.run(agent, user_input)
                print(f"\n🤖 Assistant: {result.final_output}\n")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}\n")


if __name__ == "__main__":
    asyncio.run(main())