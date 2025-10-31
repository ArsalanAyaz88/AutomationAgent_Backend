import asyncio
import os

from dotenv import load_dotenv
load_dotenv()

from openai import AsyncOpenAI

from agents import (
    Agent,
    Runner,
    function_tool,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
)

BASE_URL = os.getenv("GEMINI_BASE_URL") or ""
API_KEY = os.getenv("GEMINI_API_KEY") or ""
MODEL_NAME = os.getenv("GEMINI_IMAGE_MODEL_NAME") or ""

if not BASE_URL or not API_KEY or not MODEL_NAME:
    raise ValueError(
        "Please set GEMINI_BASE_URL, GEMINI_API_KEY, GEMINI_IMAGE_MODEL_NAME via env var or code."
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
    agent = Agent(
        name="Assistant",
        instructions="You are helpful assistant.",
        model=MODEL_NAME,
        
    )
    userinput = input("You : ")
    result = await Runner.run(agent, userinput)
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())