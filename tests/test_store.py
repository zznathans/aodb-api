from app.store import ItemStore, make_item


def test_search_matches_substring_case_insensitively():
    store = ItemStore()
    store.load([make_item(id=1, name="Notum Tank Armor", ql=200)])

    assert len(store.search(query="notum", ql=0, limit=50)) == 1
    assert len(store.search(query="TANK", ql=0, limit=50)) == 1
    assert len(store.search(query="nope", ql=0, limit=50)) == 0


def test_search_filters_by_ql():
    store = ItemStore()
    store.load(
        [
            make_item(id=1, name="Notum Tank Armor", ql=200),
            make_item(id=2, name="Notum Splitter", ql=150),
        ]
    )

    results = store.search(query="notum", ql=200, limit=50)
    assert [i.id for i in results] == [1]


def test_search_respects_limit_and_sorts_by_name():
    store = ItemStore()
    store.load(
        [
            make_item(id=1, name="Zeta Item"),
            make_item(id=2, name="Alpha Item"),
            make_item(id=3, name="Beta Item"),
        ]
    )

    results = store.search(query="Item", ql=0, limit=2)
    assert [i.name for i in results] == ["Alpha Item", "Beta Item"]


def test_len_reflects_loaded_count():
    store = ItemStore()
    assert len(store) == 0
    store.load([make_item(id=1, name="x")])
    assert len(store) == 1
