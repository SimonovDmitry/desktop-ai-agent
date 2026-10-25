from dataclasses import dataclass, field
from typing import Any, ClassVar


@dataclass
class LLMConfig:
    PROVIDERS: ClassVar = {"ollama", "openai_compatible", "mlx"}
    provider: str = "ollama"
    model: str = ""
    base_url: str = "http://127.0.0.1:11434"
    api_key: str = "ollama"
    weights: str | None = None
    temperature: float = 0.0
    top_p: float = 0.9
    top_k: int = 20
    max_tokens: int = 512
    context_window: int = 8192
    request_timeout: float = 120.0
    enable_thinking: bool = False
    manage_runtime: bool = False
    auto_start: bool = True
    auto_pull: bool = True
    startup_timeout: float = 20.0
    ollama_binary: str = "ollama"
    extra_body: dict[str, Any] = field(default_factory=dict)

    def validate(self):
        if self.provider not in self.PROVIDERS:
            raise ValueError(f"Unknown LLM provider: {self.provider}")
        if not self.model.strip():
            raise ValueError("Model name is required")
        if self.provider == "openai_compatible" and not self.base_url.strip():
            raise ValueError("Base URL is required for openai_compatible")
        if self.weights and self.provider != "ollama":
            raise ValueError("Local weights are supported only by Ollama")
        if self.context_window < 1 or self.max_tokens < 1 or self.request_timeout <= 0:
            raise ValueError("LLM limits and timeout must be positive")
        if not 0 <= self.temperature <= 2 or not 0 <= self.top_p <= 1 or self.top_k < 0:
            raise ValueError("Invalid sampling parameters")
        return self
