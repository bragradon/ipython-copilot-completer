from __future__ import annotations

from typing import TYPE_CHECKING

from IPython import get_ipython
from IPython.core.magic import Magics, magics_class, register_line_magic

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
        print("You do not have a GitHub Copilot access token setup")
        print("Please run %copilot_login to set your token")
        print("or set the GITHUB_COPILOT_ACCESS_TOKEN environment variable")

    if settings.inline:
        add_to_tab_completions(ipython)
    elif settings.auto_suggestion:
        enable_copilot_suggester(ipython)
    elif settings.key_binding:
        add_key_binding()

    # Register the magic command
    ipython.register_magics(CopilotMagics)


def unload_ipython_extension(ipython: InteractiveShell):
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
