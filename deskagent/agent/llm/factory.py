from deskagent.agent.llm.base import LLMProvider
from deskagent.agent.llm.config import LLMConfig
from deskagent.agent.llm.openai_compatible import OpenAICompatibleLLM
from deskagent.agent.llm.ollama import OllamaLLM


def create_llm(config: LLMConfig | None = None) -> LLMProvider:
    resolved_config = (config or LLMConfig()).validate()
    if resolved_config.provider == "ollama":
        return OllamaLLM(resolved_config)
    if resolved_config.provider == "openai_compatible":
        return OpenAICompatibleLLM(resolved_config)
    if resolved_config.provider == "mlx":
        from deskagent.agent.llm.mlx import MLXLLM
        return MLXLLM(resolved_config)
