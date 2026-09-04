"""
Tests for the local speech-to-text engine.

The model itself is never loaded here - these cover the wrapper around it:
device/quantisation selection, the shape of a Transcript, and the failure modes
the dispatcher relies on to tell a learner "send it as text instead".
"""
import pytest

from utils.transcription import (
    Transcriber,
    Transcript,
    TranscriptionError,
    TranscriptionUnavailable,
    _resolve_compute_type,
    _resolve_device,
    get_transcriber,
    reset_transcriber,
)


class FakeSegment:
    def __init__(self, text):
        self.text = text


class FakeInfo:
    def __init__(self, language="en", probability=0.99, duration=4.2):
        self.language = language
        self.language_probability = probability
        self.duration = duration


class FakeModel:
    """Stands in for faster_whisper.WhisperModel."""

    def __init__(self, segments=("Hello there",), info=None):
        self.segments = [FakeSegment(t) for t in segments]
        self.info = info or FakeInfo()
        self.calls = []

    def transcribe(self, audio, **kwargs):
        self.calls.append(kwargs)
        # The real API returns a generator, and forcing it is where the work
        # happens - mirror that so the wrapper is exercised the same way.
        return iter(self.segments), self.info


@pytest.fixture(autouse=True)
def _clean_singleton():
    reset_transcriber()
    yield
    reset_transcriber()


def build(model=None, **kwargs):
    """A Transcriber with the model pre-injected, so load() never downloads."""
    transcriber = Transcriber(**kwargs)
    transcriber._model = model or FakeModel()
    return transcriber


class TestDeviceSelection:
    def test_explicit_device_is_respected(self):
        assert _resolve_device("cpu") == "cpu"
        assert _resolve_device("cuda") == "cuda"

    def test_auto_falls_back_to_cpu_without_a_gpu(self, monkeypatch):
        """A machine with no CUDA must still transcribe, just slower."""
        import ctranslate2

        monkeypatch.setattr(ctranslate2, "get_cuda_device_count", lambda: 0)
        assert _resolve_device("auto") == "cpu"

    def test_auto_uses_cuda_when_available(self, monkeypatch):
        import ctranslate2

        monkeypatch.setattr(ctranslate2, "get_cuda_device_count", lambda: 1)
        assert _resolve_device("auto") == "cuda"

    def test_int8_on_cpu_float16_on_gpu(self):
        """int8 is what makes CPU transcription fast enough to be usable."""
        assert _resolve_compute_type("auto", "cpu") == "int8"
        assert _resolve_compute_type("auto", "cuda") == "float16"
        assert _resolve_compute_type("float32", "cpu") == "float32"


class TestTranscript:
    def test_speed_factor(self):
        transcript = Transcript(text="hi", audio_seconds=10.0, elapsed_seconds=2.0)
        assert transcript.speed_factor == 5.0

    def test_speed_factor_is_zero_when_untimed(self):
        assert Transcript(text="hi").speed_factor == 0.0

    def test_whitespace_only_counts_as_empty(self):
        assert Transcript(text="   \n ").is_empty is True
        assert Transcript(text="words").is_empty is False


class TestTranscribeBytes:
    def test_joins_segments_into_one_transcript(self):
        transcriber = build(FakeModel(segments=("What is ", " the leave policy")))
        result = transcriber.transcribe_bytes(b"audio")

        assert result.text == "What is the leave policy"
        assert result.language == "en"
        assert result.audio_seconds == 4.2
        assert result.segments == ["What is", "the leave policy"]

    def test_empty_audio_is_rejected_before_the_model(self):
        model = FakeModel()
        transcriber = build(model)

        with pytest.raises(TranscriptionError):
            transcriber.transcribe_bytes(b"")

        assert model.calls == []

    def test_silence_produces_an_empty_transcript_not_an_error(self):
        """A learner who taps record and says nothing gets asked to retry."""
        transcriber = build(FakeModel(segments=()))
        assert transcriber.transcribe_bytes(b"audio").is_empty is True

    def test_decoder_failure_is_wrapped(self):
        class Broken(FakeModel):
            def transcribe(self, audio, **kwargs):
                raise RuntimeError("Invalid data found when processing input")

        with pytest.raises(TranscriptionError) as exc:
            build(Broken()).transcribe_bytes(b"not-audio")

        assert exc.value.suggestion

    def test_vad_and_language_settings_reach_the_model(self):
        model = FakeModel()
        transcriber = build(model, language="ta", vad_filter=True, beam_size=3)
        transcriber.transcribe_bytes(b"audio")

        kwargs = model.calls[0]
        assert kwargs["language"] == "ta"
        assert kwargs["beam_size"] == 3
        assert kwargs["vad_filter"] is True
        # Looping on noise is Whisper's classic failure; this guard must stay on.
        assert kwargs["condition_on_previous_text"] is False

    def test_vad_parameters_are_omitted_when_vad_is_off(self):
        model = FakeModel()
        build(model, vad_filter=False).transcribe_bytes(b"audio")
        assert model.calls[0]["vad_parameters"] is None

    async def test_async_wrapper_returns_the_same_transcript(self):
        transcriber = build(FakeModel(segments=("spoken words",)))
        result = await transcriber.transcribe(b"audio")
        assert result.text == "spoken words"


class TestUnavailable:
    def test_missing_package_is_reported_once_and_cached(self, monkeypatch):
        """
        A missing install will not fix itself between two voice notes, so the
        failure is remembered rather than retried on every message.
        """
        import builtins

        real_import = builtins.__import__
        attempts = []

        def fake_import(name, *args, **kwargs):
            if name == "faster_whisper":
                attempts.append(name)
                raise ImportError("No module named 'faster_whisper'")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        transcriber = Transcriber()
        for _ in range(3):
            with pytest.raises(TranscriptionUnavailable):
                transcriber.load()

        assert len(attempts) == 1

    def test_warm_up_reports_failure_instead_of_raising(self, monkeypatch):
        """Warm-up is an optimisation; it must never stop the bot booting."""
        transcriber = Transcriber()
        monkeypatch.setattr(
            transcriber, "load",
            lambda: (_ for _ in ()).throw(TranscriptionUnavailable("nope")),
        )
        assert transcriber.warm_up() is False


class TestSingleton:
    def test_same_instance_is_reused(self):
        """The model costs seconds to load; it is loaded once per process."""
        assert get_transcriber() is get_transcriber()

    def test_reset_builds_a_new_one(self):
        first = get_transcriber()
        reset_transcriber()
        assert get_transcriber() is not first

    def test_state_is_reportable_before_loading(self):
        state = get_transcriber().get_state()
        assert state["loaded"] is False
        assert state["device"] in ("cpu", "cuda")
        assert state["model"]
