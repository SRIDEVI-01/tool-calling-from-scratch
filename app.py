import logging
import os
from typing import Optional

import requests
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from agent import run_conversation

app = FastAPI()
logger = logging.getLogger("uvicorn.error")

# Set the API_KEY env var to require an X-API-Key header on /api/chat before
# exposing this app on a public address (e.g. a RunPod proxy URL). Left
# unset, the endpoint is open — fine behind an SSH tunnel, not otherwise.
API_KEY = os.environ.get("API_KEY")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


@app.get("/", response_class=HTMLResponse)
def index():
    with open("static/index.html", encoding="utf-8") as f:
        return f.read()


@app.post("/api/chat")
def chat(req: ChatRequest, x_api_key: Optional[str] = Header(None)):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Missing or invalid X-API-Key header.")
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
