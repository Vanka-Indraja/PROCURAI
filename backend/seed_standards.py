import json
from pathlib import Path

from app.database import Base, SessionLocal, engine
from app.models import Standard


# =========================================================
# CREATE TABLES
# =========================================================

Base.metadata.create_all(bind=engine)


# =========================================================
# FILE PATHS
# =========================================================

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent

STANDARDS_FILE = (
    PROJECT_DIR
    / "data"
    / "standards.json"
)


# =========================================================
# CHECK FILE
# =========================================================

if not STANDARDS_FILE.exists():
    raise FileNotFoundError(
        f"standards.json not found at: {STANDARDS_FILE}"
    )


print(
    f"Using standards file: {STANDARDS_FILE}"
)


# =========================================================
# LOAD JSON
# =========================================================

with open(
    STANDARDS_FILE,
    "r",
    encoding="utf-8",
) as file:
    standards_data = json.load(file)


if isinstance(standards_data, dict):
    standards_data = standards_data.get(
        "standards",
        [],
    )


# =========================================================
# DATABASE
# =========================================================

db = SessionLocal()


try:
    inserted_count = 0
    updated_count = 0

    for item in standards_data:

        standard_id = (
            item.get("standard_id")
            or item.get("id")
        )

        if not standard_id:
            print(
                "Skipped record: standard_id missing"
            )
            continue


        existing = (
            db.query(Standard)
            .filter(
                Standard.standard_id
                == standard_id
            )
            .first()
        )


        if existing:

            existing.standard_number = (
                item.get("standard_number")
            )

            existing.title = (
                item.get("title")
            )

            existing.keywords = (
                item.get("keywords", [])
            )

            existing.verified = (
                item.get(
                    "verified",
                    False,
                )
            )

            existing.source_name = (
                item.get("source_name")
            )

            existing.source_url = (
                item.get("source_url")
            )

            updated_count += 1

            print(
                f"UPDATED: {standard_id}"
            )


        else:

            standard = Standard(
                standard_id=standard_id,
                standard_number=item.get(
                    "standard_number"
                ),
                title=item.get(
                    "title"
                ),
                keywords=item.get(
                    "keywords",
                    [],
                ),
                verified=item.get(
                    "verified",
                    False,
                ),
                source_name=item.get(
                    "source_name"
                ),
                source_url=item.get(
                    "source_url"
                ),
            )

            db.add(standard)

            inserted_count += 1

            print(
                f"INSERTED: {standard_id}"
            )


    db.commit()


    print()
    print("==============================")
    print("PROCURAI Standards Seed Done")
    print("==============================")

    print(
        f"Inserted: {inserted_count}"
    )

    print(
        f"Updated: {updated_count}"
    )

    print(
        f"Total standards: {len(standards_data)}"
    )


except Exception as error:

    db.rollback()

    print(
        f"ERROR: {error}"
    )

    raise


finally:
    db.close()