from __future__ import annotations

import os
from types import MethodType
from typing import TYPE_CHECKING

from IPython import get_ipython
from IPython.terminal.shortcuts import cursor_in_leading_ws
from prompt_toolkit.auto_suggest import ThreadedAutoSuggest
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.key_binding.bindings.completion import (
    display_completions_like_readline,
)
from prompt_toolkit.keys import Keys
from prompt_toolkit.filters import (
    HasFocus,
    HasSelection,
    vi_insert_mode,
    emacs_insert_mode,
)

from .auto_suggester import CopilotSuggester
from .completer import copilot_completer

if TYPE_CHECKING:
    from IPython.core.interactiveshell import InteractiveShell

# GitHub access token
# Extract this from an ide using Copilot by sniffing the network traffic
GITHUB_COPILOT_ACCESS_TOKEN = os.environ.get("GITHUB_COPILOT_ACCESS_TOKEN", None)

# Whether the completions should be displayed inline with other completions
inline_copilot = os.environ.get("GITHUB_COPILOT_INLINE_COMPLETIONS", "0") == "1"

# Whether completions should be displayed as an autosuggestion
auto_suggest = os.environ.get("GITHUB_COPILOT_AUTO_SUGGEST", "0") == "1"


def load_ipython_extension(ipython: InteractiveShell):
    """
    Add a custom completer to IPython that uses GitHub Copilot
    This completer patches the IPython completers to put Copilot at the start
    """
    if not GITHUB_COPILOT_ACCESS_TOKEN:
        print("GITHUB_ACCESS_TOKEN environment variable is not set")
        return

    completer = ipython.Completer

    if "copilot_completer" in completer.disable_matchers:
        completer.disable_matchers.remove("copilot_completer")
        return

    ipython.set_custom_completer(copilot_completer)

    if inline_copilot:

        def put_copilot_completion_first(self, *args, **kwargs):
            """
            Copilot completion is always the first completion
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

        if hasattr(completer, "_orig_completions"):
            completer._completions = completer._orig_completions
            delattr(completer, "_orig_completions")

        completer._orig_completions = completer._completions
        completer._completions = MethodType(put_copilot_completion_first, completer)
    elif auto_suggest:
        completer.disable_matchers.append("copilot_completer")
        if getattr(ipython, "pt_app", None):
            ipython.pt_app.auto_suggest = ThreadedAutoSuggest(CopilotSuggester())
    else:
        # Add a key binding to get Copilot completions
        completer.disable_matchers.append("copilot_completer")
        if getattr(ipython, "pt_app", None):
            insert_mode = vi_insert_mode | emacs_insert_mode
            registry = ipython.pt_app.key_bindings
            registry.add_binding(
                Keys.ControlSpace,
                filter=(
                    HasFocus(DEFAULT_BUFFER)
                    & ~HasSelection()
                    & insert_mode
                    & ~cursor_in_leading_ws
                ),
            )(get_copilot_completions)


def unload_ipython_extension(ipython: InteractiveShell):
    ipython.Completer.disable_matchers.append("copilot_completer")

    if inline_copilot:
        if hasattr(completer := ipython.Completer, "_orig_completions"):
            completer._completions = completer._orig_completions
            delattr(completer, "_orig_completions")
    else:
        if getattr(ipython, "pt_app", None):
            registry = ipython.pt_app.key_bindings
            registry.remove(get_copilot_completions)


def get_copilot_completions(event):
    """
    Get completions from GitHub Copilot for key binding
    This temporarily replaces the IPython completers with the Copilot completer
    """
    ip = get_ipython()
    completer = ip.Completer

    use_jedi = completer.use_jedi
    suppress_competing_matchers = completer.suppress_competing_matchers
    completer.use_jedi = False
    completer.suppress_competing_matchers = True
    completer.disable_matchers.remove("copilot_completer")

    try:
        display_completions_like_readline(event)
    finally:
        completer.use_jedi = use_jedi
        completer.suppress_competing_matchers = suppress_competing_matchers
        completer.disable_matchers.append("copilot_completer")
