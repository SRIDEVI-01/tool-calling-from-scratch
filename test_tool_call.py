import requests
import json

url = "http://127.0.0.1:11434/api/generate"

system_prompt = """You have access to these tools:
- get_weather(city: str): returns current weather for a city

When you want to use a tool, respond ONLY with:
<tool_call>{\"name\": \"get_weather\", \"arguments\": {\"city\": \"CITY_NAME\"}}</tool_call>"""

full_prompt = f"{system_prompt}\n\nUser: What's the weather in Mumbai? /no_think"

payload = {
    "model": "qwen3:4b",
    "prompt": full_prompt,
    "stream": False
}

response = requests.post(url, json=payload)
print(json.dumps(response.json(), indent=2))
