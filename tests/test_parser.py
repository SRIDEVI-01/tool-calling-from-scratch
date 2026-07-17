import pytest

from parser import ToolCallParseError, extract_tool_call


def test_extract_tool_call_wrapped():
    text = '<tool_call>{"name": "calculate", "arguments": {"expression": "1+1"}}</tool_call>'
    assert extract_tool_call(text) == {"name": "calculate", "arguments": {"expression": "1+1"}}


def test_extract_tool_call_bare_json_fallback():
    text = '{"name": "get_time", "arguments": {}}'
    assert extract_tool_call(text) == {"name": "get_time", "arguments": {}}


def test_extract_tool_call_none_for_plain_text():
    assert extract_tool_call("Hello, how can I help?") is None


def test_extract_tool_call_malformed_json_raises():
    with pytest.raises(ToolCallParseError):
        extract_tool_call("<tool_call>{not valid json}</tool_call>")


def test_extract_tool_call_missing_fields_raises():
    with pytest.raises(ToolCallParseError):
        extract_tool_call('<tool_call>{"name": "calculate"}</tool_call>')


def test_extract_tool_call_multiple_tags_raises():
    text = (
        '<tool_call>{"name": "get_weather", "arguments": {"city": "Tokyo"}}</tool_call>'
        '<tool_call>{"name": "get_time", "arguments": {"tz": "Asia/Tokyo"}}</tool_call>'
    )
    with pytest.raises(ToolCallParseError):
        extract_tool_call(text)
