# Tool Calling from Scratch

A hands-on implementation of LLM tool calling **without using any native/built-in tool-calling APIs** — no OpenAI functions, no Anthropic tool use, no LangChain. This project manually implements the entire pipeline: injecting tool definitions into the prompt, detecting tool-call syntax in the raw model output, executing the tool, and feeding the result back into the conversation.

Built to understand exactly how tool calling works "under the hood" in modern AI frameworks. There's also a [companion project](https://github.com/SRIDEVI-01/tool-calling-langchain) that implements the same four tools using LangChain's native structured tool-calling instead, for a direct side-by-side comparison of the two approaches.

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
| `get_weather` | `get_weather(city: str)` | Live current weather for a city, via the [Open-Meteo](https://open-meteo.com/) API |
| `get_time` | `get_time(tz: str)` | Current time in any IANA timezone (e.g. `Asia/Kolkata`), defaults to UTC |
| `calculate` | `calculate(expression: str)` | Evaluates a basic arithmetic expression — parsed via Python's `ast` module, no `eval()` involved |
| `send_email` | `send_email(to: str, subject: str, body: str)` | Sends an email (mock — validates address format and subject, doesn't actually send) |

If the model asks for something no tool covers (e.g. "book me a flight"), it correctly declines instead of hallucinating a fake tool call — see [Error Handling](#-error-handling).

---

## 🛠️ Tech Stack

- **Ollama** — running the `qwen2.5:3b-instruct` model locally
- **Python** — core logic for prompt building, parsing, and tool execution
- **RunPod** — GPU cloud instance used to host the model
- **Requests** — for calling Ollama's local API and the Open-Meteo weather API

> **Why `qwen2.5:3b-instruct` and not a "reasoning" model?** An earlier version of this project used `qwen3:4b`, which generates a large internal chain-of-thought before every answer — even with `/no_think` appended, responses took 40-60 seconds. Switching to a plain instruct model with no forced reasoning step dropped that to 1-5 seconds with no loss of tool-calling accuracy.

---

## 📦 Prerequisites

- [Ollama](https://ollama.com/) installed
- Model pulled:
```bash
  ollama pull qwen2.5:3b-instruct
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

### Keeping it running

`start_services.sh` is a self-healing startup script — it reinstalls Ollama and Python dependencies if missing, then starts both Ollama and the web app. It's designed to live in a persistent volume (e.g. RunPod's `/workspace`) so it survives a pod restart or even a full terminate+recreate. Safe to re-run any time; it skips whatever's already in place.

---

## 📁 Project Structure

```
tool-calling-from-scratch/
├── main.py              # CLI demo: runs sample queries through the agent, prints the trace
├── app.py               # FastAPI web server exposing the same agent over HTTP
├── agent.py             # core loop: builds prompts, calls Ollama, executes tools
├── tools.py             # tool definitions (get_weather, get_time, calculate, send_email)
├── parser.py            # extract_tool_call() — parses <tool_call> tags out of model output
├── start_services.sh    # self-healing startup script (Ollama + web app)
├── static/index.html    # single-page UI for app.py
├── requirements.txt
└── README.md
```

---

## ⚠️ Error Handling

The parser, tools, and web server are all built to fail gracefully instead of crashing on bad input:

- **Missing `<tool_call>` tags**: some models don't always wrap their tool call in the expected tags — sometimes they emit bare JSON instead. `parser.py` falls back to parsing the whole response as JSON in that case.
- **Malformed JSON**: if a `<tool_call>` tag is present but its contents aren't valid JSON (or are missing `name`/`arguments`), `extract_tool_call` raises a `ToolCallParseError` with the offending text, instead of throwing an unhandled exception.
- **Unknown tool name**: if the model hallucinates a tool that isn't in `TOOLS`, `execute_tool_call` returns an error string (fed back to the model) rather than raising a `KeyError`.
- **Bad or invalid arguments**: a `TypeError` from calling the tool with the wrong arguments, an invalid email address, an unknown timezone, or an unsafe `calculate` expression are all caught and turned into readable error messages instead of crashing.
- **No tool needed**: if the user's request doesn't match any tool (e.g. "book me a flight"), the model responds in plain language and the app reports "No tool call detected" instead of assuming one.
- **Server-level failures**: `app.py` catches Ollama connection errors, timeouts, and upstream HTTP errors and returns clean 502/503/504 responses instead of leaking a raw stack trace to the browser.

---

## 🎯 Why This Project

Most developers use tool calling as a black box provided by AI platforms. This project removes that abstraction to show:
- How prompt engineering enables structured behavior from an LLM
- How to parse streaming/non-streaming model output for custom tags
- How the "agent loop" (model → tool → model) actually works internally

For comparison, see [tool-calling-langchain](https://github.com/SRIDEVI-01/tool-calling-langchain) — the same four tools and UI, but using LangChain's `create_agent` and Ollama's native structured tool-calling API instead of hand-rolled prompt/regex parsing.

---

## 📌 Notes

- `send_email` is a mock — it validates input but doesn't perform a real send. `get_weather` and `get_time` return real, live data.
- `calculate` never calls `eval()` — expressions are parsed into an AST and only numeric literals with `+ - * /` are evaluated.
- Adding a new tool takes two steps: define the function (+ add it to `TOOLS`) and describe it in `TOOL_DESCRIPTIONS`, both in `tools.py`. No other code changes needed.

---

## 📄 License

MIT License — feel free to use, modify, and learn from this project.
