# Copyright Jamil RAICHOUNI and contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing as t

from fasthtml import svg

CLS_DEFAULT = [
    "dark:hover:stroke-neutral-100",
    "dark:stroke-neutral-400",
    "fill-none",
    "h-6",
    "stroke-[1.5]",
    "hover:stroke-2",
    "hover:stroke-neutral-600",
    "stroke-neutral-600",
    "w-6",
]


def chevron_down(*additional_classes: str) -> t.Any:
    return svg.Svg(
        svg.Path(
            d="m19.5 8.25-7.5 7.5-7.5-7.5",
        ),
        cls=(*CLS_DEFAULT, *additional_classes),
    )


def chevron_up(*additional_classes: str) -> t.Any:
    return svg.Svg(
        svg.Path(d="m4.5 15.75 7.5-7.5 7.5 7.5"),
        cls=(*CLS_DEFAULT, *additional_classes),
    )


def collapse_all(*additional_classes: str) -> t.Any:
    return svg.Svg(
        svg.Rect(width="18", height="18", x="3", y="3", rx="2"),
        svg.Path(d="M3 9h18"),
        svg.Path(d="m9 16 3-3 3 3"),
        cls=(*CLS_DEFAULT, *additional_classes),
    )


def expand_all(*additional_classes: str) -> t.Any:
    return svg.Svg(
        svg.Rect(width="18", height="18", x="3", y="3", rx="2"),
        svg.Path(d="M3 9h18"),
        svg.Path(d="m15 14-3 3-3-3"),
        cls=(*CLS_DEFAULT, *additional_classes),
    )


def hamburger(*additional_classes: str) -> svg.Svg:
    return svg.Svg(
        svg.Path(
            d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5",
        ),
        cls=(*CLS_DEFAULT, *additional_classes),
    )


def home(*additional_classes: str) -> t.Any:
    return svg.Svg(
        svg.Path(d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"),
        svg.Path(
            d=(
                "M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7"
                " 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"
            )
        ),
        cls=(*CLS_DEFAULT, *additional_classes),
    )


def positions(*additional_classes: str) -> svg.Svg:
    return svg.Svg(
        svg.Path(
            d="M8.25 6.75h12M8.25 12h12m-12 5.25h12M3.75 6.75h.007v.008H3.75V6.75Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0ZM3.75 12h.007v.008H3.75V12Zm.375 0a .375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm-.375 5.25h.007v.008H3.75v-.008Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z",
        ),
        cls=(*CLS_DEFAULT, *additional_classes),
    )


def refresh(*additional_classes: str) -> svg.Svg:
    return svg.Svg(
        svg.Path(
            d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99",
        ),
        cls=(*CLS_DEFAULT, *additional_classes),
    )
