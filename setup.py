from __future__ import annotations

import site
import sys

from setuptools import find_packages, setup

from copilot_completer import __version__


# Allow editable install into user site directory.
site.ENABLE_USER_SITE = "--user" in sys.argv[1:]

setup(
    name="IPython Copilot Completer",
    version=__version__,
    description="Use GitHub Copilot in IPython to autocomplete your code",
    long_description=open("README.md").read(),  # noqa: SIM115
    author="Brandon Navra",
    author_email="brandon.navra@gmail.com",
    packages=find_packages(),
    license="MIT",
    install_requires=[
        "ipython>=8.9.0",
        "requests",
    ],
)
