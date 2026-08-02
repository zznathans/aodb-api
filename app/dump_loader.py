"""Shared CSV -> `items` table loading logic, used both by the manual
scripts/import_dump.py CLI and by the S3 auto-import-on-empty-DB startup
hook in app/main.py.
"""

import csv
import gzip
import io
import logging
from typing import IO

from sqlalchemy.orm import Session

from .db import Item

logger = logging.getLogger(__name__)

_BATCH_SIZE = 1000


def load_items_csv(session: Session, fileobj: IO[str]) -> int:
    """Bulk-loads rows from an open CSV file object into the `items` table.
    Caller owns opening/closing fileobj and committing/closing the session.
    Returns the number of rows loaded."""
    reader = csv.DictReader(fileobj)
    batch = []
    count = 0

    for row in reader:
        # TODO: adjust these key names to match your dump's actual column headers.
        batch.append(
            Item(
                id=int(row["aoid"]),
                name=row["name"],
                ql=int(row.get("ql") or 0),
                icon=int(row.get("icon") or 0),
                description=row.get("description"),
            )
        )
        count += 1
        if len(batch) >= _BATCH_SIZE:
            session.bulk_save_objects(batch)
            session.commit()
            batch.clear()

    if batch:
        session.bulk_save_objects(batch)
        session.commit()

    return count


def load_items_bytes(session: Session, data: bytes, gzipped: bool) -> int:
    raw = gzip.decompress(data) if gzipped else data
    return load_items_csv(session, io.StringIO(raw.decode("utf-8")))


def import_from_s3(
    session: Session,
    bucket: str,
    key: str,
    endpoint_url: str | None,
    region: str,
    access_key: str,
    secret_key: str,
) -> int:
    import boto3

    client = boto3.client(
        "s3",
        endpoint_url=endpoint_url or None,
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )
    logger.info("Downloading item dump from s3://%s/%s", bucket, key)
    obj = client.get_object(Bucket=bucket, Key=key)
    data = obj["Body"].read()
    count = load_items_bytes(session, data, gzipped=key.endswith(".gz"))
    logger.info("Loaded %d items from s3://%s/%s", count, bucket, key)
    return count
