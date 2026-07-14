import requests
import json
import re

url = "http://127.0.0.1:11434/api/generate"

def get_weather(city: str):
    return f"The weather in {city} is 33C, partly cloudy."

TOOLS = {"get_weather": get_weather}

system_prompt = """You have access to these tools:
- get_weather(city: str): returns current weather for a city

When you want to use a tool, respond ONLY with:
<tool_call>{\"name\": \"get_weather\", \"arguments\": {\"city\": \"CITY_NAME\"}}</tool_call>"""

def ask_model(prompt):
    payload = {"model": "qwen3:4b", "prompt": prompt, "stream": False}
    response = requests.post(url, json=payload)
    return response.json()["response"]

def extract_tool_call(text):
    match = re.search(r"<tool_call>(.*?)</tool_call>", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    return None

def run_conversation(user_message):
    full_prompt = f"{system_prompt}\n\nUser: {user_message} /no_think"
    model_output = ask_model(full_prompt)
    print("Model first response:\n", model_output)

    tool_call = extract_tool_call(model_output)

    if tool_call:
        name = tool_call["name"]
        args = tool_call["arguments"]
        print(f"\nDetected tool call: {name}({args})")

        result = TOOLS[name](**args)
        print(f"Tool result: {result}")

        followup_prompt = f"""{system_prompt}

User: {user_message}
Assistant: <tool_call>{json.dumps(tool_call)}</tool_call>
Tool Result: {result}

Now give a natural language final answer to the user based on this tool result. /no_think"""

        final_answer = ask_model(followup_prompt)
        print("\nFinal answer:\n", final_answer)
    else:
        print("\nNo tool call detected.")

run_conversation("What's the weather in Mumbai?")
