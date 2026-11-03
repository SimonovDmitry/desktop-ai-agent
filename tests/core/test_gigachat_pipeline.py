import sys
from types import SimpleNamespace

from deskagent.agent.llm.config import LLMConfig
from deskagent.agent.llm.factory import create_llm
from scripts import _common
from scripts._common import resolve_llm
from scripts.run_llm import create_parser


class FakeMessage:
    content = "done"
    tool_calls = [{"id": "call-1", "name": "get_status", "args": {"full": True}}]
    response_metadata = {"finish_reason": "tool_calls"}


class FakeGigaChat:
    def __init__(self, **options):
        self.options = options
        self.tools = None

    def bind_tools(self, tools):
        self.tools = tools
        return self

    def invoke(self, messages):
        self.messages = messages
        return FakeMessage()

    def stream(self, messages):
        yield SimpleNamespace(content="one")
        yield SimpleNamespace(content="")
        yield SimpleNamespace(content="two")


def test_resolve_gigachat_from_dotenv(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text(
        "GIGACHAT_CREDENTIALS=test-credentials\n"
        "GIGACHAT_SCOPE=GIGACHAT_API_PERS\n"
        "GIGACHAT_MODEL=GigaChat-Test\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(_common, "ENV_FILE", tmp_path / ".env")
    for name in ("GIGACHAT_CREDENTIALS", "GIGACHAT_SCOPE", "GIGACHAT_MODEL"):
        monkeypatch.delenv(name, raising=False)

    args = create_parser().parse_args(["hello", "--provider", "gigachat"])
    _, config = resolve_llm(args)

    assert config.provider == "gigachat"
    assert config.model == "GigaChat-Test"
    assert config.api_key == "test-credentials"
    assert config.api_scope == "GIGACHAT_API_PERS"
    assert config.manage_runtime is False
    assert config.base_url == ""


def test_local_ollama_pipeline_remains_available():
    args = create_parser().parse_args(
        ["hello", "--provider", "ollama", "--model", "qwen3:4b", "--no-start"]
    )

    _, config = resolve_llm(args)

    assert config.provider == "ollama"
    assert config.model == "qwen3:4b"
    assert config.manage_runtime is True
    assert config.auto_start is False


def test_gigachat_provider_supports_tools_and_streaming(monkeypatch):
    monkeypatch.delenv("GIGACHAT_CA_BUNDLE_FILE", raising=False)
    monkeypatch.setitem(sys.modules, "langchain_gigachat", SimpleNamespace(GigaChat=FakeGigaChat))
    config = LLMConfig(
        provider="gigachat",
        model="GigaChat-Test",
        api_key="secret",
        api_scope="GIGACHAT_API_PERS",
        base_url="",
    )

    llm = create_llm(config)
    tools = [{"type": "function", "function": {"name": "get_status"}}]
    response = llm.generate([{"role": "user", "content": "status"}], tools=tools)

    assert llm._model.options["credentials"] == "secret"
    assert llm._model.options["scope"] == "GIGACHAT_API_PERS"
    assert llm._model.options["ca_bundle_file"].endswith(
        "certs/russian_trusted_root_ca_pem.crt"
    )
    assert llm._model.tools == tools
    assert response.content == "done"
    assert response.finish_reason == "tool_calls"
    assert response.tool_calls[0].name == "get_status"
    assert response.tool_calls[0].arguments == {"full": True}
    assert list(llm.stream_generate([{"role": "user", "content": "hello"}])) == [
        "one",
        "two",
    ]
