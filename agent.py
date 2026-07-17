import json
import re

import requests

from tools import TOOLS, TOOL_DESCRIPTIONS
from parser import extract_tool_call, ToolCallParseError

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5:3b-instruct"

MAX_TOOL_CALLS = 5

# Observed drift on compound requests: instead of a real <tool_call> tag,
# the model sometimes echoes the "TOOL_NAME" placeholder from the system
# prompt literally, or lists several tool names as bare text (e.g.
# "TOOL_NAME: get_weather\nTOOL_NAME: get_time"). Neither has a tool_call
# tag, so extract_tool_call correctly returns None — but treating that as a
# genuine final answer would surface the leaked placeholder to the user
# instead of retrying.
_DRIFT_RETRY_NUDGE = (
    "That wasn't a valid tool call. If you need a tool, respond with exactly "
    'one <tool_call>{"name": ..., "arguments": {...}}</tool_call> using a '
    "real tool name, not a placeholder."
)


def _looks_like_drift(text: str) -> bool:
    if "TOOL_NAME" in text:
        return True
    mentioned = [name for name in TOOLS if re.search(rf"\b{re.escape(name)}\b", text)]
    return len(mentioned) >= 2

SYSTEM_PROMPT = f"""You have access to these tools:
{TOOL_DESCRIPTIONS}

When you want to use a tool, respond ONLY with:
<tool_call>{{"name": "TOOL_NAME", "arguments": {{...}}}}</tool_call>

Call only ONE tool per response, then wait for its result. If the result is
enough to answer the user, reply in plain natural language (no tags). If you
still need another tool to fully answer, emit another <tool_call> in your
next response."""


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


def run_conversation(user_message: str) -> dict:
    """Runs the full tool-calling loop and returns a structured trace of each step.

    Loops until the model responds without a tool call, or MAX_TOOL_CALLS is
    reached — this lets a single query resolve more than one tool in sequence
    (e.g. "weather in Tokyo and what time is it there").
    """
    steps = {
        "user_message": user_message,
        "model_first_response": None,
        "tool_calls": [],
        "tool_results": [],
        "parse_error": None,
        "final_answer": None,
    }

    conversation = f"{SYSTEM_PROMPT}\n\nUser: {user_message}"
    drift_retried = False

    for _ in range(MAX_TOOL_CALLS):
        model_output = ask_model(conversation)
        if steps["model_first_response"] is None:
            steps["model_first_response"] = model_output

        try:
            tool_call = extract_tool_call(model_output)
        except ToolCallParseError as e:
            steps["parse_error"] = str(e)
            return steps

        if not tool_call:
            if not drift_retried and _looks_like_drift(model_output):
                conversation += f"\nAssistant: {model_output}\nUser: {_DRIFT_RETRY_NUDGE}"
                drift_retried = True
                continue
            steps["final_answer"] = model_output
            return steps

        result = execute_tool_call(tool_call)
        steps["tool_calls"].append(tool_call)
        steps["tool_results"].append(result)

        conversation += (
            f"\nAssistant: <tool_call>{json.dumps(tool_call)}</tool_call>"
            f"\nTool Result: {result}"
        )

    # Hit the tool-call cap without a plain-text answer — force one so the
    # user always gets a final response instead of a silent loop cutoff.
    conversation += "\n\nYou've used the maximum number of tool calls. Give your best natural language final answer now, without another tool call."
    steps["final_answer"] = ask_model(conversation)
    return steps
