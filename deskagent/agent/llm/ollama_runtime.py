import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from deskagent.agent.llm.base import LLMProviderError
from deskagent.agent.llm.config import LLMConfig


class OllamaRuntime:
    def __init__(self, config: LLMConfig):
        self.config = config

    def prepare(self):
        self._validate()
        self._require_binary()
        self._ensure_server()
        if self.config.weights:
            self._create_model(Path(self.config.weights).expanduser().resolve())
        elif not self.has_model():
            if not self.config.auto_pull:
                raise LLMProviderError(f"Ollama model is not installed: {self.config.model}")
            self._run("pull", self.config.model)

    def stop(self):
        self._require_binary()
        self._run("stop", self.config.model)

    def has_model(self) -> bool:
        try:
            with urlopen(f"{self.config.base_url.rstrip('/')}/api/tags", timeout=2) as response:
                models = json.loads(response.read()).get("models", [])
        except (OSError, URLError, json.JSONDecodeError):
            return False
        target = self.config.model if ":" in self.config.model else f"{self.config.model}:latest"
        return any(model.get("name") == target for model in models)

    def _validate(self):
        if not self.config.model.strip():
            raise LLMProviderError("Model name is required")
        if not self.config.weights:
            return
        path = Path(self.config.weights).expanduser()
        if not path.exists():
            raise LLMProviderError(f"Weights not found: {path}")
        if path.is_file() and path.suffix.lower() != ".gguf":
            raise LLMProviderError("Ollama weights must be a GGUF file or a Safetensors directory")

    def _require_binary(self):
        if not shutil.which(self.config.ollama_binary):
            raise LLMProviderError(f"Ollama executable not found: {self.config.ollama_binary}")

    def _ensure_server(self):
        if self._server_ready():
            return
        if not self.config.auto_start:
            raise LLMProviderError(f"Ollama server is unavailable: {self.config.base_url}")
        subprocess.Popen(
            [self.config.ollama_binary, "serve"], stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, start_new_session=True,
        )
        deadline = time.monotonic() + self.config.startup_timeout
        while time.monotonic() < deadline:
            if self._server_ready():
                return
            time.sleep(0.25)
        raise LLMProviderError("Ollama server did not start in time")

    def _server_ready(self) -> bool:
        try:
            with urlopen(f"{self.config.base_url.rstrip('/')}/api/tags", timeout=1):
                return True
        except (OSError, URLError):
            return False

    def _create_model(self, weights: Path):
        source = json.dumps(str(weights))
        with tempfile.NamedTemporaryFile("w", prefix="deskagent-", suffix=".Modelfile") as file:
            file.write(f"FROM {source}\nPARAMETER num_ctx {self.config.context_window}\n")
            file.flush()
            self._run("create", self.config.model, "-f", file.name)

    def _run(self, *args):
        try:
            subprocess.run([self.config.ollama_binary, *args], check=True)
        except subprocess.CalledProcessError as exc:
            raise LLMProviderError(f"Ollama command failed: {' '.join(args)}") from exc
