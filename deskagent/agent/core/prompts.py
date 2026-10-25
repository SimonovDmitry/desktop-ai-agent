from datetime import datetime
from typing import Any

BASE_PROMPT = """
You are DeskAgent, a reliable local desktop assistant for macOS.
Use tools for computer actions and trust only confirmed tool results.
Never invent system state, paths or successful actions. Stop when the task is complete.
For dangerous actions wait for user approval. Answer briefly in the user's language.
When focus_mode is enabled and procrastination is detected, be firm but respectful and add
one short, accurately attributed Stoic quote. Never fabricate quotes or block the user without consent.
""".strip()

STOIC_QUOTES = (
    "Some things are in our control and others not. — Epictetus, Enchiridion 1",
    "We suffer more often in imagination than in reality. — Seneca",
    "No man is free who is not master of himself. — Epictetus",
)


def build_system_prompt(screen=None, system=None, plan=None) -> str:
    system = system or {}
    context = {
        "time": datetime.now().astimezone().isoformat(timespec="minutes"),
        "screen": screen or {}, "system": system, "plan": plan or [],
    }
    focus = ""
    if system.get("focus_mode") and system.get("procrastination"):
        focus = f"\nFocus reminder: {STOIC_QUOTES[0]}"
    return f"{BASE_PROMPT}{focus}\n\nCurrent context:\n{_compact(context)}"


def _compact(value: Any) -> str:
    import json
    return json.dumps(value, ensure_ascii=False, default=str, separators=(",", ":"))
