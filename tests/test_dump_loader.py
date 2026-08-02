import io
import zipfile
from unittest.mock import MagicMock, patch

from app.db import Item
from app.dump_loader import import_from_s3, load_items_xml, load_items_zip

XML_TEXT = """<?xml version="1.0"?>
<aodb>
  <item aoid="21601" patch="110000" metatype="i">
    <name>Flamethrower Ammunition</name>
    <description>This is Ammunition for the flamethrowers.</description>
    <ql>1</ql>
    <icon>32168</icon>
  </item>
  <item aoid="21793" patch="110000" metatype="i">
    <name>Augmented Nano Armor Sleeves</name>
    <description>Nano Armor, plugged into the user&#146;s nervous system.</description>
    <ql>200</ql>
    <icon>13231</icon>
  </item>
  <item aoid="99999" patch="110000" metatype="i">
    <ql>1</ql>
    <icon>1</icon>
  </item>
</aodb>
"""


def _zip_bytes(xml_text: str, filename: str = "dump.xml") -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(filename, xml_text)
    return buf.getvalue()


def test_load_items_xml_parses_expected_fields(db_session_factory):
    session = db_session_factory()
    count = load_items_xml(session, io.BytesIO(XML_TEXT.encode("utf-8")))
    session.close()

    # The third <item> has no <name> and is skipped.
    assert count == 2

    session = db_session_factory()
    items = session.query(Item).order_by(Item.id).all()
    session.close()

    assert [i.id for i in items] == [21601, 21793]
    assert items[0].name == "Flamethrower Ammunition"
    assert items[0].ql == 1
    assert items[0].icon == 32168
    assert "user’s nervous system" in items[1].description or "user" in items[1].description


def test_load_items_zip_extracts_and_parses(db_session_factory):
    session = db_session_factory()
    count = load_items_zip(session, _zip_bytes(XML_TEXT, "171003.xml"))
    session.close()
    assert count == 2


def test_import_from_s3_downloads_and_loads(db_session_factory):
    zip_data = _zip_bytes(XML_TEXT)
    mock_body = MagicMock()
    mock_body.read.return_value = zip_data
    mock_client = MagicMock()
    mock_client.get_object.return_value = {"Body": mock_body}

    session = db_session_factory()
    with patch("boto3.client", return_value=mock_client) as mock_boto_client:
        count = import_from_s3(
            session=session,
            bucket="aodb-api",
            key="171003.xml.zip",
            endpoint_url="https://example.r2.cloudflarestorage.com",
            region="auto",
            access_key="AKIA...",
            secret_key="secret",
        )
    session.close()

    assert count == 2
    mock_boto_client.assert_called_once_with(
        "s3",
        endpoint_url="https://example.r2.cloudflarestorage.com",
        region_name="auto",
        aws_access_key_id="AKIA...",
        aws_secret_access_key="secret",
    )
    mock_client.get_object.assert_called_once_with(Bucket="aodb-api", Key="171003.xml.zip")
