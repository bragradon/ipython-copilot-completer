from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from prompt_toolkit.auto_suggest import (
    AutoSuggestFromHistory,
    Suggestion,
    ThreadedAutoSuggest,
)

from ..completer import get_copilot_suggestion
from ..settings import settings


if TYPE_CHECKING:
    from prompt_toolkit.buffer import Buffer
    from prompt_toolkit.document import Document


class CopilotSuggester(AutoSuggestFromHistory):
    def get_suggestion(
        self,
        buffer: Buffer,
        document: Document,
    ) -> Optional[Suggestion]:

        # Consider only the last line for the suggestion.
        text = document.text.rsplit("\n", 1)[-1]

        # Only create a suggestion when this is not an empty line.
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
        ipython.pt_app.auto_suggest = ThreadedAutoSuggest(CopilotSuggester())


def disable_copilot_suggester(ipython):
    # Revert to auto-suggesting from history
    ipython.autosuggestions_provider = "AutoSuggestFromHistory"
