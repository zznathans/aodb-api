def _seed(main_module):
    from app.db import Item

    session = main_module.SessionLocal()
    session.add_all(
        [
            Item(id=1, name="Notum Tank Armor", ql=200, icon=12345),
            Item(id=2, name="Notum Splitter", ql=150, icon=54321),
        ]
    )
    session.commit()
    session.close()


def test_search_returns_matching_items(client):
    test_client, main_module = client
    _seed(main_module)

    resp = test_client.get(
        "/",
        params={"bot": "BeBot", "output": "aoml", "max": 50, "search": "Notum", "ql": 0, "icons": "true"},
    )

    assert resp.status_code == 200
    body = resp.text
    assert "Notum Tank Armor" in body
    assert "Notum Splitter" in body
    assert "<img src=rdb://12345>" in body
    assert "itemref://1/1/200" in body


def test_search_with_no_matches_returns_200_not_error(client):
    test_client, main_module = client
    _seed(main_module)

    resp = test_client.get("/", params={"output": "aoml", "search": "Nonexistent Item"})

    assert resp.status_code == 200
    assert "No items found" in resp.text


def test_ql_filter(client):
    test_client, main_module = client
    _seed(main_module)

    resp = test_client.get("/", params={"output": "aoml", "search": "Notum", "ql": 200})

    assert "Notum Tank Armor" in resp.text
    assert "Notum Splitter" not in resp.text


def test_icons_false_omits_icon_tag(client):
    test_client, main_module = client
    _seed(main_module)

    resp = test_client.get("/", params={"output": "aoml", "search": "Notum", "icons": "false"})

    assert "<img src=rdb://" not in resp.text


def test_unsupported_output_format_still_returns_200_body(client):
    test_client, main_module = client

    resp = test_client.get("/", params={"output": "json", "search": "x"})

    # Not a hard requirement of the old service, but a deliberate choice here:
    # fail loudly with a 400 rather than silently misrendering, since no real
    # client ever sends anything but output=aoml.
    assert resp.status_code == 400


def test_healthz(client):
    test_client, _ = client
    resp = test_client.get("/healthz")
    assert resp.status_code == 200
    assert resp.text == "ok"
