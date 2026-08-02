from app.store import make_item, store


def _seed():
    store.load(
        [
            make_item(id=1, name="Notum Tank Armor", ql=200, icon=12345, description="Sturdy."),
            make_item(id=2, name="Notum Splitter", ql=150, icon=54321),
            make_item(id=3, name="Alpha Item", ql=1, icon=1),
        ]
    )


def test_get_search_returns_json_array_with_expected_fields(client):
    _seed()

    resp = client.get("/v2/items", params={"q": "notum"})

    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) == 2
    assert body[0] == {
        "id": 2,
        "name": "Notum Splitter",
        "ql": 150,
        "icon": 54321,
        "description": None,
    }
    assert body[1]["description"] == "Sturdy."


def test_get_search_sets_total_count_header(client):
    _seed()

    resp = client.get("/v2/items", params={"q": "notum", "limit": 1})

    assert resp.headers["X-Total-Count"] == "2"
    assert len(resp.json()) == 1


def test_get_search_ql_filter(client):
    _seed()

    resp = client.get("/v2/items", params={"q": "notum", "ql": 200})

    body = resp.json()
    assert len(body) == 1
    assert body[0]["name"] == "Notum Tank Armor"


def test_get_search_offset(client):
    _seed()

    resp = client.get("/v2/items", params={"q": "", "limit": 10, "offset": 1})

    names = [i["name"] for i in resp.json()]
    assert names == ["Notum Splitter", "Notum Tank Armor"]


def test_get_search_no_matches_returns_empty_array_not_error(client):
    _seed()

    resp = client.get("/v2/items", params={"q": "nonexistent"})

    assert resp.status_code == 200
    assert resp.json() == []
    assert resp.headers["X-Total-Count"] == "0"


def test_post_search_matches_get_behavior(client):
    _seed()

    resp = client.post("/v2/items", json={"q": "notum", "ql": 200})

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["name"] == "Notum Tank Armor"


def test_get_by_id_returns_item(client):
    _seed()

    resp = client.get("/v2/items/1")

    assert resp.status_code == 200
    assert resp.json()["name"] == "Notum Tank Armor"


def test_get_by_id_404s_for_unknown_id(client):
    _seed()

    resp = client.get("/v2/items/999999")

    assert resp.status_code == 404
    assert "999999" in resp.json()["detail"]


def test_limit_over_200_is_rejected(client):
    _seed()

    resp = client.get("/v2/items", params={"limit": 500})

    assert resp.status_code == 422
