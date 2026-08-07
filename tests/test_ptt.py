from __future__ import annotations

import asyncio
import unittest

from pynput import keyboard

from ptt import RightCtrlListener


class RightCtrlListenerTests(unittest.IsolatedAsyncioTestCase):
    async def test_filters_repeat_and_ignores_other_keys(self) -> None:
        listener = RightCtrlListener(asyncio.get_running_loop())
        listener._on_press(keyboard.Key.ctrl_l)
        listener._on_press(keyboard.Key.ctrl_r)
        listener._on_press(keyboard.Key.ctrl_r)
        listener._on_release(keyboard.Key.ctrl_l)
        listener._on_release(keyboard.Key.ctrl_r)
        await asyncio.sleep(0)

        first = listener.events.get_nowait()
        second = listener.events.get_nowait()
        self.assertEqual((first.kind, second.kind), ("press", "release"))
        self.assertTrue(listener.events.empty())


if __name__ == "__main__":
    unittest.main()
