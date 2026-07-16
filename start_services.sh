#!/bin/bash
# Self-healing startup for tool-calling-from-scratch.
# Lives in /workspace so it survives a full pod terminate+recreate (unlike
# /root, /usr/local, and apt/pip installs, which reset to the base image).
# Re-installs anything missing, then starts Ollama and the web app.
# Safe to re-run: skips steps that are already satisfied.

set -e

APP_DIR="/workspace/tool-calling-from-scratch"
LC_APP_DIR="/workspace/tool-calling-langchain"
export OLLAMA_MODELS="/workspace/.ollama-models"
MODEL="qwen2.5:3b-instruct"

echo "[start_services] Ensuring system deps (zstd, needed by the Ollama installer)..."
if ! command -v zstd > /dev/null 2>&1; then
    apt-get update -qq && apt-get install -y -qq zstd
fi

echo "[start_services] Ensuring Ollama is installed..."
if ! command -v ollama > /dev/null 2>&1; then
    curl -fsSL https://ollama.com/install.sh | sh
fi

echo "[start_services] Ensuring Ollama server is running..."
if ! curl -s http://127.0.0.1:11434/api/version > /dev/null 2>&1; then
    nohup ollama serve > /workspace/ollama.log 2>&1 &
    disown
    for i in $(seq 1 30); do
        curl -s http://127.0.0.1:11434/api/version > /dev/null 2>&1 && break
        sleep 1
    done
fi

echo "[start_services] Ensuring model '$MODEL' is present..."
if ! ollama list | grep -q "$MODEL"; then
    ollama pull "$MODEL"
fi

echo "[start_services] Ensuring Python deps are installed..."
if ! python3 -c "import fastapi, uvicorn, requests" > /dev/null 2>&1; then
    pip3 install -q -r "$APP_DIR/requirements.txt"
fi

echo "[start_services] Ensuring web app is running..."
if ! curl -s -o /dev/null http://127.0.0.1:8000/ 2>&1; then
    cd "$APP_DIR" && nohup python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 > /workspace/app.log 2>&1 &
    disown
fi

echo "[start_services] Ensuring LangChain Python deps are installed..."
if ! python3 -c "import langchain, langchain_ollama" > /dev/null 2>&1; then
    pip3 install -q -r "$LC_APP_DIR/requirements.txt"
fi

echo "[start_services] Ensuring LangChain web app is running..."
if ! curl -s -o /dev/null http://127.0.0.1:8002/ 2>&1; then
    cd "$LC_APP_DIR" && nohup python3 -m uvicorn app:app --host 0.0.0.0 --port 8002 > /workspace/lc_app.log 2>&1 &
    disown
fi

echo "[start_services] Done."
