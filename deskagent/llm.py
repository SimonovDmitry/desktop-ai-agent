import os

# Добавляем использование зеркала перед всеми импортами
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from agent.llm.mlx import MLXLLM

SYSTEM_PROMPT = """
You are a fast desktop AI assistant.

Rules:
- Be extremely concise.
- Answer simple questions with only the necessary answer.
- Do not explain your reasoning unless explicitly asked.
- Do not provide step-by-step explanations unless explicitly requested.
- Do not use Markdown unless necessary.
- Do not repeat the user's question.
- For simple calculations, return only the result.
- For desktop actions, use the available tools.
- Never claim that an action was completed unless the tool confirms success.
"""

def run_test():
    # Попробуем версию 2.5, так как она более стабильна в репозиториях MLX
    model_id = "/Users/yahikonetalant/PycharmProjects/desktop-ai-agent/models/qwen3.5_4b_mlx_4bit"

    print(f"Инициализация модели {model_id} через зеркало...")
    llm = MLXLLM(model_id)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Привет! Ты работаешь? Готов к первой задаче? или как?"}
    ]

    print("\nГенерация ответа...")
    response = llm.generate(messages)

    print("\n" + "=" * 40)
    print(f"ОТВЕТ:\n{response.content}")
    print("=" * 40)

    messages2 = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": """Вот код запуска модели сделай так чтобы он работал быстрее код пришли мне чтобы я его протестил: 
                                        from mlx_lm import load, stream_generate
                                        from mlx_lm.sample_utils import make_sampler
                                        
                                        from .base import LLMProvider
                                        from .response import LLMResponse
                                        
                                        
                                        class MLXLLM(LLMProvider):
                                        
                                            def __init__(self, model_id):
                                                print(f"Загрузка модели: {model_id}")
                                        
                                                self.model, self.tokenizer = load(model_id)
                                        
                                                print("Модель загружена.")
                                        
                                            def _build_prompt(self, messages):
                                                return self.tokenizer.apply_chat_template(
                                                    messages,
                                                    tokenize=False,
                                                    add_generation_prompt=True,
                                                    enable_thinking=False,
                                                )
                                        
                                            def _create_sampler(self):
                                                return make_sampler(
                                                    temp=0.7,
                                                    top_p=0.8,
                                                    top_k=20,
                                                )
                                        
                                            def stream_generate(self, messages, tools=None):
                                                prompt = self._build_prompt(messages)
                                        
                                                sampler = self._create_sampler()
                                        
                                                for response in stream_generate(
                                                    self.model,
                                                    self.tokenizer,
                                                    prompt=prompt,
                                                    max_tokens=256,
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
                                                )"""}

    ]

    response = llm.generate(messages2)

    print("\n" + "=" * 40)
    print(f"ОТВЕТ:\n{response.content}")
    print("=" * 40)


if __name__ == "__main__":
    run_test()