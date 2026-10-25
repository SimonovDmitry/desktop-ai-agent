from deskagent.agent.llm.base import LLMProvider
from deskagent.agent.llm.config import LLMConfig
from deskagent.agent.llm.openai_compatible import OpenAICompatibleLLM
from deskagent.agent.llm.ollama import OllamaLLM


def create_llm(config: LLMConfig | None = None) -> LLMProvider:
    resolved_config = config or LLMConfig()
    if resolved_config.weights and resolved_config.provider != "ollama":
        raise ValueError("Local weights are supported only by the Ollama provider")
    if resolved_config.provider == "ollama":
        return OllamaLLM(resolved_config)
    if resolved_config.provider == "openai_compatible":
        return OpenAICompatibleLLM(resolved_config)
    if resolved_config.provider == "mlx":
        from deskagent.agent.llm.mlx import MLXLLM
        return MLXLLM(resolved_config.model, max_tokens=resolved_config.max_tokens)
    raise ValueError(f"Unknown LLM provider: {resolved_config.provider}")
