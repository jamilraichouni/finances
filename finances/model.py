# Copyright Jamil RAICHOUNI and contributors
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pathlib

import pandas as pd
import yaml


def load(filepath: pathlib.Path) -> pd.DataFrame:
    with open(filepath) as f:
        df = pd.DataFrame(yaml.safe_load(f))
        # convert column `notes` to object:
        df["notes"] = df["notes"].apply(lambda x: x if x is not None else "")
        df.attrs["filepath"] = filepath
    return df
