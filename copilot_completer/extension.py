from __future__ import annotations

from typing import TYPE_CHECKING

from .completer import copilot_completer
from .modes import (
    add_key_binding,
    add_to_tab_completions,
    disable_copilot_suggester,
    enable_copilot_suggester,
    remove_from_tab_completions,
    remove_key_binding,
)
from .settings import settings


if TYPE_CHECKING:
    from IPython.core.interactiveshell import InteractiveShell


def load_ipython_extension(ipython: InteractiveShell):
    """
    Add a custom completer to IPython that uses GitHub Copilot
    This completer patches the IPython completers to put Copilot at the start
    """
    if not settings.token:
        print(
            "GITHUB_ACCESS_TOKEN environment variable is not set - Copilot will not work",
        )
        return

    # If the copilot completer is in the disabled matchers then we have already loaded
    # the extension so we don't need to do anything except re-enable the completer
    if "copilot_completer" in (completer := ipython.Completer).disable_matchers:
        completer.disable_matchers.remove("copilot_completer")
        return

    ipython.set_custom_completer(copilot_completer)

    if settings.inline:
        add_to_tab_completions(ipython)
    elif settings.auto_suggestion:
        enable_copilot_suggester(ipython)
    elif settings.key_binding:
        # Add a key binding to get Copilot completions
        completer.disable_matchers.append("copilot_completer")
        add_key_binding()


def unload_ipython_extension(ipython: InteractiveShell):
    ipython.Completer.disable_matchers.append("copilot_completer")

    if settings.inline:
        remove_from_tab_completions(ipython)
    elif settings.auto_suggestion:
        disable_copilot_suggester(ipython)
    elif settings.key_binding:
        remove_key_binding()
