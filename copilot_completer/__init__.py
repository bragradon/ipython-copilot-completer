from __future__ import annotations


__version__ = "0.0.7"

from .extension import load_ipython_extension, unload_ipython_extension


__all__ = ["load_ipython_extension", "unload_ipython_extension", "__version__"]
