import json
import re

from deskagent.agent.llm.base import LLMProvider, LLMProviderError
from deskagent.agent.llm.response import LLMResponse, ToolCall


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
    def __init__(self, model_id: str, max_tokens: int = 1024):
        try:
            from mlx_lm import load
        except ImportError as exc:
            raise LLMProviderError("Package 'mlx-lm' is required for MLXLLM") from exc

        self.model, self.tokenizer = load(model_id)
        self.max_tokens = max_tokens

    def _build_prompt(self, messages, tools=None):
        kwargs = {"tokenize": False, "add_generation_prompt": True, "enable_thinking": False}
        if tools:
            kwargs["tools"] = tools
        return self.tokenizer.apply_chat_template(messages, **kwargs)

    def _create_sampler(self):
        from mlx_lm.sample_utils import make_sampler
        return make_sampler(temp=0.0, top_p=0.8, top_k=20)

    def stream_generate(self, messages, tools=None):
        from mlx_lm import stream_generate
        prompt = self._build_prompt(messages, tools=tools)
        sampler = self._create_sampler()
        for response in stream_generate(
            self.model, self.tokenizer, prompt=prompt, max_tokens=self.max_tokens, sampler=sampler
        ):
            yield response.text

    def generate(self, messages, tools=None):
        chunks = list(self.stream_generate(messages, tools=tools))
        raw_text = "".join(chunks).strip()
        if tools:
            clean_content, tool_calls = parse_tool_calls(raw_text)
            return LLMResponse(content=clean_content, tool_calls=tool_calls, finish_reason="stop")
        return LLMResponse(content=raw_text, finish_reason="stop")
