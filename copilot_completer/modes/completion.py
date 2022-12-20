from __future__ import annotations

from types import MethodType

from ..completer import copilot_completer


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

    # If the copilot completer is in the disabled matchers then we have already loaded
    # the extension so we don't need to do anything except re-enable the completer
    if "copilot_completer" in (completer := ipython.Completer).disable_matchers:
        print("Copilot extension already loaded")
        completer.disable_matchers.remove("copilot_completer")
    else:
        # Add our completer to the front of the list of completers
        ipython.set_custom_completer(copilot_completer)

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

    # Disable the copilot completer
    if "copilot_completer" not in completer.disable_matchers:
        completer.disable_matchers.append("copilot_completer")

    # Remove the monkey patch
    if hasattr(completer, "_orig_completions"):
        completer._completions = completer._orig_completions
        delattr(completer, "_orig_completions")
