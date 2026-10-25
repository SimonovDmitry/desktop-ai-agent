import json
import re
from pathlib import Path


class SkillStore:
    def __init__(self, registry, path="~/.deskagent/skills"):
        self.registry = registry
        self.path = Path(path).expanduser()
        self.path.mkdir(parents=True, exist_ok=True)

    def save(self, name: str, steps: list[dict], description=""):
        slug = re.sub(r"[^a-z0-9_-]+", "-", name.lower()).strip("-")
        if not slug or not steps:
            raise ValueError("Skill name and steps are required")
        for step in steps:
            if not self.registry.contains(step.get("action", "")):
                raise ValueError(f"Unknown skill action: {step.get('action')}")
        payload = {"name": name, "description": description, "steps": steps, "enabled": False}
        (self.path / f"{slug}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return slug

    def load(self, slug: str):
        return json.loads((self.path / f"{slug}.json").read_text(encoding="utf-8"))

    def enable(self, slug: str, enabled=True):
        skill = self.load(slug)
        skill["enabled"] = enabled
        (self.path / f"{slug}.json").write_text(json.dumps(skill, ensure_ascii=False, indent=2), encoding="utf-8")

    def list(self):
        return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(self.path.glob("*.json"))]
