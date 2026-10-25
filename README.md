# DeskAgent

Локальный desktop-агент с LangGraph и сменными LLM-провайдерами.

Архитектура политик, подтверждений, audit log и аварийной остановки описана в [SECURITY.md](SECURITY.md).

```bash
python scripts/run_agent.py --provider ollama --model qwen3:4b "Покажи заряд батареи"
python scripts/run_llm.py --provider mlx --model ./models/model "Привет"
```

Параметры можно хранить в `config.yaml` или переменных окружения `DESKAGENT_*`.
Полный список аргументов доступен через `--help`.
