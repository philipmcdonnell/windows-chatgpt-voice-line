"""Background console-line input for typed voice turns on Windows."""

from __future__ import annotations

import asyncio
import threading


class TypedInput:
    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self.lines: asyncio.Queue[str] = asyncio.Queue()
        self._loop = loop
        self._thread = threading.Thread(target=self._read_lines, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def _read_lines(self) -> None:
        while True:
            try:
                line = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                line = "goodbye"
            self._loop.call_soon_threadsafe(self.lines.put_nowait, line)
            if line.lower() in {"goodbye", "end voice mode", "hang up", "/quit"}:
                return
