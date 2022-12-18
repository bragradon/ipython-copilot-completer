from __future__ import annotations

import json
import os
import time
from contextlib import suppress
from types import MethodType
from typing import TYPE_CHECKING

import requests
from IPython import get_ipython
from IPython.core.completer import (
    _convert_matcher_v1_result_to_v2,
    context_matcher,
)
from IPython.terminal.shortcuts import cursor_in_leading_ws
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.key_binding.bindings.completion import display_completions_like_readline
from prompt_toolkit.keys import Keys
from prompt_toolkit.filters import HasFocus, HasSelection, vi_insert_mode, emacs_insert_mode

if TYPE_CHECKING:
    from IPython.core.interactiveshell import InteractiveShell
    from IPython.core.completer import (
        Completer,
        CompletionContext,
        SimpleMatcherResult,
    )


# GitHub access token
# Extract this from an ide using Copilot by sniffing the network traffic
GITHUB_COPILOT_ACCESS_TOKEN = os.environ.get("GITHUB_COPILOT_ACCESS_TOKEN", None)

# Whether the completions should be displayed inline with other completions
inline_copilot = os.environ.get("GITHUB_COPILOT_INLINE_COMPLETIONS", "0") == "1"


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
    else:
        # Add a key binding to get Copilot completions
        completer.disable_matchers.append("copilot_completer")
        if getattr(ipython, 'pt_app', None):
            insert_mode = vi_insert_mode | emacs_insert_mode
            registry = ipython.pt_app.key_bindings
            registry.add_binding(
                Keys.ControlSpace,
                filter=(
                        HasFocus(DEFAULT_BUFFER)
                        & ~HasSelection()
                        & insert_mode
                        & ~cursor_in_leading_ws
                )
            )(get_copilot_completions)


def unload_ipython_extension(ipython: InteractiveShell):
    ipython.Completer.disable_matchers.append("copilot_completer")

    if inline_copilot:
        if hasattr(completer:=ipython.Completer, "_orig_completions"):
            completer._completions = completer._orig_completions
            delattr(completer, "_orig_completions")
    else:
        if getattr(ipython, 'pt_app', None):
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


@context_matcher()
def copilot_completer(
    self: Completer, context: CompletionContext
) -> SimpleMatcherResult:
    """
    Use GitHub Copilot to complete code the current line
    This uses the current session as the context for the completion
    but ignores lines that start with % or ! as these are not valid Python
    """

    # Get the current session as a list of lines joined by newlines
    hm = self.shell.history_manager
    session = "\n".join(
        [
            i[-1]
            for i in hm.get_range(hm.session_number)
            if not i[-1].startswith(("%", "!"))
        ]
    )

    # Get the current line
    line = context.full_text
    is_comment = line.startswith("#")
    if is_comment:
        line += '\n'

    # Create the prompt for Copilot
    prompt = f"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
{session}
{line}"""

    # Get the suggestion from Copilot
    # If the current line starts with # then we allow the suggestion to be a comment
    code = get_suggestion(prompt, stops=["\n\n" if is_comment else "\n"])

    # If the line is a comment then we need to add a newline as the suggestion
    # appears after the comment on a new line
    text = f"{context.token}\n" if is_comment else context.token

    # Return the suggestion
    result: dict = _convert_matcher_v1_result_to_v2(
        matches=[text + code],
        type="copilot",
        suppress_if_matches=False,
    )
    result |= {
        "ordered": True,  # Place Copilot suggestions at the top (though below jedi)
    }
    return result


def get_suggestion(prompt: str, stops: list[str]) -> str:
    """
    Get a suggestion from GitHub Copilot
    """

    def get_temperature(line_count):
        line_count = max(1, line_count - 2)
        if line_count <= 1:
            return 0
        elif line_count <= 10:
            return 0.2
        elif line_count < 20:
            return 0.4
        else:
            return 0.8

    payload = json.dumps(
        {
            "prompt": prompt,
            "max_tokens": 200,
            "temperature": get_temperature(prompt.count("\n")),
            "top_p": 1,
            "n": 1,
            "logprobs": 0,
            "stop": stops,
            "stream": True,  # The API must be called with stream=True
            "extra": {
                "language": "python",
                "next_indent": 0,
                "trim_by_indentation": True,
            },
        },
    )
    headers = {
        "OpenAI-Intent": "copilot-ghost",
        "OpenAI-Organization": "github-copilot",
        "Authorization": f"Bearer {get_copilot_token()}",
        "Content-Type": "application/json",
    }

    lines = []

    with requests.post(
        "https://copilot-proxy.githubusercontent.com/v1/engines/copilot-codex/completions",
        data=payload,
        headers=headers,
        stream=True,
    ) as resp:
        # The API returns a stream of JSON-like objects or blank lines
        # We need to parse the JSON-like objects and ignore the blank lines
        # The format of the JSON-like objects is:
        # data: {"choices": [{"text": "suggestion"}]}}

        for line in resp.iter_lines():
            if line:
                line = line.decode("utf-8")[6:]  # Remove the data: prefix
                with suppress(json.JSONDecodeError):
                    lines.append(json.loads(line)["choices"][0]["text"])

    return "".join(lines)


def memoize_with_expiry(func):
    """
    Function to memoize the return value of a function call
    The function func must return a tuple of value and expiry time
    The expiry time is used to determine when to expire the cache
    """
    cache = {}

    def wrapper(*args, **kwargs):
        key = (args, tuple(kwargs.items()))
        if key in cache:
            value, expiry = cache[key]
            if expiry > time.time():
                return value
        value, expiry = func(*args, **kwargs)
        cache[key] = (value, expiry)
        return value

    return wrapper


@memoize_with_expiry
def get_copilot_token() -> tuple[str, str]:
    """
    Get the Copilot token from the GitHub API
    """
    response = requests.get(
        "https://api.github.com/copilot_internal/v2/token",
        headers={
            "content-type": "application/json",
            "accept": "application/json",
            "Authorization": f"token {GITHUB_COPILOT_ACCESS_TOKEN}",
        },
    )

    response.raise_for_status()
    result = response.json()
    return result["token"], result["expires_at"]

