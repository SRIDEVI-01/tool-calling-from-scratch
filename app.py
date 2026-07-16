import logging

import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from agent import run_conversation

app = FastAPI()
logger = logging.getLogger("uvicorn.error")


class ChatRequest(BaseModel):
    message: str


@app.get("/", response_class=HTMLResponse)
def index():
    with open("static/index.html", encoding="utf-8") as f:
        return f.read()


@app.post("/api/chat")
def chat(req: ChatRequest):
    try:
        return run_conversation(req.message)
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Cannot reach the model server. Is Ollama running?")
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="The model took too long to respond.")
    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Model server returned an error: {e}")
    except Exception:
        logger.exception("Unexpected error in /api/chat")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
