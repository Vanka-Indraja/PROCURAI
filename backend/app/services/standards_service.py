from app.database import SessionLocal
from app.models import Standard


def load_standards():
    db = SessionLocal()

    try:
        database_standards = (
            db.query(Standard)
            .order_by(Standard.id.asc())
            .all()
        )

        standards = []

        for standard in database_standards:
            standards.append(
                {
                    # Keep both keys for compatibility
                    "id": standard.standard_id,
                    "standard_id": standard.standard_id,

                    "standard_number": (
                        standard.standard_number
                    ),

                    "title": standard.title,

                    "keywords": (
                        standard.keywords
                        if standard.keywords
                        else []
                    ),

                    "verified": (
                        standard.verified
                    ),

                    "source_name": (
                        standard.source_name
                    ),

                    "source_url": (
                        standard.source_url
                    ),
                }
            )

        return standards

    finally:
        db.close()