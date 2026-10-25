import argparse
import json
import logging
import os
import shlex
import sys

from deskagent.agent.factory import create_desktop_agent
from deskagent.agent.llm.base import LLMProviderError
from deskagent.agent.llm.config import LLMConfig
from deskagent.agent.models import AgentSession


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="deskagent", description="Run the local DeskAgent")
    parser.add_argument("request", nargs="?", help="Desktop task to perform")
    parser.add_argument("--provider", choices=("ollama", "openai_compatible", "mlx"), default="ollama")
    parser.add_argument("--model", required=True, help="Model tag or local model path")
    parser.add_argument("--weights", help="GGUF file or Safetensors directory for Ollama import")
    parser.add_argument("--base-url", help="Provider URL")
    parser.add_argument("--api-key", help="API key for an OpenAI-compatible provider")
    parser.add_argument("--no-pull", action="store_true", help="Do not download a missing Ollama model")
    parser.add_argument("--no-start", action="store_true", help="Do not start Ollama automatically")
    parser.add_argument("--context-window", type=int, default=8192)
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--thread-id", default="cli")
    parser.add_argument("--checkpoints")
    parser.add_argument("--stream", action="store_true")
    decision = parser.add_mutually_exclusive_group()
    decision.add_argument("--approve", action="store_true")
    decision.add_argument("--deny", action="store_true")
    parser.add_argument("--verbose", action="store_true", help="Enable action logs")
    return parser


def main(argv=None) -> int:
    args = create_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)
    base_url = args.base_url or ("http://127.0.0.1:11434" if args.provider == "ollama" else None)
    if args.provider == "openai_compatible" and not base_url:
        raise SystemExit("--base-url is required for openai_compatible")
    config = LLMConfig(
        provider=args.provider, model=args.model, weights=args.weights, base_url=base_url or "",
        api_key=args.api_key or os.getenv("DESKAGENT_API_KEY", "ollama"),
        context_window=args.context_window, max_tokens=args.max_tokens,
        manage_runtime=args.provider == "ollama", auto_start=not args.no_start,
        auto_pull=not args.no_pull,
    )
    try:
        agent = create_desktop_agent(config, checkpoint_path=args.checkpoints)
        if args.approve or args.deny:
            response = agent.confirm(args.thread_id, approved=args.approve)
        elif args.stream:
            if not args.request:
                raise ValueError("Request is required")
            for event in agent.stream_ask(args.request, AgentSession(args.thread_id)):
                print(json.dumps(event, ensure_ascii=False, default=str), flush=True)
            return 0
        else:
            if not args.request:
                raise ValueError("Request is required")
            response = agent.ask(args.request, session=AgentSession(args.thread_id))
    except (LLMProviderError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 2
    print(response.content)
    if response.pending_confirmation:
        print(json.dumps(response.pending_confirmation, ensure_ascii=False))
        resume = [sys.executable, "-m", "deskagent.agent", "--provider", args.provider,
                  "--model", args.model, "--thread-id", response.thread_id, "--approve"]
        if args.base_url:
            resume += ["--base-url", args.base_url]
        if args.checkpoints:
            resume += ["--checkpoints", args.checkpoints]
        print("Resume:", shlex.join(resume))
    return 1 if response.error else 0


if __name__ == "__main__":
    raise SystemExit(main())
