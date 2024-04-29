from __future__ import annotations

import site
import sys
from pathlib import Path

from setuptools import find_packages, setup


# Allow editable install into user site directory.
site.ENABLE_USER_SITE = "--user" in sys.argv[1:]

setup(
    name="IPython Copilot Completer",
    version="0.0.10",
    description="Use GitHub Copilot in IPython to autocomplete your code",
    long_description=Path("README.md").open().read(),
    author="Brandon Navra",
    author_email="brandon.navra@gmail.com",
    packages=find_packages(),
    license="MIT",
    install_requires=[
        "IPython>=8.18.0",
        "aiohttp>=3.9.1",
        "pickleshare>=0.7.5",
        "requests>=2.26.0",
    ],
)
