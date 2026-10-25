from typing import Any


class ConversationManager:
    @staticmethod
    def user_message(content: str) -> dict[str, str]:
        text = content.strip()
        if not text:
            raise ValueError("User message cannot be empty")
        return {"role": "user", "content": text}

    @staticmethod
    def last_assistant_content(messages: list[Any]) -> str:
        for message in reversed(messages):
            if isinstance(message, dict):
                role = message.get("role")
                content = message.get("content", "")
            else:
                role = getattr(message, "type", None)
                content = getattr(message, "content", "")

            if role in ("assistant", "ai") and content:
                return str(content)

        return ""
