"""Global Right Ctrl push-to-talk input and microphone recording."""

from __future__ import annotations

import asyncio
import threading
import time
from dataclasses import dataclass

import numpy as np
import sounddevice as sd
from pynput import keyboard


SAMPLE_RATE = 16_000
RELEASE_TAIL_SECONDS = 0.18
MINIMUM_HOLD_SECONDS = 0.25


@dataclass(frozen=True, slots=True)
class PushToTalkEvent:
    kind: str
    timestamp: float


class RightCtrlListener:
    """Translate global Right Ctrl transitions into asyncio events."""

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self.events: asyncio.Queue[PushToTalkEvent] = asyncio.Queue()
        self._loop = loop
        self._held = False
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )

    def start(self) -> None:
        self._listener.start()

    def stop(self) -> None:
        self._listener.stop()

    def _emit(self, kind: str) -> None:
        self._loop.call_soon_threadsafe(
            self.events.put_nowait,
            PushToTalkEvent(kind, time.perf_counter()),
        )

    def _on_press(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        if key != keyboard.Key.ctrl_r or self._held:
            return
        self._held = True
        self._emit("press")

    def _on_release(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        if key != keyboard.Key.ctrl_r or not self._held:
            return
        self._held = False
        self._emit("release")


class PushToTalkRecorder:
    """Capture microphone samples only while explicitly active."""

    def __init__(self) -> None:
        self._chunks: list[np.ndarray] = []
        self._lock = threading.Lock()
        self._stream: sd.InputStream | None = None
        self._started_at = 0.0

    @property
    def active(self) -> bool:
        return self._stream is not None

    def start(self) -> None:
        if self.active:
            return
        with self._lock:
            self._chunks.clear()
        self._started_at = time.perf_counter()
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            device=sd.default.device[0],
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> np.ndarray | None:
        stream = self._stream
        if stream is None:
            return None
        held_seconds = time.perf_counter() - self._started_at
        time.sleep(RELEASE_TAIL_SECONDS)
        stream.stop()
        stream.close()
        self._stream = None

        with self._lock:
            recording = np.concatenate(self._chunks, axis=0) if self._chunks else None
            self._chunks.clear()
        if held_seconds < MINIMUM_HOLD_SECONDS:
            return None
        return recording

    def abort(self) -> None:
        stream = self._stream
        if stream is not None:
            stream.abort()
            stream.close()
            self._stream = None
        with self._lock:
            self._chunks.clear()

    def _callback(self, indata, _frames, _time_info, status) -> None:
        if status:
            print(f"Microphone status: {status}", flush=True)
        with self._lock:
            self._chunks.append(indata.copy())
