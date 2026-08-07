# Windows ChatGPT Voice Line

Give a Codex-powered assistant a local Windows voice: hold **Right Ctrl**, speak, release, and hear a concise spoken reply grounded in your chosen Codex workspace and its `AGENTS.md` instructions.

This is an independent ChatGPT/Codex adaptation of [Jared Rhodenizer's Voice Line: Windows Edition](https://github.com/jaredrhod/prompts/blob/main/voice-line-prompt-windows.md). See [ATTRIBUTION.md](ATTRIBUTION.md).

## What it does

- Captures audio only while Right Ctrl is held
- Transcribes locally with whisper.cpp `base.en`
- Uses one persistent Codex conversation and your saved ChatGPT/Codex authentication
- Loads context from a configurable local Codex workspace
- Speaks locally through Kokoro's British `bm_george` voice by default
- Streams complete sentences into speech to reduce perceived latency
- Supports interruption, typed input, quit phrases, and optional signal files
- Plays a delayed local processing sound while the response is prepared

The microphone, transcription, and speech synthesis remain local. The transcript is sent to Codex because Codex is the assistant brain.

## Requirements

- Windows 10 or 11, 64-bit
- A working microphone and speakers
- Windows PowerShell 5.1 or PowerShell 7
- `winget`, or an existing [uv](https://docs.astral.sh/uv/) installation
- A working Codex sign-in (`codex login` if needed)
- A local Codex workspace; `AGENTS.md` is recommended for persistent identity and behavior

No API key is required when the Codex SDK can reuse your saved ChatGPT/Codex authentication. Account availability and usage limits still apply.

## Quick install

Clone the repository, open PowerShell in it, and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup.ps1 `
  -CodexWorkspace "C:\Users\YOU\Documents\your-assistant-workspace" `
  -UserName "Your Name" `
  -AssistantName "Alfred"
```

The installer creates an isolated Python 3.12 environment, installs pinned Python packages, downloads the pinned whisper.cpp build and speech models, creates your ignored `config.json`, compiles the project, and runs the automated tests. Downloads are several hundred megabytes.

Then start the application:

```powershell
.\run-voice-line.bat
```

## Controls

- Hold **Right Ctrl** while speaking; release to send.
- A tap shorter than 250 ms is ignored.
- Press Right Ctrl while the assistant is speaking to interrupt and begin another recording.
- Type a console line to use the same conversation without the microphone.
- Type `/quit`, `goodbye`, `end voice mode`, or `hang up` to close.
- `Ctrl-C` also closes the application.

## Configuration

`setup.ps1` creates `config.json`, which is excluded from Git. To configure manually, copy `config.example.json` and edit:

```json
{
  "assistant_name": "Alfred",
  "user_name": "Your Name",
  "codex_workspace": "C:\\Users\\YOU\\Documents\\your-assistant-workspace",
  "voice": "bm_george",
  "forms_of_address": ["sir", "kind sir"]
}
```

The workspace is the durable brain. Voice Line does not create a memory system by itself; it gives voice access to the Codex workspace you already use.

## Privacy and safety

- The microphone opens only while Right Ctrl is held, plus a 180 ms release tail.
- Temporary transcription WAV files are deleted immediately.
- Whisper and Kokoro listen only on or run only on the local computer.
- whisper.cpp binds to `127.0.0.1:2022`, not the network.
- Voice Line uses Codex's normal sandbox and approval safeguards.
- `config.json`, downloaded models, logs, recordings, and signal files are ignored by Git.
- Review consequential actions on screen; a charming voice is not authorization.

## Troubleshooting

List audio devices:

```powershell
.\.venv\Scripts\python.exe .\list_audio_devices.py
```

Run package checks:

```powershell
.\verify-package.ps1
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

If the Whisper server fails, inspect `whisper-server.stderr.log`. If `config.json` is rejected, confirm the workspace path exists and uses doubled backslashes in JSON.

CPU-only systems work, but response latency depends on the machine and Codex. The tested laptop required roughly nine seconds from key release to first audio before sentence streaming improvements.

## Builder prompt

If you prefer a guided Codex build or want to adapt the architecture, use [windows-voice-line-prompt-chatgpt.md](windows-voice-line-prompt-chatgpt.md). The prompt instructs Codex to inspect the machine, ask for approval before installations, build in phases, and verify the complete loop.

## License

[CC BY-NC-SA 4.0](LICENSE). You may share and adapt this project noncommercially with attribution and the same license.
