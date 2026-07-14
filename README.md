# tool-calling-from-scratch
LLM tool calling implemented from scratch using Ollama
# Tool Calling from Scratch

A hands-on implementation of LLM tool calling **without using any native/built-in tool-calling APIs** — no OpenAI functions, no Anthropic tool use, no LangChain. This project manually implements the entire pipeline: injecting tool definitions into the prompt, detecting tool-call syntax in the raw model output, executing the tool, and feeding the result back into the conversation.

Built to understand exactly how tool calling works "under the hood" in modern AI frameworks.

---

## 🚀 Overview

Large Language Models can only generate text — they can't natively send emails, check weather, or run code. Every "AI agent" or "tool calling" feature is actually built on a simple pattern:

1. Tell the model what tools exist (via the prompt)
2. Let the model respond with a specially formatted string when it wants to use one
3. Parse that string with regular code
4. Execute the real function
5. Feed the result back to the model so it can respond naturally

This repo implements that pattern end-to-end using a locally hosted open-source model.

---

## 🧠 How It Works

1. **System prompt** tells the model which tools are available and the exact format to respond in:
<tool_call>{"name": "tool_name", "arguments": {...}}</tool_call>
2. The model (running via **Ollama**) generates a response — if it decides to use a tool, it outputs the tag above as plain text.
3. A custom parser checks the model's output for `<tool_call>...</tool_call>` and extracts the JSON inside.
4. The corresponding Python function is executed with the parsed arguments.
5. The tool's result is injected back into the conversation, and the model is called again to produce a final natural-language answer.

---

## 🧰 Available Tools

| Tool | Signature | Description |
|---|---|---|
| `get_weather` | `get_weather(city: str)` | Returns current weather for a city (mock) |
| `get_time` | `get_time(tz: str)` | Returns the current time |
| `calculate` | `calculate(expression: str)` | Evaluates a basic arithmetic expression |
| `send_email` | `send_email(to: str, subject: str, body: str)` | Sends an email (mock) |

If the model asks for something no tool covers (e.g. "book me a flight"), it correctly declines instead of hallucinating a fake tool call — see [Error Handling](#-error-handling).

---

## 🛠️ Tech Stack

- **Ollama** — running the `qwen3:4b` model locally
- **Python** — core logic for prompt building, parsing, and tool execution
- **RunPod** — GPU cloud instance used to host the model
- **Requests** — for calling Ollama's local API

---

## 📦 Prerequisites

- [Ollama](https://ollama.com/) installed
- Model pulled:
```bash
  ollama pull qwen3:4b
```
- Python 3.10+
- Install dependencies:
```bash
  pip install -r requirements.txt
```

---

## ▶️ Usage

1. Make sure Ollama is running (locally or on a remote server):
```bash
   ollama serve
```
2. Run the demo:
```bash
   python3 main.py
```
3. It runs through a set of sample prompts, e.g.:
   - `"What's the weather in Mumbai?"`
   - `"What's 12 times 7 plus 3?"`
   - `"Send an email to john@example.com about tomorrow's meeting"`
   - `"Can you book me a flight to Tokyo?"` (no matching tool — tests graceful decline)

For each one you'll see the model's raw output, the detected tool call (if any), the tool's result, and the final natural-language answer.

### Web UI

There's also a small FastAPI + vanilla JS front end that shows the same pipeline live in the browser:

```bash
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000
```

Then open `http://localhost:8000` (if running on a remote box, tunnel the port first: `ssh -L 8000:localhost:8000 <host>`). Type a question or click one of the example chips, and watch the trace unfold: **User → Model raw output → Tool call detected → Tool result → Final answer**.

---

## 📁 Project Structure

```
tool-calling-from-scratch/
├── main.py            # CLI demo: runs sample queries through the agent, prints the trace
├── app.py              # FastAPI web server exposing the same agent over HTTP
├── agent.py            # core loop: builds prompts, calls Ollama, executes tools
├── tools.py            # tool definitions (get_weather, get_time, calculate, send_email)
├── parser.py           # extract_tool_call() — parses <tool_call> tags out of model output
├── static/index.html   # single-page UI for app.py
├── requirements.txt
└── README.md
```

---

## ⚠️ Error Handling

The parser and executor are built to fail gracefully instead of crashing on bad model output:

- **Missing `<tool_call>` tags**: Qwen3 doesn't always wrap its tool call in the expected tags — sometimes it emits bare JSON instead. `parser.py` falls back to parsing the whole response as JSON in that case.
- **Malformed JSON**: if a `<tool_call>` tag is present but its contents aren't valid JSON (or are missing `name`/`arguments`), `extract_tool_call` raises a `ToolCallParseError` with the offending text, instead of throwing an unhandled exception.
- **Unknown tool name**: if the model hallucinates a tool that isn't in `TOOLS`, `execute_tool_call` returns an error string (fed back to the model) rather than raising a `KeyError`.
- **Bad arguments**: a `TypeError` from calling the tool with the wrong arguments is caught and turned into a readable error message.
- **No tool needed**: if the user's request doesn't match any tool (e.g. "book me a flight"), the model responds in plain language and the app reports "No tool call detected" instead of assuming one.

---

## 🎯 Why This Project

Most developers use tool calling as a black box provided by AI platforms. This project removes that abstraction to show:
- How prompt engineering enables structured behavior from an LLM
- How to parse streaming/non-streaming model output for custom tags
- How the "agent loop" (model → tool → model) actually works internally

---

## 📌 Notes

- Tools in this repo are currently **stub functions** (they simulate execution but don't perform real actions like sending real emails).
- Tested with Qwen3, which requires `/no_think` appended to prompts to suppress its default chain-of-thought reasoning output.
- Adding a new tool takes two steps: define the function (+ add it to `TOOLS`) and describe it in `TOOL_DESCRIPTIONS`, both in `tools.py`. No other code changes needed.

---

## 📄 License

MIT License — feel free to use, modify, and learn from this project.
