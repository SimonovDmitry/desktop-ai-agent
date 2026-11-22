import struct
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from deskagent.audio import AudioClip, AudioError, VoiceAssistant
from deskagent.audio.devices import UtteranceDetector
from deskagent.audio.providers import OpenAIAudio, SileroTTS, TOneSTT, split_text
from deskagent.core.config import AudioSettings, Settings


def test_wav_roundtrip_and_reject_stereo():
    clip = AudioClip(struct.pack('<hhh', -32768, 0, 32767), 16000)
    assert AudioClip.from_wav(clip.to_wav()) == clip
    with pytest.raises(AudioError):
        AudioClip.from_wav(b'not a wav')


def test_silence_and_endpoint():
    settings = AudioSettings(silence_seconds=0.09, min_speech_seconds=0.06)
    silence = b'\0\0' * 480
    speech = struct.pack('<h', 6000) * 480
    detector = UtteranceDetector(settings)
    for _ in range(400):
        if detector.feed(silence):
            break
    assert detector.result() is None
    assert detector.elapsed < 11
    detector = UtteranceDetector(settings)
    for frame in [silence] * 3 + [speech] * 4 + [silence] * 4:
        if detector.feed(frame):
            break
    assert detector.result().pcm.startswith(silence)
    assert detector.result().duration < 0.4


def assistant(**overrides):
    settings = AudioSettings(enabled=True, **overrides)
    stt = Mock()
    stt.transcribe.return_value = 'открой файл'
    tts = Mock()
    tts.synthesize.return_value = AudioClip(b'\0\0', 24000)
    devices = Mock()
    devices.record.return_value = AudioClip(b'\0\0', 16000)
    return VoiceAssistant(settings, stt=stt, tts=tts, devices=devices)


def test_turn_preserves_confirmation_and_speech_failure():
    voice = assistant()
    response = SimpleNamespace(content='Нужно подтверждение', pending_confirmation={'id': 'one'})
    agent = Mock()
    agent.ask.return_value = response
    voice.tts.synthesize.side_effect = RuntimeError('failure')
    result = voice.turn(agent, 'session')
    agent.ask.assert_called_once_with('открой файл', 'session')
    assert result.response is response
    assert result.speech_error
    assert response.pending_confirmation == {'id': 'one'}
    agent.confirm.assert_not_called()


def test_wake_word_silence_and_cancel_do_not_call_agent():
    agent = Mock()
    voice = assistant(wake_word='Агент')
    assert voice.turn(agent, 's').response is None
    voice.stt.transcribe.return_value = 'Агент, открой файл'
    voice.turn(agent, 's')
    agent.ask.assert_called_once_with('открой файл', 's')
    agent.reset_mock()
    voice.stop()
    voice.turn(agent, 's')
    agent.ask.assert_not_called()
    voice = assistant()
    voice.devices.record.return_value = None
    voice.turn(agent, 's')
    voice.stt.transcribe.assert_not_called()


def test_api_contract_and_safe_errors():
    backend = OpenAIAudio('http://localhost:8000/v1', '', 'model')
    backend._client = Mock()
    backend._client.audio.transcriptions.create.return_value = SimpleNamespace(text=' текст ')
    assert backend.transcribe(AudioClip(b'\0\0', 16000)) == 'текст'
    request = backend._client.audio.transcriptions.create.call_args.kwargs
    assert request['file'][1].read().startswith(b'RIFF')
    backend._client.audio.speech.create.return_value = SimpleNamespace(content=b'\0\0')
    assert backend.synthesize('Привет').sample_rate == 24000
    backend._client.audio.transcriptions.create.side_effect = RuntimeError('secret-key')
    with pytest.raises(AudioError, match='STT API') as error:
        backend.transcribe(AudioClip(b'\0\0', 16000))
    assert 'secret-key' not in str(error.value)


def test_text_chunks_preserve_tail():
    text = 'Привет мир. ' * 200 + 'x' * 2000
    chunks = list(split_text(text))
    assert all(0 < len(chunk) <= 800 for chunk in chunks)
    assert ''.join(chunks).replace(' ', '') == text.replace(' ', '')


def test_config_environment_and_invalid_limits():
    config = Settings.load(environ={'DESKAGENT_AUDIO__STT_PROVIDER': 'openai_compatible',
                                    'DESKAGENT_AUDIO__API_TIMEOUT': '15',
                                    'DESKAGENT_AUDIO__SPEAK_RESPONSES': 'false'})
    assert config.audio.api_timeout == 15
    assert not config.audio.speak_responses
    with pytest.raises(ValueError):
        AudioSettings(max_record_seconds=float('nan')).validate()
    with pytest.raises(ValueError):
        AudioSettings(tts_provider='unknown').validate()


def test_local_providers_load_lazily():
    assert TOneSTT('/missing')._model is None
    assert SileroTTS('/missing')._model is None


def test_local_tone_loads_once_and_normalizes_pcm(monkeypatch, tmp_path):
    import sys
    import numpy as np
    model = Mock()
    model.recognize.return_value = 'тест'
    load = Mock(return_value=model)
    monkeypatch.setitem(sys.modules, 'onnx_asr', SimpleNamespace(load_model=load))
    backend = TOneSTT(tmp_path)
    clip = AudioClip(struct.pack('<hh', -32768, 16384), 16000)
    assert backend.transcribe(clip) == 'тест'
    assert backend.transcribe(clip) == 'тест'
    load.assert_called_once_with('t-tech/t-one', str(tmp_path))
    np.testing.assert_allclose(model.recognize.call_args.args[0], [-1, 0.5])
    assert model.recognize.call_args.kwargs['sample_rate'] == 16000


def test_cli_voice_preserves_approval_flow(monkeypatch, capsys):
    from scripts import run_agent
    config = SimpleNamespace(provider='ollama', model='test')
    monkeypatch.setattr(run_agent, 'resolve_llm', lambda args: (Settings(), config))
    agent = Mock()
    response = SimpleNamespace(content='Подтвердите', pending_confirmation={'action': 'delete'},
                               thread_id='cli', error=None)
    turn = SimpleNamespace(transcript='удали файл', response=response, speech_error='')
    monkeypatch.setattr(run_agent, 'create_desktop_agent', lambda *args, **kwargs: agent)
    voice = Mock()
    voice.turn.return_value = turn
    monkeypatch.setattr('deskagent.audio.VoiceAssistant', lambda settings: voice)
    assert run_agent.main(['--voice-loop', '--model', 'test']) == 0
    output = capsys.readouterr().out
    assert 'Подтвердите' in output
    assert '--approve' in output
    assert voice.turn.call_count == 1
    agent.confirm.assert_not_called()


def test_silero_package_contract(monkeypatch, tmp_path):
    import sys
    from contextlib import nullcontext
    import numpy as np
    model_file = tmp_path / 'v5_ru.pt'
    model_file.touch()
    model = Mock()
    tensor = Mock()
    tensor.detach.return_value.cpu.return_value.numpy.return_value = np.array([-2, 0, 2], dtype=np.float32)
    model.apply_tts.return_value = tensor
    importer = Mock()
    importer.return_value.load_pickle.return_value = model
    torch = SimpleNamespace(package=SimpleNamespace(PackageImporter=importer), device=lambda value: value,
                            inference_mode=nullcontext)
    monkeypatch.setitem(sys.modules, 'torch', torch)
    backend = SileroTTS(model_file)
    clip = backend.synthesize('Привет')
    assert struct.unpack('<hhh', clip.pcm) == (-32767, 0, 32767)
    assert clip.sample_rate == 48000
    model.apply_tts.assert_called_once_with(text='Привет', speaker='xenia', sample_rate=48000)
    importer.return_value.load_pickle.assert_called_once_with('tts_models', 'model')
