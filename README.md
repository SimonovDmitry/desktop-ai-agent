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
существующего каталога действий. Он поддерживает DAG-зависимости и параллельные
ветки, передачу результатов между шагами, декларативную проверку, безопасные
повторы, строгие подтверждения, перепланирование, компенсации, отмену и
автоматическое восстановление после перезапуска.

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

Для длительно работающего приложения используется `AutopilotWorker`: он честно
обходит активные сессии, удерживает lease только на время одного тика и запускает
готовые повторы по сохранённому `retry_at`. Независимые шаги выполняются параллельно,
если их `resources` не пересекаются.

Управление workflow из терминала:

```bash
python scripts/run_workflow.py save examples/prepare_for_work.yaml
python scripts/run_workflow.py run prepare_for_work --inputs '{"focus_volume": 25}'
python scripts/run_workflow.py list
python scripts/run_workflow.py status <session-id>
```

Секретные входы workflow содержат только имя секрета. Значение разрешается во
время выполнения из переменной `DESKAGENT_SECRET_<NAME>` и не записывается в план,
журнал событий или историю запусков.

## Accessibility на macOS

Модуль `deskagent.perception.accessibility` читает семантическое дерево интерфейса
через `AXUIElement`, ищет элементы по роли и тексту (включая fuzzy-поиск), возвращает
координаты, AX actions, confidence и повторно используемый `ax://` locator. Доступны
действия чтения, изменения состояния и отменяемые ожидания с таймаутом, например
`find_ui_element`, `press_ui_element`, `wait_for_ui_element` и
`verify_ui_element_state`.

Перед первым использованием вызовите `request_accessibility_permission`, затем
разрешите приложению доступ в **System Settings → Privacy & Security →
Accessibility**. Подробности контракта и внутренней архитектуры находятся в
[`deskagent/perception/accessibility/README.md`](deskagent/perception/accessibility/README.md).
