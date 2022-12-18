from __future__ import annotations

from types import MethodType


def add_to_tab_completions(ipython):
    def put_copilot_completion_first(self, *args, **kwargs):
        """
        Ensure Copilot completion is always the first completion in the list
        """
        copilot_completions = []
        other_completions = []

        for completion in self._orig_completions(*args, **kwargs):
            if completion.type == "copilot":
                copilot_completions.append(completion)
            else:
                other_completions.append(completion)
        else:
            yield from copilot_completions
            yield from other_completions

    # Monkey patch the completions method
    completer = ipython.Completer
    if hasattr(completer, "_orig_completions"):
        # Already patched - remove the old patch
        completer._completions = completer._orig_completions
        delattr(completer, "_orig_completions")

    completer._orig_completions = completer._completions
    completer._completions = MethodType(put_copilot_completion_first, completer)


def remove_from_tab_completions(ipython):
    completer = ipython.Completer
    if hasattr(completer, "_orig_completions"):
        # Remove the monkey patch
        completer._completions = completer._orig_completions
        delattr(completer, "_orig_completions")
