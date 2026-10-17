from sqlalchemy import text

from app.database import engine


STATEMENTS = [
    """
    ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS ocr_used BOOLEAN NOT NULL DEFAULT FALSE
    """,
    """
    ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS ocr_pages JSON
    """,
    """
    ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS native_text_pages JSON
    """,
    """
    ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS total_pages INTEGER
    """,
    """
    ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS ocr_confidence DOUBLE PRECISION
    """,
    """
    ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS low_confidence_pages JSON
    """,
    """
    ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS ocr_metadata JSON
    """,
    """
    UPDATE documents
    SET ocr_used = ocr_required
    WHERE ocr_required = TRUE
      AND ocr_used = FALSE
    """,
]


with engine.begin() as connection:
    for statement in STATEMENTS:
        connection.execute(text(statement))


print("OCR metadata migration completed successfully.")
