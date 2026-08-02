from app.store import NanoStore, make_nano


def _seed():
    store = NanoStore()
    store.load(
        [
            make_nano(id=1, name="Death's Gaze", ql=142, school="Combat", profession=5),
            make_nano(id=2, name="Complete Heal", ql=100, school="Healing", profession=3),
            make_nano(id=3, name="Combat Boost", ql=142, school="Combat", profession=3),
        ]
    )
    return store


def test_search_matches_substring_case_insensitively():
    store = _seed()
    assert len(store.search(query="gaze", ql=0, school="", profession=None, limit=50)) == 1
    assert len(store.search(query="GAZE", ql=0, school="", profession=None, limit=50)) == 1


def test_search_filters_by_school():
    store = _seed()
    results = store.search(query="", ql=0, school="Combat", profession=None, limit=50)
    assert {n.id for n in results} == {1, 3}


def test_search_filters_by_profession():
    store = _seed()
    results = store.search(query="", ql=0, school="", profession=3, limit=50)
    assert {n.id for n in results} == {2, 3}


def test_search_combines_filters():
    store = _seed()
    results = store.search(query="", ql=0, school="Combat", profession=3, limit=50)
    assert [n.id for n in results] == [3]


def test_count_reflects_total_matches_not_limit():
    store = _seed()
    assert store.count(query="", ql=142, school="", profession=None) == 2
    assert len(store.search(query="", ql=142, school="", profession=None, limit=1)) == 1


def test_get_returns_nano_by_id_or_none():
    store = _seed()
    assert store.get(1).name == "Death's Gaze"
    assert store.get(999) is None
