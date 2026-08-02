"""One-off loader from your local aodb XML dump zip (e.g. "171003.xml.zip")
into the `items` table this service reads from (see app/db.py:Item for the
target schema, app/dump_loader.py for the parsing).

For a dump hosted in S3 that should load automatically on first boot, see
the S3_BUCKET/S3_KEY/etc. env vars handled by app/main.py's startup hook
instead - this script is for a one-off local file, or for manually
re-loading after emptying the table.

Usage:
    DATABASE_URL=mysql+pymysql://user:pass@host:3306/aodb \
        python scripts/import_dump.py /path/to/171003.xml.zip
"""

import sys

from app.db import make_session_factory
from app.dump_loader import load_items_zip


def main(dump_path: str) -> None:
    SessionLocal = make_session_factory()
    session = SessionLocal()
    with open(dump_path, "rb") as f:
        count = load_items_zip(session, f.read())
    session.close()
    print(f"Import complete: {count} items loaded.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1])
