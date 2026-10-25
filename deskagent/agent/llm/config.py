from dataclasses import dataclass


@dataclass
class LLMConfig:
    provider: str = "ollama"
    model: str = "qwen3:4b"
    base_url: str = "http://127.0.0.1:11434"
    api_key: str = "ollama"
    temperature: float = 0.0
    top_p: float = 0.9
    top_k: int = 20
    max_tokens: int = 512
    context_window: int = 8192
    request_timeout: float = 120.0
    enable_thinking: bool = False
