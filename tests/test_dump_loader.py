import gzip
import io
from unittest.mock import MagicMock, patch

from app.db import Item
from app.dump_loader import import_from_s3, load_items_bytes, load_items_csv

CSV_TEXT = "aoid,name,ql,icon,description\n1,Notum Tank Armor,200,12345,Sturdy.\n2,Notum Splitter,150,54321,\n"


def _session(tmp_session_factory):
    return tmp_session_factory()


def test_load_items_csv_loads_expected_rows(db_session_factory):
    session = db_session_factory()
    count = load_items_csv(session, io.StringIO(CSV_TEXT))
    session.close()

    assert count == 2

    session = db_session_factory()
    items = session.query(Item).order_by(Item.id).all()
    session.close()

    assert [i.id for i in items] == [1, 2]
    assert items[0].name == "Notum Tank Armor"
    assert items[0].ql == 200
    assert items[0].icon == 12345
    assert items[1].description is None or items[1].description == ""


def test_load_items_bytes_handles_gzip(db_session_factory):
    session = db_session_factory()
    count = load_items_bytes(session, gzip.compress(CSV_TEXT.encode("utf-8")), gzipped=True)
    session.close()
    assert count == 2


def test_load_items_bytes_handles_plain(db_session_factory):
    session = db_session_factory()
    count = load_items_bytes(session, CSV_TEXT.encode("utf-8"), gzipped=False)
    session.close()
    assert count == 2


def test_import_from_s3_downloads_and_loads(db_session_factory):
    mock_body = MagicMock()
    mock_body.read.return_value = CSV_TEXT.encode("utf-8")
    mock_client = MagicMock()
    mock_client.get_object.return_value = {"Body": mock_body}

    session = db_session_factory()
    with patch("boto3.client", return_value=mock_client) as mock_boto_client:
        count = import_from_s3(
            session=session,
            bucket="my-bucket",
            key="dumps/items.csv",
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
    mock_client.get_object.assert_called_once_with(Bucket="my-bucket", Key="dumps/items.csv")
