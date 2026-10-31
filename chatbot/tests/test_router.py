"""Routing between the template layer and the LLM (modes llm / template / hybrid)."""
import importlib.util
from pathlib import Path

import pytest
from conftest import FakeDB, QueryError, QueryResult
from fastapi.testclient import TestClient

from secim_chatbot.entities import default_index
from secim_chatbot.llm import FakeLLM
from secim_chatbot.pipeline import NO_TEMPLATE, ChatPipeline
from secim_chatbot.templates import TemplateEngine, TemplateMatch
from secim_chatbot.web.app import create_app

LLM_SQL = "SELECT b.ad AS il, b.katilim FROM birim b WHERE b.seviye = 'il' ORDER BY b.katilim DESC LIMIT 2"
TEMPLATE_Q = "2023 genel seçiminde AK Parti Türkiye genelinde kaç oy aldı?"
ROWS = QueryResult(columns=["aday_parti", "oy", "oran"], rows=[["AK Parti", 19127097, 35.23]])


def engine():
    return TemplateEngine(index=default_index())


def pipe(mode, routes=None, script=None, templates=None):
    llm = FakeLLM(script=script if script is not None else [LLM_SQL] * 4, known=[])
    db = FakeDB(routes=routes if routes is not None else [("AK Parti", ROWS)],
                default=QueryResult(columns=["il", "katilim"], rows=[["Düzce", 92.26]]))
    return ChatPipeline(llm if mode != "template" else None, db, templates=templates or engine(), mode=mode), llm, db


def sql_calls(llm):
    return [c for c in llm.calls if c["step"] == "sql"]


def test_hybrid_template_hit_skips_the_llm():
    p, llm, db = pipe("hybrid")
    r = p.ask(TEMPLATE_Q)
    assert r.status == "ok" and r.route == "template" and r.answered_by == "şablon" and r.template == "ulusal-oy"
    assert llm.calls == []                                       # neither SQL nor answer step
    assert "19.127.097" in r.answer and r.elapsed_ms >= 0
    assert db.executed and "LIMIT" in db.executed[0]             # went through the safety layer
    assert p.name == "hybrid+fake"


def test_hybrid_falls_through_to_llm_when_no_template_fits():
    p, llm, db = pipe("hybrid")
    r = p.ask("Yenişehir'de 2019'da kim kazandı?")              # ambiguous district
    assert r.route == "llm" and r.answered_by == "fake" and r.status == "ok"
    assert len(sql_calls(llm)) == 1


def test_hybrid_falls_through_on_template_db_error_and_on_empty_result():
    p, llm, _ = pipe("hybrid", routes=[("AK Parti", QueryError("[1146] boom"))])
    assert p.ask(TEMPLATE_Q).route == "llm" and len(sql_calls(llm)) == 1
    p, llm, _ = pipe("hybrid", routes=[("AK Parti", QueryResult(columns=["x"], rows=[]))])
    assert p.ask(TEMPLATE_Q).route == "llm"


def test_template_mode_never_calls_an_llm():
    p, _, db = pipe("template")
    assert p.llm is None and p.name == "template"
    r = p.ask(TEMPLATE_Q)
    assert r.route == "template" and r.status == "ok"
    r = p.ask("Galatasaray kaç şampiyonluk kazandı?")
    assert r.status == "refused" and r.route == "none" and r.answer == NO_TEMPLATE and r.answered_by == ""


def test_template_mode_db_error_is_failed_not_fallback():
    p, _, _ = pipe("template", routes=[("AK Parti", QueryError("[2013] lost connection"))])
    r = p.ask(TEMPLATE_Q)
    assert r.status == "failed" and r.route == "template"


def test_rule_based_refusal_does_not_reach_the_llm():
    p, llm, db = pipe("hybrid")
    r = p.ask("2023'te İstanbul'dan seçilen milletvekillerinin isimleri neler?")
    assert r.status == "refused" and r.route == "template" and r.template == "veri-yok"
    assert llm.calls == [] and db.executed == []


def test_llm_mode_ignores_templates():
    p, llm, _ = pipe("llm")
    r = p.ask(TEMPLATE_Q)
    assert r.route == "llm" and len(sql_calls(llm)) == 1 and p.name == "llm:fake"


def test_per_request_mode_override():
    p, llm, _ = pipe("llm")
    assert p.ask(TEMPLATE_Q, mode="hybrid").route == "template"
    assert p.ask(TEMPLATE_Q, mode="template").mode == "template"
    assert p.ask(TEMPLATE_Q, mode="nonsense").route == "llm"      # unknown → the pipeline's own mode


class EvilTemplates:
    """A template layer with a bug must still not be able to run unsafe SQL."""

    def match(self, question, history=None):
        return TemplateMatch("kotu", sql="DELETE FROM oy")


class BrokenTemplates:
    def match(self, question, history=None):
        raise RuntimeError("bug")


def test_unsafe_template_sql_is_never_executed():
    p, llm, db = pipe("hybrid", templates=EvilTemplates())
    r = p.ask("soru")
    assert r.route == "llm" and all("DELETE" not in s for s in db.executed)
    p, _, db = pipe("template", templates=EvilTemplates())
    r = p.ask("soru")
    assert r.status == "failed" and db.executed == []


def test_template_exception_falls_through():
    p, llm, _ = pipe("hybrid", templates=BrokenTemplates())
    assert p.ask("soru").route == "llm"


def test_constructor_validation():
    with pytest.raises(ValueError):
        ChatPipeline(None, FakeDB(), mode="llm")
    with pytest.raises(ValueError):
        ChatPipeline(FakeLLM(known=[]), FakeDB(), mode="hybrid")
    with pytest.raises(ValueError):
        ChatPipeline(FakeLLM(known=[]), FakeDB(), templates=engine(), mode="auto")


def test_api_exposes_modes_and_route():
    p, _, _ = pipe("hybrid")
    c = TestClient(create_app(p))
    h = c.get("/api/health").json()
    assert h["mode"] == "hybrid" and h["modes"] == ["hybrid", "template", "llm"]
    d = c.post("/api/ask", json={"question": TEMPLATE_Q}).json()
    assert d["route"] == "template" and d["answered_by"] == "şablon" and isinstance(d["elapsed_ms"], int)
    d = c.post("/api/ask", json={"question": TEMPLATE_Q, "mode": "llm"}).json()
    assert d["route"] == "llm" and d["answered_by"] == "fake"
    assert c.post("/api/ask", json={"question": "x", "mode": "auto"}).status_code == 422
    tp = TestClient(create_app(pipe("template")[0])).get("/api/health").json()
    assert tp["modes"] == ["template"] and tp["model"] == ""


def test_build_pipeline_modes(monkeypatch):
    from secim_chatbot import build_pipeline
    from secim_chatbot.config import Settings

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    p = build_pipeline(Settings(mode="template"), db=FakeDB())
    assert p.llm is None and p.mode == "template"
    p = build_pipeline(Settings(mode="hybrid", llm_provider="fake"), db=FakeDB())
    assert p.mode == "hybrid" and p.llm.name == "fake" and p.templates is not None


# ---------------------------------------------------------------------------- benchmark runner
def _run_eval():
    spec = importlib.util.spec_from_file_location("run_eval", Path(__file__).resolve().parent.parent / "eval" / "run_eval.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _rec(i, ok, ms, route="llm", answerable="yes", status="ok", cat="il", usage=None):
    return {"id": i, "category": cat, "correct": ok, "answerable": answerable, "route": route, "status": status,
            "retries": 0, "ms": ms, "usage": usage or {}, "data_drift": False}


def test_summary_metrics_and_table(tmp_path):
    ev = _run_eval()
    assert ev.percentile([10, 20, 30, 40, 50, 60, 70, 80, 90, 100], 50) == 50
    assert ev.percentile([10, 20, 30, 40, 50, 60, 70, 80, 90, 100], 95) == 100
    recs = [_rec("a", True, 10, "template"), _rec("b", False, 900, "llm", usage={"input_tokens": 1000, "output_tokens": 100}),
            _rec("c", True, 5, "template", "no", "refused", "veri-yok"), _rec("d", False, 20, "none", status="refused")]
    s = ev.summarize(recs, run="hybrid+anthropic:claude-x", mode="hybrid", provider="anthropic", which="bank",
                     split="test", price_in=3, price_out=15, wall_s=1.0)
    assert s["correct"] == 2 and s["template"] == {"answered": 2, "correct": 2, "share": 0.5}
    assert s["refusal"] == {"correct": 1, "n": 1} and s["false_refusals"] == 1
    assert s["est_cost_usd"] == round((1000 * 3 + 100 * 15) / 1e6, 4)
    t = dict(s, run="template", mode="template", provider="-", est_cost_usd=None)
    path = tmp_path / "runs.json"
    ev.record_run(s, path)
    runs = ev.record_run(t, path)
    md = ev.render_table(runs)
    assert md.index("`template`") < md.index("`hybrid+anthropic:claude-x`")       # stable order
    assert "Soru bankası — test bölümü (n = 4)" in md and "| il |" in md
