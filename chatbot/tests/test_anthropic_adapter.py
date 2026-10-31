"""AnthropicLLM against a stub client: checks the request we send and how responses are parsed."""
from types import SimpleNamespace as NS

from secim_chatbot.db import QueryResult
from secim_chatbot.llm import AnthropicLLM, SqlAttempt, Turn


class StubMessages:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def create(self, **kwargs):
        self.requests.append(kwargs)
        return self.responses.pop(0)


def client(*responses):
    return NS(messages=StubMessages(responses))


def usage(i=1000, o=50, cr=900):
    return NS(input_tokens=i, output_tokens=o, cache_read_input_tokens=cr, cache_creation_input_tokens=0)


def tool_use(name, data):
    return NS(type="tool_use", id="toolu_1", name=name, input=data)


def test_run_sql_tool_call_is_parsed_and_request_is_well_formed():
    c = client(NS(content=[NS(type="text", text="..."), tool_use("run_sql", {"sql": "SELECT 1", "explanation": "x"})],
                  usage=usage()))
    llm = AnthropicLLM(model="claude-test", client=c)
    d = llm.generate_sql("soru?", [], [])
    assert d.sql == "SELECT 1" and d.refusal is None
    assert d.usage.input_tokens == 1000 and d.usage.cache_read_tokens == 900
    req = c.messages.requests[0]
    assert req["model"] == "claude-test"
    assert req["tool_choice"] == {"type": "any"}
    assert {t["name"] for t in req["tools"]} == {"run_sql", "cannot_answer"}
    assert req["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert req["messages"] == [{"role": "user", "content": "soru?"}]


def test_cannot_answer_tool_becomes_refusal():
    c = client(NS(content=[tool_use("cannot_answer", {"reason": "Veri yok."})], usage=usage()))
    d = AnthropicLLM(model="m", client=c).generate_sql("hava?", [], [])
    assert d.sql is None and d.refusal == "Veri yok."


def test_retry_sends_failed_attempt_as_error_tool_result():
    msgs = AnthropicLLM.build_sql_messages("soru", [], [SqlAttempt(sql="SELECT x", error="[1054] Unknown column")])
    assert msgs[1]["role"] == "assistant" and msgs[1]["content"][0]["type"] == "tool_use"
    result = msgs[2]["content"][0]
    assert result["type"] == "tool_result" and result["is_error"] is True
    assert result["tool_use_id"] == msgs[1]["content"][0]["id"]
    assert "Unknown column" in result["content"]


def test_history_turns_precede_question():
    msgs = AnthropicLLM.build_sql_messages("peki 2018?", [Turn("2023 kaç vekil?", "SELECT 1", "268")], [])
    assert [m["role"] for m in msgs] == ["user", "assistant", "user"]
    assert "SELECT 1" in msgs[1]["content"] and msgs[2]["content"] == "peki 2018?"


def test_write_answer_uses_text_blocks_and_includes_result():
    c = client(NS(content=[NS(type="text", text="CHP 31 vekil çıkardı.")], usage=usage(200, 20, 0)))
    llm = AnthropicLLM(model="m", client=c)
    a = llm.write_answer("soru", "SELECT 1", QueryResult(columns=["vekil"], rows=[[31]]))
    assert a.text == "CHP 31 vekil çıkardı."
    assert '"rows": [[31]]' in c.messages.requests[0]["messages"][0]["content"]
