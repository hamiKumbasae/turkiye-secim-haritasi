"""Question -> SQL -> safety check -> execute -> answer."""
from __future__ import annotations

import logging
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from .db import Database, QueryError, QueryResult
from .llm import LLM, SqlAttempt, Turn, Usage, template_answer
from .safety import UnsafeSQLError, validate_sql

log = logging.getLogger("secim_chatbot")


@dataclass
class ChatResponse:
    question: str
    answer: str
    status: str                       # "ok" | "refused" | "failed"
    sql: str | None = None            # the query that was executed (after the safety layer)
    explanation: str = ""
    columns: list[str] = field(default_factory=list)
    rows: list[list[Any]] = field(default_factory=list)
    truncated: bool = False
    limit_added: bool = False
    attempts: list[dict] = field(default_factory=list)   # failed attempts: {"sql", "error"}
    elapsed_ms: int = 0
    db_ms: int = 0
    model: str = ""
    usage: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class ChatPipeline:
    def __init__(self, llm: LLM, db: Database, max_rows: int = 200, max_attempts: int = 2):
        self.llm = llm
        self.db = db
        self.max_rows = max_rows
        self.max_attempts = max(1, max_attempts)

    def ask(self, question: str, history: list[Turn] | None = None) -> ChatResponse:
        start = time.perf_counter()
        question = (question or "").strip()
        history = history or []
        usage = Usage()
        attempts: list[SqlAttempt] = []

        def done(**kw) -> ChatResponse:
            return ChatResponse(
                question=question, model=self.llm.name, usage=asdict(usage),
                attempts=[asdict(a) for a in attempts],
                elapsed_ms=int((time.perf_counter() - start) * 1000), **kw,
            )

        if not question:
            return done(answer="Lütfen bir soru yazın.", status="refused")
        if len(question) > 1000:
            return done(answer="Soru çok uzun; lütfen 1000 karakterin altında tutun.", status="refused")

        result: QueryResult | None = None
        safe = None
        decision = None
        for _ in range(self.max_attempts):
            try:
                decision = self.llm.generate_sql(question, history, attempts)
            except Exception as e:  # network / auth / rate-limit errors
                log.exception("LLM SQL step failed")
                return done(answer=f"Dil modeline ulaşılamadı: {type(e).__name__}: {e}", status="failed")
            usage.add(decision.usage)
            if decision.refusal:
                return done(answer=decision.refusal, status="refused")
            try:
                safe = validate_sql(decision.sql or "", max_rows=self.max_rows)
                result = self.db.run(safe.sql, self.max_rows)
                break
            except (UnsafeSQLError, QueryError) as e:
                log.info("attempt failed: %s", e)
                attempts.append(SqlAttempt(sql=decision.sql or "", error=str(e)))
                safe = None

        if result is None or safe is None:
            last = attempts[-1] if attempts else None
            return done(
                answer="Bu soru için çalışan bir sorgu üretilemedi. Soruyu biraz farklı sormayı deneyin.",
                status="failed", sql=last.sql if last else None,
            )

        try:
            answer = self.llm.write_answer(question, safe.sql, result)
            usage.add(answer.usage)
            text = answer.text
        except Exception:
            log.exception("LLM answer step failed; using template answer")
            text = template_answer(result)

        return done(
            answer=text, status="ok", sql=safe.sql, explanation=decision.explanation if decision else "",
            columns=result.columns, rows=result.rows, truncated=result.truncated,
            limit_added=safe.limit_added, db_ms=result.elapsed_ms,
        )
