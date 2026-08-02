# aodb-api

Self-hosted replacement for the third-party "Central Item Database"
(`cidb.bebot.link`) that BeBot's `!items` command relies on, which has been
suffering Cloudflare 522 (origin timeout) outages. Implements the same
query-string contract and returns the same raw AOML text BeBot expects, so
it's a drop-in replacement via BeBot's `Items.CIDB` setting.

## API

`GET /?bot=BeBot&output=aoml&max=50&search=<name>&ql=<ql>&icons=true&color_header=<hex>&color_highlight=<hex>&color_normal=<hex>`

Only `output=aoml` is implemented (the only value BeBot ever sends). Always
returns HTTP 200 with a body (including "no results"), since BeBot's client
does no status-code checking and shows the raw response verbatim in chat.

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
