"""In-memory item/nano-program stores. The dump is the single source of
truth and is small (~65MB/125k rows) and rarely-changing, so each pod
independently loads its own copy into memory on startup rather than
sharing state via an external database - no DB/cache layer to run or keep
in sync."""

from dataclasses import dataclass, field


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


@dataclass(frozen=True)
class Requirement:
    attribute: str
    operator: str
    value: str


@dataclass(frozen=True)
class NanoProgram:
    id: int
    name: str
    name_lower: str
    ql: int
    icon: int
    description: str | None
    school: str | None
    strain: int | None
    nanocost: int | None
    ncu: int | None
    crystal_id: int | None
    duration: int | None
    profession: int | None
    requirements: tuple[Requirement, ...] = field(default_factory=tuple)


def make_nano(
    id: int,
    name: str,
    ql: int = 0,
    icon: int = 0,
    description: str | None = None,
    school: str | None = None,
    strain: int | None = None,
    nanocost: int | None = None,
    ncu: int | None = None,
    crystal_id: int | None = None,
    duration: int | None = None,
    profession: int | None = None,
    requirements: tuple[Requirement, ...] = (),
) -> NanoProgram:
    return NanoProgram(
        id=id,
        name=name,
        name_lower=name.lower(),
        ql=ql,
        icon=icon,
        description=description,
        school=school,
        strain=strain,
        nanocost=nanocost,
        ncu=ncu,
        crystal_id=crystal_id,
        duration=duration,
        profession=profession,
        requirements=requirements,
    )


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


class NanoStore:
    def __init__(self) -> None:
        self._nanos: list[NanoProgram] = []

    def load(self, nanos: list[NanoProgram]) -> None:
        self._nanos = nanos

    def __len__(self) -> int:
        return len(self._nanos)

    def _matches(self, query: str, ql: int, school: str, profession: int | None) -> list[NanoProgram]:
        needle = query.lower()
        school_needle = school.lower()
        matches = [
            nano
            for nano in self._nanos
            if (not needle or needle in nano.name_lower)
            and (not ql or nano.ql == ql)
            and (not school_needle or (nano.school or "").lower() == school_needle)
            and (profession is None or nano.profession == profession)
        ]
        matches.sort(key=lambda nano: nano.name)
        return matches

    def count(self, query: str, ql: int, school: str, profession: int | None) -> int:
        return len(self._matches(query, ql, school, profession))

    def search(
        self, query: str, ql: int, school: str, profession: int | None, limit: int, offset: int = 0
    ) -> list[NanoProgram]:
        return self._matches(query, ql, school, profession)[offset : offset + limit]

    def get(self, aoid: int) -> NanoProgram | None:
        return next((nano for nano in self._nanos if nano.id == aoid), None)


# Single shared instances: the v1 (app/main.py) and v2 (app/v2.py) routers
# all read from the same in-memory data, loaded once at startup.
store = ItemStore()
nano_store = NanoStore()
