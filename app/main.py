import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Response
from fastapi.responses import PlainTextResponse

from .aoml import render_results
from .dump_loader import import_from_url, parse_dump_zip
from .store import nano_store, store
from .v2 import router as v2_router

logger = logging.getLogger(__name__)


def _load_items() -> None:
    """Loads the item dump into memory before the app starts accepting
    traffic. DUMP_URL pulls the dump zip from its public HTTPS URL - the
    normal deployed path. DUMP_PATH loads a local dump zip instead, for
    local dev. With neither set, the stores stay empty and the API serves
    "no results" for everything rather than failing to start."""
    dump_url = os.environ.get("DUMP_URL")
    if dump_url:
        items, nanos = import_from_url(dump_url)
        store.load(items)
        nano_store.load(nanos)
        return

    dump_path = os.environ.get("DUMP_PATH")
    if dump_path:
        with open(dump_path, "rb") as f:
            items, nanos = parse_dump_zip(f.read())
        store.load(items)
        nano_store.load(nanos)
        return

    logger.warning("Neither DUMP_URL nor DUMP_PATH is set - serving with empty item/nano stores")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _load_items()
    yield


app = FastAPI(title="aodb-api", lifespan=lifespan)
app.include_router(v2_router)


def _truthy(value: str) -> bool:
    return value.strip().lower() in ("1", "true", "yes", "on")


@app.get("/", response_class=PlainTextResponse)
def search(
    response: Response,
    bot: str = Query(default=""),
    output: str = Query(default="aoml"),
    max: int = Query(default=50, ge=1, le=200, alias="max"),
    search: str = Query(default=""),
    ql: int = Query(default=0),
    icons: str = Query(default="true"),
    color_header: str | None = Query(default=None),
    color_highlight: str | None = Query(default=None),
    color_normal: str | None = Query(default=None),
):
    # BeBot never checks the HTTP status code and shows the raw body verbatim
    # in chat - so even error cases must return 200 with a body, never a
    # 4xx/5xx that would otherwise be dropped silently by the client.
    if output != "aoml":
        response.status_code = 400
        return f"Unsupported output format '{output}' (only 'aoml' is implemented)."

    items = store.search(query=search, ql=ql, limit=max)

    return render_results(
        items=items,
        search=search,
        show_icons=_truthy(icons),
        color_header=color_header,
        color_highlight=color_highlight,
        color_normal=color_normal,
    )


@app.get("/healthz", response_class=PlainTextResponse, include_in_schema=False)
def healthz():
    return "ok"
