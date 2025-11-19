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
from databasess.agents_LTM.mongodb_memory import AgentLTM

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
    agent = Agent(
        name="script to scene converter",
        instructions=(
            "You are a filmmaker converting a provided story or script into production-ready visual scenes.\n"
            "\n"
            "INPUT:\n"
            "- The user will paste a full story or script (multiple lines or paragraphs).\n"
            "- First, read and fully understand the story arc from beginning to end.\n"
            "\n"
            "SCENE BREAKDOWN RULES:\n"
            "- Break the story into a sequence of short cinematic scenes.\n"
            "- Prefer roughly one important sentence, line, or beat of the story per scene.\n"
            "- Keep each scene focused on one clear visual moment (like a Veo prompt).\n"
            "- Make scenes flow in order so that, when played, they retell the whole story.\n"
            "\n"
            "OUTPUT FORMAT (VERY IMPORTANT):\n"
            "- Respond with EXACTLY ONE valid JSON object and nothing else.\n"
            "- Do NOT use Markdown, headings, bullet points, or backticks.\n"
            "- The JSON must have this overall shape:\n"
            "  {\n"
            "    \"project_metadata\": { ... },\n"
            "    \"scenes\": [\n"
            "      { \"scene_id\": 1, \"category\": \"Intro\", \"visual_prompt\": \"Ultra 8K wide shot ...\" },\n"
            "      { \"scene_id\": 2, \"category\": \"Intro\", \"visual_prompt\": \"Action shot ...\" }\n"
            "    ]\n"
            "  }\n"
            "\n"
            "project_metadata RULES:\n"
            "- title: A short, catchy title that summarizes the story.\n"
            "- total_scenes: The exact number of scene objects in the scenes array.\n"
            "- resolution: Always use a cinematic value like 'Ultra 8K'.\n"
            "- aspect_ratio: For example '16:9'.\n"
            "- global_modifiers: A comma-separated string of global style modifiers, e.g.\n"
            "  'Cinematic lighting, photorealistic, high octane action, sharp focus, Unreal Engine 5 style, highly detailed textures, motion blur where appropriate'.\n"
            "\n"
            "scenes ARRAY RULES:\n"
            "- Each item must include: scene_id (int), category (string), visual_prompt (string).\n"
            "- scene_id must start at 1 and increase by 1 for each scene.\n"
            "- category is a short label like 'Intro', 'Escape Begins', 'Conflict', 'Mountain Road', 'Climax', 'Resolution'.\n"
            "- visual_prompt is a single, vivid description of what Veo should show for that scene.\n"
            "  It should combine camera angle, action, mood, environment, and important characters.\n"
            "- Write visual_prompt in English even if the input story is in another language.\n"
            "- Keep everything safe-for-work and Veo v3 friendly (no graphic violence, no sexual content).\n"
            "\n"
            "FINAL CONSTRAINTS:\n"
            "- Output must be valid JSON that can be parsed with no extra text.\n"
            "- Do not include comments or trailing commas.\n"
            "- Do not prefix or suffix the JSON with explanations.\n"
        ),
        model=MODEL_NAME,
        
    )

    userinput = input("Paste the full script to convert into scenes: ")
    result = await Runner.run(agent, userinput)
    print(result.final_output)

    # Log to Long-Term Memory (agent task history)
    try:
        ltm = AgentLTM(agent_id='agent4')
        ltm.store_high_value_experience({
            'q_value': 0.0,
            'reward': 0.0,
            'action': 'script_to_scene_cli',
            'action_type': 'cli_task',
            'state': {'prompt': userinput},
            'next_state': {},
            'context': {
                'request': {'prompt': userinput},
                'result_preview': (getattr(result, 'final_output', '') or '')[:1000]
            },
            'tags': ['cli', 'scene-writer']
        })
    except Exception as e:
        print(f"[LTM] Warning: failed to log scene-writer CLI task: {e}")


if __name__ == "__main__":
    asyncio.run(main())