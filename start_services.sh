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

# Export API_KEY before running this script to require an X-API-Key header
# on both apps' /api/chat — recommended if 8000/8002 are reachable outside
# the SSH tunnel (e.g. via a RunPod public proxy URL).

# Runs a uvicorn app in the background and restarts it if it ever exits
# (crash, OOM, etc.) instead of leaving the port dead until the next manual
# start_services.sh run.
run_with_respawn() {
    local dir="$1" port="$2" log="$3"
    (
        cd "$dir"
        while true; do
            python3 -m uvicorn app:app --host 0.0.0.0 --port "$port" >> "$log" 2>&1
            echo "[start_services] app on port $port exited, restarting in 3s..." >> "$log"
            sleep 3
        done
    ) &
    disown
}

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
    run_with_respawn "$APP_DIR" 8000 /workspace/app.log
fi

echo "[start_services] Ensuring LangChain Python deps are installed..."
if ! python3 -c "import langchain, langchain_ollama" > /dev/null 2>&1; then
    pip3 install -q -r "$LC_APP_DIR/requirements.txt"
fi

echo "[start_services] Ensuring LangChain web app is running..."
if ! curl -s -o /dev/null http://127.0.0.1:8002/ 2>&1; then
    run_with_respawn "$LC_APP_DIR" 8002 /workspace/lc_app.log
fi

echo "[start_services] Done."
