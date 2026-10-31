"""OllamaLLM against a local mock of Ollama's /api/chat (no Ollama needed)."""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from conftest import FakeDB, QueryResult

from secim_chatbot.fewshot import FewShotRetriever, load_pool
from secim_chatbot.llm import SqlAttempt, Turn
from secim_chatbot.ollama import OllamaError, OllamaLLM, parse_model_output
from secim_chatbot.pipeline import ChatPipeline
from secim_chatbot.prompts import OLLAMA_OUTPUT_SCHEMA

GOOD_SQL = "SELECT o.vekil FROM oy o JOIN birim b ON b.id = o.birim_id WHERE b.plaka = 34"


class MockOllama:
    """Serves queued responses: dict → JSON body, ('sleep', s) → delay, ('http', code, body) → error."""

    def __init__(self):
        self.queue: list = []
        self.requests: list[dict] = []
        mock = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                mock.requests.append({"path": self.path, "body": body})
                item = mock.queue.pop(0) if mock.queue else {"message": {"content": "{}"}}
                if isinstance(item, tuple) and item[0] == "sleep":
                    time.sleep(item[1])
                    item = {"message": {"content": "{}"}}
                if isinstance(item, tuple) and item[0] == "http":
                    self.send_response(item[1])
                    self.end_headers()
                    self.wfile.write(json.dumps(item[2]).encode())
                    return
                data = json.dumps(item).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                try:
                    self.wfile.write(data)
                except BrokenPipeError:
                    pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def reply(self, content: str, prompt_tokens=1200, out_tokens=40):
        self.queue.append({"model": "m", "message": {"role": "assistant", "content": content}, "done": True,
                           "prompt_eval_count": prompt_tokens, "eval_count": out_tokens})

    def close(self):
        self.server.shutdown()


@pytest.fixture
def ollama():
    m = MockOllama()
    yield m
    m.close()


@pytest.fixture(scope="module")
def retriever():
    return FewShotRetriever()


def make(ollama, retriever, **kw):
    return OllamaLLM(model="qwen2.5-coder:7b", host=ollama.url, retriever=retriever, **kw)


# ---------------------------------------------------------------------------- success
def test_request_shape_and_successful_sql(ollama, retriever):
    ollama.reply(json.dumps({"action": "run_sql", "sql": GOOD_SQL, "explanation": "İstanbul vekilleri"}))
    llm = make(ollama, retriever, temperature=0.1, num_ctx=6144, k=3)
    d = llm.generate_sql("2023'te CHP İstanbul'dan kaç milletvekili çıkardı?", [], [])
    assert d.sql == GOOD_SQL and d.refusal is None and d.error is None
    assert d.usage.input_tokens == 1200 and d.usage.output_tokens == 40

    req = ollama.requests[0]
    assert req["path"] == "/api/chat"
    body = req["body"]
    assert body["model"] == "qwen2.5-coder:7b" and body["stream"] is False
    assert body["format"] == OLLAMA_OUTPUT_SCHEMA                    # structured JSON output
    assert body["options"]["temperature"] == 0.1 and body["options"]["num_ctx"] == 6144
    msgs = body["messages"]
    assert msgs[0]["role"] == "system" and "Türkiye geneli" in msgs[0]["content"]
    # 3 retrieved examples as user/assistant pairs, then the question
    assert [m["role"] for m in msgs[1:7]] == ["user", "assistant"] * 3
    assert msgs[-1] == {"role": "user", "content": "2023'te CHP İstanbul'dan kaç milletvekili çıkardı?"}
    assert json.loads(msgs[2]["content"])["action"] in ("run_sql", "cannot_answer")


def test_few_shot_examples_come_from_dev_split_only(ollama, retriever):
    import yaml

    from secim_chatbot.fewshot import BANK

    test_q = {b["question"] for b in yaml.safe_load(BANK.read_text(encoding="utf-8")) if b["split"] == "test"}
    ollama.reply(json.dumps({"action": "run_sql", "sql": GOOD_SQL}))
    make(ollama, retriever, k=6).generate_sql("2017 referandumunda Kadıköy'de Hayır oranı?", [], [])
    shots = [m["content"] for m in ollama.requests[0]["body"]["messages"][1:-1] if m["role"] == "user"]
    assert len(shots) == 6 and not set(shots) & test_q


def test_refusal(ollama, retriever):
    ollama.reply('{"action": "cannot_answer", "reason": "Sandık sonuçları veride yok."}')
    d = make(ollama, retriever).generate_sql("Sandık sonuçları?", [], [])
    assert d.refusal == "Sandık sonuçları veride yok." and d.sql is None


def test_history_and_retry_are_sent_as_turns(ollama, retriever):
    ollama.reply(json.dumps({"action": "run_sql", "sql": GOOD_SQL}))
    llm = make(ollama, retriever, k=1)
    llm.generate_sql("peki 2018'de?", [Turn("2023'te kaç vekil?", sql="SELECT 1")],
                     [SqlAttempt(sql="SELECT nope FROM birim", error="[1054] Unknown column 'nope'")])
    msgs = ollama.requests[0]["body"]["messages"]
    assert {"role": "user", "content": "2023'te kaç vekil?"} in msgs
    assert msgs[-2]["role"] == "assistant" and "nope" in msgs[-2]["content"]
    assert msgs[-1]["role"] == "user" and "Unknown column" in msgs[-1]["content"]


def test_answer_step_uses_plain_chat_and_template_option(ollama, retriever):
    ollama.reply("CHP İstanbul'dan 31 milletvekili çıkardı.")
    res = QueryResult(columns=["vekil"], rows=[[31]])
    a = make(ollama, retriever).write_answer("soru", GOOD_SQL, res)
    assert a.text.startswith("CHP") and "format" not in ollama.requests[0]["body"]
    b = make(ollama, retriever, answer_with_model=False).write_answer("soru", GOOD_SQL, res)
    assert "31" in b.text and len(ollama.requests) == 1                  # no second HTTP call


# ---------------------------------------------------------------------------- malformed output
@pytest.mark.parametrize("content,expected", [
    ('```json\n{"action": "run_sql", "sql": "SELECT 1"}\n```', "SELECT 1"),
    ('Tabii! İşte sorgu: {"action": "run_sql", "sql": "SELECT 2;"} umarım yardımcı olur', "SELECT 2"),
    ('{"action": "run_sql", "sql": "```sql\\nSELECT 3\\n```"}', "SELECT 3"),
    ("```sql\nSELECT b.ad FROM birim b\n```", "SELECT b.ad FROM birim b"),
    ("Sorgu şu: SELECT 4", "SELECT 4"),
    ('{"sql": "SELECT 5"}', "SELECT 5"),
])
def test_parser_recovers_sql(content, expected):
    d = parse_model_output(content)
    assert d.sql == expected and d.error is None


@pytest.mark.parametrize("content", ["", "Bilmiyorum.", '{"action": "run_sql", "sql": ""}', "{not json"])
def test_parser_reports_unusable_output(content):
    d = parse_model_output(content)
    assert d.sql in (None, "") and d.error


def test_malformed_output_gets_one_retry_in_pipeline(ollama, retriever):
    ollama.reply("Üzgünüm, anlayamadım.")                               # no JSON, no SQL
    ollama.reply(json.dumps({"action": "run_sql", "sql": GOOD_SQL}))
    db = FakeDB(routes=[("vekil", QueryResult(columns=["vekil"], rows=[[31]]))])
    pipe = ChatPipeline(make(ollama, retriever, answer_with_model=False), db)
    r = pipe.ask("2023'te CHP İstanbul'dan kaç milletvekili çıkardı?")
    assert r.status == "ok" and r.rows == [[31]]
    assert len(r.attempts) == 1 and "JSON" in r.attempts[0]["error"]
    assert "JSON" in ollama.requests[1]["body"]["messages"][-1]["content"]   # the error went back to the model
    assert r.answered_by == "ollama:qwen2.5-coder:7b" and r.route == "llm"


def test_unsafe_model_sql_is_rejected_then_retried(ollama, retriever):
    ollama.reply(json.dumps({"action": "run_sql", "sql": "DELETE FROM oy"}))
    ollama.reply(json.dumps({"action": "run_sql", "sql": GOOD_SQL}))
    db = FakeDB(routes=[("vekil", QueryResult(columns=["vekil"], rows=[[31]]))])
    r = ChatPipeline(make(ollama, retriever, answer_with_model=False), db).ask("soru")
    assert r.status == "ok" and all("DELETE" not in s for s in db.executed)


# ---------------------------------------------------------------------------- failures
def test_timeout(ollama, retriever):
    ollama.queue.append(("sleep", 1.5))
    llm = make(ollama, retriever, timeout=0.3)
    with pytest.raises(OllamaError, match="yanıt vermedi"):
        llm.generate_sql("soru", [], [])
    # in the pipeline a timeout is a clean 'failed' answer, nothing executed
    ollama.queue.append(("sleep", 1.5))
    db = FakeDB()
    r = ChatPipeline(llm, db).ask("soru")
    assert r.status == "failed" and "yanıt vermedi" in r.answer and db.executed == []


def test_model_not_pulled(ollama, retriever):
    ollama.queue.append(("http", 404, {"error": "model 'qwen2.5-coder:14b' not found"}))
    with pytest.raises(OllamaError, match="ollama pull qwen2.5-coder:7b"):
        make(ollama, retriever).generate_sql("soru", [], [])


def test_server_down(retriever):
    llm = OllamaLLM(host="http://127.0.0.1:9", retriever=retriever, timeout=2)
    with pytest.raises(OllamaError, match="ulaşılamadı"):
        llm.generate_sql("soru", [], [])


def test_settings_and_factory(monkeypatch):
    from secim_chatbot.config import Settings
    from secim_chatbot.llm import make_llm

    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen2.5-coder:14b")
    monkeypatch.setenv("OLLAMA_HOST", "192.168.1.5:11434")
    monkeypatch.setenv("OLLAMA_TIMEOUT", "30")
    monkeypatch.setenv("OLLAMA_TEMPERATURE", "0.2")
    llm = make_llm(Settings())
    assert isinstance(llm, OllamaLLM) and llm.name == "ollama:qwen2.5-coder:14b"
    assert llm.host == "http://192.168.1.5:11434" and llm.timeout == 30 and llm.temperature == 0.2
    monkeypatch.setenv("LLM_PROVIDER", "gpt")
    with pytest.raises(ValueError):
        make_llm(Settings())


def test_pool_is_dev_only():
    pool = load_pool()
    ids = {e.id for e in pool}
    assert any(i.startswith("fs") for i in ids) and any(i.startswith("b") for i in ids)
    import yaml

    from secim_chatbot.fewshot import BANK

    test_ids = {b["id"] for b in yaml.safe_load(BANK.read_text(encoding="utf-8")) if b["split"] == "test"}
    assert not ids & test_ids
