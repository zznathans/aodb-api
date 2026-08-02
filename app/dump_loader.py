"""Loads the real AO item dump format into the `items` table: a zip archive
containing a single large <aodb><item aoid="..." .../>...</aodb> XML file
(e.g. "171003.xml.zip"). Used both by the manual scripts/import_dump.py CLI
and by the S3 auto-import-on-empty-DB startup hook in app/main.py.

Parses with ET.iterparse and clears each <item> element after reading it,
so peak memory stays proportional to one item at a time rather than the
whole ~180MB decompressed document - important since this can run at
container startup under a modest memory limit.
"""

import io
import logging
import zipfile
from typing import IO
from xml.etree import ElementTree as ET

from sqlalchemy.orm import Session

from .db import Item

logger = logging.getLogger(__name__)

_BATCH_SIZE = 1000


def _parse_item(elem: ET.Element) -> Item | None:
    aoid = elem.get("aoid")
    name_el = elem.find("name")
    name = (name_el.text or "").strip() if name_el is not None else ""
    if not aoid or not name:
        return None

    ql_el = elem.find("ql")
    icon_el = elem.find("icon")
    desc_el = elem.find("description")

    return Item(
        id=int(aoid),
        name=name,
        ql=int(ql_el.text) if ql_el is not None and ql_el.text else 0,
        icon=int(icon_el.text) if icon_el is not None and icon_el.text else 0,
        description=(desc_el.text or None) if desc_el is not None else None,
    )


def load_items_xml(session: Session, fileobj: IO[bytes]) -> int:
    """Streams <item> elements from an open aodb XML file object into the
    `items` table. Caller owns opening/closing fileobj. Returns the number
    of rows loaded (items with no aoid/name are skipped and logged)."""
    batch = []
    count = 0
    skipped = 0

    for _event, elem in ET.iterparse(fileobj, events=("end",)):
        if elem.tag != "item":
            continue

        item = _parse_item(elem)
        elem.clear()

        if item is None:
            skipped += 1
            continue

        batch.append(item)
        count += 1
        if len(batch) >= _BATCH_SIZE:
            session.bulk_save_objects(batch)
            session.commit()
            batch.clear()

    if batch:
        session.bulk_save_objects(batch)
        session.commit()

    if skipped:
        logger.warning("Skipped %d <item> elements with no aoid/name", skipped)

    return count


def load_items_zip(session: Session, data: bytes) -> int:
    """Opens a zip archive (bytes) and streams the first .xml member found
    into load_items_xml, without materializing the decompressed XML as a
    single in-memory string."""
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        xml_names = [n for n in zf.namelist() if n.endswith(".xml")]
        if not xml_names:
            raise ValueError("No .xml member found in dump zip")
        with zf.open(xml_names[0]) as xml_file:
            return load_items_xml(session, xml_file)


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
    count = load_items_zip(session, data)
    logger.info("Loaded %d items from s3://%s/%s", count, bucket, key)
    return count
