from __future__ import annotations

import dataclasses
import os
from functools import lru_cache


DEFAULT = "GITHUB_COPILOT_AUTO_SUGGEST"


@dataclasses.dataclass
class Settings:
    token: str
    inline: bool
    auto_suggestion: bool
    key_binding: bool

    @staticmethod
    @lru_cache(maxsize=1)
    def from_env():
        if DEFAULT not in os.environ:
            os.environ[DEFAULT] = "1"

        return Settings(
            token=os.environ.get("GITHUB_COPILOT_ACCESS_TOKEN", ""),
            # Whether the completions should be displayed inline with other completions
            inline=os.environ.get("GITHUB_COPILOT_INLINE_COMPLETIONS", "0") == "1",
            # Whether completions should be displayed as an autosuggestion
            auto_suggestion=os.environ.get("GITHUB_COPILOT_AUTO_SUGGEST", "0") == "1",
            # Whether to add a key binding to get Copilot completions
            key_binding=os.environ.get("GITHUB_COPILOT_KEY_BINDING", "0") == "1",
        )


settings = Settings.from_env()
