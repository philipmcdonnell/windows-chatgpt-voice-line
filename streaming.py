"""Incremental text-to-sentence buffering for streamed Codex replies."""

from __future__ import annotations

import re
from collections.abc import AsyncIterator


SENTENCE = re.compile(r'^(.+?[.!?]["\'’”]?)(?=\s|$)', re.DOTALL)


class SentenceBuffer:
    def __init__(self) -> None:
        self._buffer = ""

    def feed(self, delta: str) -> list[str]:
        self._buffer += delta
        sentences: list[str] = []
        while True:
            self._buffer = self._buffer.lstrip()
            match = SENTENCE.match(self._buffer)
            if match is None:
                break
            sentence = match.group(1).strip()
            if sentence:
                sentences.append(sentence)
            self._buffer = self._buffer[match.end() :]
        return sentences

    def flush(self) -> str | None:
        remainder = self._buffer.strip()
        self._buffer = ""
        return remainder or None


async def sentence_stream(deltas: AsyncIterator[str]) -> AsyncIterator[str]:
    buffer = SentenceBuffer()
    async for delta in deltas:
        for sentence in buffer.feed(delta):
            yield sentence
    remainder = buffer.flush()
    if remainder:
        yield remainder
