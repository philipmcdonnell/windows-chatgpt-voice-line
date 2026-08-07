"""Foreground Right Ctrl and typed conversation loop for Alfred."""

from __future__ import annotations

import asyncio
import contextlib
import time
from pathlib import Path

from brain import AlfredBrain
from ears import WhisperEars
from mouth import KokoroMouth
from ptt import PushToTalkRecorder, RightCtrlListener
from signals import SignalBus
from settings import SETTINGS
from streaming import sentence_stream
from thinking_sound import ThinkingSound
from typed_input import TypedInput


PROJECT_ROOT = Path(__file__).resolve().parent
QUIT_PHRASES = {"goodbye", "end voice mode", "hang up", "/quit"}


async def handle_text(
    text: str,
    brain: AlfredBrain,
    mouth: KokoroMouth,
    bus: SignalBus,
    thinking: ThinkingSound,
) -> None:
    response_started = time.perf_counter()

    async def visible_deltas():
        print("Alfred: ", end="", flush=True)
        async for delta in brain.stream_reply(text):
            print(delta, end="", flush=True)
            yield delta
        print()

    try:
        first_audio, total = await mouth.speak_stream(
            sentence_stream(visible_deltas()), before_first_audio=thinking.stop
        )
        print(
            f"First audio: {first_audio:.2f}s; streamed response/playback: {total:.2f}s; "
            f"turn elapsed: {time.perf_counter() - response_started:.2f}s",
            flush=True,
        )
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        print(f"Voice turn failed: {exc}", flush=True)
    finally:
        thinking.stop()
        bus.state("idle")


async def handle_recording(recording, ears, brain, mouth, bus, thinking) -> None:
    try:
        transcript, whisper_seconds = await asyncio.to_thread(ears.transcribe, recording)
        print(f"You: {transcript} ({whisper_seconds:.2f}s)")
        await handle_text(transcript, brain, mouth, bus, thinking)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        print(f"Voice turn failed: {exc}", flush=True)
        bus.state("idle")


async def cancel_active(
    active_turn: asyncio.Task[None] | None,
    brain: AlfredBrain,
    mouth: KokoroMouth,
) -> None:
    if active_turn is None or active_turn.done():
        return
    mouth.interrupt()
    await brain.interrupt()
    active_turn.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await active_turn


async def main() -> None:
    assistant_name = SETTINGS["assistant_name"]
    voice = SETTINGS["voice"]
    print(f"Loading {assistant_name} and voice {voice}...", flush=True)
    bus = SignalBus(PROJECT_ROOT)
    thinking = ThinkingSound(PROJECT_ROOT / "assets" / "thinking.wav")
    bus.state("thinking")
    mouth = await asyncio.to_thread(KokoroMouth, voice, bus)
    ears = WhisperEars()
    recorder = PushToTalkRecorder()
    loop = asyncio.get_running_loop()
    listener = RightCtrlListener(loop)
    typed = TypedInput(loop)
    active_turn: asyncio.Task[None] | None = None

    async with AlfredBrain() as brain:
        await brain.warmup()
        listener.start()
        typed.start()
        bus.state("idle")
        print(
            "Ready. Hold Right Ctrl to talk; release to send. "
            "Typed lines use the same conversation. Type /quit or press Ctrl-C to exit."
        )
        ptt_wait = asyncio.create_task(listener.events.get())
        typed_wait = asyncio.create_task(typed.lines.get())
        try:
            running = True
            while running:
                done, _pending = await asyncio.wait(
                    {ptt_wait, typed_wait}, return_when=asyncio.FIRST_COMPLETED
                )

                if ptt_wait in done:
                    event = ptt_wait.result()
                    ptt_wait = asyncio.create_task(listener.events.get())
                    if event.kind == "press":
                        thinking.stop()
                        await cancel_active(active_turn, brain, mouth)
                        recorder.start()
                        bus.state("listening")
                        print("Listening...", flush=True)
                    else:
                        recording = await asyncio.to_thread(recorder.stop)
                        if recording is None:
                            bus.state("idle")
                            print("Tap ignored; hold Right Ctrl while speaking.")
                        else:
                            bus.state("thinking")
                            print("Thinking...", flush=True)
                            thinking.start()
                            active_turn = asyncio.create_task(
                                handle_recording(
                                    recording, ears, brain, mouth, bus, thinking
                                )
                            )

                if typed_wait in done:
                    text = typed_wait.result().strip()
                    typed_wait = asyncio.create_task(typed.lines.get())
                    if text.lower() in QUIT_PHRASES:
                        running = False
                        continue
                    if not text:
                        continue
                    await cancel_active(active_turn, brain, mouth)
                    bus.state("thinking")
                    print(f"You: {text}")
                    thinking.start()
                    active_turn = asyncio.create_task(
                        handle_text(text, brain, mouth, bus, thinking)
                    )
        finally:
            ptt_wait.cancel()
            typed_wait.cancel()
            listener.stop()
            recorder.abort()
            thinking.stop()
            mouth.interrupt()
            await cancel_active(active_turn, brain, mouth)
            bus.state("idle")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nVoice line closed.")
