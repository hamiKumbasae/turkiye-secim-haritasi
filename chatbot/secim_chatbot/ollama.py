"""Local LLM provider: Ollama (https://ollama.com) over its HTTP API.

    LLM_PROVIDER=ollama OLLAMA_MODEL=qwen2.5-coder:7b python -m secim_chatbot.cli

Implements the same `LLM` protocol as AnthropicLLM, so the pipeline, the safety layer and the
one-retry-on-error loop are unchanged.

* `POST {OLLAMA_HOST}/api/chat` with `stream: false` and a JSON-schema `format`, which makes Ollama
  constrain decoding to {"action": "run_sql" | "cannot_answer", "sql", "explanation", "reason"}.
* Prompt for small models (prompts.OLLAMA_SQL_SYSTEM): compact schema + the domain pitfalls, then the
  k most similar solved examples from the dev split (fewshot.py) as earlier user/assistant turns.
* The output is still parsed defensively (code fences, prose around the JSON, SQL without JSON),
  because older Ollama versions ignore `format` schemas and small models sometimes wrap their answer.
  Output that yields no SQL becomes `SqlDecision(error=...)`, which the pipeline feeds back once.
* `num_ctx` is set explicitly: Ollama's default context (2–4k tokens) silently truncates the prompt.

Standard library only (urllib); the proxy environment is ignored because Ollama runs locally.
"""
from __future__ import annotations

import json
import re
import socket
import urllib.error
import urllib.request

from .db import QueryResult
from .fewshot import FewShotRetriever
from .formatting import result_for_prompt
from .llm import AnswerText, SqlAttempt, SqlDecision, Turn, Usage, template_answer
from .prompts import ANSWER_SYSTEM_PROMPT, OLLAMA_OUTPUT_SCHEMA, OLLAMA_SQL_SYSTEM


class OllamaError(RuntimeError):
    """Ollama unreachable, timed out or returned an HTTP error (the pipeline reports it as 'failed')."""


_FENCE = re.compile(r"```(?:json|sql|mysql)?\s*(.*?)```", re.S | re.I)
_SQL_START = re.compile(r"\b(WITH|SELECT)\b", re.I)


def clean_sql(sql: str) -> str:
    sql = (sql or "").strip()
    m = _FENCE.search(sql)
    if m:
        sql = m.group(1).strip()
    sql = re.sub(r"^(sql|SQL)\s*:\s*", "", sql)
    return sql.strip().rstrip(";").strip()


def _first_json_object(text: str) -> dict | None:
    dec = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch == "{":
            try:
                obj, _ = dec.raw_decode(text[i:])
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                return obj
    return None


def parse_model_output(text: str) -> SqlDecision:
    """Turn whatever the model wrote into a SqlDecision (sql / refusal / error)."""
    raw = (text or "").strip()
    if not raw:
        return SqlDecision(error="Model boş yanıt döndürdü. Yalnız istenen JSON'u döndür.")
    body = raw
    m = _FENCE.search(raw)
    if m and "{" in m.group(1):
        body = m.group(1)
    obj = None
    try:
        obj = json.loads(body)
    except json.JSONDecodeError:
        obj = _first_json_object(body)
    if isinstance(obj, dict):
        action = str(obj.get("action", "")).lower()
        sql = clean_sql(str(obj.get("sql") or obj.get("query") or ""))
        if action == "cannot_answer" or (not sql and obj.get("reason")):
            return SqlDecision(refusal=str(obj.get("reason") or "Bu soru veritabanıyla yanıtlanamıyor."))
        if sql:
            return SqlDecision(sql=sql, explanation=str(obj.get("explanation") or ""))
        return SqlDecision(error="JSON'da 'sql' alanı boş. run_sql için dolu bir SELECT sorgusu yaz.")
    # no JSON at all: accept a fenced or bare SELECT
    sql = clean_sql(raw) if m else ""
    if not _SQL_START.match(sql or ""):
        start = _SQL_START.search(raw)
        sql = clean_sql(raw[start.start():]) if start else ""
    if sql and _SQL_START.match(sql):
        return SqlDecision(sql=sql, explanation="")
    return SqlDecision(error=f"Yanıt geçerli JSON değildi ve sorgu içermiyordu: {raw[:200]!r}. "
                             "Yalnız {\"action\": ..., \"sql\": ...} biçiminde JSON döndür.")


class OllamaLLM:
    def __init__(self, model: str = "qwen2.5-coder:7b", host: str = "http://localhost:11434",
                 temperature: float = 0.0, timeout: float = 120.0, num_ctx: int = 8192, k: int = 4,
                 retriever: FewShotRetriever | None = None, answer_with_model: bool = True, keep_alive: str = "30m"):
        self.model = model
        self.host = host.rstrip("/")
        if not self.host.startswith(("http://", "https://")):
            self.host = "http://" + self.host
        self.temperature = temperature
        self.timeout = timeout
        self.num_ctx = num_ctx
        self.k = k
        self._retriever = retriever
        self.answer_with_model = answer_with_model
        self.keep_alive = keep_alive
        self.name = f"ollama:{model}"
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    @property
    def retriever(self) -> FewShotRetriever:
        if self._retriever is None:
            self._retriever = FewShotRetriever()
        return self._retriever

    # ------------------------------------------------------------------ HTTP
    def _chat(self, messages: list[dict], fmt=None, num_predict: int = 512) -> tuple[str, Usage]:
        payload = {
            "model": self.model, "messages": messages, "stream": False, "keep_alive": self.keep_alive,
            "options": {"temperature": self.temperature, "num_ctx": self.num_ctx, "num_predict": num_predict},
        }
        if fmt is not None:
            payload["format"] = fmt
        req = urllib.request.Request(f"{self.host}/api/chat", data=json.dumps(payload).encode("utf-8"),
                                     headers={"Content-Type": "application/json"}, method="POST")
        try:
            with self._opener.open(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            hint = f" — modeli indirin: ollama pull {self.model}" if e.code == 404 else ""
            raise OllamaError(f"Ollama HTTP {e.code}: {detail}{hint}") from e
        except (socket.timeout, TimeoutError) as e:
            raise OllamaError(f"Ollama {self.timeout:g} sn içinde yanıt vermedi (OLLAMA_TIMEOUT).") from e
        except urllib.error.URLError as e:
            if isinstance(e.reason, (socket.timeout, TimeoutError)):
                raise OllamaError(f"Ollama {self.timeout:g} sn içinde yanıt vermedi (OLLAMA_TIMEOUT).") from e
            raise OllamaError(f"Ollama'ya ulaşılamadı ({self.host}): {e.reason}. `ollama serve` çalışıyor mu?") from e
        except json.JSONDecodeError as e:
            raise OllamaError("Ollama geçersiz JSON döndürdü.") from e
        if "error" in data:
            raise OllamaError(f"Ollama: {data['error']}")
        content = ((data.get("message") or {}).get("content")) or ""
        usage = Usage(input_tokens=int(data.get("prompt_eval_count") or 0), output_tokens=int(data.get("eval_count") or 0))
        return content, usage

    # ------------------------------------------------------------------ prompt
    def build_sql_messages(self, question: str, history: list[Turn], attempts: list[SqlAttempt]) -> list[dict]:
        messages = [{"role": "system", "content": OLLAMA_SQL_SYSTEM}]
        for _, ex in self.retriever.top(question, self.k):
            messages.append({"role": "user", "content": ex.question})
            out = ({"action": "run_sql", "sql": ex.sql, "explanation": ""} if ex.sql
                   else {"action": "cannot_answer", "reason": ex.refusal})
            messages.append({"role": "assistant", "content": json.dumps(out, ensure_ascii=False)})
        for turn in history[-3:]:
            messages.append({"role": "user", "content": turn.question})
            prev = {"action": "run_sql", "sql": turn.sql} if turn.sql else {"action": "cannot_answer", "reason": turn.answer or ""}
            messages.append({"role": "assistant", "content": json.dumps(prev, ensure_ascii=False)})
        messages.append({"role": "user", "content": question})
        for a in attempts:
            messages.append({"role": "assistant",
                             "content": json.dumps({"action": "run_sql", "sql": a.sql}, ensure_ascii=False)})
            messages.append({"role": "user", "content": f"Sorgu başarısız: {a.error}\nHatayı düzelt ve yalnız JSON döndür."})
        return messages

    # ------------------------------------------------------------------ LLM protocol
    def generate_sql(self, question: str, history: list[Turn], attempts: list[SqlAttempt]) -> SqlDecision:
        content, usage = self._chat(self.build_sql_messages(question, history, attempts), fmt=OLLAMA_OUTPUT_SCHEMA)
        decision = parse_model_output(content)
        decision.usage = usage
        return decision

    def write_answer(self, question: str, sql: str, result: QueryResult) -> AnswerText:
        if not self.answer_with_model:
            return AnswerText(text=template_answer(result))
        content = (f"Soru: {question}\n\nÇalıştırılan SQL:\n{sql}\n\n"
                   f"Sonuç (JSON):\n{result_for_prompt(result.columns, result.rows, result.truncated, max_rows=30)}")
        text, usage = self._chat([{"role": "system", "content": ANSWER_SYSTEM_PROMPT},
                                  {"role": "user", "content": content}], num_predict=300)
        return AnswerText(text=text.strip() or template_answer(result), usage=usage)
