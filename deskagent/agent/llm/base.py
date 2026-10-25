from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any

from deskagent.agent.llm.response import LLMResponse


class LLMProviderError(RuntimeError):
    pass


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, messages: list[Any], tools: list[dict[str, Any]] | None = None) -> LLMResponse:
        pass

    def stream_generate(self, messages: list[Any], tools: list[dict[str, Any]] | None = None) -> Iterable[str]:
        response = self.generate(messages, tools=tools)
        if response.content:
            yield response.content

    def is_available(self) -> bool:
        return True
