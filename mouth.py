"""Warm local Kokoro TTS with overlapped synthesis and playback."""

from __future__ import annotations

import asyncio
import re
import threading
import time
from collections.abc import AsyncIterator
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path

import numpy as np
import sounddevice as sd
from kokoro_onnx import Kokoro

from signals import SignalBus
from settings import SETTINGS


PROJECT_ROOT = Path(__file__).resolve().parent
MODEL_PATH = PROJECT_ROOT / "models" / "kokoro" / "kokoro-v1.0.onnx"
VOICES_PATH = PROJECT_ROOT / "models" / "kokoro" / "voices-v1.0.bin"
SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


class KokoroMouth:
    def __init__(self, voice: str | None = None, signal_bus: SignalBus | None = None) -> None:
        voice = voice or SETTINGS["voice"]
        self.voice = voice
        self.signal_bus = signal_bus
        self._kokoro = Kokoro(str(MODEL_PATH), str(VOICES_PATH))
        if voice not in self._kokoro.get_voices():
            raise RuntimeError(f"Kokoro voice {voice!r} is unavailable.")
        self._kokoro.create(
            "Voice system ready.", voice=voice, speed=1.0, lang="en-gb"
        )
        self._cancelled = threading.Event()

    def _synthesize(self, sentence: str) -> tuple[np.ndarray, int, float]:
        started = time.perf_counter()
        samples, sample_rate = self._kokoro.create(
            sentence, voice=self.voice, speed=1.0, lang="en-gb"
        )
        return samples, sample_rate, time.perf_counter() - started

    def speak(self, text: str) -> tuple[float, float]:
        self._cancelled.clear()
        sentences = [part.strip() for part in SENTENCE_BOUNDARY.split(text) if part.strip()]
        if not sentences:
            return 0.0, 0.0

        overall_started = time.perf_counter()
        first_audio_seconds = 0.0
        with ThreadPoolExecutor(max_workers=1) as executor:
            pending: Future[tuple[np.ndarray, int, float]] = executor.submit(
                self._synthesize, sentences[0]
            )
            for index, _sentence in enumerate(sentences):
                samples, sample_rate, _synthesis_seconds = pending.result()
                if self._cancelled.is_set():
                    break
                if index == 0:
                    first_audio_seconds = time.perf_counter() - overall_started
                if index + 1 < len(sentences):
                    pending = executor.submit(self._synthesize, sentences[index + 1])
                sd.play(samples, samplerate=sample_rate)
                sd.wait()

        return first_audio_seconds, time.perf_counter() - overall_started

    async def speak_stream(
        self,
        sentences: AsyncIterator[str],
        before_first_audio: Callable[[], None] | None = None,
    ) -> tuple[float, float]:
        """Overlap synthesis of the next sentence with current playback."""
        self._cancelled.clear()
        started = time.perf_counter()
        first_audio: float | None = None
        audio_queue: asyncio.Queue[tuple[np.ndarray, int] | None] = asyncio.Queue()

        async def synthesize() -> None:
            try:
                async for sentence in sentences:
                    if self._cancelled.is_set():
                        break
                    samples, sample_rate, _elapsed = await asyncio.to_thread(
                        self._synthesize, sentence
                    )
                    if self._cancelled.is_set():
                        break
                    await audio_queue.put((samples, sample_rate))
            finally:
                await audio_queue.put(None)

        async def play() -> None:
            nonlocal first_audio
            while True:
                audio = await audio_queue.get()
                if audio is None or self._cancelled.is_set():
                    break
                samples, sample_rate = audio
                if first_audio is None:
                    if before_first_audio is not None:
                        await asyncio.to_thread(before_first_audio)
                    first_audio = time.perf_counter() - started
                await asyncio.to_thread(self._play, samples, sample_rate)

        await asyncio.gather(synthesize(), play())
        return first_audio or 0.0, time.perf_counter() - started

    @staticmethod
    def _play_raw(samples: np.ndarray, sample_rate: int) -> None:
        sd.play(samples, samplerate=sample_rate)
        sd.wait()

    def _play(self, samples: np.ndarray, sample_rate: int) -> None:
        if self.signal_bus is not None:
            self.signal_bus.state("speaking")
            self.signal_bus.waveform(samples)
        self._play_raw(samples, sample_rate)
        if self.signal_bus is not None and not self._cancelled.is_set():
            self.signal_bus.state("idle")

    def interrupt(self) -> None:
        self._cancelled.set()
        sd.stop()
