from openai import OpenAI

from deskagent.agent.llm.base import LLMProvider, LLMProviderError
from deskagent.agent.llm.response import LLMResponse, ToolCall


class OpenAICompatibleLLM(LLMProvider):
    def __init__(self, config):
        self.config = config.validate()
        self.client = OpenAI(base_url=config.base_url, api_key=config.api_key)

    def generate(self, messages, tools=None):
        params = {
            "model": self.config.model, "messages": messages,
            "temperature": self.config.temperature, "max_tokens": self.config.max_tokens,
            "top_p": self.config.top_p,
        }
        if tools:
            params["tools"] = tools
        if self.config.extra_body:
            params["extra_body"] = self.config.extra_body
        try:
            completion = self.client.chat.completions.create(**params)
        except Exception as exc:
            raise LLMProviderError(f"OpenAI-compatible request failed: {exc}") from exc
        message = completion.choices[0].message
        return LLMResponse(
            content=message.content or "",
            tool_calls=[ToolCall.from_value(tc) for tc in getattr(message, "tool_calls", [])],
            finish_reason=completion.choices[0].finish_reason, raw=message,
        )

    def stream_generate(self, messages, tools=None):
        params = {
            "model": self.config.model, "messages": messages, "stream": True,
            "temperature": self.config.temperature, "max_tokens": self.config.max_tokens,
            "top_p": self.config.top_p,
        }
        if tools:
            params["tools"] = tools
        if self.config.extra_body:
            params["extra_body"] = self.config.extra_body
        try:
            stream = self.client.chat.completions.create(**params)
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as exc:
            raise LLMProviderError(f"OpenAI-compatible stream failed: {exc}") from exc
