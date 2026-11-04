#!/usr/bin/env python3
import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from deskagent.agent.runtime.factory import create_desktop_agent  # noqa: E402
from deskagent.autopilot import AutopilotMode  # noqa: E402
from deskagent.ui.autopilot import SessionPresenter  # noqa: E402
from scripts._common import add_llm_arguments, resolve_llm  # noqa: E402


def create_parser():
    parser = argparse.ArgumentParser(description="Manage durable DeskAgent workflows")
    add_llm_arguments(parser)
    parser.add_argument("--verbose", action="store_true")
    commands = parser.add_subparsers(dest="command", required=True)
    save = commands.add_parser("save")
    save.add_argument("path", type=Path)
    run = commands.add_parser("run")
    run.add_argument("name")
    run.add_argument("--inputs", default="{}", help="JSON object")
    run.add_argument("--mode", choices=[item.value for item in AutopilotMode], default="guided")
    run.add_argument("--dry-run", action="store_true")
    status = commands.add_parser("status")
    status.add_argument("session_id")
    approve = commands.add_parser("approve")
    approve.add_argument("session_id")
    approve.add_argument("--confirmation-id")
    approve.add_argument("--text")
    commands.add_parser("list")
    return parser


def main(argv=None):
    args = create_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)
    settings, llm_config = resolve_llm(args)
    agent = create_desktop_agent(llm_config, settings=settings)
    if args.command == "save":
        result = agent.workflows.save(args.path)
    elif args.command == "list":
        result = agent.workflows.list(detailed=True)
    elif args.command == "run":
        result = agent.run_workflow(
            args.name, json.loads(args.inputs),
            mode=AutopilotMode(args.mode), dry_run=args.dry_run,
        )
        result = SessionPresenter.present(result, agent.autopilot.store.events(result.id))
    elif args.command == "status":
        session = agent.autopilot.store.get(args.session_id)
        result = SessionPresenter.present(session, agent.autopilot.store.events(session.id))
    else:
        answer = {
            "approved": True,
            "confirmation_id": args.confirmation_id,
            "text": args.text,
        }
        session = agent.autopilot.approve(args.session_id, answer)
        result = SessionPresenter.present(session, agent.autopilot.store.events(session.id))
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
