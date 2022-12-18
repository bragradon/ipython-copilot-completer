from __future__ import annotations

from typing import TYPE_CHECKING

from IPython import get_ipython
from IPython.core.magic import Magics, magics_class, register_line_magic

from .completer import copilot_completer
from .github_auth import get_github_access_token
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
            "GITHUB_COPILOT_ACCESS_TOKEN environment variable is not set - Copilot will not work",
        )
        print("Please run %copilot_login to set your token")

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

    # Register the magic command
    ipython.register_magics(CopilotMagics)


def unload_ipython_extension(ipython: InteractiveShell):
    ipython.Completer.disable_matchers.append("copilot_completer")

    if settings.inline:
        remove_from_tab_completions(ipython)
    elif settings.auto_suggestion:
        disable_copilot_suggester(ipython)
    elif settings.key_binding:
        remove_key_binding()


if get_ipython():
    # We need this so setuptools can create the wheel
    # because the magic decorator will fail due to ipython not being loaded
    @magics_class
    class CopilotMagics(Magics):
        @register_line_magic
        def copilot_login(self, line=None):
            """
            Get a GitHub access token for Copilot
            """
            if token := get_github_access_token():
                print(f"Your GitHub access token is: {token.access_token}")

                ip = get_ipython()
                db = ip.db
                db["github_copilot_access_token"] = token.access_token
                settings.reset()
            else:
                print("Failed to get access token")
