# Copyright Jamil RAICHOUNI and contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import calendar
import importlib.resources
import os
import pathlib
import sys
import tempfile
import typing as t

import fasthtml.common as fh

from finances import core

ABBREVIATED_MONTH_NAMES: t.Final[tuple[str, ...]] = tuple(
    calendar.month_abbr[i] for i in range(1, 13)
)
DATA_DIR: t.Final[pathlib.Path] = (
    pathlib.Path.home() / "googledrive/JAR/finances"
)
TMP_DIR: t.Final[pathlib.Path] = pathlib.Path(tempfile.gettempdir())
DATABASE_FILE: t.Final[pathlib.Path] = DATA_DIR / "finances.db"
FINTS_CLIENT_FILE: t.Final[pathlib.Path] = TMP_DIR / "fints_client.blob"
FINTS_DIALOG_FILE: t.Final[pathlib.Path] = TMP_DIR / "fints_dialog.blob"
FINTS_SYSTEM_ID_FILE: t.Final[pathlib.Path] = TMP_DIR / "systemid.blob"
FINTS_TAN_FILE: t.Final[pathlib.Path] = TMP_DIR / "fints_tan.blob"

STATIC_DIR: t.Final[pathlib.Path] = pathlib.Path(
    str(importlib.resources.files(__package__) / "static")
)
INPUT_CSS_PATH: t.Final[pathlib.Path] = STATIC_DIR / "css/input.css"
main_css_file: t.Final[str] = "css/main.min.css"
MAIN_CSS_PATH: t.Final[pathlib.Path] = STATIC_DIR / main_css_file
_main_css_hash: t.Final[str] = core.compute_file_hash(MAIN_CSS_PATH)

favicon_file: t.Final[str] = "favicon.svg"
FAVICON_PATH: t.Final[pathlib.Path] = STATIC_DIR / favicon_file
_favicon_hash: t.Final[str] = core.compute_file_hash(FAVICON_PATH)
HEADERS: t.Final[list[fh.Link | fh.Script]] = [
    fh.HighlightJS(langs=["python"]),
    fh.Link(
        rel="stylesheet",
        href=f"static/{main_css_file}?v={_main_css_hash}",
        type="text/css",
    ),
    fh.Link(
        rel="icon",
        href=f"static/{favicon_file}?v={_favicon_hash}",
        type="image/x-icon",
    ),
    fh.Script(
        charset="utf-8",
        src="static/js/plotly-3.0.0.min.js",
    ),
    fh.Style(
        f":root {{ --primary-color-hue: {os.getenv('PRIMARY_COLOR_HUE', '231')}; }}"
    ),
]
if sys.stderr.isatty():
    _logging_colors = {
        "CRITICAL": "\x1b[1;31m",  # Bold and red
        "ERROR": "\x1b[31m",  # red
        "WARNING": "\x1b[33m",  # yellow
        "INFO": "\x1b[32m",  # green
        "DEBUG": "\x1b[3;90m",  # Italic and dark gray
        "RESET": "\x1b[m",
    }
else:
    _logging_colors = {
        "CRITICAL": "",
        "ERROR": "",
        "WARNING": "",
        "INFO": "",
        "DEBUG": "",
        "RESET": "",
    }
LOGGING_COLORS: t.Final[dict[str, str]] = _logging_colors
