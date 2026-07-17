import json
import re

TOOL_CALL_PATTERN = re.compile(r"<tool_call>(.*?)</tool_call>", re.DOTALL)


class ToolCallParseError(Exception):
    """Raised when the model emits a <tool_call> tag that isn't valid."""


def extract_tool_call(text: str):
    """Returns the parsed {"name", "arguments"} dict, or None if the text has no tool call.

    Handles two model behaviors:
    - The well-behaved case: JSON wrapped in <tool_call>...</tool_call>
    - A drift case seen in practice: the model skips the tags and emits bare JSON

    Raises ToolCallParseError if something that looks like a tool call is
    malformed, or if the response contains more than one <tool_call> tag —
    the agent loop expects at most one tool call per turn, so a model that
    stacks several in a single response should surface as an error rather
    than silently executing only the first and dropping the rest.
    """
    matches = list(TOOL_CALL_PATTERN.finditer(text))
    if len(matches) > 1:
        raise ToolCallParseError(
            f"model emitted {len(matches)} tool calls in a single response; only one is allowed per turn"
        )

    match = matches[0] if matches else None
    raw = match.group(1).strip() if match else text.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        if match:
            raise ToolCallParseError(f"malformed tool call JSON: {raw!r}")
        return None

    if not isinstance(data, dict) or "name" not in data or "arguments" not in data:
        if match:
            raise ToolCallParseError(f"tool call missing 'name' or 'arguments': {data!r}")
        return None

    return data
