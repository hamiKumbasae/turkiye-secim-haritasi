"""FastAPI backend for the chat UI.

    uvicorn secim_chatbot.web.app:app --port 8000          # real model (ANTHROPIC_API_KEY)
    LLM_PROVIDER=fake uvicorn secim_chatbot.web.app:app      # demo mode, no key needed
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .. import build_pipeline, get_settings
from ..llm import Turn
from ..pipeline import ChatPipeline
from ..prompts import EXAMPLE_QUESTIONS

STATIC = Path(__file__).resolve().parent / "static"
log = logging.getLogger("secim_chatbot.web")


class HistoryItem(BaseModel):
    question: str = Field(max_length=1000)
    sql: str | None = Field(default=None, max_length=8000)
    answer: str | None = Field(default=None, max_length=4000)


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    history: list[HistoryItem] = Field(default_factory=list, max_length=10)


class RateLimiter:
    """Tiny in-memory limiter (per client IP) so a public demo cannot burn the API budget."""

    def __init__(self, per_minute: int = 20):
        self.per_minute = per_minute
        self.hits: dict[str, deque] = defaultdict(deque)

    def check(self, key: str) -> bool:
        now = time.monotonic()
        q = self.hits[key]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= self.per_minute:
            return False
        q.append(now)
        return True


def create_app(pipeline: ChatPipeline | None = None, rate_per_minute: int = 20) -> FastAPI:
    app = FastAPI(title="Seçim Sohbet Botu", version="0.1.0")
    state = {"pipeline": pipeline}
    limiter = RateLimiter(rate_per_minute)

    def get_pipeline() -> ChatPipeline:
        if state["pipeline"] is None:
            state["pipeline"] = build_pipeline(get_settings())
        return state["pipeline"]

    @app.get("/api/health")
    def health():
        pipe = get_pipeline()
        db_ok = pipe.db.ping() if hasattr(pipe.db, "ping") else True
        return {"ok": True, "model": pipe.llm.name, "demo": pipe.llm.name == "fake", "db": db_ok}

    @app.get("/api/examples")
    def examples():
        return {"examples": EXAMPLE_QUESTIONS}

    @app.post("/api/ask")
    def ask(req: AskRequest, request: Request):
        client = request.client.host if request.client else "?"
        if not limiter.check(client):
            raise HTTPException(status_code=429, detail="Çok fazla istek; bir dakika sonra tekrar deneyin.")
        history = [Turn(question=h.question, sql=h.sql, answer=h.answer) for h in req.history]
        resp = get_pipeline().ask(req.question, history)
        log.info("ask status=%s ms=%s q=%r", resp.status, resp.elapsed_ms, req.question[:80])
        return resp.to_dict()

    @app.get("/")
    def index():
        return FileResponse(STATIC / "index.html")

    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    return app


app = create_app()
