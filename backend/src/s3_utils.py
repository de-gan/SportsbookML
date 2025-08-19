import os
from typing import Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

_S3 = boto3.client("s3")
PREDICTIONS_BUCKET = os.environ.get("PREDICTIONS_BUCKET")
MODELS_BUCKET = os.environ.get("MODELS_BUCKET", PREDICTIONS_BUCKET)

def upload_file(local_path: str, key: str, bucket: Optional[str] = None) -> None:
    """Upload a local file to S3 with private ACL."""
    bucket = bucket or PREDICTIONS_BUCKET
    if not bucket:
        return
    try:
        _S3.upload_file(local_path, bucket, key, ExtraArgs={"ACL": "private"})
    except (BotoCoreError, ClientError) as exc:
        print(f"Failed to upload {local_path} to s3://{bucket}/{key}: {exc}")

def upload_model(local_path: str, key: Optional[str] = None) -> None:
    """Upload a trained model to S3 using the models bucket."""
    bucket = MODELS_BUCKET or PREDICTIONS_BUCKET
    dest_key = key or os.path.basename(local_path)
    upload_file(local_path, dest_key, bucket=bucket)


def download_file(key: str, local_path: str, bucket: Optional[str] = None) -> None:
    """Download a file from S3."""
    bucket = bucket or PREDICTIONS_BUCKET
    if not bucket:
        return
    try:
        _S3.download_file(bucket, key, local_path)
    except (BotoCoreError, ClientError) as exc:
        print(f"Failed to download s3://{bucket}/{key}: {exc}")
