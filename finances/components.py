# Copyright Jamil RAICHOUNI and contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
import typing as t

import fasthtml.common as fh
import pandas as pd

from finances import app, constants, core, icons, onlinebanking, state

logger = logging.getLogger(__name__)
core.setup_logging(logger, level="DEBUG")


def _balances(balances_: pd.DataFrame) -> t.Any:
    balances_.sort_values(by="product_name", inplace=True)
    balance_divs = []
    for balance in balances_.itertuples():
        balance_div = fh.Div(
            fh.Div(
                f"{balance.product_name}:",
                cls="grow text-left text-nowrap",
            ),
            fh.Div(
                core.display_amount(balance.amount),
                cls=(
                    "grow",
                    "text-nowrap",
                    "text-red-700" if balance.amount < 0 else "text-green-700",
                    "text-right",
                ),
            ),
            cls="flex space-x-2",
        )
        balance_divs.append(balance_div)
    return fh.Div(
        *balance_divs,
        id="balances",
        cls=(
            "dark:text-neutral-400",
            "gap-x-4",
            "grid",
            "md:grid-cols-1",
            "md:grid-cols-2",
            "w-full",
            # "text-center",
            "text-neutral-600",
            "text-[0.5rem]",
            "md:text-xs",
        ),
    )


def balances(request: fh.Request | None = None) -> t.Any:
    if request:
        core.sync_all()
        balances_ = core.compute_balances()
        if balances_.empty:
            return balances()
        return _balances(balances_)
    balances_ = core.compute_balances()
    if balances_.empty:
        return fh.A(
            icons.refresh(
                "stroke-neutral-200 refresh-btn-icon refresh-btn-icon-static"
            ),
            icons.refresh(
                "stroke-neutral-200 refresh-btn-icon refresh-btn-icon-animated animate-spin stroke-red-500"
            ),
            fh.Div("Kontodaten aktualisieren"),
            id="balances-indicator",
            hx_get=app.app.url_path_for("balances"),
            hx_indicator=".refresh-btn-icon",
            hx_trigger="click",
            hx_swap="outerHTML",
            cls=(
                "bg-primary-500",
                "border",
                "border-neutral-400",
                "dark:border-neutral-600",
                "text-neutral-400",
                "flex",
                "px-2",
                "py-1",
                "rounded-lg",
                "space-x-2",
            ),
        )
    return _balances(balances_)


def chrome(content: t.Any) -> t.Any:
    return fh.Body(
        page_header(),
        fh.Main(
            content,
            cls=(
                "self-center",
                "self-stretch",
                "flex",
                "grow",
            ),
        ),
        hx_boost="true",
        cls=(
            "bg-neutral-100",
            "dark:bg-neutral-900",
            "flex",
            "flex-col",
            "overflow-auto",
            "min-h-screen",
            # "space-y-2",
        ),
    ), fh.Title("Finances")


def page_header() -> t.Any:
    return fh.Nav(
        fh.A(
            icons.home(),
            hx_get=app.app.url_path_for("index"),
            hx_target="main",
            hx_select="main",
            hx_push_url="true",
            cls=(
                "flex",
                "grow",
                "justify-start",
                "w-1/3",
            ),
        ),
        balances(),
        fh.Div(
            fh.A(
                icons.hamburger("sm:w-0"),
            ),
            cls=(
                "flex",
                "grow",
                "justify-end",
                "space-x-4",
                "w-1/3",
            ),
        ),
        id="page-header",
        cls=(
            "bg-neutral-200",
            "border-b",
            "border-neutral-400",
            "content-center",
            "dark:bg-neutral-800",
            "dark:border-neutral-700",
            "flex",
            "h-12",
            "items-center",
            "justify-center",
            "print:hidden",
            "px-4",
            "sticky",
            "top-0",
            "w-full",
        ),
    )


def position_item(position: pd.Series) -> t.Any:
    time_frame, time_frame_data = None, []
    if position.start and position.end:
        time_frame_data = [
            fh.Tr(
                fh.Td("Erste:", cls="text-right"),
                fh.Td("2025-10-01", cls="pl-2"),
            ),
            fh.Tr(
                fh.Td("Letzte:", cls="text-right"),
                fh.Td("2025-10-01", cls="pl-2"),
            ),
        ]
    elif position.start:
        time_frame_data = [
            fh.Tr(
                fh.Td("Erste:", cls="text-right"),
                fh.Td("2025-10-01", cls="pl-2"),
            )
        ]
    elif position.end:
        time_frame_data = [
            fh.Tr(
                fh.Td("Letzte:", cls="text-right"),
                fh.Td("2025-10-01", cls="pl-2"),
            )
        ]
    if time_frame_data:
        time_frame_title = fh.Tr(
            fh.Td("Ausführung", cls="text-center", colspan="2"),
        )
        time_frame = fh.Table(
            time_frame_title,
            *time_frame_data,
            cls="ml-4 text-[0.5rem] text-neutral-500 dark:text-neutral-500",
        )
    partner_and_name = (
        fh.Div(
            fh.P(position.partner, cls="text-xs"),
            fh.P(position.name, cls="text-sm"),
            cls=(
                "dark:border-neutral-600",
                "border-neutral-300",
                "mr-4",
                "flex",
                "flex-col",
            ),
        ),
    )
    amount = (
        fh.P(
            core.display_amount(position.amount),
            cls=(
                "grow",
                "self-center",
                "min-h-full",
                "text-red-700" if position.amount < 0 else "text-green-700",
                "text-right",
                "text-xl",
            ),
        ),
    )
    schedule = fh.Div(
        fh.Table(
            fh.Div(
                fh.Tr(
                    *[
                        fh.Td(
                            month,
                            cls=(
                                "border",
                                "border-neutral-400",
                                "dark:border-neutral-600",
                                "text-center",
                            ),
                        )
                        for month in constants.ABBREVIATED_MONTH_NAMES
                    ],
                ),
                fh.Tr(
                    *[
                        fh.Td(
                            position.schedule.get(month + 1, ""),
                            cls=(
                                "border",
                                "border-neutral-400",
                                "dark:border-neutral-600",
                                "text-center",
                                "pr-1",
                            ),
                        )
                        for month, _ in enumerate(
                            constants.ABBREVIATED_MONTH_NAMES
                        )
                    ],
                ),
                cls=("flex", "grow"),
            ),
            cls=(
                "mt-4",
                "text-xs",
                "w-full",
            ),
        ),
        cls=(
            "flex",
            "flex-col",
        ),
    )
    notes = None
    if position.notes:
        notes = fh.Div(
            fh.P("Notizen:"),
            fh.P(position.notes),
            cls=(
                "dark:text-neutral-500",
                "flex",
                "flex-col",
                "mt-4",
                "text-neutral-500",
                "text-[0.6rem]",
            ),
        )
    return fh.Li(
        fh.Div(
            partner_and_name,
            time_frame,
            amount,
            cls=(
                "flex",
                "grow",
            ),
        ),
        schedule,
        notes,
        cls=(
            "dark:text-neutral-400",
            "flex-col",
            "py-8",
            "text-neutral-600",
        ),
    )


def position_list(positions: pd.DataFrame) -> t.Any:
    positions = positions.sort_values(
        by=[
            "partner",
            "name",
        ]
    )
    return fh.Ol(
        *[
            position_item(position=p)
            for p in positions.itertuples(index=False)
        ],
        cls=(
            "divide-y",
            "dark:divide-neutral-700",
            "divide-neutral-300",
            "grow",
            "px-2",
            "min-h-content",
        ),
    )


def positions_button() -> t.Any:
    return fh.A(
        fh.Div(
            icons.positions("scale-200"),
            fh.P("Positions", cls="text-2xl dark:text-neutral-400"),
            cls=(
                "flex",
                "grow",
                "min-h-24",
                "place-items-center",
                "space-x-8",
            ),
        ),
        hx_get=app.app.url_path_for("positions"),
        hx_select="main",
        hx_target="main",
        hx_push_url="true",
        cls=(
            "bg-neutral-200",
            "dark:bg-neutral-800",
            "border-[1px]",
            "border-neutral-400",
            "dark:border-neutral-700",
            "flex",
            "hover:bg-neutral-200",
            "hover:dark:bg-neutral-800",
            "hover:scale-105",
            "place-items-center",
            "px-16",
            "rounded-full",
            "max-h-24",
            "min-w-96",
            # "shadow-xs",
            # "shadow-neutral-500",
            "justify-between",
            "transition-transform",
        ),
    )


def category_item(*, category: str, expanded: bool = False) -> t.Any:
    category_header = (
        fh.A(
            category,
            icons.chevron_up() if expanded else icons.chevron_down(),
            aria_expanded="true" if expanded else "false",
            hx_get=app.category_item.to(
                category=category, expanded="false" if expanded else "true"
            ),
            hx_target="closest li",
            hx_swap="outerHTML",
            cls=(
                "_category-header",
                "bg-neutral-300",
                "dark:bg-neutral-700",
                "flex",
                "grow",
                "items-center",
                "justify-between",
                "min-h-12",
                "px-2",
                "rounded-t-lg",
                "text-xl",
            ),
        ),
    )
    positions = state.positions.loc[state.positions["category"] == category]
    return fh.Li(
        fh.Div(
            category_header,
            position_list(positions) if expanded else None,
            cls=(
                "flex",
                "flex-col",
                "grow",
            ),
        ),
        id=f"category-{category}",
        aria_expanded="true" if expanded else "false",
        cls=(
            "bg-neutral-200",
            "dark:bg-neutral-800",
            "dark:text-neutral-300",
            "flex",
            "items-center",
            # "px-4",
            "rounded-lg" if expanded else "rounded-t-lg",
            "shadow-md",
            "text-left",
            "transition-colors",
        ),
    )


def category_list() -> t.Any:
    categories = sorted(state.positions["category"].unique().tolist())
    return fh.Ol(
        *[category_item(category=c, expanded=True) for c in categories],
        cls=(
            "flex",
            "flex-col",
            "grow",
            "space-y-4",
        ),
    )
