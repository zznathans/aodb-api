# aodb-api

Self-hosted replacement for the third-party "Central Item Database"
(`cidb.bebot.link`) that BeBot's `!items` command relies on, which has been
suffering Cloudflare 522 (origin timeout) outages. Implements the same
query-string contract and returns the same raw AOML text BeBot expects, so
it's a drop-in replacement via BeBot's `Items.CIDB` setting.

## API

### v1 (BeBot / AOML)

`GET /?bot=BeBot&output=aoml&max=50&search=<name>&ql=<ql>&icons=true&color_header=<hex>&color_highlight=<hex>&color_normal=<hex>`

Only `output=aoml` is implemented (the only value BeBot ever sends). Always
returns HTTP 200 with a body (including "no results"), since BeBot's client
does no status-code checking and shows the raw response verbatim in chat.

### v2 (plain JSON)

A normal JSON API for anything else that wants item data - no BeBot-specific
quirks, real HTTP status codes.

- `GET /v2/items?q=<name>&ql=<ql>&limit=50&offset=0` or the equivalent
  `POST /v2/items` with the same fields as a JSON body - both return a bare
  JSON array of `{"id", "name", "ql", "icon", "description"}`, with the
  total match count (pre-pagination) in the `X-Total-Count` response header.
- `GET /v2/items/{aoid}` - direct lookup by item id, 404 (JSON body) if not
  found.
- `GET`/`POST /v2/nanos` - same shape as `/v2/items`, plus `school` (exact
  match, e.g. `Combat`/`Healing`/`Psionic`/`Space`/`Protection`) and
  `profession` (raw numeric profession id as it appears in the dump - not
  translated to a name, since there's no authoritative id→name mapping
  available to verify against). Response objects additionally include
  `strain`, `nanocost`, `ncu`, `crystal_id`, `duration`, `profession`, and
  `requirements` (the full list of casting requirements from the dump, as
  `{"attribute", "operator", "value"}`).
- `GET /v2/nanos/{aoid}` - direct lookup by nano id.
- Interactive docs at `/docs` (Swagger UI), machine-readable spec at
  `/openapi.json` (`/healthz` is intentionally excluded from both).

## Data

No database - the item dump (a zipped `<aodb><item aoid="..." .../></aodb>`
XML file, e.g. `171003.xml.zip`) is small (~65MB in memory, ~125k items)
and changes rarely, so each pod loads its own in-memory copy from a public
HTTPS URL on startup (`app/dump_loader.py`, `app/store.py`). Readiness is
gated on this completing.

## Local development

```
pip install -r requirements-dev.txt
DUMP_PATH=/path/to/171003.xml.zip uvicorn app.main:app --reload
pytest
```

`DUMP_URL` (used in production) works too; `DUMP_PATH` is for a local file
without needing network access.
