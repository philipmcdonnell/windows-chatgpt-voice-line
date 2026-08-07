"""Persistent Codex brain for Alfred Voice Line."""

from __future__ import annotations

from collections.abc import AsyncIterator
from openai_codex import AsyncCodex, AsyncThread, Sandbox
from openai_codex.generated.v2_all import AgentMessageDeltaNotification

from settings import SETTINGS

ASSISTANT_NAME = SETTINGS["assistant_name"]
USER_NAME = SETTINGS["user_name"]
CODEX_WORKSPACE = SETTINGS["codex_workspace"]
FORMS_OF_ADDRESS = SETTINGS.get("forms_of_address", ["sir"])

SPOKEN_INSTRUCTIONS = f"""
You are speaking aloud as {ASSISTANT_NAME}, {USER_NAME}'s assistant. Follow the
workspace's AGENTS.md instructions when present. Write for the ear: use short,
natural sentences without Markdown, code blocks, tables, citations, or long
lists unless {USER_NAME} explicitly asks for them. Be concise, candid, formal, and
occasionally dryly sarcastic. Never claim an external action succeeded unless
you verified it. When a requested action is consequential, request the same
approval you would require in a normal Codex session.

Do not address {USER_NAME} in every response. Usually omit a form of address.
When one sounds natural, vary among {', '.join([USER_NAME, *FORMS_OF_ADDRESS])}.
Never use the same form of address in consecutive responses.
""".strip()


class AlfredBrain:
    """Own one Codex process and one warm conversation thread."""

    def __init__(self) -> None:
        self._codex: AsyncCodex | None = None
        self._thread: AsyncThread | None = None
        self._active_turn = None

    async def __aenter__(self) -> "AlfredBrain":
        self._codex = AsyncCodex()
        await self._codex.__aenter__()
        self._thread = await self._codex.thread_start(
            cwd=str(CODEX_WORKSPACE),
            developer_instructions=SPOKEN_INSTRUCTIONS,
            sandbox=Sandbox.workspace_write,
        )
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        if self._codex is not None:
            await self._codex.__aexit__(exc_type, exc, traceback)
        self._thread = None
        self._codex = None

    async def account_summary(self) -> str:
        if self._codex is None:
            raise RuntimeError("AlfredBrain has not been started.")
        account = await self._codex.account()
        return account.model_dump_json(exclude_none=True)

    async def ask(self, text: str) -> str:
        if self._thread is None:
            raise RuntimeError("AlfredBrain has not been started.")
        result = await self._thread.run(self._voice_prompt(text))
        response = (result.final_response or "").strip()
        if not response:
            raise RuntimeError("Codex completed the turn without a final response.")
        return response

    async def stream_reply(self, text: str) -> AsyncIterator[str]:
        """Yield assistant text deltas as Codex generates them."""
        if self._thread is None:
            raise RuntimeError("AlfredBrain has not been started.")
        voice_prompt = self._voice_prompt(text)
        turn = await self._thread.turn(voice_prompt)
        self._active_turn = turn
        try:
            async for event in turn.stream():
                payload = event.payload
                if isinstance(payload, AgentMessageDeltaNotification) and payload.delta:
                    yield payload.delta
        finally:
            self._active_turn = None

    async def interrupt(self) -> None:
        """Interrupt the current Codex turn, if one is active."""
        if self._active_turn is not None:
            await self._active_turn.interrupt()

    async def warmup(self) -> None:
        if self._thread is None:
            raise RuntimeError("AlfredBrain has not been started.")
        result = await self._thread.run(
            "Run the AGENTS.md startup sequence now and load the required vault "
            "context. This is a silent initialization turn. Reply only: Ready."
        )
        if not (result.final_response or "").strip():
            raise RuntimeError("Codex warm-up completed without a response.")

    @staticmethod
    def _voice_prompt(text: str) -> str:
        return (
            f"{USER_NAME} said this through the voice interface:\n\n"
            f"{text}\n\n"
            "Answer in no more than two short spoken sentences. The first "
            "sentence must contain no more than six words; the second must "
            "contain no more than fourteen words. Give only the direct answer: "
            "no Markdown, headings, lists, citations, progress report, or "
            "housekeeping commentary. Use tools only when the answer actually "
            f"requires them. Usually do not address {USER_NAME} by name or title; when "
            "it is natural, follow the varied forms-of-address rule in your "
            "spoken instructions."
        )
