import os
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from deskagent.agent.llm.base import LLMProvider, LLMProviderError
from deskagent.agent.llm.config import LLMConfig
from deskagent.agent.llm.response import LLMResponse, ToolCall

BUNDLED_CA = Path(__file__).resolve().parents[3] / "models" / "gigachat" / "russian_trusted_root_ca_pem.crt"


class GigaChatLLM(LLMProvider):
    """GigaChat API provider backed by the official LangChain integration."""

    def __init__(self, config: LLMConfig):
        self.config = config.validate()
        self._model = self._create_model()

    def _create_model(self):
        try:
            from langchain_gigachat import GigaChat
        except ImportError as exc:
            raise LLMProviderError("Package 'langchain-gigachat' is required for GigaChatLLM") from exc

        options = {
            "model": self.config.model,
            "credentials": self.config.api_key,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "max_tokens": self.config.max_tokens,
            "timeout": self.config.request_timeout,
        }
        if self.config.api_scope:
            options["scope"] = self.config.api_scope
        if self.config.base_url:
            options["base_url"] = self.config.base_url
        ca_bundle = os.getenv("GIGACHAT_CA_BUNDLE_FILE")
        if ca_bundle:
            options["ca_bundle_file"] = ca_bundle
        elif BUNDLED_CA.is_file():
            options["ca_bundle_file"] = str(BUNDLED_CA)
        return GigaChat(**options)

    def generate(self, messages: list[Any], tools: list[dict[str, Any]] | None = None) -> LLMResponse:
        model = self._model.bind_tools(tools) if tools else self._model
        try:
            message = model.invoke(messages)
        except Exception as exc:
            raise LLMProviderError(f"GigaChat request failed: {exc}") from exc

        metadata = getattr(message, "response_metadata", {}) or {}
        return LLMResponse(
            content=self._content_to_text(getattr(message, "content", "")),
            tool_calls=[ToolCall.from_value(tc) for tc in getattr(message, "tool_calls", [])],
            finish_reason=metadata.get("finish_reason"),
            raw=message,
        )

    def stream_generate(self, messages: list[Any], tools: list[dict[str, Any]] | None = None) -> Iterable[str]:
        model = self._model.bind_tools(tools) if tools else self._model
        try:
            for chunk in model.stream(messages):
                content = self._content_to_text(getattr(chunk, "content", ""))
                if content:
                    yield content
        except Exception as exc:
            raise LLMProviderError(f"GigaChat stream failed: {exc}") from exc

    @staticmethod
    def _content_to_text(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(block.get("text", "") for block in content if isinstance(block, dict))
        return str(content or "")
