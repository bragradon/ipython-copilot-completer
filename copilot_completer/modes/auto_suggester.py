from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from IPython import get_ipython
from IPython.core.completer import provisionalcompleter
from prompt_toolkit.auto_suggest import (
    AutoSuggestFromHistory,
    Suggestion,
    ThreadedAutoSuggest,
)
from prompt_toolkit.patch_stdout import patch_stdout

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

        text = document.text.rsplit("\n", 1)[-1]
        if text.strip() and settings.token:
            # Get a suggestion from Copilot
            suggestion = self.get_copilot_suggestion(text)
            if suggestion:
                return Suggestion(suggestion)

        return super().get_suggestion(buffer, document)

    def get_copilot_suggestion(self, text: str) -> Optional[str]:
        ip = get_ipython()
        completer = ip.Completer

        # Store the current completer state
        # We want jedi off and to suppress all other matchers
        use_jedi = completer.use_jedi
        suppress_competing_matchers = completer.suppress_competing_matchers

        # Temporarily replace the completer state with the Copilot completer
        completer.use_jedi = False
        completer.suppress_competing_matchers = True
        completer.disable_matchers.remove("copilot_completer")

        try:
            with patch_stdout(), provisionalcompleter():
                suggestion = list(completer.completions(text, 0))

            if suggestion:
                return suggestion[0].text
            else:
                return None
        finally:
            # Restore the original completer state
            completer.use_jedi = use_jedi
            completer.suppress_competing_matchers = suppress_competing_matchers
            completer.disable_matchers.append("copilot_completer")


def enable_copilot_suggester(ipython):
    completer = ipython.Completer
    completer.disable_matchers.append("copilot_completer")
    if getattr(ipython, "pt_app", None):
        ipython.pt_app.auto_suggest = ThreadedAutoSuggest(CopilotSuggester())


def disable_copilot_suggester(ipython):
    # Revert to auto-suggesting from history
    ipython.autosuggestions_provider = "AutoSuggestFromHistory"
