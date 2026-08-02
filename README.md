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

Backed by a MariaDB `items` table (`id`, `name`, `ql`, `icon`, `description`
— see `app/db.py`). Load your item dump with `scripts/import_dump.py`
(adjust the column mapping to match your dump's actual format first).

## Local development

```
pip install -r requirements-dev.txt
DATABASE_URL=sqlite:///./dev.sqlite3 uvicorn app.main:app --reload
pytest
```

## Deployment

Built and pushed to `ghcr.io/zznathans/aodb-api` on each GitHub Release
(`.github/workflows/docker.yml`), then rolled out via the
[`aodb-api-helm`](https://github.com/zznathans/aodb-api-helm) chart,
deployed through ArgoCD from `zznathans/charts`.
