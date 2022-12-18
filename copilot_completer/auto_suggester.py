from typing import Optional

from IPython import get_ipython
from IPython.core.completer import provisionalcompleter
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory, Suggestion
from prompt_toolkit.document import Document
from prompt_toolkit.patch_stdout import patch_stdout


class CopilotSuggester(AutoSuggestFromHistory):
    def get_suggestion(
        self, buffer: "Buffer", document: Document
    ) -> Optional[Suggestion]:

        text = document.text.rsplit("\n", 1)[-1]
        if text.strip():
            # Get a suggestion from Copilot
            suggestion = self.get_copilot_suggestion(text)
            if suggestion:
                return Suggestion(suggestion)

        return super().get_suggestion(buffer, document)

    def get_copilot_suggestion(self, text: str) -> Optional[str]:
        ip = get_ipython()
        completer = ip.Completer

        # Store the current completers
        use_jedi = completer.use_jedi
        suppress_competing_matchers = completer.suppress_competing_matchers

        # Temporarily replace the completers with the Copilot completer
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
            # Restore the original completers
            completer.use_jedi = use_jedi
            completer.suppress_competing_matchers = suppress_competing_matchers
            completer.disable_matchers.append("copilot_completer")
