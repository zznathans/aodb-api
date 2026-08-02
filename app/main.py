import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Response
from fastapi.responses import PlainTextResponse

from .aoml import render_results
from .db import Item, make_session_factory
from .dump_loader import import_from_s3

logger = logging.getLogger(__name__)


def _import_from_s3_if_empty() -> None:
    """One-time bootstrap: if S3_BUCKET is configured and the items table is
    empty, pull and load the dump before serving traffic. Meant for a dump
    that changes rarely - readiness is intentionally gated on this
    completing, so a bad/missing dump surfaces as a stuck rollout rather
    than an API silently serving zero results. Re-run manually (via
    scripts/import_dump.py, or by emptying the table and restarting) to
    pick up a refreshed dump - this only ever fires once per empty table."""
    bucket = os.environ.get("S3_BUCKET")
    if not bucket:
        return

    session = SessionLocal()
    try:
        if session.query(Item).first() is not None:
            logger.info("items table already populated, skipping S3 import")
            return

        import_from_s3(
            session=session,
            bucket=bucket,
            key=os.environ["S3_KEY"],
            endpoint_url=os.environ.get("S3_ENDPOINT"),
            region=os.environ.get("S3_REGION", "auto"),
            access_key=os.environ["S3_ACCESS_KEY"],
            secret_key=os.environ["S3_SECRET_KEY"],
        )
    finally:
        session.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    _import_from_s3_if_empty()
    yield


app = FastAPI(title="aodb-api", lifespan=lifespan)
SessionLocal = make_session_factory()


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

    session = SessionLocal()
    try:
        query = session.query(Item)
        if search:
            query = query.filter(Item.name.ilike(f"%{search}%"))
        if ql:
            query = query.filter(Item.ql == ql)
        items = query.order_by(Item.name).limit(max).all()
    finally:
        session.close()

    return render_results(
        items=items,
        search=search,
        show_icons=_truthy(icons),
        color_header=color_header,
        color_highlight=color_highlight,
        color_normal=color_normal,
    )


@app.get("/healthz", response_class=PlainTextResponse)
def healthz():
    return "ok"
