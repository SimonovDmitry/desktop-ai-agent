from __future__ import annotations

import os
from typing import Protocol


class SecretProvider(Protocol):
    def get(self, name: str) -> str:
        ...


class EnvironmentSecretProvider:
    """Resolve durable secret references without storing their values in plans."""

    def __init__(self, prefix: str = "DESKAGENT_SECRET_"):
        self.prefix = prefix

    def get(self, name: str) -> str:
        key = self.prefix + name.upper().replace("-", "_")
        if key not in os.environ:
            raise KeyError(f"Secret is not configured: {name}")
        return os.environ[key]
