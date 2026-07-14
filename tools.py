from datetime import datetime, timezone
import re


def get_weather(city: str):
    """Returns current weather for a city (mock data)."""
    return f"The weather in {city} is 33C, partly cloudy."


def get_time(tz: str = "UTC"):
    """Returns the current UTC time (mock — does not convert between timezones)."""
    now = datetime.now(timezone.utc).strftime("%H:%M:%S")
    return f"The current time ({tz}) is {now}."


def calculate(expression: str):
    """Evaluates a basic arithmetic expression, e.g. '12 * 7 + 3'."""
    if not re.fullmatch(r"[0-9+\-*/(). ]+", expression):
        raise ValueError(f"unsafe or invalid expression: {expression!r}")
    return str(eval(expression, {"__builtins__": {}}, {}))


def send_email(to: str, subject: str, body: str = ""):
    """Mock-sends an email (stub — does not actually send anything)."""
    return f"Email sent to {to} with subject '{subject}'."


TOOLS = {
    "get_weather": get_weather,
    "get_time": get_time,
    "calculate": calculate,
    "send_email": send_email,
}

TOOL_DESCRIPTIONS = """- get_weather(city: str): returns current weather for a city
- get_time(tz: str): returns the current time
- calculate(expression: str): evaluates a basic arithmetic expression
- send_email(to: str, subject: str, body: str): sends an email"""
