#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from deskagent.agent.llm.base import LLMProviderError
from deskagent.agent.llm.factory import create_llm
from scripts._common import add_llm_arguments, resolve_llm


def create_parser():
    parser = argparse.ArgumentParser(description="Run an LLM without the desktop agent")
    parser.add_argument("prompt", help="Prompt to send")
    parser.add_argument("--system", default="You are a concise desktop assistant.")
    parser.add_argument("--stream", action="store_true")
    add_llm_arguments(parser)
    return parser


def main(argv=None):
    args = create_parser().parse_args(argv)
    try:
        _, config = resolve_llm(args)
        llm = create_llm(config)
        messages = [{"role": "system", "content": args.system}, {"role": "user", "content": args.prompt}]
        if args.stream:
            for token in llm.stream_generate(messages):
                print(token, end="", flush=True)
            print()
        else:
            print(llm.generate(messages).content)
        return 0
    except (LLMProviderError, OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
