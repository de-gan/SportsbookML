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
    """Upload the day's predictions to Supabase and clear stale data."""
    if _client is None:
        raise RuntimeError("Supabase client is not configured. Set SUPABASE_URL and SUPABASE_KEY.")

    records = df.where(pd.notnull(df), None).to_dict("records")
    if records:
        if table == "predictions":
            _client.table(table).delete().neq("id", 0).execute()
        if table == "history":
            _client.table(table).delete().neq("id", 0).execute()
        _client.table(table).upsert(records).execute()
