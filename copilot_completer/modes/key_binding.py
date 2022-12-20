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
from prompt_toolkit.keys import Keys

from copilot_completer.completer import get_copilot_suggestion


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

    buffer = event.current_buffer

    if suggestion := get_copilot_suggestion(buffer.document.text):
        buffer.insert_text(suggestion)
