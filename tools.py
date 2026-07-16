from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import re

import requests

WMO_WEATHER_CODES = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "depositing rime fog",
    51: "light drizzle", 53: "moderate drizzle", 55: "dense drizzle",
    56: "light freezing drizzle", 57: "dense freezing drizzle",
    61: "slight rain", 63: "moderate rain", 65: "heavy rain",
    66: "light freezing rain", 67: "heavy freezing rain",
    71: "slight snow fall", 73: "moderate snow fall", 75: "heavy snow fall",
    77: "snow grains",
    80: "slight rain showers", 81: "moderate rain showers", 82: "violent rain showers",
    85: "slight snow showers", 86: "heavy snow showers",
    95: "thunderstorm", 96: "thunderstorm with slight hail", 99: "thunderstorm with heavy hail",
}


def get_weather(city: str):
    """Returns current weather for a city using live data from Open-Meteo."""
    geo_resp = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1},
        timeout=10,
    )
    geo_resp.raise_for_status()
    results = geo_resp.json().get("results")
    if not results:
        raise ValueError(f"could not find location: {city!r}")
    location = results[0]
    resolved_name = location.get("name", city)

    weather_resp = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={"latitude": location["latitude"], "longitude": location["longitude"], "current_weather": "true"},
        timeout=10,
    )
    weather_resp.raise_for_status()
    current = weather_resp.json()["current_weather"]
    condition = WMO_WEATHER_CODES.get(current["weathercode"], "unknown conditions")
    return f"The weather in {resolved_name} is {current['temperature']}C, {condition}."


def get_time(tz: str = "UTC"):
    """Returns the current time in the given IANA timezone (e.g. 'Asia/Kolkata', 'America/New_York'). Defaults to UTC."""
    tz = tz or "UTC"
    try:
        zone = ZoneInfo(tz)
    except ZoneInfoNotFoundError:
        raise ValueError(f"unknown timezone: {tz!r}")
    now = datetime.now(zone).strftime("%H:%M:%S")
    return f"The current time ({tz}) is {now}."


def calculate(expression: str):
    """Evaluates a basic arithmetic expression, e.g. '12 * 7 + 3'."""
    if not re.fullmatch(r"[0-9+\-*/(). ]+", expression):
        raise ValueError(f"unsafe or invalid expression: {expression!r}")
    return str(eval(expression, {"__builtins__": {}}, {}))


def send_email(to: str, subject: str, body: str = ""):
    """Mock-sends an email (stub — does not actually send anything)."""
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", to):
        raise ValueError(f"invalid email address: {to!r}")
    if not subject:
        raise ValueError("email subject cannot be empty")
    return f"Email sent to {to} with subject '{subject}'."


TOOLS = {
    "get_weather": get_weather,
    "get_time": get_time,
    "calculate": calculate,
    "send_email": send_email,
}

TOOL_DESCRIPTIONS = """- get_weather(city: str): returns live current weather for a city
- get_time(tz: str): returns the current time in the given IANA timezone (e.g. "Asia/Kolkata", "America/New_York", "UTC")
- calculate(expression: str): evaluates a basic arithmetic expression
- send_email(to: str, subject: str, body: str): sends an email"""
