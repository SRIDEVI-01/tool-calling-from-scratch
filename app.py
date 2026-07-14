from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from agent import run_conversation

app = FastAPI()


class ChatRequest(BaseModel):
    message: str


@app.get("/", response_class=HTMLResponse)
def index():
    with open("static/index.html", encoding="utf-8") as f:
        return f.read()


@app.post("/api/chat")
def chat(req: ChatRequest):
    return run_conversation(req.message)
