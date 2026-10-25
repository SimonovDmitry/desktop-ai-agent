import argparse

from deskagent.agent.llm.config import LLMConfig
from deskagent.core.config import Settings


def add_llm_arguments(parser: argparse.ArgumentParser):
    parser.add_argument("--config", help="YAML configuration path")
    parser.add_argument("--provider", choices=("ollama", "openai_compatible", "mlx"))
    parser.add_argument("--model", help="Model tag or local model path")
    parser.add_argument("--weights", help="GGUF file or Safetensors directory for Ollama import")
    parser.add_argument("--base-url", help="Provider URL")
    parser.add_argument("--api-key", help="API key for an OpenAI-compatible provider")
    parser.add_argument("--context-window", type=int)
    parser.add_argument("--max-tokens", type=int)
    parser.add_argument("--no-pull", action="store_true", help="Do not pull a missing Ollama model")
    parser.add_argument("--no-start", action="store_true", help="Do not start Ollama automatically")


def resolve_llm(args) -> tuple[Settings, LLMConfig]:
    settings = Settings.load(args.config)
    provider = args.provider or settings.llm.provider
    model = args.model or settings.llm.model
    if not model and (provider == "mlx" or not args.provider):
        from pathlib import Path
        if Path("models/qwen3.5_4b_mlx_4bit").is_dir():
            provider = "mlx"
            model = "models/qwen3.5_4b_mlx_4bit"
    if not model:
        raise ValueError("--model is required unless llm.model is configured")
    base_url = args.base_url or settings.llm.base_url
    if provider == "openai_compatible" and not base_url:
        raise ValueError("--base-url is required for openai_compatible")
    return settings, LLMConfig(
        provider=provider, model=model, weights=args.weights, base_url=base_url or "",
        api_key=args.api_key or settings.llm.api_key or "ollama",
        context_window=args.context_window or settings.llm.context_window,
        max_tokens=args.max_tokens or settings.llm.max_tokens,
        manage_runtime=provider == "ollama", auto_start=not args.no_start,
        auto_pull=not args.no_pull,
    )
