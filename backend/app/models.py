from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)

from sqlalchemy.orm import relationship

from app.database import Base


# =========================================================
# DOCUMENT
# =========================================================

class Document(Base):
    __tablename__ = "documents"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    filename = Column(
        String(255),
        nullable=False,
    )

    file_size = Column(
        Integer,
        nullable=False,
    )

    characters_extracted = Column(
        Integer,
        nullable=True,
    )

    ocr_required = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    uploaded_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    analyses = relationship(
        "Analysis",
        back_populates="document",
        cascade="all, delete-orphan",
    )


# =========================================================
# ANALYSIS
# =========================================================

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    analysis_id = Column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    document_id = Column(
        Integer,
        ForeignKey(
            "documents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    analysis_timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    matcher_version = Column(
        String(100),
        nullable=True,
    )

    document_status = Column(
        String(100),
        nullable=True,
    )

    review_risk_score = Column(
        Float,
        nullable=True,
    )

    review_risk_level = Column(
        String(50),
        nullable=True,
    )

    analysis_completion_percentage = Column(
        Float,
        nullable=True,
    )

    document_review_reasons = Column(
        JSON,
        nullable=True,
    )

    top_priority_issues = Column(
        JSON,
        nullable=True,
    )

    summary = Column(
        JSON,
        nullable=True,
    )

    document = relationship(
        "Document",
        back_populates="analyses",
    )

    requirements = relationship(
        "Requirement",
        back_populates="analysis",
        cascade="all, delete-orphan",
    )


# =========================================================
# REQUIREMENT
# =========================================================

class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    analysis_db_id = Column(
        Integer,
        ForeignKey(
            "analyses.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    requirement_code = Column(
        String(50),
        nullable=False,
    )

    requirement_name = Column(
        String(255),
        nullable=False,
    )

    value = Column(
        Text,
        nullable=True,
    )

    notes = Column(
        Text,
        nullable=True,
    )

    requirement_type = Column(
        String(100),
        nullable=True,
    )

    status = Column(
        String(100),
        nullable=True,
    )

    # =====================================================
    # GENERALIZED EXTRACTION FIELDS
    # =====================================================

    category = Column(
        String(100),
        nullable=True,
    )

    source_text = Column(
        Text,
        nullable=True,
    )

    # =====================================================
    # REVIEW / DECISION FIELDS
    # =====================================================

    decision = Column(
        String(100),
        nullable=True,
    )

    decision_reason = Column(
        Text,
        nullable=True,
    )

    review_flags = Column(
        JSON,
        nullable=True,
    )

    recommended_action = Column(
        Text,
        nullable=True,
    )

    review_priority = Column(
        String(50),
        nullable=True,
    )

    analysis = relationship(
        "Analysis",
        back_populates="requirements",
    )

    matches = relationship(
        "StandardMatch",
        back_populates="requirement",
        cascade="all, delete-orphan",
    )


# =========================================================
# STANDARD MATCH
# =========================================================

class StandardMatch(Base):
    __tablename__ = "standard_matches"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    requirement_id = Column(
        Integer,
        ForeignKey(
            "requirements.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    traceability_id = Column(
        String(100),
        nullable=True,
    )

    standard_id = Column(
        String(100),
        nullable=True,
    )

    standard_number = Column(
        String(100),
        nullable=True,
    )

    title = Column(
        String(500),
        nullable=True,
    )

    match_score = Column(
        Float,
        nullable=True,
    )

    confidence = Column(
        Float,
        nullable=True,
    )

    confidence_level = Column(
        String(50),
        nullable=True,
    )

    evidence_strength = Column(
        String(50),
        nullable=True,
    )

    verified = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    needs_human_review = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    source_verification_status = Column(
        String(100),
        nullable=True,
    )

    source_name = Column(
        String(255),
        nullable=True,
    )

    source_url = Column(
        Text,
        nullable=True,
    )

    evidence_type = Column(
        String(100),
        nullable=True,
    )

    match_method = Column(
        String(100),
        nullable=True,
    )

    evidence = Column(
        JSON,
        nullable=True,
    )

    is_best_match = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    # =====================================================
    # HYBRID AI FIELDS
    # =====================================================

    keyword_score = Column(
        Float,
        nullable=True,
    )

    semantic_score = Column(
        Float,
        nullable=True,
    )

    hybrid_score = Column(
        Float,
        nullable=True,
    )

    model_name = Column(
        String(255),
        nullable=True,
    )

    matched_keywords = Column(
        JSON,
        nullable=True,
    )

    requirement = relationship(
        "Requirement",
        back_populates="matches",
    )


# =========================================================
# STANDARD MASTER TABLE
# =========================================================

class Standard(Base):
    __tablename__ = "standards"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    standard_id = Column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    standard_number = Column(
        String(150),
        unique=True,
        index=True,
        nullable=False,
    )

    title = Column(
        String(500),
        nullable=False,
    )

    keywords = Column(
        JSON,
        nullable=False,
        default=list,
    )

    verified = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    source_name = Column(
        String(255),
        nullable=True,
    )

    source_url = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )