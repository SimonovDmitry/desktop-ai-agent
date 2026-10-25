from deskagent.agent.llm.base import LLMProvider
from deskagent.agent.llm.config import LLMConfig
from deskagent.agent.llm.ollama import OllamaLLM
from deskagent.agent.llm.qwen import QwenLLM


def create_llm(config: LLMConfig | None = None) -> LLMProvider:
    resolved_config = config or LLMConfig()
    if resolved_config.provider == "ollama":
        return OllamaLLM(resolved_config)
    if resolved_config.provider == "openai_compatible":
        return QwenLLM(resolved_config)
    raise ValueError(f"Unknown LLM provider: {resolved_config.provider}")
