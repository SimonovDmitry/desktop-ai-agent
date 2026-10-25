from deskagent.agent.llm.config import LLMConfig
from deskagent.agent.llm.openai_compatible import OpenAICompatibleLLM

__test__ = False


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

def test_api():
    # Имя модели ДОЛЖНО совпадать с путем, который ты указал в терминале
    # Если ты запускал сервер как --model ./models/qwen3.5_4b_mlx_4bit
    # то и здесь должно быть точно так же
    model_path = "./models/qwen3.5_4b_mlx_4bit"

    config = LLMConfig(
        model=model_path,
        enable_thinking=False
    )

    llm = OpenAICompatibleLLM(config)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Привет! Сколько будет 2+(2*2)"}
    ]

    print(f"Запрос к серверу (модель: {model_path})...")
    response = llm.generate(messages)

    print(f"\nОТВЕТ: {response.content}")
    print(f"TOOL CALLS: {response.tool_calls}")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Скажи мне как устроена LLM внутри со всеми тонкостями"}
    ]

    print(f"Запрос к серверу (модель: {model_path})...")
    response = llm.generate(messages)

    print(f"\nОТВЕТ: {response.content}")
    print(f"TOOL CALLS: {response.tool_calls}")


if __name__ == "__main__":
    test_api()
