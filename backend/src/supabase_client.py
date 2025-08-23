import os
from typing import Optional

import pandas as pd
from supabase import Client, create_client


_SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
_SUPABASE_KEY: Optional[str] = os.getenv("SUPABASE_KEY")

_client: Optional[Client] = None
if _SUPABASE_URL and _SUPABASE_KEY:
    _client = create_client(_SUPABASE_URL, _SUPABASE_KEY)


def upsert_predictions(df: pd.DataFrame, table: str = "predictions") -> None:
    """Upload the day's predictions to Supabase and clear stale data.

    Parameters
    ----------
    df: pandas.DataFrame
        DataFrame containing prediction rows.
    table: str
        Target Supabase table name.
    """
    if _client is None:
        raise RuntimeError("Supabase client is not configured. Set SUPABASE_URL and SUPABASE_KEY.")

    records = df.where(pd.notnull(df), None).to_dict("records")
    if records:
        if table == "predictions":
            _client.table(table).delete().neq("id", 0).execute()
        if table == "history":
            _client.table(table).delete().neq("id", 0).execute()
        _client.table(table).upsert(records).execute()


def upload_file(
    local_path: str,
    bucket: str = "mlb-data",
    dest_path: Optional[str] = None,
) -> None:
    """Upload a local file to a Supabase storage bucket.

    Parameters
    ----------
    local_path: str
        Path to the local file to upload.
    bucket: str
        Name of the Supabase storage bucket.
    dest_path: Optional[str]
        Path (including filename) to store within the bucket. If omitted,
        the file's basename is used.
    """
    if _client is None:
        raise RuntimeError("Supabase client is not configured. Set SUPABASE_URL and SUPABASE_KEY.")

    target_path = dest_path or os.path.basename(local_path)
    with open(local_path, "rb") as f:
        # All header values must be strings. The Supabase client forwards the
        # options dictionary directly to the underlying HTTP headers, so using a
        # boolean here results in ``Header value must be str or bytes`` at runtime.
        # See issue described in previous commit.
        _client.storage.from_(bucket).upload(target_path, f, {"upsert": "true"})
