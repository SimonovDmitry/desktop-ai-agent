from openai import OpenAI

from deskagent.agent.llm.base import LLMProvider, LLMProviderError
from deskagent.agent.llm.response import LLMResponse, ToolCall


class QwenLLM(LLMProvider):
    def __init__(self, config):
        self.config = config
        self.client = OpenAI(base_url=config.base_url, api_key=config.api_key)

    def generate(self, messages, tools=None):
        try:
            params = {
                "model": self.config.model,
                "messages": messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "top_p": self.config.top_p,
                "extra_body": {
                    "top_k": 20,
                    "chat_template_kwargs": {"enable_thinking": self.config.enable_thinking},
                },
            }
            if tools:
                params["tools"] = tools

            completion = self.client.chat.completions.create(**params)
            message = completion.choices[0].message
            return LLMResponse(
                content=message.content or "",
                tool_calls=[ToolCall.from_value(tc) for tc in getattr(message, "tool_calls", [])],
                finish_reason=completion.choices[0].finish_reason,
                raw=message,
            )
        except Exception as exc:
            raise LLMProviderError(f"OpenAI-compatible request failed: {exc}") from exc

    def stream_generate(self, messages, tools=None):
        stream = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            stream=True,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
