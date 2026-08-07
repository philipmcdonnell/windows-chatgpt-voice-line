"""Best-effort state files for optional Alfred visualizers."""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np


class SignalBus:
    def __init__(self, root: Path) -> None:
        self.root = root

    def state(self, value: str) -> None:
        if value not in {"idle", "listening", "thinking", "speaking"}:
            return
        self._write(".voice_state", value)

    def waveform(self, samples: np.ndarray) -> None:
        try:
            mono = np.asarray(samples, dtype=np.float32).reshape(-1)
            if mono.size == 0:
                points = [0.0] * 64
            else:
                indices = np.linspace(0, mono.size - 1, 64).astype(int)
                points = np.abs(mono[indices]).astype(float).tolist()
            self._write(
                ".voice_waveform",
                json.dumps({"ts": time.time(), "samples": points}),
            )
            self.state("speaking")
        except Exception:
            pass
    def _write(self, name: str, contents: str) -> None:
        try:
            (self.root / name).write_text(contents, encoding="utf-8")
        except Exception:
            pass
