import json
from collections.abc import Iterable
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from deskagent.agent.llm.base import LLMProvider, LLMProviderError
from deskagent.agent.llm.config import LLMConfig
from deskagent.agent.llm.response import LLMResponse, ToolCall


class OllamaLLM(LLMProvider):
    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig()
        self._model = self._create_model()

    def _create_model(self):
        try:
            from langchain_ollama import ChatOllama
        except ImportError as exc:
            raise LLMProviderError("Package 'langchain-ollama' is required for OllamaLLM") from exc

        return ChatOllama(
            model=self.config.model,
            base_url=self.config.base_url,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            top_k=self.config.top_k,
            num_ctx=self.config.context_window,
            num_predict=self.config.max_tokens,
            client_kwargs={"timeout": self.config.request_timeout},
        )

    def generate(self, messages: list[Any], tools: list[dict[str, Any]] | None = None) -> LLMResponse:
        model = self._model.bind_tools(tools) if tools else self._model
        try:
            message = model.invoke(messages)
        except Exception as exc:
            raise LLMProviderError(f"Ollama request failed: {exc}") from exc

        tool_calls = [ToolCall.from_value(tc) for tc in getattr(message, "tool_calls", [])]
        metadata = getattr(message, "response_metadata", {}) or {}
        return LLMResponse(
            content=self._content_to_text(getattr(message, "content", "")),
            tool_calls=tool_calls,
            finish_reason=metadata.get("done_reason"),
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
            raise LLMProviderError(f"Ollama stream failed: {exc}") from exc

    def is_available(self) -> bool:
        url = f"{self.config.base_url.rstrip('/')}/api/tags"
        try:
            with urlopen(url, timeout=2) as response:
                payload = json.loads(response.read())
        except (OSError, URLError, json.JSONDecodeError):
            return False

        target_base = self.config.model.split(":")[0]
        return any(m.get("name", "").split(":")[0] == target_base for m in payload.get("models", []))

    @staticmethod
    def _content_to_text(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(b.get("text", "") for b in content if isinstance(b, dict))
        return str(content or "")
