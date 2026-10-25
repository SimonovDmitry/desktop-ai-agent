import argparse
import logging
import os
import sys

from deskagent.agent.factory import create_desktop_agent
from deskagent.agent.llm.config import LLMConfig
from deskagent.agent.llm.base import LLMProviderError
from deskagent.agent.models import AgentSession


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="deskagent", description="Run the local DeskAgent MVP")
    parser.add_argument("request", help="Desktop task to perform")
    parser.add_argument("--provider", choices=("ollama", "openai_compatible"), default="ollama")
    parser.add_argument("--model", required=True, help="Model tag or local model alias")
    parser.add_argument("--weights", help="GGUF file or Safetensors directory for Ollama import")
    parser.add_argument("--base-url", help="Provider URL")
    parser.add_argument("--api-key", help="API key for an OpenAI-compatible provider")
    parser.add_argument("--no-pull", action="store_true", help="Do not download a missing Ollama model")
    parser.add_argument("--no-start", action="store_true", help="Do not start Ollama automatically")
    parser.add_argument("--context-window", type=int, default=8192)
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--verbose", action="store_true", help="Enable action logs")
    return parser


def main(argv=None) -> int:
    args = create_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)
    base_url = args.base_url or ("http://127.0.0.1:11434" if args.provider == "ollama" else None)
    if not base_url:
        raise SystemExit("--base-url is required for openai_compatible")
    config = LLMConfig(
        provider=args.provider, model=args.model, weights=args.weights, base_url=base_url,
        api_key=args.api_key or os.getenv("DESKAGENT_API_KEY", "ollama"),
        context_window=args.context_window, max_tokens=args.max_tokens,
        manage_runtime=args.provider == "ollama", auto_start=not args.no_start,
        auto_pull=not args.no_pull,
    )
    try:
        agent = create_desktop_agent(config)
        response = agent.ask(args.request, session=AgentSession(thread_id="cli"))
    except (LLMProviderError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 2
    print(response.content)
    return 1 if response.error else 0


if __name__ == "__main__":
    raise SystemExit(main())
