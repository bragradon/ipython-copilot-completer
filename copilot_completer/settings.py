from __future__ import annotations

import dataclasses
import os
from functools import lru_cache

from IPython.core.getipython import get_ipython


@dataclasses.dataclass
class Settings:
    token: str

    def reset(self):
        global settings
        self.from_env.cache_clear()
        settings = self.from_env()

    @staticmethod
    @lru_cache(maxsize=1)
    def from_env():
        return Settings(
            token=Settings.get_token(),
        )

    @staticmethod
    def get_token():
        if env_token := os.environ.get("GITHUB_COPILOT_ACCESS_TOKEN", ""):
            return env_token
        else:
            ip = get_ipython()
            assert ip is not None
            db = ip.db
            return db.get("github_copilot_access_token", "")


settings = Settings.from_env()
