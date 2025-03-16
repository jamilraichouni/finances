# Copyright Jamil RAICHOUNI and contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    import fints.client
    import fints.models
    import pandas as pd

bank_accounts: list[dict[str, t.Any]]
sepa_accounts: list[fints.models.SEPAAccount]
fintsclient: fints.client.FinTS3PinTanClient = None
fints_dialog: bytes
fints_tan: bytes = b""
positions: pd.DataFrame
