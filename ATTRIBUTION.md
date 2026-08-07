# Attribution

This project adapts Jared Rhodenizer's **Voice Line: Windows Edition** concept and build prompt:

- Source: https://github.com/jaredrhod/prompts/blob/main/voice-line-prompt-windows.md
- Author: Jared Rhodenizer
- License: Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International

## Nature of this adaptation

This independent Windows implementation replaces the Claude-specific brain with OpenAI's Codex SDK and adds:

- A persistent Codex thread rooted in a configurable local workspace
- `AGENTS.md`-compatible assistant instructions
- Local whisper.cpp transcription and local Kokoro speech
- Right Ctrl push-to-talk, interruption, and typed input
- Streamed sentence synthesis and playback
- A local processing sound and optional visualizer signals
- A reusable PowerShell installer and configuration file

It is not affiliated with or endorsed by Jared Rhodenizer, OpenAI, Microsoft, or the upstream speech projects.
