import json
import re
from typing import Any

from deskagent.agent.llm.base import LLMProvider, LLMProviderError
from deskagent.agent.llm.config import LLMConfig
from deskagent.agent.llm.response import LLMResponse, ToolCall


def normalize_messages(messages: list[Any]) -> list[dict[str, Any]]:
    system_parts, chat_messages = [], []
    for msg in messages:
        if isinstance(msg, dict):
            role, content = msg.get("role") or "user", msg.get("content", "")
            if role == "system":
                if content:
                    system_parts.append(str(content))
                continue
            item = {"role": role, "content": str(content)}
            if "tool_calls" in msg:
                item["tool_calls"] = msg["tool_calls"]
            if "tool_call_id" in msg:
                item["tool_call_id"] = msg["tool_call_id"]
            chat_messages.append(item)
            continue

        msg_type = getattr(msg, "type", None) or getattr(msg, "role", "user")
        if msg_type in ("human", "user"):
            role = "user"
        elif msg_type in ("ai", "assistant"):
            role = "assistant"
        elif msg_type == "system":
            content = getattr(msg, "content", "")
            if content:
                system_parts.append(str(content))
            continue
        elif msg_type == "tool":
            role = "tool"
        else:
            role = "user"

        content = getattr(msg, "content", "")
        item = {"role": role, "content": str(content)}
        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            item["tool_calls"] = tool_calls
        tool_call_id = getattr(msg, "tool_call_id", None)
        if tool_call_id:
            item["tool_call_id"] = tool_call_id
        chat_messages.append(item)

    result = []
    if system_parts:
        result.append({"role": "system", "content": "\n\n".join(system_parts)})
    result.extend(chat_messages)
    return result


def parse_tool_calls(text: str) -> tuple[str, list[ToolCall]]:
    tool_calls = []
    for block in re.findall(r"<tool_call>(.*?)</tool_call>", text, re.DOTALL):
        block = block.strip()
        if block.startswith("{") and block.endswith("}"):
            try:
                data = json.loads(block)
                if data.get("name"):
                    tool_calls.append(ToolCall(name=data["name"], arguments=data.get("arguments", {})))
                    continue
            except Exception:
                pass
        func_match = re.search(r"<function=([^>]+)>(.*?)</function>", block, re.DOTALL)
        if func_match:
            name = func_match.group(1).strip()
            args = {}
            for pm in re.finditer(r"<parameter=([^>]+)>(.*?)</parameter>", func_match.group(2), re.DOTALL):
                val = pm.group(2).strip()
                try:
                    args[pm.group(1).strip()] = json.loads(val)
                except Exception:
                    args[pm.group(1).strip()] = val
            tool_calls.append(ToolCall(name=name, arguments=args))

    clean_content = re.sub(r"<tool_call>.*?</tool_call>", "", text, flags=re.DOTALL).strip()
    return clean_content, tool_calls


class MLXLLM(LLMProvider):
    def __init__(self, config: LLMConfig | str, max_tokens=1024):
        try:
            from mlx_lm import load
        except ImportError as exc:
            raise LLMProviderError("Package 'mlx-lm' is required for MLXLLM") from exc
        self.config = (config if isinstance(config, LLMConfig)
                       else LLMConfig(provider="mlx", model=config, max_tokens=max_tokens)).validate()
        self.model, self.tokenizer = load(self.config.model)

    def _build_prompt(self, messages, tools=None):
        kwargs = {"tokenize": False, "add_generation_prompt": True,
                  "enable_thinking": self.config.enable_thinking}
        if tools:
            kwargs["tools"] = tools
        norm_messages = normalize_messages(messages)
        return self.tokenizer.apply_chat_template(norm_messages, **kwargs)

    def _create_sampler(self):
        from mlx_lm.sample_utils import make_sampler
        return make_sampler(temp=self.config.temperature, top_p=self.config.top_p,
                            top_k=self.config.top_k)

    def stream_generate(self, messages, tools=None):
        from mlx_lm import stream_generate
        prompt = self._build_prompt(messages, tools=tools)
        sampler = self._create_sampler()
        for response in stream_generate(
            self.model, self.tokenizer, prompt=prompt, max_tokens=self.config.max_tokens,
            sampler=sampler,
        ):
            yield response.text

    def generate(self, messages, tools=None):
        chunks = list(self.stream_generate(messages, tools=tools))
        raw_text = "".join(chunks).strip()
        if tools:
            clean_content, tool_calls = parse_tool_calls(raw_text)
            return LLMResponse(content=clean_content, tool_calls=tool_calls, finish_reason="stop")
        return LLMResponse(content=raw_text, finish_reason="stop")
