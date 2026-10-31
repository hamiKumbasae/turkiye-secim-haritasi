from conftest import FakeDB, QueryError, QueryResult

from secim_chatbot.llm import FakeLLM, SqlDecision, Turn, Usage
from secim_chatbot.pipeline import ChatPipeline

GOOD = "SELECT o.vekil FROM oy o JOIN birim b ON b.id = o.birim_id WHERE b.plaka = 34"
RESULT = QueryResult(columns=["vekil"], rows=[[31]])


def make(script, routes=None, answers=None, **kw):
    llm = FakeLLM(script=script, known=[], answers=answers)
    db = FakeDB(routes=routes or [("vekil", RESULT)])
    return ChatPipeline(llm, db, **kw), llm, db


def test_happy_path_returns_answer_sql_and_table():
    pipe, llm, db = make([GOOD], answers=["CHP İstanbul'dan 31 milletvekili çıkardı."])
    r = pipe.ask("2023'te CHP İstanbul'dan kaç vekil çıkardı?")
    assert r.status == "ok"
    assert r.answer.startswith("CHP")
    assert r.columns == ["vekil"] and r.rows == [[31]]
    assert "LIMIT" in r.sql                      # safety layer added a LIMIT
    assert r.limit_added and r.attempts == []
    assert db.executed == [r.sql]                # exactly the validated SQL was executed
    assert [c["step"] for c in llm.calls] == ["sql", "answer"]


def test_unsafe_sql_is_never_executed_and_model_retries():
    pipe, llm, db = make(["DELETE FROM oy", GOOD])
    r = pipe.ask("soru")
    assert r.status == "ok"
    assert len(r.attempts) == 1 and "SELECT" in r.attempts[0]["error"]
    assert all("DELETE" not in s for s in db.executed)
    # the second SQL call saw the failed attempt (this is what is sent back to the model)
    second = [c for c in llm.calls if c["step"] == "sql"][1]
    assert second["attempts"][0].sql == "DELETE FROM oy"


def test_db_error_triggers_one_retry_with_error_message():
    bad = "SELECT nope FROM birim"
    pipe, llm, db = make([bad, GOOD], routes=[("nope", QueryError("[1054] Unknown column 'nope'")), ("vekil", RESULT)])
    r = pipe.ask("soru")
    assert r.status == "ok"
    assert "Unknown column" in r.attempts[0]["error"]
    assert len(db.executed) == 2


def test_gives_up_after_max_attempts():
    pipe, llm, db = make(["DROP TABLE oy", "DROP TABLE birim", GOOD], max_attempts=2)
    r = pipe.ask("soru")
    assert r.status == "failed"
    assert len(r.attempts) == 2
    assert db.executed == []
    assert r.rows == []


def test_refusal_is_passed_through():
    pipe, _, db = make([SqlDecision(refusal="Bu veritabanında hava durumu yok.")])
    r = pipe.ask("Yarın hava nasıl?")
    assert r.status == "refused" and "hava" in r.answer
    assert db.executed == []


def test_llm_exception_becomes_failed_response():
    class Boom(FakeLLM):
        def generate_sql(self, *a, **k):
            raise ConnectionError("ağ yok")

    pipe = ChatPipeline(Boom(known=[]), FakeDB())
    r = pipe.ask("soru")
    assert r.status == "failed" and "ağ yok" in r.answer


def test_answer_step_failure_falls_back_to_template():
    class NoAnswer(FakeLLM):
        def write_answer(self, *a, **k):
            raise TimeoutError

    pipe = ChatPipeline(NoAnswer(script=[GOOD], known=[]), FakeDB(routes=[("vekil", RESULT)]))
    r = pipe.ask("soru")
    assert r.status == "ok" and "31" in r.answer


def test_empty_and_too_long_questions():
    pipe, _, db = make([GOOD])
    assert pipe.ask("   ").status == "refused"
    assert pipe.ask("x" * 1001).status == "refused"
    assert db.executed == []


def test_history_is_forwarded_to_llm():
    seen = {}

    class Spy(FakeLLM):
        def generate_sql(self, question, history, attempts):
            seen["history"] = history
            return SqlDecision(sql=GOOD)

    pipe = ChatPipeline(Spy(known=[]), FakeDB(routes=[("vekil", RESULT)]))
    pipe.ask("peki 2018'de?", [Turn(question="2023'te kaç vekil?", sql=GOOD)])
    assert seen["history"][0].question == "2023'te kaç vekil?"


def test_usage_is_accumulated_over_retries():
    pipe, _, _ = make([SqlDecision(sql="DELETE FROM oy", usage=Usage(100, 10)), SqlDecision(sql=GOOD, usage=Usage(120, 12))])
    r = pipe.ask("soru")
    assert r.usage["input_tokens"] == 220 and r.usage["output_tokens"] == 22


def test_demo_mode_fake_knows_gold_questions_with_fuzzy_match():
    llm = FakeLLM()
    d = llm.generate_sql("2023'te CHP İstanbul'dan kaç milletvekili çıkardı", [], [])  # no '?'
    assert d.sql and "plaka = 34" in d.sql
    assert llm.generate_sql("Galatasaray kaç şampiyonluk kazandı?", [], []).refusal
