#!/usr/bin/env python3
import argparse
import json
import logging
import shlex
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from deskagent.agent.core.models import AgentSession
from deskagent.agent.llm.base import LLMProviderError
from deskagent.agent.runtime.factory import create_desktop_agent
from scripts._common import add_llm_arguments, resolve_llm


def create_parser():
    parser = argparse.ArgumentParser(description="Run DeskAgent")
    parser.add_argument("request", nargs="?", help="Desktop task to perform")
    add_llm_arguments(parser)
    parser.add_argument("--thread-id", default="cli")
    parser.add_argument("--checkpoints")
    parser.add_argument("--stream", action="store_true")
    audio_input = parser.add_mutually_exclusive_group()
    audio_input.add_argument("--voice", action="store_true", help="Record a spoken request and speak the response")
    audio_input.add_argument("--voice-loop", action="store_true", help="Keep taking voice turns until Ctrl+C")
    audio_input.add_argument("--audio-file", help="Use a mono PCM16 WAV as a spoken request")
    parser.add_argument("--speak", action="store_true", help="Speak a text request's response")
    decision = parser.add_mutually_exclusive_group()
    decision.add_argument("--approve", action="store_true")
    decision.add_argument("--deny", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser


def main(argv=None):
    args = create_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)
    try:
        from deskagent.audio import AudioClip, AudioError, VoiceAssistant
        settings, llm_config = resolve_llm(args)
        voice_input = args.voice or args.voice_loop or args.audio_file
        if voice_input and (args.request or args.stream or args.approve or args.deny):
            raise ValueError("Voice input cannot be combined with a text request, stream or confirmation")
        if args.speak and args.stream:
            raise ValueError("--speak cannot be combined with --stream")
        if voice_input or args.speak:
            settings.audio.enabled = True
            voice = VoiceAssistant(settings.audio)
        agent = create_desktop_agent(llm_config, checkpoint_path=args.checkpoints, settings=settings)
        if voice_input:
            while True:
                print("Listening…" if not args.audio_file else "Transcribing…", file=sys.stderr, flush=True)
                clip = AudioClip.from_wav(Path(args.audio_file).expanduser().read_bytes()) if args.audio_file else None
                turn = voice.turn(agent, AgentSession(args.thread_id), clip=clip)
                if turn.speech_error:
                    print(turn.speech_error, file=sys.stderr)
                if turn.response is not None:
                    print("You:", turn.transcript)
                    response = turn.response
                    if not args.voice_loop or response.pending_confirmation or response.error:
                        break
                    print(response.content, flush=True)
                elif not args.voice_loop:
                    print("No speech detected", file=sys.stderr)
                    return 0
        elif args.approve or args.deny:
            response = agent.confirm(args.thread_id, args.approve)
        elif args.stream:
            if not args.request:
                raise ValueError("Request is required")
            for event in agent.stream_ask(args.request, AgentSession(args.thread_id)):
                print(json.dumps(event, ensure_ascii=False, default=str), flush=True)
            return 0
        else:
            if not args.request:
                raise ValueError("Request is required")
            response = agent.ask(args.request, AgentSession(args.thread_id))
        if args.speak and not voice_input:
            try:
                voice.speak(response.content)
            except AudioError as exc:
                print(exc, file=sys.stderr)
    except KeyboardInterrupt:
        return 130
    except (LLMProviderError, AudioError, OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 2
    print(response.content)
    if response.pending_confirmation:
        print(json.dumps(response.pending_confirmation, ensure_ascii=False))
        print("Resume:", shlex.join(_resume_command(args, llm_config.provider, llm_config.model, response.thread_id)))
    return 1 if response.error else 0


def _resume_command(args, provider, model, thread_id):
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--provider",
        provider,
        "--model",
        model,
        "--thread-id",
        thread_id,
        "--approve",
    ]
    for option, value in (
        ("--config", args.config),
        ("--base-url", args.base_url),
        ("--api-scope", args.api_scope),
        ("--weights", args.weights),
        ("--checkpoints", args.checkpoints),
        ("--context-window", args.context_window),
        ("--max-tokens", args.max_tokens),
    ):
        if value is not None:
            command += [option, str(value)]
    if args.no_pull:
        command.append("--no-pull")
    if args.no_start:
        command.append("--no-start")
    return command


if __name__ == "__main__":
    raise SystemExit(main())
