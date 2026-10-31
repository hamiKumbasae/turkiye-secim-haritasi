"""LLM interface and implementations.

`LLM` is a small protocol with two steps:

* `generate_sql` – question (+ earlier conversation turns, + failed attempts) -> SqlDecision
* `write_answer` – question + SQL + result table -> short Turkish answer

`AnthropicLLM` implements it with the official `anthropic` SDK using tool use:
the model must call either `run_sql` or `cannot_answer` (tool_choice = "any"), so the
SQL always arrives as structured JSON, never parsed out of prose. A failed attempt is
sent back as a `tool_result` with `is_error: true`, which is exactly how the API expects
tool errors to be reported, and the model gets one chance to fix its query.

`FakeLLM` is deterministic and needs no network: it answers questions it knows (gold set
+ few-shot examples) and can also be scripted with a queue of decisions for unit tests.
"""
from __future__ import annotations

import difflib
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Protocol

from .db import QueryResult
from .formatting import normalize_question, result_for_prompt, tr_number
from .prompts import (
    ANSWER_SYSTEM_PROMPT,
    CANNOT_ANSWER_TOOL,
    FEW_SHOT,
    RUN_SQL_TOOL,
    SQL_SYSTEM_PROMPT,
)


@dataclass
class Turn:
    """An earlier question in the same chat, used to resolve follow-ups ("peki 2018'de?")."""
    question: str
    sql: str | None = None
    answer: str | None = None


@dataclass
class SqlAttempt:
    sql: str
    error: str


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    def add(self, other: "Usage") -> None:
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.cache_read_tokens += other.cache_read_tokens
        self.cache_write_tokens += other.cache_write_tokens


@dataclass
class SqlDecision:
    sql: str | None = None
    explanation: str = ""
    refusal: str | None = None
    usage: Usage = field(default_factory=Usage)
    error: str | None = None          # the model output could not be parsed; sent back for the one retry


@dataclass
class AnswerText:
    text: str
    usage: Usage = field(default_factory=Usage)


class LLM(Protocol):
    name: str

    def generate_sql(self, question: str, history: list[Turn], attempts: list[SqlAttempt]) -> SqlDecision: ...

    def write_answer(self, question: str, sql: str, result: QueryResult) -> AnswerText: ...


# --------------------------------------------------------------------------- template answer
def template_answer(result: QueryResult) -> str:
    """Deterministic fallback answer (used by FakeLLM and if the answer call fails)."""
    if not result.rows:
        return "Sorgu sonuç döndürmedi; ad yazımını ya da seçim yılını kontrol edin."
    if len(result.rows) == 1:
        parts = [f"{c}: {tr_number(v)}" for c, v in zip(result.columns, result.rows[0])]
        return "Sonuç — " + ", ".join(parts) + "."
    first = ", ".join(f"{c}: {tr_number(v)}" for c, v in zip(result.columns, result.rows[0]))
    more = " (ilk satırlar gösteriliyor)" if result.truncated else ""
    return f"Sorgu {len(result.rows)} satır döndürdü{more}. İlk satır — {first}."


# --------------------------------------------------------------------------- Anthropic
class AnthropicLLM:
    def __init__(self, model: str, api_key: str | None = None, client=None, max_tokens: int = 1024):
        if client is None:
            import anthropic

            client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        self.client = client
        self.model = model
        self.name = f"anthropic:{model}"
        self.max_tokens = max_tokens

    @staticmethod
    def _usage(response) -> Usage:
        u = getattr(response, "usage", None)
        if u is None:
            return Usage()
        return Usage(
            input_tokens=getattr(u, "input_tokens", 0) or 0,
            output_tokens=getattr(u, "output_tokens", 0) or 0,
            cache_read_tokens=getattr(u, "cache_read_input_tokens", 0) or 0,
            cache_write_tokens=getattr(u, "cache_creation_input_tokens", 0) or 0,
        )

    @staticmethod
    def build_sql_messages(question: str, history: list[Turn], attempts: list[SqlAttempt]) -> list[dict]:
        messages: list[dict] = []
        for turn in history[-3:]:
            messages.append({"role": "user", "content": turn.question})
            summary = f"Önceki sorgu:\n{turn.sql}" if turn.sql else "(sorgu üretilmedi)"
            if turn.answer:
                summary += f"\nYanıt: {turn.answer}"
            messages.append({"role": "assistant", "content": summary})
        messages.append({"role": "user", "content": question})
        for i, attempt in enumerate(attempts):
            tool_id = f"toolu_retry_{i}"
            messages.append({
                "role": "assistant",
                "content": [{"type": "tool_use", "id": tool_id, "name": "run_sql",
                             "input": {"sql": attempt.sql, "explanation": "önceki deneme"}}],
            })
            messages.append({
                "role": "user",
                "content": [{"type": "tool_result", "tool_use_id": tool_id, "is_error": True,
                             "content": f"Sorgu başarısız: {attempt.error}\nHatayı düzelterek run_sql'i tekrar çağır."}],
            })
        return messages

    def generate_sql(self, question: str, history: list[Turn], attempts: list[SqlAttempt]) -> SqlDecision:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            # the long, static system prompt is cached: later questions read it at a fraction of the cost
            system=[{"type": "text", "text": SQL_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            tools=[RUN_SQL_TOOL, CANNOT_ANSWER_TOOL],
            tool_choice={"type": "any"},
            messages=self.build_sql_messages(question, history, attempts),
        )
        usage = self._usage(response)
        for block in response.content:
            if getattr(block, "type", None) != "tool_use":
                continue
            data = block.input or {}
            if block.name == "run_sql":
                return SqlDecision(sql=data.get("sql", ""), explanation=data.get("explanation", ""), usage=usage)
            if block.name == "cannot_answer":
                return SqlDecision(refusal=data.get("reason") or "Bu soru yanıtlanamıyor.", usage=usage)
        return SqlDecision(refusal="Model bir sorgu üretmedi.", usage=usage)

    def write_answer(self, question: str, sql: str, result: QueryResult) -> AnswerText:
        content = (
            f"Soru: {question}\n\nÇalıştırılan SQL:\n{sql}\n\n"
            f"Sonuç (JSON):\n{result_for_prompt(result.columns, result.rows, result.truncated)}"
        )
        response = self.client.messages.create(
            model=self.model,
            max_tokens=400,
            system=[{"type": "text", "text": ANSWER_SYSTEM_PROMPT}],
            messages=[{"role": "user", "content": content}],
        )
        text = "".join(getattr(b, "text", "") for b in response.content if getattr(b, "type", "") == "text").strip()
        return AnswerText(text=text or template_answer(result), usage=self._usage(response))


# --------------------------------------------------------------------------- Fake
def _load_known_pairs() -> list[tuple[str, str, str | None]]:
    """(question, verified SQL, human-written answer or None) from few-shot examples + gold set."""
    pairs: list[tuple[str, str, str | None]] = [(ex["question"], ex["sql"], None) for ex in FEW_SHOT]
    gold = Path(__file__).resolve().parent.parent / "eval" / "gold.yaml"
    if gold.exists():
        import yaml

        for item in yaml.safe_load(gold.read_text(encoding="utf-8")) or []:
            pairs.append((item["question"], item["sql"], item.get("expected_answer")))
    return pairs


class FakeLLM:
    """Offline stand-in for the real model.

    * `FakeLLM()` – "demo mode": knows the gold-set and few-shot questions (fuzzy match),
      refuses everything else. Used for the UI demo, screenshots and smoke tests.
    * `FakeLLM(script=[...])` – returns the given SqlDecision objects (or SQL strings) in order;
      used by unit tests to simulate bad SQL, retries and refusals.
    """

    name = "fake"

    def __init__(self, script: Iterable[SqlDecision | str] | None = None,
                 known: list[tuple[str, str, str | None]] | None = None, answers: Iterable[str] | None = None,
                 threshold: float = 0.82):
        self.script = deque(script) if script is not None else None
        self.answers = deque(answers) if answers is not None else None
        self.known = known if known is not None else _load_known_pairs()
        self._index = {normalize_question(k[0]): k for k in self.known}
        self.threshold = threshold
        self.calls: list[dict] = []

    def _lookup(self, question: str) -> tuple | None:
        key = normalize_question(question)
        if key in self._index:
            return self._index[key]
        match = difflib.get_close_matches(key, list(self._index), n=1, cutoff=self.threshold)
        return self._index[match[0]] if match else None

    def generate_sql(self, question: str, history: list[Turn], attempts: list[SqlAttempt]) -> SqlDecision:
        self.calls.append({"step": "sql", "question": question, "attempts": list(attempts)})
        if self.script is not None:
            if not self.script:
                return SqlDecision(refusal="(senaryo bitti)")
            item = self.script.popleft()
            return SqlDecision(sql=item, explanation="senaryo") if isinstance(item, str) else item
        hit = self._lookup(question)
        if hit is None:
            return SqlDecision(refusal=(
                "Demo modundayım (gerçek model bağlı değil): yalnız örnek sorulara yanıt verebiliyorum. "
                "Gerçek yanıtlar için ANTHROPIC_API_KEY tanımlayın."
            ))
        return SqlDecision(sql=hit[1], explanation="Demo: bilinen sorunun doğrulanmış SQL'i.")

    def write_answer(self, question: str, sql: str, result: QueryResult) -> AnswerText:
        self.calls.append({"step": "answer", "question": question, "sql": sql})
        if self.answers:
            return AnswerText(text=self.answers.popleft())
        if self.script is None:
            hit = self._lookup(question)
            if hit and hit[2] and result.rows:
                # demo mode: the hand-written gold answer (verified against the same SQL)
                return AnswerText(text=hit[2])
        return AnswerText(text=template_answer(result))


PROVIDERS = ("anthropic", "claude", "ollama", "fake")


def make_llm(settings) -> LLM:
    provider = (settings.llm_provider or "anthropic").lower()
    if provider not in PROVIDERS:
        raise ValueError(f"LLM_PROVIDER must be one of {PROVIDERS}, got {provider!r}")
    if provider == "ollama":
        from .ollama import OllamaLLM

        return OllamaLLM(model=settings.ollama_model, host=settings.ollama_host,
                         temperature=settings.ollama_temperature, timeout=settings.ollama_timeout_s,
                         num_ctx=settings.ollama_num_ctx, k=settings.fewshot_k,
                         answer_with_model=settings.ollama_answer != "sablon")
    if provider == "fake" or not settings.anthropic_api_key:
        return FakeLLM()
    return AnthropicLLM(model=settings.model, api_key=settings.anthropic_api_key)
