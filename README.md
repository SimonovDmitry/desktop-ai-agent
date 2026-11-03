## DeskAgent

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

Для TLS используется включённый в проект корневой сертификат НУЦ Минцифры из
`models/gigachat/russian_trusted_root_ca_pem.crt`. При необходимости его можно
переопределить через `GIGACHAT_CA_BUNDLE_FILE`. Отключать проверку TLS не следует.

Параметры локальных провайдеров можно хранить в `config.yaml` или переменных
окружения `DESKAGENT_*`. Аргументы командной строки имеют приоритет над `.env` и
конфигурацией.
Полный список аргументов доступен через `--help`.

## Сессии, планы и автопилот

Пакет `deskagent.autopilot` выполняет сохраняемые многошаговые планы поверх
существующего каталога действий. Он поддерживает DAG-зависимости, передачу
результатов между шагами, проверку результата, безопасные повторы, подтверждения,
перепланирование, отмену и восстановление после перезапуска.

```python
from deskagent.autopilot import AutopilotEngine, Plan, SessionStore, Step

store = SessionStore("data/sessions.sqlite")
engine = AutopilotEngine(action_catalog, store)
session = engine.create_session(
    "Подготовить рабочее окружение",
    Plan([
        Step(
            id="open_ide",
            title="Открыть PyCharm",
            action="launch_application",
            arguments={"application": "PyCharm"},
            idempotent=True,
        ),
        Step(
            id="set_volume",
            title="Установить громкость",
            action="set_volume",
            arguments={"volume": 25},
            depends_on=("open_ide",),
            idempotent=True,
        ),
    ]),
)
result = engine.start(session.id)
```

Сохранённые сценарии описываются декларативным YAML без выполнения произвольного
Python или shell-кода. Пример находится в `examples/prepare_for_work.yaml`.
