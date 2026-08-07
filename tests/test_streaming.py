from __future__ import annotations

import asyncio
import unittest

from streaming import SentenceBuffer, sentence_stream


class SentenceBufferTests(unittest.TestCase):
    def test_waits_for_complete_sentence(self) -> None:
        buffer = SentenceBuffer()
        self.assertEqual(buffer.feed("Good afternoon"), [])
        self.assertEqual(buffer.feed(", Phil."), ["Good afternoon, Phil."])
        self.assertIsNone(buffer.flush())

    def test_returns_multiple_sentences_and_remainder(self) -> None:
        buffer = SentenceBuffer()
        self.assertEqual(
            buffer.feed("First sentence. Second sentence! Partial"),
            ["First sentence.", "Second sentence!"],
        )
        self.assertEqual(buffer.flush(), "Partial")

    def test_preserves_closing_quote(self) -> None:
        buffer = SentenceBuffer()
        self.assertEqual(buffer.feed('Alfred said, "Ready." '), ['Alfred said, "Ready."'])


class SentenceStreamTests(unittest.IsolatedAsyncioTestCase):
    async def test_stream_flushes_final_unpunctuated_text(self) -> None:
        async def deltas():
            for delta in ("One.", " Two", " words"):
                yield delta
                await asyncio.sleep(0)

        self.assertEqual(
            [sentence async for sentence in sentence_stream(deltas())],
            ["One.", "Two words"],
        )


if __name__ == "__main__":
    unittest.main()
