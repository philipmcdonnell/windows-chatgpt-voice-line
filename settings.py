"""Load local Voice Line settings without publishing personal configuration."""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_ROOT / "config.json"


def load_settings() -> dict:
    if not CONFIG_PATH.exists():
        raise RuntimeError(
            "config.json is missing. Copy config.example.json to config.json "
            "and set your Codex workspace and names."
        )
    settings = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    required = {"assistant_name", "user_name", "codex_workspace", "voice"}
    missing = sorted(required.difference(settings))
    if missing:
        raise RuntimeError(f"config.json is missing: {', '.join(missing)}")
    workspace = Path(settings["codex_workspace"]).expanduser()
    if not workspace.is_dir():
        raise RuntimeError(f"Codex workspace does not exist: {workspace}")
    settings["codex_workspace"] = workspace
    return settings


SETTINGS = load_settings()
