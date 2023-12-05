from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from prompt_toolkit.auto_suggest import AutoSuggest, Suggestion
from typing_extensions import override

from .completer import fetch_copilot_suggestion
from .settings import settings


if TYPE_CHECKING:
    from IPython.terminal.interactiveshell import TerminalInteractiveShell
    from prompt_toolkit.buffer import Buffer
    from prompt_toolkit.document import Document


class AsyncCopilotSuggest(AutoSuggest):
    def __init__(self):
        super().__init__()
        self.loop = asyncio.get_event_loop()
        self.last_text = ""
        self.debounce_time = 0.5  # 500 milliseconds

    @override
    def get_suggestion(
        self,
        buffer: Buffer,
        document: Document,
    ) -> Suggestion | None:
        # Consider only the last line for the suggestion.
        text = document.text.rsplit("\n", 1)[-1].strip()

        # Only proceed if text has changed and is not empty
        if text != self.last_text and text and settings.token:
            self.last_text = text
            _ = asyncio.ensure_future(self.debounce_fetch(buffer, text))

        return None

    async def debounce_fetch(self, buffer: Buffer, text: str):
        await asyncio.sleep(self.debounce_time)
        if text == self.last_text:  # Check if text is unchanged
            suggestion = await fetch_copilot_suggestion(text)
            if suggestion:
                buffer.suggestion = Suggestion(suggestion)
                buffer.on_suggestion_set.fire()


def enable_copilot_suggester(ipython: TerminalInteractiveShell):
    if getattr(ipython, "pt_app", None) and ipython.pt_app:
        ipython.autosuggestions_provider = None
        ipython.pt_app.auto_suggest = AsyncCopilotSuggest()


def disable_copilot_suggester(ipython: TerminalInteractiveShell):
    # Revert to auto-suggesting from history
    if getattr(ipython, "pt_app", None):
        ipython.autosuggestions_provider = "NavigableAutoSuggestFromHistory"
