"""One-off loader from your items-database dump into the `items` table this
service reads from (see app/db.py:Item for the target schema: id, name, ql,
icon, description).

This is deliberately NOT wired into the app's startup or CI - it's a manual
step you run once against the target MariaDB (or re-run whenever you refresh
the dump). Adjust SOURCE_PATH and the row-mapping below to match your dump's
actual columns/format before running.

Usage:
    DATABASE_URL=mysql+pymysql://user:pass@host:3306/aodb \
        python scripts/import_dump.py /path/to/your/dump.csv
"""

import csv
import sys

from app.db import Item, make_session_factory


def main(dump_path: str) -> None:
    SessionLocal = make_session_factory()
    session = SessionLocal()

    with open(dump_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        batch = []
        for row in reader:
            # TODO: adjust these key names to match your dump's actual
            # column headers once you know its exact shape.
            batch.append(
                Item(
                    id=int(row["aoid"]),
                    name=row["name"],
                    ql=int(row.get("ql") or 0),
                    icon=int(row.get("icon") or 0),
                    description=row.get("description"),
                )
            )
            if len(batch) >= 1000:
                session.bulk_save_objects(batch)
                session.commit()
                batch.clear()

        if batch:
            session.bulk_save_objects(batch)
            session.commit()

    session.close()
    print("Import complete.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1])
