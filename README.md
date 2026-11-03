# DeskAgent

Desktop-агент с LangGraph и сменными локальными и API LLM-провайдерами.

Архитектура политик, подтверждений, audit log и аварийной остановки описана в [SECURITY.md](SECURITY.md).

```bash
# Локальная модель через Ollama
python scripts/run_agent.py --provider ollama --model qwen3:4b "Покажи заряд батареи"

# Локальная модель через MLX
python scripts/run_llm.py --provider mlx --model ./models/model "Привет"
```

## GigaChat API

Установите зависимости и положите параметры доступа в `.env` в корне проекта:

```bash
pip install -r requirements.txt
```

```dotenv
GIGACHAT_CREDENTIALS=<authorization-key>
GIGACHAT_SCOPE=GIGACHAT_API_PERS
GIGACHAT_MODEL=<model-name>
```

Файл `.env` исключён из Git. Запуск через API не поднимает локальную модель:

```bash
python scripts/run_agent.py --provider gigachat "Покажи заряд батареи"
python scripts/run_llm.py --provider gigachat --stream "Привет"
```

При необходимости задайте `GIGACHAT_CA_BUNDLE_FILE` с путём к корневому
сертификату НУЦ Минцифры. Отключать проверку TLS для рабочего окружения не следует.

Параметры локальных провайдеров можно хранить в `config.yaml` или переменных
окружения `DESKAGENT_*`. Аргументы командной строки имеют приоритет над `.env` и
конфигурацией.
Полный список аргументов доступен через `--help`.
