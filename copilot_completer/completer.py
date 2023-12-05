from __future__ import annotations

import json
import time
from collections.abc import Callable
from contextlib import suppress
from typing import TYPE_CHECKING, Any, ParamSpec, cast

import aiohttp
import requests
from IPython.core.completer import (
    CompletionContext,
    IPCompleter,
    SimpleCompletion,
    SimpleMatcherResult,
)
from IPython.core.getipython import get_ipython

from .settings import settings


if TYPE_CHECKING:
    from IPython.core.history import HistoryManager
    from IPython.core.interactiveshell import InteractiveShell


async def fetch_copilot_suggestion(text: str) -> str | None:
    if not (ip := get_ipython()):
        return None

    completer = ip.Completer
    context = CompletionContext(
        full_text=text,
        cursor_position=0,
        cursor_line=0,
        token=completer.splitter.split_line(text, 0),
        limit=1,
    )

    suggestion = await copilot_completer(completer, context)

    if completions := suggestion["completions"]:
        return completions[0].text
    else:
        return None


async def copilot_completer(
    completer: IPCompleter,
    context: CompletionContext,
) -> SimpleMatcherResult:
    """
    Use GitHub Copilot to complete code the current line
    This uses the current session as the context for the completion
    but ignores lines that start with % or ! as these are not valid Python
    """

    if not settings.token:
        return SimpleMatcherResult(completions=[])

    # Get the current session as a list of lines joined by newlines
    if TYPE_CHECKING:
        assert isinstance(completer.shell, InteractiveShell)
        hm = cast(HistoryManager, completer.shell.history_manager)
    else:
        hm = completer.shell.history_manager

    session_number = cast(int, hm.session_number)

    session = "\n".join(
        [
            i[-1]
            for i in cast(list[str], hm.get_range(session_number))
            if not i[-1].startswith(("%", "!"))
        ],
    )

    # Get the current line
    line = context.full_text
    is_comment = line.startswith("#")
    if is_comment:
        line += "\n"

    # Create the prompt for Copilot
    prompt = f"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
{session}
{line}"""

    # Get the suggestion from Copilot
    # If the current line starts with # then we allow the suggestion to be a comment
    code = await fetch_suggestion(prompt, stops=["\n\n" if is_comment else "\n"])

    # If the line is a comment then we need to add a newline as the suggestion
    # appears after the comment on a new line
    text = f"{context.token}\n" if is_comment else context.token

    # Return the suggestion
    return SimpleMatcherResult(
        completions=[SimpleCompletion(text=text + code, type="copilot")]
    )


async def fetch_suggestion(prompt: str, stops: list[str], suffix: str = "") -> str:
    """
    Get a suggestion from GitHub Copilot asynchronously using aiohttp.
    """

    def get_temperature(line_count: int) -> float:
        line_count = max(1, line_count - 2)
        if line_count <= 1:
            return 0
        elif line_count <= 10:
            return 0.2
        elif line_count < 20:
            return 0.4
        else:
            return 0.8

    if suffix:
        stops += ["def ", "class ", "if ", "\n#"]

    # TODO: Calculate next indent

    payload = json.dumps(
        {
            "prompt": prompt,
            "suffix": suffix,
            "max_tokens": 200,
            "temperature": get_temperature(prompt.count("\n")),
            "top_p": 1,
            "n": 1,
            # "logprobs": 0,
            "stop": stops,
            "stream": True,  # The API must be called with stream=True
            # "feature_flags": ["trim_to_block"],
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

    async with aiohttp.ClientSession() as session:  # noqa: SIM117
        async with session.post(
            "https://copilot-proxy.githubusercontent.com/v1/engines/copilot-codex/completions",
            data=payload,
            headers=headers,
        ) as resp:
            async for line in resp.content:
                if line:
                    line = line.decode("utf-8")[6:]  # Remove the data: prefix
                    with suppress(json.JSONDecodeError):
                        lines.append(json.loads(line)["choices"][0]["text"])

    return "".join(lines)


P = ParamSpec("P")
R = tuple[str, float]


def memoize_with_expiry(func: Callable[P, R]) -> Callable[..., str]:
    """
    Function to memoize the return value of a function call
    The function func must return a tuple of value and expiry time
    The expiry time is used to determine when to expire the cache
    """
    cache: dict[Any, R] = {}

    def wrapper(*args: P.args, **kwargs: P.kwargs) -> str:
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
def get_copilot_token() -> R:
    """
    Get the Copilot token from the GitHub API
    """
    response = requests.get(
        "https://api.github.com/copilot_internal/v2/token",
        headers={
            "content-type": "application/json",
            "accept": "application/json",
            "Authorization": f"token {settings.token}",
        },
    )

    response.raise_for_status()
    result = response.json()
    return result["token"], result["expires_at"]
