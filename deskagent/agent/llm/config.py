from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMConfig:
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
