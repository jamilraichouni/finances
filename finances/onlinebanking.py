# Copyright Jamil RAICHOUNI and contributors
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import contextlib
import datetime
import logging
import os
import pathlib
import typing as t

import fints.client
import fints.hhd.flicker
import fints.models
import fints.utils
import mt940.models
import pandas as pd

from finances import constants, core, state

UNINTERESTING_TRANSACTION_ATTRS: tuple[str, ...] = (
    "additional_position_date",
    "additional_position_reference",
    "additional_purpose",
    "applicant_creditor_id",
    "bank_reference",
    "compensation_amount",
    "customer_reference",
    "debitor_identifier",
    "deviate_applicant",
    "deviate_recipient",
    "end_to_end_reference",
    "extra_details",
    "FRST_ONE_OFF_RECC",
    "funds_code",
    "gvc_applicant_bin",
    "gvc_applicant_iban",
    "id",
    "old_SEPA_additional_position_reference",
    "old_SEPA_CI",
    "original_amount",
    "prima_nota",
    "purpose_code",
    "recipient_name",
    "return_debit_notes",
    "settlement_tag",
    "status",
    "transaction_code",
)

logger = logging.getLogger(__package__)


def select_tan_mechanism(tan_mechanism_name: str) -> None:
    """Obtain from fints/utils.py:minimal_interactive_cli_bootstrap()."""
    if not state.fintsclient.get_current_tan_mechanism():
        state.fintsclient.fetch_tan_mechanisms()
        mechanisms = list(state.fintsclient.get_tan_mechanisms().items())
        if len(mechanisms) > 1:
            for _, mechanism in enumerate(mechanisms):
                if mechanism[1].name == tan_mechanism_name:
                    state.fintsclient.set_tan_mechanism(mechanism[0])
                    break


def select_tan_medium(tan_medium_name: str) -> bool:
    """Obtain from fints/utils.py:minimal_interactive_cli_bootstrap()."""
    success = False
    available_tan_medium_names = []
    if (
        state.fintsclient.selected_tan_medium is None
        and state.fintsclient.is_tan_media_required()
    ):
        m = state.fintsclient.get_tan_media()
        if len(m[1]) == 1:
            state.fintsclient.set_tan_medium(m[1][0])
        else:
            for i, mm in enumerate(m[1]):
                available_tan_medium_names.append(mm.tan_medium_name)
                if mm.tan_medium_name == tan_medium_name:
                    state.fintsclient.set_tan_medium(m[1][i])
                    success = True
                    break
    if not success:
        logger.error(
            "Could not select TAN medium '%s' out of available tan media: %s",
            tan_medium_name,
            ", ".join(available_tan_medium_names),
        )
    return success


def disconnect() -> None:
    """Disconnect from online banking."""
    if state.fintsclient is not None:
        logger.debug("Disconnect from online banking.")
        with state.fintsclient.resume_dialog(state.fints_dialog):
            state.fints_dialog = state.fintsclient.pause_dialog()
            if not constants.FINTS_DIALOG_FILE.is_file():
                constants.FINTS_DIALOG_FILE.write_bytes(state.fints_dialog)
        client_data = state.fintsclient.deconstruct(including_private=True)
        if not constants.FINTS_CLIENT_FILE.is_file():
            pathlib.Path(constants.FINTS_CLIENT_FILE).write_bytes(client_data)
        del state.fintsclient


def get_client(*, reuse_dialog: bool = False) -> None:
    if not reuse_dialog:
        for path in (
            # constants.FINTS_CLIENT_FILE,
            constants.FINTS_DIALOG_FILE,
            constants.FINTS_SYSTEM_ID_FILE,
            constants.FINTS_TAN_FILE,
        ):
            if path.is_file():
                path.unlink()
    constants.DATA_DIR.mkdir(parents=True, exist_ok=True)
    client_data, system_id = None, None
    if constants.FINTS_CLIENT_FILE.is_file():
        client_data = constants.FINTS_CLIENT_FILE.read_bytes()
        if constants.FINTS_SYSTEM_ID_FILE.is_file():
            system_id = constants.FINTS_SYSTEM_ID_FILE.read_bytes().decode()
    state.fintsclient = fints.client.FinTS3PinTanClient(
        bank_identifier=os.environ["FINTS_CLIENT_BANK_IDENTIFIER"],
        user_id=os.environ["FINTS_CLIENT_USER_ID"],
        pin=os.environ["FINTS_CLIENT_PIN"],
        server=os.environ["FINTS_CLIENT_SERVER"],
        product_id=os.environ["FINTS_CLIENT_PRODUCT_ID"],
        from_data=client_data,
        system_id=system_id,
    )
    constants.FINTS_SYSTEM_ID_FILE.write_bytes(
        state.fintsclient.system_id.encode()
    )
    if client_data is None:
        select_tan_mechanism(os.environ["TAN_MECHANISM"])
        if not select_tan_medium(os.environ["TAN_MEDIUM_NAME"]):
            raise ValueError("Could not select TAN medium.")


def ask_for_tan(
    response: fints.client.NeedTANResponse,
) -> fints.client.TANResponse:
    if getattr(response, "challenge_hhduc", None):
        with contextlib.suppress(KeyboardInterrupt):
            fints.hhd.flicker.terminal_flicker_unix(response.challenge_hhduc)
    if response.decoupled:
        tan = ""
    else:
        tan = input("Please enter TAN:\n")
    if constants.FINTS_TAN_FILE.is_file():
        tan_data = constants.FINTS_TAN_FILE.read_bytes()
        tan_request = fints.client.NeedRetryResponse.from_data(tan_data)
        return state.fintsclient.send_tan(tan_request, tan)
    if (
        hasattr(response, "get_data")
        and not constants.FINTS_TAN_FILE.is_file()
    ):
        constants.FINTS_TAN_FILE.write_bytes(response.get_data())
    return state.fintsclient.send_tan(response, tan)


def get_response(response: fints.client.Response) -> fints.client.Response:
    while isinstance(response, fints.client.NeedTANResponse):
        response = ask_for_tan(response)
    return response


def invoke(*, methodname: str, **kwargs: t.Any) -> fints.client.Response:
    try:
        if constants.FINTS_DIALOG_FILE.is_file():
            fintscontext = state.fintsclient.resume_dialog(
                constants.FINTS_DIALOG_FILE.read_bytes()
            )
        else:
            fintscontext = state.fintsclient
        with fintscontext:
            method = getattr(state.fintsclient, methodname, None)
            if method is None:
                raise AttributeError(
                    f"Method {methodname} not found in fintsclient."
                )
            response = getattr(state.fintsclient, methodname)(**kwargs)
            response = get_response(response)
            dialog_data = state.fintsclient.pause_dialog()
        client_data = state.fintsclient.deconstruct(including_private=True)
        if not constants.FINTS_CLIENT_FILE.is_file():
            pathlib.Path(constants.FINTS_CLIENT_FILE).write_bytes(client_data)
        assert dialog_data is not None
        # if not constants.FINTS_DIALOG_FILE.is_file():
        pathlib.Path(constants.FINTS_DIALOG_FILE).write_bytes(dialog_data)
    except fints.client.FinTSDialogStateError:
        response = None
    except fints.client.FinTSClientError:
        for path in (
            constants.FINTS_CLIENT_FILE,
            constants.FINTS_DIALOG_FILE,
            constants.FINTS_SYSTEM_ID_FILE,
            constants.FINTS_TAN_FILE,
        ):
            if path.is_file():
                path.unlink()
        response = invoke(methodname=methodname, **kwargs)
    return response


def fetch_transactions() -> list[fints.models.Transaction]:
    fetched_transactions = []
    if not hasattr(state, "sepa_accounts"):
        state.sepa_accounts = invoke(methodname="get_sepa_accounts")
    for account in state.sepa_accounts:
        fetched_account_transactions = invoke(
            methodname="get_transactions",
            account=account,
            include_pending=True,
        )
        if not fetched_account_transactions:
            continue
        for ta in fetched_account_transactions:
            for k, v in ta.data.items():
                if isinstance(v, mt940.models.Amount):
                    ta.data[k] = float(v.amount)
                elif isinstance(v, mt940.models.Date):
                    ta.data[k] = v.strftime("%Y-%m-%d")
            ta.data.update(
                {
                    "fin_id": core.compute_hash_string(
                        "".join([str(v) for v in ta.data.values() if v])
                    )
                }
            )
            ta.data.update(
                {"fin_datetime": pd.to_datetime(datetime.datetime.now())}
            )
            ta.data.update({"fin_iban": account.iban})
            ta.data.update({"fin_bic": account.bic})
            # Move the keys to the front
            ta.data = {
                "fin_id": ta.data.pop("fin_id"),
                "fin_datetime": ta.data.pop("fin_datetime"),
                "fin_iban": ta.data.pop("fin_iban"),
                "fin_bic": ta.data.pop("fin_bic"),
                **ta.data,
            }
        fetched_transactions.extend(fetched_account_transactions)
    return fetched_transactions


def fetch_balances() -> dict[fints.models.Account, fints.models.Balance]:
    fetched_balances = {}
    if not hasattr(state, "sepa_accounts"):
        state.sepa_accounts = invoke(methodname="get_sepa_accounts")
    for account in state.sepa_accounts:
        fetched_balances[account] = invoke(
            methodname="get_balance",
            account=account,
        )
    return fetched_balances


def fetch_all() -> tuple[
    dict[fints.models.Account, fints.models.Balance],
    list[fints.models.Transaction],
]:
    get_client()
    return fetch_balances(), fetch_transactions()
