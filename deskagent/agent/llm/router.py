from deskagent.agent.llm.base import LLMProvider, LLMProviderError


class FallbackLLM(LLMProvider):
    def __init__(self, providers: list[LLMProvider]):
        if not providers:
            raise ValueError("At least one LLM provider is required")
        self.providers = providers
        self.active_provider = None

    def generate(self, messages, tools=None):
        errors = []
        for provider in self.providers:
            try:
                response = provider.generate(messages, tools)
                self.active_provider = provider
                return response
            except LLMProviderError as exc:
                errors.append(str(exc))
        raise LLMProviderError("All LLM providers failed: " + " | ".join(errors))

    def stream_generate(self, messages, tools=None):
        errors = []
        for provider in self.providers:
            emitted = False
            try:
                for chunk in provider.stream_generate(messages, tools):
                    emitted = True
                    yield chunk
                self.active_provider = provider
                return
            except LLMProviderError as exc:
                if emitted:
                    raise
                errors.append(str(exc))
        raise LLMProviderError("All LLM providers failed: " + " | ".join(errors))

    def is_available(self):
        return any(provider.is_available() for provider in self.providers)
