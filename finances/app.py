# Copyright Jamil RAICHOUNI and contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import contextlib
import locale
import logging
import os
import typing as t

import fasthtml.common as fh

import finances.constants as c
from finances import components, constants, core, icons, onlinebanking, state

logger = logging.getLogger(__package__)
core.setup_logging(logger)


locale.setlocale(locale.LC_ALL, "de_DE")

if os.getenv("FIN_DEV_MODE", "0") == "1":
    _app_cls = fh.FastHTMLWithLiveReload
else:
    _app_cls = fh.FastHTML


@contextlib.asynccontextmanager
async def lifespan(_: t.Any) -> t.Any:
    state.positions = core.read_positions()
    yield


app: fh.FastHTML = _app_cls(
    exts="ws",
    hdrs=c.HEADERS,
    lifespan=lifespan,
    live=os.getenv("FIN_DEV_MODE", "0") == "1",
    pico=False,
)
app.static_route_exts("/static", c.STATIC_DIR)


@app.get("/balances")
def balances(request: fh.Request) -> t.Any:
    return components.balances(request)


@app.get("/category-item")
def category_item(category: str = "", expanded: bool = False) -> t.Any:  # noqa
    return components.category_item(category=category, expanded=expanded)


@app.get("/positions")
def positions() -> t.Any:
    content = fh.Div(
        fh.Div(
            fh.Div(
                icons.collapse_all("stroke-1"),
                onclick="document.querySelectorAll("
                "'._category-header[aria-expanded=\"true\"]'"
                ").forEach(element => element.click());",
                cls="cursor-pointer flex w-full justify-end grow",
            ),
            fh.Div(
                icons.expand_all("stroke-1"),
                onclick="document.querySelectorAll("
                "'._category-header[aria-expanded=\"false\"]'"
                ").forEach(element => element.click());",
                cls="cursor-pointer flex justify-end",
            ),
            cls="flex py-4 pr-4 space-x-4",
        ),
        components.category_list(),
        cls=(
            "flex",
            "flex-col",
            "grow",
            "px-4",
        ),
    )
    return components.chrome(content)


@app.get("/")
def index() -> t.Any:
    return components.chrome(
        fh.Div(
            components.positions_button(),
            cls=(
                "flex",
                "grow",
                "justify-center",
                "my-16",
            ),
        )
    )


@app.get("/debug")
def debug() -> t.Any:
    breakpoint()  # noqa
