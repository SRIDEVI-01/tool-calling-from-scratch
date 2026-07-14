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
  pip install requests
```

---

## ▶️ Usage

1. Make sure Ollama is running (locally or on a remote server):
```bash
   ollama serve
```
2. Run the test script:
```bash
   python3 test_tool_call.py
```
3. Try prompts like:
   - `"What's the weather in Mumbai?"`
   - `"Send an email to john@example.com about tomorrow's meeting"`

You should see the model respond with a `<tool_call>` tag, which is then parsed and "executed" by the corresponding stub function.

---

## 📁 Project Structure
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

---

## 📄 License

MIT License — feel free to use, modify, and learn from this project.
