from __future__ import annotations

from typing import TYPE_CHECKING

from IPython.core.getipython import get_ipython
from IPython.core.magic import Magics, magics_class, register_line_magic

from .auto_suggester import (
    disable_copilot_suggester,
    enable_copilot_suggester,
)
from .github_auth import get_github_access_token
from .settings import settings


if TYPE_CHECKING:
    from IPython.core.interactiveshell import InteractiveShell
    from IPython.core.magic import MagicsManager


def load_ipython_extension(ipython: InteractiveShell):
    """
    Add a custom completer to IPython that uses GitHub Copilot
    This completer patches the IPython completers to put Copilot at the start
    """
    if not settings.token:
        print("You do not have a GitHub Copilot access token setup")
        print("Please run %copilot_login to set your token")
        print("or set the GITHUB_COPILOT_ACCESS_TOKEN environment variable")

    enable_copilot_suggester(ipython)

    # Register the magic command
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
                assert ip is not None
                db = ip.db
                db["github_copilot_access_token"] = token.access_token
                settings.reset()
            else:
                print("Failed to get access token")

    ipython.register_magics(CopilotMagics)


def unload_ipython_extension(ipython: InteractiveShell):
    disable_copilot_suggester(ipython)

    # Unregister the magic command
    if ipython.magics_manager:
        if TYPE_CHECKING:
            assert isinstance(ipython.magics_manager, MagicsManager)
            assert isinstance(ipython.magics_manager.magics, dict)
        del ipython.magics_manager.magics["line"]["copilot_login"]
