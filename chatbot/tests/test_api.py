from conftest import FakeDB, QueryResult
from fastapi.testclient import TestClient

from secim_chatbot.llm import FakeLLM
from secim_chatbot.pipeline import ChatPipeline
from secim_chatbot.web.app import create_app

SQL = "SELECT b.ad AS il, b.katilim FROM birim b WHERE b.seviye = 'il' ORDER BY b.katilim DESC LIMIT 2"


def client(rate=20, script=None):
    db = FakeDB(default=QueryResult(columns=["il", "katilim"], rows=[["Düzce", 92.26], ["Amasya", 92.15]]))
    llm = FakeLLM(script=script if script is not None else [SQL] * 10, known=[])
    return TestClient(create_app(ChatPipeline(llm, db), rate_per_minute=rate))


def test_index_and_static_served():
    c = client()
    assert "Seçim Sohbeti" in c.get("/").text
    assert c.get("/static/app.js").status_code == 200


def test_health_and_examples():
    c = client()
    h = c.get("/api/health").json()
    assert h["ok"] and h["demo"] and h["db"]
    assert len(c.get("/api/examples").json()["examples"]) >= 4


def test_ask_returns_structured_response():
    r = client().post("/api/ask", json={"question": "Katılım en yüksek il?", "history": []})
    assert r.status_code == 200
    d = r.json()
    assert d["status"] == "ok" and d["columns"] == ["il", "katilim"] and d["rows"][0] == ["Düzce", 92.26]
    assert d["sql"].startswith("SELECT")


def test_validation_errors():
    c = client()
    assert c.post("/api/ask", json={"question": ""}).status_code == 422
    assert c.post("/api/ask", json={"question": "x" * 2000}).status_code == 422


def test_rate_limit():
    c = client(rate=2)
    codes = [c.post("/api/ask", json={"question": "soru"}).status_code for _ in range(3)]
    assert codes == [200, 200, 429]
