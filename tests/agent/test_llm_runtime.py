from pathlib import Path

import pytest
from deskagent.agent.cli import create_parser

from deskagent.agent.llm.base import LLMProviderError
from deskagent.agent.llm.config import LLMConfig
from deskagent.agent.llm.ollama_runtime import OllamaRuntime


def test_cli_requires_model():
    with pytest.raises(SystemExit):
        create_parser().parse_args(["hello"])


def test_cli_accepts_model_and_weights():
    args = create_parser().parse_args(
        [
            "hello",
            "--model",
            "my-model",
            "--weights",
            "model.gguf",
        ]
    )
    assert args.model == "my-model"
    assert args.weights == "model.gguf"


def test_runtime_rejects_missing_weights(tmp_path):
    config = LLMConfig(model="local", weights=str(tmp_path / "missing.gguf"))
    with pytest.raises(LLMProviderError, match="Weights not found"):
        OllamaRuntime(config)._validate()


def test_runtime_rejects_unsupported_weight_file(tmp_path):
    weights = tmp_path / "model.bin"
    weights.write_bytes(b"test")
    config = LLMConfig(model="local", weights=str(weights))
    with pytest.raises(LLMProviderError, match="GGUF"):
        OllamaRuntime(config)._validate()


def test_runtime_creates_modelfile_for_gguf(tmp_path, monkeypatch):
    weights = tmp_path / "model.gguf"
    weights.write_bytes(b"test")
    runtime = OllamaRuntime(LLMConfig(model="local", weights=str(weights)))
    captured = {}

    def fake_run(*args):
        captured["args"] = args
        captured["modelfile"] = Path(args[-1]).read_text()

    monkeypatch.setattr(runtime, "_run", fake_run)
    runtime._create_model(weights.resolve())

    assert captured["args"][:2] == ("create", "local")
    assert f'FROM "{weights.resolve()}"' in captured["modelfile"]
