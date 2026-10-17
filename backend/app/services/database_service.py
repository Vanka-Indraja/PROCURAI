from datetime import datetime

from sqlalchemy import func

from app.database import SessionLocal
from app.models import (
    Analysis,
    Document,
    Requirement,
    StandardMatch,
)


# =========================================================
# HELPERS
# =========================================================

def parse_timestamp(timestamp_value):
    if isinstance(timestamp_value, datetime):
        return timestamp_value

    if timestamp_value is None:
        return None

    if isinstance(timestamp_value, str):
        timestamp_value = timestamp_value.replace(
            "Z",
            "+00:00",
        )

    return datetime.fromisoformat(timestamp_value)


def build_ocr_metadata(response_data):
    return {
        "ocr_quality_status": response_data.get(
            "ocr_quality_status"
        ),
        "ocr_review_required": response_data.get(
            "ocr_review_required",
            False,
        ),
        "ocr_page_details": response_data.get(
            "ocr_page_details",
            [],
        ),
        "ocr_warnings": response_data.get(
            "ocr_warnings",
            [],
        ),
        "extraction_mode": response_data.get(
            "extraction_mode"
        ),
        "ocr_engine": response_data.get(
            "ocr_engine"
        ),
    }


# =========================================================
# SAVE COMPLETE ANALYSIS
# =========================================================

def save_analysis_to_database(
    response_data,
    file_size,
):
    db = SessionLocal()

    try:
        # =================================================
        # DOCUMENT
        # =================================================

        document = Document(
            filename=response_data["filename"],
            file_size=file_size,
            characters_extracted=response_data.get(
                "characters_extracted"
            ),
            ocr_required=response_data.get(
                "ocr_required",
                False,
            ),
            ocr_used=response_data.get(
                "ocr_used",
                False,
            ),
            ocr_pages=response_data.get(
                "ocr_pages",
                [],
            ),
            native_text_pages=response_data.get(
                "native_text_pages",
                [],
            ),
            total_pages=response_data.get(
                "total_pages"
            ),
            ocr_confidence=response_data.get(
                "ocr_confidence"
            ),
            low_confidence_pages=response_data.get(
                "low_confidence_pages",
                [],
            ),
            ocr_metadata=build_ocr_metadata(
                response_data
            ),
        )

        db.add(document)
        db.flush()

        # =================================================
        # ANALYSIS
        # =================================================

        analysis = Analysis(
            analysis_id=response_data["analysis_id"],
            document_id=document.id,
            analysis_timestamp=parse_timestamp(
                response_data["analysis_timestamp"]
            ),
            matcher_version=response_data.get(
                "matcher_version"
            ),
            document_status=response_data.get(
                "document_status"
            ),
            review_risk_score=response_data.get(
                "review_risk_score"
            ),
            review_risk_level=response_data.get(
                "review_risk_level"
            ),
            analysis_completion_percentage=(
                response_data.get(
                    "analysis_completion_percentage"
                )
            ),
            document_review_reasons=response_data.get(
                "document_review_reasons"
            ),
            top_priority_issues=response_data.get(
                "top_priority_issues"
            ),
            summary=response_data.get(
                "summary"
            ),
        )

        db.add(analysis)
        db.flush()

        # =================================================
        # REQUIREMENTS
        # =================================================

        for result in response_data.get(
            "results",
            [],
        ):
            requirement_data = result.get(
                "requirement",
                {},
            )

            requirement = Requirement(
                analysis_db_id=analysis.id,
                requirement_code=requirement_data.get(
                    "id"
                ),
                requirement_name=requirement_data.get(
                    "requirement"
                ),
                value=requirement_data.get(
                    "value"
                ),
                notes=requirement_data.get(
                    "notes"
                ),
                requirement_type=requirement_data.get(
                    "type"
                ),
                status=requirement_data.get(
                    "status"
                ),
                category=requirement_data.get(
                    "category"
                ),
                source_text=requirement_data.get(
                    "source_text"
                ),
                decision=result.get(
                    "decision"
                ),
                decision_reason=result.get(
                    "decision_reason"
                ),
                review_flags=result.get(
                    "review_flags",
                    [],
                ),
                recommended_action=result.get(
                    "recommended_action"
                ),
                review_priority=result.get(
                    "review_priority"
                ),
            )

            db.add(requirement)
            db.flush()

            # =============================================
            # STANDARD MATCHES
            # =============================================

            best_match = (
                result.get("best_match")
                or {}
            )

            best_traceability_id = (
                best_match.get(
                    "traceability_id"
                )
            )

            for match_data in result.get(
                "all_matches",
                [],
            ):
                matched_keywords = (
                    match_data.get(
                        "matched_keywords"
                    )
                )

                if matched_keywords is None:
                    evidence_data = (
                        match_data.get(
                            "evidence"
                        )
                        or {}
                    )

                    matched_keywords = (
                        evidence_data.get(
                            "matched_keywords",
                            [],
                        )
                    )

                standard_match = StandardMatch(
                    requirement_id=requirement.id,

                    traceability_id=match_data.get(
                        "traceability_id"
                    ),

                    standard_id=match_data.get(
                        "standard_id"
                    ),

                    standard_number=match_data.get(
                        "standard_number"
                    ),

                    title=match_data.get(
                        "title"
                    ),

                    match_score=match_data.get(
                        "match_score"
                    ),

                    confidence=match_data.get(
                        "confidence"
                    ),

                    confidence_level=match_data.get(
                        "confidence_level"
                    ),

                    evidence_strength=match_data.get(
                        "evidence_strength"
                    ),

                    verified=match_data.get(
                        "verified",
                        False,
                    ),

                    needs_human_review=match_data.get(
                        "needs_human_review",
                        True,
                    ),

                    source_verification_status=(
                        match_data.get(
                            "source_verification_status"
                        )
                    ),

                    source_name=match_data.get(
                        "source_name"
                    ),

                    source_url=match_data.get(
                        "source_url"
                    ),

                    evidence_type=match_data.get(
                        "evidence_type"
                    ),

                    match_method=match_data.get(
                        "match_method"
                    ),

                    evidence=match_data.get(
                        "evidence"
                    ),

                    keyword_score=match_data.get(
                        "keyword_score"
                    ),

                    semantic_score=match_data.get(
                        "semantic_score"
                    ),

                    hybrid_score=match_data.get(
                        "hybrid_score"
                    ),

                    model_name=match_data.get(
                        "model_name"
                    ),

                    matched_keywords=(
                        matched_keywords
                    ),

                    is_best_match=(
                        match_data.get(
                            "traceability_id"
                        )
                        == best_traceability_id
                    ),
                )

                # CRITICAL:
                # Add every standard match to DB session.
                db.add(standard_match)

        # =================================================
        # PERMANENT DATABASE SAVE
        # =================================================

        # CRITICAL:
        # flush() alone is not permanent.
        # commit() permanently saves the complete transaction.
        db.commit()

        return {
            "saved": True,
            "document_id": document.id,
            "analysis_db_id": analysis.id,
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

# ======================================opened ===================
# LIST REPORTS
# =========================================================

def list_reports_from_database():
    db = SessionLocal()

    try:
        analyses = (
            db.query(Analysis)
            .order_by(
                Analysis.analysis_timestamp.desc()
            )
            .all()
        )

        reports = []

        for analysis in analyses:
            document = analysis.document

            reports.append(
                {
                    "analysis_id": analysis.analysis_id,
                    "filename": (
                        document.filename
                        if document
                        else None
                    ),
                    "analysis_timestamp": (
                        analysis.analysis_timestamp.isoformat()
                        if analysis.analysis_timestamp
                        else None
                    ),
                    "matcher_version": (
                        analysis.matcher_version
                    ),
                    "document_status": (
                        analysis.document_status
                    ),
                    "review_risk_level": (
                        analysis.review_risk_level
                    ),
                    "ocr_used": (
                        document.ocr_used
                        if document
                        else False
                    ),
                    "ocr_confidence": (
                        document.ocr_confidence
                        if document
                        else None
                    ),
                    "total_pages": (
                        document.total_pages
                        if document
                        else None
                    ),
                }
            )

        return {
            "count": len(reports),
            "reports": reports,
        }

    finally:
        db.close()





# =========================================================
# MATCH SERIALIZATION
# =========================================================

def serialize_match(match):
    return {
        "traceability_id": match.traceability_id,
        "standard_id": match.standard_id,
        "standard_number": match.standard_number,
        "title": match.title,
        "match_score": match.match_score,
        "keyword_score": match.keyword_score,
        "semantic_score": match.semantic_score,
        "hybrid_score": match.hybrid_score,
        "confidence": match.confidence,
        "confidence_level": match.confidence_level,
        "evidence_strength": match.evidence_strength,
        "matched_keywords": (
            match.matched_keywords
            if match.matched_keywords
            else []
        ),
        "verified": match.verified,
        "needs_human_review": (
            match.needs_human_review
        ),
        "source_verification_status": (
            match.source_verification_status
        ),
        "source_name": match.source_name,
        "source_url": match.source_url,
        "evidence_type": match.evidence_type,
        "match_method": match.match_method,
        "model_name": match.model_name,
        "evidence": match.evidence,
        "is_best_match": match.is_best_match,
    }


def get_match_sort_score(match_data):
    if match_data.get("hybrid_score") is not None:
        return match_data["hybrid_score"]

    if match_data.get("confidence") is not None:
        return match_data["confidence"]

    if match_data.get("match_score") is not None:
        return match_data["match_score"]

    return 0


# =========================================================
# GET COMPLETE REPORT
# =========================================================

def get_report_from_database(analysis_id):
    db = SessionLocal()

    try:
        analysis = (
            db.query(Analysis)
            .filter(
                Analysis.analysis_id == analysis_id
            )
            .first()
        )

        if analysis is None:
            return None

        results = []

        for requirement in analysis.requirements:
            all_matches = [
                serialize_match(match)
                for match in requirement.matches
            ]

            all_matches.sort(
                key=get_match_sort_score,
                reverse=True,
            )

            best_match = None

            for match in requirement.matches:
                if match.is_best_match:
                    best_match = serialize_match(match)
                    break

            match_method = analysis.matcher_version

            if best_match:
                match_method = (
                    best_match.get("match_method")
                    or analysis.matcher_version
                )
            elif all_matches:
                match_method = (
                    all_matches[0].get("match_method")
                    or analysis.matcher_version
                )

            results.append(
                {
                    "requirement": {
                        "id": requirement.requirement_code,
                        "requirement": (
                            requirement.requirement_name
                        ),
                        "value": requirement.value,
                        "notes": requirement.notes,
                        "type": (
                            requirement.requirement_type
                        ),
                        "status": requirement.status,
                        "category": requirement.category,
                        "source_text": (
                            requirement.source_text
                        ),
                    },
                    "decision": requirement.decision,
                    "decision_reason": (
                        requirement.decision_reason
                    ),
                    "review_flags": (
                        requirement.review_flags
                        if requirement.review_flags
                        else []
                    ),
                    "recommended_action": (
                        requirement.recommended_action
                    ),
                    "review_priority": (
                        requirement.review_priority
                    ),
                    "best_match": best_match,
                    "all_matches": all_matches,
                    "match_method": match_method,
                }
            )

        priority_order = {
            "HIGH": 1,
            "MEDIUM": 2,
            "LOW": 3,
        }

        results.sort(
            key=lambda item: priority_order.get(
                item.get("review_priority"),
                4,
            )
        )

        matching_engine = (
            "Hybrid Keyword + Semantic AI"
            if analysis.matcher_version
            == "HYBRID_KEYWORD_SEMANTIC_V1"
            else "Legacy Matching Engine"
        )

        document = analysis.document
        metadata = (
            document.ocr_metadata
            if document and document.ocr_metadata
            else {}
        )

        return{
            "filename": (
                document.filename
                if document
                else None
            ),
            "status": "PDF processed successfully",
            "characters_extracted": (
                document.characters_extracted
                if document
                else None
            ),
            "ocr_required": (
                document.ocr_required
                if document
                else False
            ),
            "ocr_used": (
                document.ocr_used
                if document
                else False
            ),
            "ocr_pages": (
                document.ocr_pages
                if document and document.ocr_pages
                else []
            ),
            "native_text_pages": (
                document.native_text_pages
                if document and document.native_text_pages
                else []
            ),
            "total_pages": (
                document.total_pages
                if document
                else None
            ),
            "ocr_confidence": (
                document.ocr_confidence
                if document
                else None
            ),
            "low_confidence_pages": (
                document.low_confidence_pages
                if document and document.low_confidence_pages
                else []
            ),
            "ocr_quality_status": metadata.get(
                "ocr_quality_status"
            ),
            "ocr_review_required": metadata.get(
                "ocr_review_required",
                False,
            ),
            "ocr_page_details": metadata.get(
                "ocr_page_details",
                [],
            ),
            "ocr_warnings": metadata.get(
                "ocr_warnings",
                [],
            ),
            "extraction_mode": metadata.get(
                "extraction_mode"
            ),
            "ocr_engine": metadata.get(
                "ocr_engine"
            ),
            "analysis_id": analysis.analysis_id,
            "analysis_timestamp": (
                analysis.analysis_timestamp.isoformat()
                if analysis.analysis_timestamp
                else None
            ),
            "matcher_version": analysis.matcher_version,
            "matching_engine": matching_engine,
            "document_status": analysis.document_status,
            "review_risk_score": (
                analysis.review_risk_score
            ),
            "review_risk_level": (
                analysis.review_risk_level
            ),
            "document_review_reasons": (
                analysis.document_review_reasons
                if analysis.document_review_reasons
                else []
            ),
             "top_priority_issues": (
                analysis.top_priority_issues
                if analysis.top_priority_issues
                else []
            ),
            "analysis_completion_percentage": (
                analysis.analysis_completion_percentage
            ),
            "summary": (
                analysis.summary
                if analysis.summary
                else {}
            ),
            "results": results,
            "database": {
                "saved": True,
                "document_id": analysis.document_id,
                "analysis_db_id": analysis.id,
            },
        }

    finally:
        db.close()


# =========================================================
# DELETE REPORT
# =========================================================

def delete_report_from_database(analysis_id):
    db = SessionLocal()

    try:
        analysis = (
            db.query(Analysis)
            .filter(
                Analysis.analysis_id == analysis_id
            )
            .first()
        )

        if analysis is None:
            return False

        document_id = analysis.document_id

        analysis_count = (
            db.query(func.count(Analysis.id))
            .filter(
                Analysis.document_id == document_id
            )
            .scalar()
        )

        db.delete(analysis)
        db.flush()

        if analysis_count <= 1:
            document = (
                db.query(Document)
                .filter(Document.id == document_id)
                .first()
            )

            if document is not None:
                db.delete(document)

        db.commit()
        return True

    except Exception:
        db.rollback()
        raise
