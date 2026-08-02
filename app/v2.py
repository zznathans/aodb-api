"""A plain JSON API for item search/lookup, independent of the BeBot/AOML
contract v1 (GET /) implements. Simple query params or a JSON body in,
structured JSON out, real HTTP status codes."""

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from .store import Item, store

router = APIRouter(prefix="/v2")


class ItemOut(BaseModel):
    id: int
    name: str
    ql: int
    icon: int
    description: str | None

    @classmethod
    def from_item(cls, item: Item) -> "ItemOut":
        return cls(id=item.id, name=item.name, ql=item.ql, icon=item.icon, description=item.description)


class ItemQuery(BaseModel):
    q: str = ""
    ql: int = 0
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


def _search(query: ItemQuery, response: Response) -> list[ItemOut]:
    total = store.count(query.q, query.ql)
    items = store.search(query.q, query.ql, query.limit, query.offset)
    response.headers["X-Total-Count"] = str(total)
    return [ItemOut.from_item(item) for item in items]


@router.get("/items")
def search_items_get(
    response: Response,
    q: str = Query(default=""),
    ql: int = Query(default=0),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ItemOut]:
    return _search(ItemQuery(q=q, ql=ql, limit=limit, offset=offset), response)


@router.post("/items")
def search_items_post(query: ItemQuery, response: Response) -> list[ItemOut]:
    return _search(query, response)


@router.get("/items/{aoid}")
def get_item(aoid: int) -> ItemOut:
    item = store.get(aoid)
    if item is None:
        raise HTTPException(status_code=404, detail=f"No item with id {aoid}")
    return ItemOut.from_item(item)
