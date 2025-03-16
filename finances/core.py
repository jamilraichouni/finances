# Copyright Jamil RAICHOUNI and contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import base64
import datetime
import decimal
import hashlib
import logging
import pathlib
import sqlite3

import fints
import pandas as pd

import finances.constants as c
from finances import constants, model, onlinebanking, state


def compute_file_hash(file_path: pathlib.Path | str) -> str:
    """Compute a hash for the given file."""
    if not pathlib.Path(file_path).exists():
        return ""
    hasher = hashlib.blake2b(digest_size=9, usedforsecurity=False)
    with open(file_path, "rb") as f:
        buf = f.read()
        hasher.update(buf)
    return base64.urlsafe_b64encode(hasher.digest()).decode("utf-8")


def compute_hash_string(string: str) -> str:
    """Compute a hash for the string."""
    hasher = hashlib.blake2b(digest_size=9, usedforsecurity=False)
    hasher.update(string.encode("utf-8"))
    return base64.urlsafe_b64encode(hasher.digest()).decode("utf-8")


def display_amount(amount: float) -> str:
    """Display amount with optional decimal places.

    If the amount is an integer, display it as an integer. Use a comma
    as decimal separator and a dot as thousands separator.
    """
    decimal_amount = decimal.Decimal(amount).quantize(
        decimal.Decimal("0.00"), rounding=decimal.ROUND_DOWN
    )
    if decimal_amount == decimal_amount.to_integral_value():
        return f"{int(decimal_amount):n} €"
    return f"{decimal_amount:n} €"


class ColoredFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs) -> None:  # type: ignore
        super().__init__(*args, **kwargs)

    def format(self, record: logging.LogRecord) -> str:
        reset_seq = "\033[0m"
        levelname = record.levelname
        msg = record.msg
        if levelname in c.LOGGING_COLORS:
            levelname_colored = (
                f"{c.LOGGING_COLORS[levelname]}{levelname:8}{reset_seq}"
            )
            msg_color = c.LOGGING_COLORS[levelname] + msg + reset_seq
        else:
            levelname_colored = levelname
            msg_color = msg
        record.levelname = levelname_colored
        record.msg = msg_color
        return super().format(record)


def read_positions() -> pd.DataFrame:
    positions = model.load(
        pathlib.Path.home() / "googledrive/JAR/finances/positions.yaml"
    )
    for column in (
        "category",
        "partner",
        "name",
        "amount",
        "schedule",
        "start",
        "end",
        "notes",
    ):
        if column not in positions.columns:
            positions[column] = None
        if column not in ("amount", "schedule", "start", "end"):
            positions[column] = positions[column].fillna("")
    return positions


def set_column_types(df: pd.DataFrame) -> pd.DataFrame:
    typemap = {c: "datetime64[ns]" for c in df.columns if "date" in c}
    typemap.update({c: "float64" for c in df.columns if "amount" in c})
    if typemap:
        df = df.astype(typemap)
    return df


def setup_logging(logger: logging.Logger, level: str = "WARNING") -> None:
    logger.setLevel(level)
    formatter = ColoredFormatter("%(levelname)-8s : %(message)s")
    if not logger.hasHandlers():
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    else:
        for handler in logger.handlers:
            handler.setFormatter(formatter)


def read_sql_table(name: str) -> pd.DataFrame:
    df = pd.DataFrame()
    if not constants.DATABASE_FILE.exists():
        return df
    con = sqlite3.connect(constants.DATABASE_FILE)
    if (
        con.execute(
            "SELECT name FROM sqlite_master"
            f" WHERE type='table' AND name='{name}';"
        ).fetchone()
        is not None
    ):
        df = pd.read_sql_query(f"SELECT * FROM {name};", con)
        df = set_column_types(df)
    con.close()
    return df


def compute_balances() -> pd.DataFrame:
    """Compute balances considering pending transactions."""
    balances = read_sql_table("balances")
    if balances.empty:
        return balances
    transactions = read_sql_table("transactions")
    transaction_sums = (
        transactions.loc[transactions["entry_date"].isna()]
        .groupby("fin_iban")["amount"]
        .sum()
        .reset_index()
    )
    balances = balances.merge(
        transaction_sums,
        left_on="iban",
        right_on="fin_iban",
        how="left",
        suffixes=("", "_trans"),
    )
    balances["amount"] = balances["amount"].fillna(0) + balances[
        "amount_trans"
    ].fillna(0)
    balances.drop(columns=["amount_trans", "fin_iban"], inplace=True)
    return balances


def sync_transactions(
    fetched_transactions: list[fints.models.Transaction],
) -> pd.DataFrame:
    new_transactions_df = pd.DataFrame([t.data for t in fetched_transactions])
    if new_transactions_df.empty:
        return new_transactions_df
    new_transactions_df = set_column_types(new_transactions_df)
    con = sqlite3.connect(constants.DATABASE_FILE)
    if (
        con.execute(
            "SELECT name FROM sqlite_master"
            " WHERE type='table' AND name='transactions';"
        ).fetchone()
        is None
    ):
        new_transactions_df.to_sql(name="transactions", con=con, index=False)
        resulting_df = new_transactions_df
    else:
        # remove pending transactions
        con.execute("DELETE FROM transactions WHERE entry_date IS null;")
        con.commit()
        old_transactions_df = pd.read_sql_query(
            "SELECT * FROM transactions;", con
        )
        old_transactions_df = set_column_types(old_transactions_df)
        transactions_df = pd.concat(
            [old_transactions_df, new_transactions_df]
        ).drop_duplicates(subset=["fin_id"])
        transactions_df.to_sql(
            name="transactions", con=con, if_exists="replace", index=False
        )
        resulting_df = transactions_df
    con.close()
    return resulting_df


def sync_balances(
    fetched_balances: dict[fints.models.Account, fints.models.Balance],
) -> pd.DataFrame:
    con = sqlite3.connect(constants.DATABASE_FILE)
    product_name = {
        a["iban"]: a["product_name"].replace("  ", " ")
        for a in state.fintsclient.get_information()["accounts"]
        if a["iban"] is not None
    }
    balances_df = pd.DataFrame(
        [
            {
                "fin_datetime": pd.to_datetime(datetime.datetime.now()),
                "product_name": product_name[account.iban],
                "iban": account.iban,
                "amount": float(balance.amount.amount),
                "date": balance.date.strftime("%Y-%m-%d"),
            }
            for account, balance in fetched_balances.items()
        ]
    )
    balances_df.to_sql(
        name="balances", con=con, if_exists="replace", index=False
    )
    con.close()
    return balances_df


def sync_all() -> tuple[pd.DataFrame, pd.DataFrame]:
    fetched_balances, fetched_transactions = onlinebanking.fetch_all()
    return sync_balances(fetched_balances), sync_transactions(
        fetched_transactions
    )


def transform_transaction(row: pd.Series) -> pd.Series:
    """Transform a transaction row."""
    for column in ("amount", "compensation_amount", "original_amount"):
        if row[column] is None:
            continue
        row[column] = str(row[column]).replace(row["currency"], "").strip()
        row[column] = float(row[column])
    for column in ("date", "entry_date", "guessed_entry_date"):
        row[column] = pd.to_datetime(row[column])
    return row
