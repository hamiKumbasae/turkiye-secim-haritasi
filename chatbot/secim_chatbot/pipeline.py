"""Question -> SQL -> safety check -> execute -> answer.

Routing (`mode`):

* `llm`      – the language model writes the SQL (Claude, Ollama or the offline fake);
* `template` – only the deterministic template layer (templates.py); questions no template fits
               get an honest "no template" refusal;
* `hybrid`   – template first; if no template fits, or the template query fails / returns no rows,
               the question falls through to the LLM.

Template SQL goes through exactly the same safety layer and read-only execution as model SQL.
`ChatResponse.route` says which path answered ("template" | "llm" | "none") and `answered_by`
is the label the UI shows ("şablon" or the model name).
"""
from __future__ import annotations

import logging
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from .db import Database, QueryError, QueryResult
from .llm import LLM, SqlAttempt, Turn, Usage, template_answer
from .safety import UnsafeSQLError, validate_sql

MODES = ("llm", "template", "hybrid")
NO_TEMPLATE = ("Bu soru hazır şablonlardan birine uymadı (şablon modu: dil modeli kullanılmıyor). "
               "Soruyu seçim, yer ve parti adıyla daha açık sormayı deneyin.")

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
    route: str = "llm"                # "template" | "llm" | "none" (template mode, no template fitted)
    answered_by: str = ""             # what the UI shows: "şablon" or the model name
    template: str | None = None       # template id when route == "template"
    mode: str = "llm"

    def to_dict(self) -> dict:
        return asdict(self)


class ChatPipeline:
    def __init__(self, llm: LLM | None, db: Database, max_rows: int = 200, max_attempts: int = 2,
                 templates=None, mode: str = "llm"):
        if mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}")
        if mode in ("template", "hybrid") and templates is None:
            raise ValueError(f"mode={mode} needs a TemplateEngine")
        if mode in ("llm", "hybrid") and llm is None:
            raise ValueError(f"mode={mode} needs an LLM")
        self.llm = llm
        self.db = db
        self.max_rows = max_rows
        self.max_attempts = max(1, max_attempts)
        self.templates = templates
        self.mode = mode

    @property
    def name(self) -> str:
        """Run label: 'template', 'llm:anthropic:claude-…', 'hybrid+ollama:qwen2.5-coder:7b'."""
        if self.mode == "template":
            return "template"
        return f"{'hybrid+' if self.mode == 'hybrid' else 'llm:'}{self.llm.name}"

    def ask(self, question: str, history: list[Turn] | None = None, mode: str | None = None) -> ChatResponse:
        start = time.perf_counter()
        question = (question or "").strip()
        history = history or []
        mode = mode or self.mode
        if mode not in MODES or (mode != "llm" and self.templates is None) or (mode != "template" and self.llm is None):
            mode = self.mode
        usage = Usage()
        attempts: list[SqlAttempt] = []
        llm_name = self.llm.name if self.llm is not None else ""

        def done(route: str = "llm", **kw) -> ChatResponse:
            by = "şablon" if route == "template" else (llm_name if route == "llm" else "")
            return ChatResponse(
                question=question, model=by or llm_name or "şablon", usage=asdict(usage),
                attempts=[asdict(a) for a in attempts], route=route, answered_by=by, mode=mode,
                elapsed_ms=int((time.perf_counter() - start) * 1000), **kw,
            )

        if not question:
            return done(answer="Lütfen bir soru yazın.", status="refused", route="none")
        if len(question) > 1000:
            return done(answer="Soru çok uzun; lütfen 1000 karakterin altında tutun.", status="refused", route="none")

        if mode in ("template", "hybrid"):
            hit = self._try_template(question, history, done, fallback=mode == "hybrid")
            if hit is not None:
                return hit
            if mode == "template":
                return done(answer=NO_TEMPLATE, status="refused", route="none")

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
            if decision.error:                       # unparsable model output: feed the error back once
                attempts.append(SqlAttempt(sql=decision.sql or "", error=decision.error))
                continue
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

    # ------------------------------------------------------------------ template path
    def _try_template(self, question, history, done, fallback: bool):
        """Run the template layer. Returns a response, or None to fall through to the LLM / 'no template'."""
        try:
            hit = self.templates.match(question, history)
        except Exception:  # a template bug must never break the chat
            log.exception("template layer failed")
            return None
        if hit is None:
            return None
        if hit.refusal:
            return done(answer=hit.refusal, status="refused", route="template", template=hit.template,
                        explanation=hit.explanation)
        try:
            safe = validate_sql(hit.sql or "", max_rows=self.max_rows)
            result = self.db.run(safe.sql, self.max_rows)
        except (UnsafeSQLError, QueryError) as e:
            log.warning("template %s failed: %s", hit.template, e)
            if fallback:
                return None
            return done(answer="Şablon sorgusu çalıştırılamadı.", status="failed", route="template",
                        template=hit.template, sql=hit.sql)
        if not result.rows:
            if fallback:
                return None                    # maybe a name the template misread: let the model try
            return done(answer="Veride bu soru için kayıt yok (ör. o seçimde bu birim ya da yurt dışı sonucu yok).",
                        status="refused", route="template", template=hit.template, sql=safe.sql,
                        explanation=hit.explanation, db_ms=result.elapsed_ms)
        return done(
            answer=hit.answer(result), status="ok", route="template", template=hit.template, sql=safe.sql,
            explanation=hit.explanation, columns=result.columns, rows=result.rows, truncated=result.truncated,
            limit_added=safe.limit_added, db_ms=result.elapsed_ms,
        )
