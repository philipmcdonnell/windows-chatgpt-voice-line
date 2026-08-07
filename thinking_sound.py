"""A quiet, cancellable local sound loop for Alfred's thinking state."""

from __future__ import annotations

import threading
from pathlib import Path

import sounddevice as sd
import soundfile as sf


class ThinkingSound:
    """Play a WAV in short blocks until stopped, without using sd.play()."""

    def __init__(
        self, path: Path, block_size: int = 1024, delay_seconds: float = 0.65
    ) -> None:
        samples, sample_rate = sf.read(path, dtype="float32", always_2d=True)
        self._samples = samples
        self._sample_rate = sample_rate
        self._block_size = block_size
        self._delay_seconds = delay_seconds
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop.clear()
            self._thread = threading.Thread(
                target=self._run, name="alfred-thinking-sound", daemon=True
            )
            self._thread.start()

    def stop(self) -> None:
        with self._lock:
            thread = self._thread
            self._stop.set()
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=1.0)
        with self._lock:
            if self._thread is thread:
                self._thread = None

    def _run(self) -> None:
        try:
            if self._stop.wait(self._delay_seconds):
                return
            channels = self._samples.shape[1]
            with sd.OutputStream(
                samplerate=self._sample_rate, channels=channels, dtype="float32"
            ) as stream:
                while not self._stop.is_set():
                    for offset in range(0, len(self._samples), self._block_size):
                        if self._stop.is_set():
                            return
                        stream.write(self._samples[offset : offset + self._block_size])
        except Exception as exc:
            print(f"Thinking sound unavailable: {exc}", flush=True)
