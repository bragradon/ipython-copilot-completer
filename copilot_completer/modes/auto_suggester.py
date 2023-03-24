from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

from IPython.terminal.shortcuts.auto_suggest import NavigableAutoSuggestFromHistory
from prompt_toolkit.auto_suggest import Suggestion, ThreadedAutoSuggest
from requests import RequestException

from ..completer import get_copilot_suggestion
from ..settings import settings


if TYPE_CHECKING:
    from prompt_toolkit.buffer import Buffer
    from prompt_toolkit.document import Document


class CopilotSuggester(NavigableAutoSuggestFromHistory):
    def get_suggestion(
        self,
        buffer: Buffer,
        document: Document,
    ) -> Suggestion | None:

        # Consider only the last line for the suggestion.
        text = document.text.rsplit("\n", 1)[-1]

        # Only create a suggestion when this is not an empty line.
        with suppress(RequestException):
            if (
                text.strip()
                and settings.token
                and (suggestion := get_copilot_suggestion(text))
            ):
                return Suggestion(suggestion)

        # Fallback to history
        return super().get_suggestion(buffer, document)


def enable_copilot_suggester(ipython):
    if getattr(ipython, "pt_app", None):
        ipython.autosuggestions_provider = None
        ipython.pt_app.auto_suggest = ThreadedAutoSuggest(CopilotSuggester())


def disable_copilot_suggester(ipython):
    # Revert to auto-suggesting from history
    if getattr(ipython, "pt_app", None):
        ipython.autosuggestions_provider = "NavigableAutoSuggestFromHistory"
