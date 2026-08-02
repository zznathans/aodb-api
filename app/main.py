from fastapi import FastAPI, Query, Response
from fastapi.responses import PlainTextResponse

from .aoml import render_results
from .db import Item, make_session_factory

app = FastAPI(title="aodb-api")
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
