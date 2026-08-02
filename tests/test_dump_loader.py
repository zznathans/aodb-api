import io
import zipfile
from unittest.mock import MagicMock, patch

from app.dump_loader import import_from_url, parse_items_xml, parse_items_zip

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


def test_parse_items_xml_parses_expected_fields():
    items = parse_items_xml(io.BytesIO(XML_TEXT.encode("utf-8")))

    # The third <item> has no <name> and is skipped.
    assert len(items) == 2
    assert [i.id for i in items] == [21601, 21793]
    assert items[0].name == "Flamethrower Ammunition"
    assert items[0].name_lower == "flamethrower ammunition"
    assert items[0].ql == 1
    assert items[0].icon == 32168
    assert "nervous system" in items[1].description


def test_parse_items_zip_extracts_and_parses():
    items = parse_items_zip(_zip_bytes(XML_TEXT, "171003.xml"))
    assert len(items) == 2


def test_import_from_url_downloads_and_parses():
    zip_data = _zip_bytes(XML_TEXT)
    mock_resp = MagicMock()
    mock_resp.read.return_value = zip_data
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        items = import_from_url("https://aodb-api.s3.yeetbox.net/171003.xml.zip")

    assert len(items) == 2
    (request,), _ = mock_urlopen.call_args
    assert request.full_url == "https://aodb-api.s3.yeetbox.net/171003.xml.zip"
    # Cloudflare blocks the default "Python-urllib/..." UA on the real bucket.
    assert request.get_header("User-agent") == "aodb-api/1.0"
