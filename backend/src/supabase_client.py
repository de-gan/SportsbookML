import os
from typing import Optional
import pandas as pd
from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()
_SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
_SUPABASE_KEY: Optional[str] = os.getenv("SUPABASE_KEY")
_SUPABASE_BUCKET: Optional[str] = os.getenv("SUPABASE_BUCKET")

_client: Optional[Client] = None
if _SUPABASE_URL and _SUPABASE_KEY:
    _client = create_client(_SUPABASE_URL, _SUPABASE_KEY)
    
def _require_client() -> Client:
    """Return a configured Supabase client or raise an error."""
    if _client is None:
        raise RuntimeError(
            "Supabase client is not configured. Set SUPABASE_URL and SUPABASE_KEY."
        )
    return _client

def ensure_local_file(bucket: str, storage_path: str, local_path: str) -> str:
    """Download a file from a Supabase storage bucket if it is missing locally."""
    if not os.path.exists(local_path):
        client = _require_client()
        data = client.storage.from_(bucket).download(storage_path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(data)
        print("Downloaded ", storage_path, " from Supabase bucket")
    return local_path


def upsert_predictions(df: pd.DataFrame, table: str = "predictions") -> None:
    """Upload the day's predictions to Supabase and clear stale data."""
    client = _require_client()
    records = df.where(pd.notnull(df), None).to_dict("records")
    if records:
        if table == "predictions":
            client.table(table).delete().neq("id", 0).execute()
        if table == "history":
            client.table(table).delete().neq("id", 0).execute()
        client.table(table).upsert(records).execute()
        
        
def upload_file_to_bucket(file_path: str, bucket: Optional[str] = None, dest_path: Optional[str] = None) -> None:
    """Upload a file to the configured Supabase storage bucket."""
    if _client is None:
        raise RuntimeError(
            "Supabase client is not configured. Set SUPABASE_URL and SUPABASE_KEY."
        ) 

    bucket_name = bucket or _SUPABASE_BUCKET
    if not bucket_name:
        raise RuntimeError(
            "Supabase storage bucket is not configured. Set SUPABASE_BUCKET or pass bucket."
        )

    target_path = dest_path or os.path.basename(file_path)

    with open(file_path, "rb") as f:
        _client.storage.from_(bucket_name).upload(target_path, f, {"upsert": "true"})
    print("Uploaded", file_path, "to Supabase bucket")
