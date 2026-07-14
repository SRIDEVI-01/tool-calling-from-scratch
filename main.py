import json
import requests

from tools import TOOLS, TOOL_DESCRIPTIONS
from parser import extract_tool_call, ToolCallParseError

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen3:4b"

SYSTEM_PROMPT = f"""You have access to these tools:
{TOOL_DESCRIPTIONS}

When you want to use a tool, respond ONLY with:
<tool_call>{{"name": "TOOL_NAME", "arguments": {{...}}}}</tool_call>"""


def ask_model(prompt: str) -> str:
    payload = {"model": MODEL, "prompt": prompt, "stream": False}
    response = requests.post(OLLAMA_URL, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()["response"]


def execute_tool_call(tool_call: dict) -> str:
    name = tool_call["name"]
    args = tool_call.get("arguments", {})

    if name not in TOOLS:
        return f"Error: unknown tool '{name}'. Available tools: {', '.join(TOOLS)}"

    try:
        return TOOLS[name](**args)
    except TypeError as e:
        return f"Error: invalid arguments for '{name}': {e}"
    except Exception as e:
        return f"Error: '{name}' failed during execution: {e}"


def run_conversation(user_message: str):
    full_prompt = f"{SYSTEM_PROMPT}\n\nUser: {user_message} /no_think"
    model_output = ask_model(full_prompt)
    print("Model first response:\n", model_output)

    try:
        tool_call = extract_tool_call(model_output)
    except ToolCallParseError as e:
        print(f"\nCould not parse tool call: {e}")
        return

    if not tool_call:
        print("\nNo tool call detected.")
        return

    print(f"\nDetected tool call: {tool_call['name']}({tool_call.get('arguments', {})})")
    result = execute_tool_call(tool_call)
    print(f"Tool result: {result}")

    followup_prompt = f"""{SYSTEM_PROMPT}

User: {user_message}
Assistant: <tool_call>{json.dumps(tool_call)}</tool_call>
Tool Result: {result}

Now give a natural language final answer to the user based on this tool result. /no_think"""

    final_answer = ask_model(followup_prompt)
    print("\nFinal answer:\n", final_answer)


if __name__ == "__main__":
    demo_queries = [
        "What's the weather in Mumbai?",
        "What time is it right now?",
        "What's 12 times 7 plus 3?",
        "Send an email to john@example.com about tomorrow's meeting",
        "Can you book me a flight to Tokyo?",
    ]

    for query in demo_queries:
        print("=" * 60)
        print(f"User: {query}")
        print("=" * 60)
        run_conversation(query)
        print()
