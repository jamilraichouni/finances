# Copyright Jamil RAICHOUNI and contributors
# SPDX-License-Identifier: Apache-2.0
"""The finances package."""

__all__ = [
    "app",
    "constants",
    "core",
    "model",
    "onlinebanking",
    "state",
]
from importlib import metadata

try:
    __version__ = metadata.version("finances")
except metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0+unknown"
del metadata
