import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import ClassVar


@dataclass
class LLMSettings:
    provider: str = "ollama"
    model: str = ""
    base_url: str = "http://127.0.0.1:11434"
    api_key: str = ""
    context_window: int = 8192
    max_tokens: int = 512


@dataclass
class AgentSettings:
    max_iterations: int = 8
    max_tools: int = 18
    max_tool_calls_per_iteration: int = 6


@dataclass
class SecuritySettings:
    allowed_paths: list[str] = field(default_factory=lambda: [
        "~/Downloads", "~/Documents/DeskAgent", ".",
    ])
    blocked_paths: list[str] = field(default_factory=lambda: [
        "~/.ssh", "~/.gnupg", "~/Library/Keychains", "/System", "/Library",
    ])
    allowed_applications: list[str] = field(default_factory=list)
    excluded_apps: list[str] = field(default_factory=list)
    dry_run: bool = False
    allow_shell: bool = False
    shell_allowed_commands: list[str] = field(default_factory=list)
    strict_mode: bool = True
    confirm_medium: bool = True
    max_actions: int = 24
    max_clicks_per_minute: int = 60
    max_consecutive_failures: int = 3


@dataclass
class StorageSettings:
    checkpoints: str = "~/.deskagent/checkpoints.sqlite"
    memory: str = "~/.deskagent/memory.sqlite"
    telemetry: str = "~/.deskagent/telemetry.jsonl"
    audit: str = "~/.deskagent/audit.sqlite"
    skills: str = "~/.deskagent/skills"


@dataclass
class VisionSettings:
    enabled: bool = False
    capture_interval: float = 30.0
    ocr: bool = True
    model: str = ""


@dataclass
class AudioSettings:
    enabled: bool = False
    wake_word: str = ""
    stt_provider: str = "local"
    tts_provider: str = "system"


class BaseConfig:
    def to_dict(self):
        return asdict(self)


@dataclass
class Settings(BaseConfig):
    llm: LLMSettings = field(default_factory=LLMSettings)
    agent: AgentSettings = field(default_factory=AgentSettings)
    security: SecuritySettings = field(default_factory=SecuritySettings)
    storage: StorageSettings = field(default_factory=StorageSettings)
    vision: VisionSettings = field(default_factory=VisionSettings)
    audio: AudioSettings = field(default_factory=AudioSettings)

    SECTIONS: ClassVar = {
        "llm": LLMSettings, "agent": AgentSettings, "security": SecuritySettings,
        "storage": StorageSettings, "vision": VisionSettings, "audio": AudioSettings,
    }
    ENV_ALIASES: ClassVar = {
        "MODEL": "llm.model", "PROVIDER": "llm.provider", "BASE_URL": "llm.base_url",
        "API_KEY": "llm.api_key", "CHECKPOINTS": "storage.checkpoints",
        "MEMORY": "storage.memory", "TELEMETRY": "storage.telemetry", "SKILLS": "storage.skills",
        "AUDIT": "storage.audit",
        "ALLOWED_PATHS": "security.allowed_paths", "ALLOWED_APPLICATIONS": "security.allowed_applications",
        "EXCLUDED_APPS": "security.excluded_apps", "DRY_RUN": "security.dry_run",
        "ALLOW_SHELL": "security.allow_shell", "MAX_ACTIONS": "security.max_actions",
        "SHELL_ALLOWED_COMMANDS": "security.shell_allowed_commands",
        "STRICT_MODE": "security.strict_mode", "CONFIRM_MEDIUM": "security.confirm_medium",
        "MAX_CLICKS_PER_MINUTE": "security.max_clicks_per_minute",
        "MAX_CONSECUTIVE_FAILURES": "security.max_consecutive_failures",
        "MAX_ITERATIONS": "agent.max_iterations", "MAX_TOOLS": "agent.max_tools",
        "VISION_ENABLED": "vision.enabled", "AUDIO_ENABLED": "audio.enabled",
    }

    @classmethod
    def load(cls, path=None, environ=None):
        data = cls._read_yaml(path) if path else {}
        settings = cls(**{name: section(**data.get(name, {})) for name, section in cls.SECTIONS.items()})
        settings._apply_environment(os.environ if environ is None else environ)
        settings.validate()
        return settings

    def validate(self):
        if self.agent.max_iterations < 1 or self.agent.max_tools < 1:
            raise ValueError("Agent limits must be positive")
        if self.security.max_actions < 1:
            raise ValueError("security.max_actions must be positive")
        if self.security.max_clicks_per_minute < 1 or self.security.max_consecutive_failures < 1:
            raise ValueError("Security rate and repeat limits must be positive")
        if self.llm.context_window < 1 or self.llm.max_tokens < 1:
            raise ValueError("LLM token limits must be positive")
        return self

    def _apply_environment(self, environ):
        for key, value in environ.items():
            if not key.startswith("DESKAGENT_"):
                continue
            suffix = key.removeprefix("DESKAGENT_")
            target = self.ENV_ALIASES.get(suffix, suffix.lower().replace("__", "."))
            if "." not in target:
                continue
            section, name = target.split(".", 1)
            if hasattr(self, section) and hasattr(getattr(self, section), name):
                current = getattr(getattr(self, section), name)
                setattr(getattr(self, section), name, self._convert(value, current))

    @staticmethod
    def _convert(value, current):
        if isinstance(current, bool):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        if isinstance(current, int):
            return int(value)
        if isinstance(current, float):
            return float(value)
        if isinstance(current, list):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @staticmethod
    def _read_yaml(path):
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError("PyYAML is required to load a YAML config") from exc
        target = Path(path).expanduser()
        if not target.exists():
            raise FileNotFoundError(target)
        data = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise ValueError("Config root must be a mapping")
        unknown = set(data) - set(Settings.SECTIONS)
        if unknown:
            raise ValueError(f"Unknown config sections: {', '.join(sorted(unknown))}")
        return data
