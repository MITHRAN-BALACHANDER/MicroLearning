"""
Local speech-to-text, so a learner can talk instead of type.

Runs faster-whisper (OpenAI's Whisper re-implemented on CTranslate2) entirely
on this machine: no audio leaves the server, there is no per-minute API bill,
and the bot keeps working offline once the model is cached.

Three details drive the design:

1. **Lazy load.** The model is a few hundred MB and takes seconds to load, so
   it is built on first use (or deliberately, via `warm_up()`) rather than at
   import - `python main.py` must not pay for it when nobody sends voice.
2. **Off the event loop.** Transcription is CPU-bound and blocking. Every
   public async entry point hands the work to a thread so the bot keeps
   answering other learners while one voice note is being decoded.
3. **Never a hard crash.** A missing package or an undownloadable model raises
   `TranscriptionUnavailable`, which the dispatcher turns into "send it as
   text instead". A learner should never see a stack trace because the GPU box
   was rebuilt.

Audio is decoded by faster-whisper through PyAV, which bundles its own FFmpeg -
so OGG/Opus voice notes work with no `ffmpeg` binary on PATH. That matters on
Windows, where installing FFmpeg system-wide is the step people skip.
"""
import asyncio
import io
import threading
import time
from dataclasses import dataclass, field
from typing import List, Optional

from loguru import logger

from config import settings


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class TranscriptionError(Exception):
    """Transcription failed for this particular clip."""

    def __init__(self, message: str, *, suggestion: str = ""):
        super().__init__(message)
        self.message = message
        self.suggestion = suggestion


class TranscriptionUnavailable(TranscriptionError):
    """The engine itself cannot run (package missing, model won't load)."""


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------


@dataclass
class Transcript:
    """What the model heard, plus enough context to judge whether to trust it."""

    text: str
    language: Optional[str] = None
    language_probability: float = 0.0
    audio_seconds: float = 0.0
    elapsed_seconds: float = 0.0
    model: str = ""
    segments: List[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.text.strip()

    @property
    def speed_factor(self) -> float:
        """How many seconds of audio were handled per second of compute."""
        if self.elapsed_seconds <= 0:
            return 0.0
        return self.audio_seconds / self.elapsed_seconds

    def summary(self) -> str:
        return (
            f"{self.audio_seconds:.1f}s audio in {self.elapsed_seconds:.1f}s "
            f"({self.speed_factor:.1f}x realtime), language={self.language or '?'} "
            f"p={self.language_probability:.2f}, model={self.model}"
        )


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


def _resolve_device(requested: str) -> str:
    """
    Pick the device to run on.

    "auto" means CUDA when CTranslate2 can actually see a GPU. We ask
    CTranslate2 rather than torch because it is the library that will do the
    work, and because a torch build without CUDA on a machine that has a GPU
    would give the wrong answer.
    """
    requested = (requested or "auto").strip().lower()
    if requested != "auto":
        return requested

    try:
        import ctranslate2

        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda"
    except Exception as exc:  # noqa: BLE001 - any failure means "no usable GPU"
        logger.debug(f"No CUDA device visible to CTranslate2 ({exc}); using CPU")

    return "cpu"


def _resolve_compute_type(requested: str, device: str) -> str:
    """
    Pick the quantisation.

    int8 on CPU is the whole reason this is viable on a laptop-class box: it is
    several times faster than float32 and costs well under a point of word
    error rate. float16 is the GPU equivalent.
    """
    requested = (requested or "auto").strip().lower()
    if requested != "auto":
        return requested
    return "float16" if device == "cuda" else "int8"


class Transcriber:
    """
    A lazily-loaded faster-whisper model with an async-safe front door.

    One instance is shared process-wide (see `get_transcriber`). The model is
    thread-safe for inference, but loading is not, so the load is guarded by a
    lock and every caller after the first gets the already-built model.
    """

    def __init__(
        self,
        model_size: Optional[str] = None,
        *,
        device: Optional[str] = None,
        compute_type: Optional[str] = None,
        language: Optional[str] = None,
        beam_size: Optional[int] = None,
        vad_filter: Optional[bool] = None,
        cpu_threads: Optional[int] = None,
        download_root: Optional[str] = None,
    ):
        self.model_size = model_size or settings.WHISPER_MODEL
        self.requested_device = device or settings.WHISPER_DEVICE
        self.requested_compute_type = compute_type or settings.WHISPER_COMPUTE_TYPE
        # None means "detect the language per clip" - the right default for a
        # workforce that does not all speak the same language.
        self.language = language if language is not None else settings.WHISPER_LANGUAGE
        self.beam_size = beam_size if beam_size is not None else settings.WHISPER_BEAM_SIZE
        self.vad_filter = vad_filter if vad_filter is not None else settings.WHISPER_VAD_FILTER
        self.cpu_threads = cpu_threads if cpu_threads is not None else settings.WHISPER_CPU_THREADS
        self.download_root = download_root or settings.WHISPER_MODEL_DIR

        self.device = _resolve_device(self.requested_device)
        self.compute_type = _resolve_compute_type(self.requested_compute_type, self.device)

        self._model = None
        self._load_lock = threading.Lock()
        self._load_error: Optional[TranscriptionUnavailable] = None

    # -- model ------------------------------------------------------------

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def load(self):
        """
        Build the model, downloading it on first run. Blocking; safe to call
        from any thread and safe to call repeatedly.
        """
        if self._model is not None:
            return self._model

        with self._load_lock:
            if self._model is not None:
                return self._model
            if self._load_error is not None:
                # A missing package will not fix itself between two voice
                # notes; re-raise rather than retrying a 30s download each time.
                raise self._load_error

            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                self._load_error = TranscriptionUnavailable(
                    "faster-whisper is not installed",
                    suggestion="pip install faster-whisper (see requirements.txt)",
                )
                raise self._load_error from exc

            started = time.time()
            logger.info(
                f"Loading Whisper '{self.model_size}' on {self.device} "
                f"({self.compute_type})... first run downloads the model"
            )

            try:
                self._model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                    cpu_threads=self.cpu_threads,
                    download_root=self.download_root,
                )
            except Exception as exc:
                self._load_error = TranscriptionUnavailable(
                    f"Could not load Whisper model '{self.model_size}': {exc}",
                    suggestion=(
                        "Check WHISPER_MODEL is a valid size (tiny/base/small/medium/"
                        "large-v3/large-v3-turbo), that the machine can reach "
                        "huggingface.co on first run, and that WHISPER_DEVICE matches "
                        "the hardware."
                    ),
                )
                logger.error(self._load_error.message)
                raise self._load_error from exc

            logger.info(
                f"Whisper '{self.model_size}' ready in {time.time() - started:.1f}s "
                f"({self.device}/{self.compute_type})"
            )
            return self._model

    def warm_up(self) -> bool:
        """
        Load the model and run one throwaway inference ahead of the first
        learner. Returns False instead of raising: a warm-up is an
        optimisation, not a startup requirement.

        The dummy pass matters as much as the load. Loading the weights leaves
        the CUDA kernels and CPU kernel selection uncompiled, so the *first*
        real clip still runs several times slower than every clip after it -
        measured at 0.6x realtime against 11.7x on the same GPU. Better that
        cost lands on startup than on a learner waiting for an answer.
        """
        try:
            model = self.load()
        except TranscriptionUnavailable as exc:
            logger.warning(f"Voice input unavailable: {exc.message} | {exc.suggestion}")
            return False

        try:
            import numpy as np

            started = time.time()
            # A second of near-silence at Whisper's 16 kHz. Quiet noise rather
            # than digital silence, and VAD off, so the encoder actually runs
            # instead of the clip being trimmed away to nothing.
            audio = (np.random.default_rng(0).standard_normal(16000) * 1e-4).astype("float32")
            segments, _ = model.transcribe(audio, language="en", beam_size=1, vad_filter=False)
            list(segments)
            logger.info(f"Whisper warm-up pass took {time.time() - started:.1f}s")
        except Exception as exc:  # noqa: BLE001 - the model is loaded; this is a bonus
            logger.debug(f"Whisper warm-up inference skipped: {exc}")

        return True

    # -- transcription ----------------------------------------------------

    def transcribe_bytes(self, data: bytes, *, filename_hint: str = "audio",
                         task: str = "transcribe") -> Transcript:
        """
        Transcribe raw audio bytes. Blocking - call `transcribe` from async code.

        The bytes go straight to the decoder as an in-memory stream: voice
        notes are small, and not writing them to disk means no temp file to
        clean up and no recording of the learner's voice left on the server.

        `task="translate"` is Whisper's own speech-to-English mode: it renders
        any of its 99 languages into English in a single pass. The dispatcher
        uses it to recognise a spoken command in a language nobody wrote a
        keyword list for - "adutha video anuppu" becomes "send the next video",
        which routes like any English phrase.
        """
        if not data:
            raise TranscriptionError(
                "The audio file was empty",
                suggestion="Re-record the message and send it again.",
            )

        model = self.load()
        started = time.time()

        try:
            segments, info = model.transcribe(
                io.BytesIO(data),
                task=task,
                # Translation has to detect the source language for itself, so
                # a pinned language is only passed on a plain transcription.
                language=self.language if task == "transcribe" else None,
                beam_size=self.beam_size,
                # Voice notes start with a tap and end with a fumble for the
                # send button. Trimming the silence is both faster and more
                # accurate - Whisper hallucinates text over long silences.
                vad_filter=self.vad_filter,
                vad_parameters={"min_silence_duration_ms": 500} if self.vad_filter else None,
                # Whisper is prone to looping on noise; these are the standard
                # guards from the reference implementation.
                condition_on_previous_text=False,
                temperature=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
            )

            # `segments` is a generator - the actual work happens here.
            texts = [segment.text.strip() for segment in segments]
        except Exception as exc:
            raise TranscriptionError(
                f"Could not transcribe the audio: {exc}",
                suggestion="The file may be corrupt or in an unsupported format.",
            ) from exc

        parts = [text for text in texts if text]
        transcript = Transcript(
            text=" ".join(parts).strip(),
            language=getattr(info, "language", None),
            language_probability=float(getattr(info, "language_probability", 0.0) or 0.0),
            audio_seconds=float(getattr(info, "duration", 0.0) or 0.0),
            elapsed_seconds=time.time() - started,
            model=self.model_size,
            segments=parts,
        )

        logger.info(
            f"{'Translated' if task == 'translate' else 'Transcribed'} "
            f"{filename_hint}: {transcript.summary()}"
        )
        return transcript

    async def transcribe(self, data: bytes, *, filename_hint: str = "audio",
                         task: str = "transcribe") -> Transcript:
        """Async wrapper - runs the blocking work on a worker thread."""
        return await asyncio.to_thread(
            self.transcribe_bytes, data, filename_hint=filename_hint, task=task
        )

    # -- diagnostics ------------------------------------------------------

    def get_state(self) -> dict:
        """Shown on /health so an operator can see what is actually running."""
        return {
            "enabled": settings.VOICE_INPUT_ENABLED,
            "model": self.model_size,
            "device": self.device,
            "compute_type": self.compute_type,
            "language": self.language or "auto-detect",
            "loaded": self.is_loaded,
            "error": self._load_error.message if self._load_error else None,
        }


# ---------------------------------------------------------------------------
# Process-wide instance
# ---------------------------------------------------------------------------

_transcriber: Optional[Transcriber] = None
_instance_lock = threading.Lock()


def get_transcriber() -> Transcriber:
    """The shared Transcriber. The model is loaded once per process, not per call."""
    global _transcriber
    if _transcriber is None:
        with _instance_lock:
            if _transcriber is None:
                _transcriber = Transcriber()
    return _transcriber


def reset_transcriber() -> None:
    """Drop the shared instance. Used by tests and by config reloads."""
    global _transcriber
    with _instance_lock:
        _transcriber = None
