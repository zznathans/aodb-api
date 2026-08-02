from app.store import make_nano, nano_store


def _seed():
    nano_store.load(
        [
            make_nano(
                id=25980,
                name="Death's Gaze",
                ql=142,
                icon=16248,
                description="Holds the target in place.",
                school="Combat",
                strain=147,
                nanocost=265,
                ncu=44,
                crystal_id=26017,
                duration=453,
                profession=5,
                requirements=(),
            ),
            make_nano(id=25982, name="Change Form: Opifex", ql=-1, school="Healing", profession=None),
        ]
    )


def test_search_returns_nano_specific_fields(client):
    _seed()

    resp = client.get("/v2/nanos", params={"q": "gaze"})

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    nano = body[0]
    assert nano["id"] == 25980
    assert nano["school"] == "Combat"
    assert nano["strain"] == 147
    assert nano["nanocost"] == 265
    assert nano["ncu"] == 44
    assert nano["crystal_id"] == 26017
    assert nano["duration"] == 453
    assert nano["profession"] == 5


def test_search_filters_by_school(client):
    _seed()

    resp = client.get("/v2/nanos", params={"school": "Healing"})

    body = resp.json()
    assert len(body) == 1
    assert body[0]["name"] == "Change Form: Opifex"


def test_search_filters_by_profession(client):
    _seed()

    resp = client.get("/v2/nanos", params={"profession": 5})

    body = resp.json()
    assert len(body) == 1
    assert body[0]["id"] == 25980


def test_search_sets_total_count_header(client):
    _seed()

    resp = client.get("/v2/nanos", params={"limit": 1})

    assert resp.headers["X-Total-Count"] == "2"
    assert len(resp.json()) == 1


def test_post_search_matches_get_behavior(client):
    _seed()

    resp = client.post("/v2/nanos", json={"school": "Combat"})

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["name"] == "Death's Gaze"


def test_get_by_id_returns_nano(client):
    _seed()

    resp = client.get("/v2/nanos/25980")

    assert resp.status_code == 200
    assert resp.json()["name"] == "Death's Gaze"


def test_get_by_id_404s_for_unknown_id(client):
    _seed()

    resp = client.get("/v2/nanos/999999")

    assert resp.status_code == 404
    assert "999999" in resp.json()["detail"]


def test_items_endpoints_unaffected_by_nano_data(client):
    _seed()

    resp = client.get("/v2/items", params={"q": "gaze"})

    assert resp.status_code == 200
    assert resp.json() == []
