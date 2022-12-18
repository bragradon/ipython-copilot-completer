from __future__ import annotations

from IPython import get_ipython
from IPython.terminal.shortcuts import cursor_in_leading_ws
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.filters import (
    HasFocus,
    HasSelection,
    emacs_insert_mode,
    vi_insert_mode,
)
from prompt_toolkit.key_binding.bindings.completion import (
    display_completions_like_readline,
)
from prompt_toolkit.keys import Keys


def add_key_binding():
    ip = get_ipython()
    if getattr(ip, "pt_app", None):
        insert_mode = vi_insert_mode | emacs_insert_mode
        registry = ip.pt_app.key_bindings
        registry.add_binding(
            Keys.ControlSpace,
            filter=(
                HasFocus(DEFAULT_BUFFER)
                & ~HasSelection()
                & insert_mode
                & ~cursor_in_leading_ws
            ),
        )(get_copilot_completions)


def remove_key_binding():
    ip = get_ipython()
    if getattr(ip, "pt_app", None):
        registry = ip.pt_app.key_bindings
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
