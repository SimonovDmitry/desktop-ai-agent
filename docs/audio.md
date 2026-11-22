# Голосовой ввод и озвучивание

`deskagent.audio` связывает микрофон → STT → существующий `agent.ask` → TTS → динамики.
STT и TTS выбираются независимо: `local`, `openai` или `openai_compatible`.
Никакого автоматического переключения с локальных моделей на облако нет.
Аудиозаписи живут в памяти; модуль не сохраняет их на диск. Распознанный текст
попадает в обычную историю агента и подчиняется её правилам хранения.

## Установка локальных моделей

```sh
pip install -r requirements-audio.txt
```

На macOS для sounddevice может потребоваться `brew install portaudio` и разрешение
микрофона для терминала/приложения. Для Linux установите системную PortAudio.
Текстовый режим работает без опциональных аудиозависимостей.

T-one запускается через ONNX-адаптер `onnx-asr` с CTC-декодированием. Один раз
подготовьте каталог с моделью при доступном интернете:

```python
import onnx_asr
onnx_asr.load_model("t-tech/t-one", "models/t-one")
```

Скачайте пакет **Silero TTS v5_ru** из официального источника:

```sh
mkdir -p models/silero
curl -fL https://models.silero.ai/models/tts/ru/v5_ru.pt -o models/silero/v5_ru.pt
```

Загружайте только доверенные PyTorch-пакеты: загрузка модели выполняет её Python-код.
После подготовки полных каталогов локальные модели работают без облачного API.
Для строгой офлайн-работы задайте `HF_HUB_OFFLINE=1` и `HF_HUB_DISABLE_TELEMETRY=1`.
Неполный каталог T-one может вызвать попытку загрузки недостающих файлов библиотекой
onnx-asr; офлайн-переменная запрещает это.

## Запуск

```sh
python -m deskagent.agent --config examples/audio-local.yaml --voice
python -m deskagent.agent --config examples/audio-local.yaml --voice-loop
python -m deskagent.agent --config examples/audio-local.yaml --audio-file request.wav
python -m deskagent.agent --config examples/audio-local.yaml 'Привет' --speak
```

В YAML задайте свою LLM или добавьте обычные `--provider` и `--model`.
`--voice` слушает одну фразу; `--voice-loop` повторяет диалог в одном thread-id.
Ctrl+C завершает CLI. Во время синтеза/ответа микрофон закрыт, чтобы агент не слышал себя.
При запросе подтверждения цикл останавливается и печатает стандартную команду
`--approve`; голосовая фраза не вызывает `agent.confirm`.
`--speak` также работает при продолжении через `--approve` или `--deny`.

Входной файл: несжатый mono PCM16 WAV. Устройство захвата: mono PCM16, по умолчанию
16 kHz. Пауза 0.8 с завершает фразу; ожидание начала ограничено 10 с, запись — 20 с.
Энергетический детектор имеет 300 мс предзаписи. Настройте `energy_threshold`
под микрофон и шум комнаты: это простой детектор уровня, а не нейросетевой VAD.
Опциональный `wake_word` проверяется в начале **распознанного текста**, поэтому
при API-распознавании звук передаётся провайдеру до проверки слова.

Текущая реализация — последовательный диалог по фразам, без перебивания голоса
и без частичных транскрипций. ONNX-адаптер T-one не использует оригинальный
streaming pipeline. Файлы длиннее 20 с обрабатываются окнами по 20 с; слово на
границе может распознаться хуже. Для диктовки предпочтительны короткие фразы.
Оригинальная T-one специализируется на русской телефонной речи; качество на
конкретном микрофоне следует проверить отдельно.

## API и смешанные конфигурации

Пример: `examples/audio-api.yaml`. Ключи задаются через окружение или `.env`:

```sh
export DESKAGENT_AUDIO__STT_API_KEY='...'
export DESKAGENT_AUDIO__TTS_API_KEY='...'
python -m deskagent.agent --config examples/audio-api.yaml --voice
```

Каждое поле AudioSettings доступно через `DESKAGENT_AUDIO__ИМЯ_ПОЛЯ`.
Например, можно оставить T-one локально, а `tts_provider` изменить на `openai`.
У STT/TTS отдельные URL, ключи и имена моделей, независимые от настроек LLM.
API имеет таймаут (60 с), без автоматических повторов платного запроса.
TTS endpoint должен поддерживать `response_format=pcm`: mono PCM16 LE, 24 kHz.
STT endpoint должен принимать multipart WAV и возвращать JSON с полем `text`.
Самостоятельно размещённые совместимые серверы могут использовать пустой ключ;
для облачного OpenAI задайте настоящий ключ для каждого направления.

Подходящие сервисы:

| Сервис | Возможности | Подключение здесь |
| --- | --- | --- |
| OpenAI Audio | STT и TTS | Готовый адаптер `openai`; модель и голос настраиваются |
| OpenAI-совместимый собственный сервер | Зависит от сервера | `openai_compatible`, свой `base_url` с `/v1` |
| ElevenLabs | STT и выразительное TTS | Отдельный адаптер или совместимый шлюз; native API пока не реализован |
| Yandex SpeechKit | STT и TTS, включая русский | Отдельный адаптер или шлюз; native API пока не реализован |

Провайдер можно расширить реализацией контрактов `SpeechToText.transcribe(AudioClip)`
и `TextToSpeech.synthesize(str)` и передать через `VoiceAssistant(..., stt=..., tts=...)`.
`SoundDeviceIO` также заменяется через `devices` для UI или тестового источника.
`VoiceAssistant.stop()` прекращает запись/воспроизведение на ближайшем блоке;
текущий синхронный вызов модели/API/агента завершится самостоятельно (API ограничен
таймаутом). После stop создайте новый экземпляр для новой сессии.
Сбой TTS сохраняет текстовый ответ и возвращает `VoiceTurn.speech_error`.

Источники: [T-one](https://github.com/voicekit-team/T-one),
[onnx-asr](https://istupakov.github.io/onnx-asr/usage/),
[Silero](https://github.com/snakers4/silero-models#text-to-speech),
[OpenAI STT](https://developers.openai.com/api/docs/guides/speech-to-text),
[ElevenLabs](https://elevenlabs.io/docs/eleven-api/guides/cookbooks/speech-to-text),
[SpeechKit](https://aistudio.yandex.ru/en/docs/speechkit/stt/).
