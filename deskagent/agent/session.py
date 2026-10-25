import uuid
from dataclasses import dataclass, field


@dataclass
class AgentSession:
    thread_id: str = field(
        default_factory=lambda: f"session_{uuid.uuid4().hex}"
    )

    def graph_config(self) -> dict:
        return {
            "configurable": {
                "thread_id": self.thread_id,
            }
        }
