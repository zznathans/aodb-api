"""In-memory item store. The dump is the single source of truth and is
small (~65MB/125k rows) and rarely-changing, so each pod independently
loads its own copy into memory on startup rather than sharing state via an
external database - no DB/cache layer to run or keep in sync."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    id: int
    name: str
    name_lower: str
    ql: int
    icon: int
    description: str | None


def make_item(id: int, name: str, ql: int = 0, icon: int = 0, description: str | None = None) -> Item:
    return Item(id=id, name=name, name_lower=name.lower(), ql=ql, icon=icon, description=description)


class ItemStore:
    def __init__(self) -> None:
        self._items: list[Item] = []

    def load(self, items: list[Item]) -> None:
        self._items = items

    def __len__(self) -> int:
        return len(self._items)

    def _matches(self, query: str, ql: int) -> list[Item]:
        needle = query.lower()
        matches = [
            item
            for item in self._items
            if (not needle or needle in item.name_lower) and (not ql or item.ql == ql)
        ]
        matches.sort(key=lambda item: item.name)
        return matches

    def count(self, query: str, ql: int) -> int:
        return len(self._matches(query, ql))

    def search(self, query: str, ql: int, limit: int, offset: int = 0) -> list[Item]:
        return self._matches(query, ql)[offset : offset + limit]

    def get(self, aoid: int) -> Item | None:
        return next((item for item in self._items if item.id == aoid), None)


# Single shared instance: both the v1 (app/main.py) and v2 (app/v2.py)
# routers read from the same in-memory data, loaded once at startup.
store = ItemStore()
