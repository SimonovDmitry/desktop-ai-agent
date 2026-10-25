from deskagent.agent.llm.base import LLMProvider, LLMProviderError
from deskagent.agent.llm.response import LLMResponse


class MLXLLM(LLMProvider):
    def __init__(self, model_id, max_tokens=1024):
        try:
            from mlx_lm import load
        except ImportError as exc:
            raise LLMProviderError(
                "Package 'mlx-lm' is required for MLXLLM"
            ) from exc

        self.model, self.tokenizer = load(model_id)
        self.max_tokens = max_tokens

    def _build_prompt(self, messages):
        return self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )

    def _create_sampler(self):
        from mlx_lm.sample_utils import make_sampler

        return make_sampler(
            temp=0.7,
            top_p=0.8,
            top_k=20,
        )

    def stream_generate(self, messages, tools=None):
        if tools:
            raise LLMProviderError(
                "MLXLLM tool calling is not implemented"
            )

        from mlx_lm import stream_generate

        prompt = self._build_prompt(messages)

        sampler = self._create_sampler()

        for response in stream_generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=self.max_tokens,
            sampler=sampler,
        ):
            yield response.text

    def generate(self, messages, tools=None):
        chunks = []

        for chunk in self.stream_generate(
            messages,
            tools=tools,
        ):
            chunks.append(chunk)

        return LLMResponse(
            content="".join(chunks).strip(),
            finish_reason="stop",
        )
