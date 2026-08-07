"""Microphone capture and local whisper.cpp transcription."""

from __future__ import annotations

import tempfile
import time
import wave
import winsound
from pathlib import Path

import httpx
import numpy as np
import sounddevice as sd


WHISPER_URL = "http://127.0.0.1:2022/inference"
SAMPLE_RATE = 16_000


class WhisperEars:
    def __init__(self, duration_seconds: float = 6.0) -> None:
        self.duration_seconds = duration_seconds

    def listen(self) -> tuple[str, float]:
        for remaining in (3, 2, 1):
            print(remaining, flush=True)
            winsound.Beep(700, 120)
            time.sleep(0.35)

        winsound.Beep(1_000, 180)
        print("Listening...", flush=True)
        recording = sd.rec(
            int(self.duration_seconds * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            device=sd.default.device[0],
        )
        sd.wait()

        if float(np.max(np.abs(recording))) < 0.005:
            raise RuntimeError("The microphone recording was nearly silent.")

        return self.transcribe(recording)

    def transcribe(self, recording: np.ndarray) -> tuple[str, float]:
        """Transcribe an in-memory mono float32 recording."""
        if recording.ndim == 1:
            recording = recording.reshape(-1, 1)
        if recording.size == 0 or float(np.max(np.abs(recording))) < 0.005:
            raise RuntimeError("The microphone recording was nearly silent.")

        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = Path(temp_file.name)
            self._write_wav(temp_path, recording)

            started = time.perf_counter()
            with temp_path.open("rb") as audio_file:
                response = httpx.post(
                    WHISPER_URL,
                    files={"file": ("speech.wav", audio_file, "audio/wav")},
                    data={"response_format": "json", "temperature": "0.0"},
                    timeout=90.0,
                )
            elapsed = time.perf_counter() - started
            response.raise_for_status()
            transcript = str(response.json().get("text", "")).strip()
            if not transcript:
                raise RuntimeError("Whisper returned an empty transcript.")
            return transcript, elapsed
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

    @staticmethod
    def _write_wav(path: Path, recording: np.ndarray) -> None:
        pcm = np.clip(recording[:, 0], -1.0, 1.0)
        pcm16 = (pcm * 32767).astype(np.int16)
        with wave.open(str(path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(SAMPLE_RATE)
            wav_file.writeframes(pcm16.tobytes())
