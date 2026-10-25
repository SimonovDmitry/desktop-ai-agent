import argparse
import logging

from deskagent.agent.factory import create_desktop_agent
from deskagent.agent.llm.config import LLMConfig
from deskagent.agent.session import AgentSession


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="deskagent",
        description="Run the local DeskAgent MVP",
    )
    parser.add_argument("request", help="Desktop task to perform")
    parser.add_argument(
        "--model",
        default="qwen3:4b",
        help="Ollama model name",
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:11434",
        help="Ollama server URL",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable action logs",
    )
    return parser


def main(argv=None) -> int:
    args = create_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING
    )
    agent = create_desktop_agent(
        LLMConfig(
            model=args.model,
            base_url=args.base_url,
        )
    )
    response = agent.ask(
        args.request,
        session=AgentSession(thread_id="cli"),
    )

    print(response.content)
    return 1 if response.error else 0


if __name__ == "__main__":
    raise SystemExit(main())
