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
# TIMESTAMP PARSER
# =========================================================

def parse_timestamp(timestamp_value):
    if isinstance(
        timestamp_value,
        datetime,
    ):
        return timestamp_value

    return datetime.fromisoformat(
        timestamp_value
    )


# =========================================================
# SAVE COMPLETE ANALYSIS TO POSTGRESQL
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
            filename=response_data[
                "filename"
            ],

            file_size=file_size,

            characters_extracted=(
                response_data.get(
                    "characters_extracted"
                )
            ),

            ocr_required=(
                response_data.get(
                    "ocr_required",
                    False,
                )
            ),
        )

        db.add(document)

        db.flush()


        # =================================================
        # ANALYSIS
        # =================================================

        analysis = Analysis(
            analysis_id=response_data[
                "analysis_id"
            ],

            document_id=document.id,

            analysis_timestamp=(
                parse_timestamp(
                    response_data[
                        "analysis_timestamp"
                    ]
                )
            ),

            matcher_version=(
                response_data.get(
                    "matcher_version"
                )
            ),

            document_status=(
                response_data.get(
                    "document_status"
                )
            ),

            review_risk_score=(
                response_data.get(
                    "review_risk_score"
                )
            ),

            review_risk_level=(
                response_data.get(
                    "review_risk_level"
                )
            ),

            analysis_completion_percentage=(
                response_data.get(
                    "analysis_completion_percentage"
                )
            ),

            document_review_reasons=(
                response_data.get(
                    "document_review_reasons"
                )
            ),

            top_priority_issues=(
                response_data.get(
                    "top_priority_issues"
                )
            ),

            summary=(
                response_data.get(
                    "summary"
                )
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

            requirement_data = (
                result["requirement"]
            )


            requirement = Requirement(
                analysis_db_id=analysis.id,

                requirement_code=(
                    requirement_data[
                        "id"
                    ]
                ),

                requirement_name=(
                    requirement_data[
                        "requirement"
                    ]
                ),

                value=(
                    requirement_data.get(
                        "value"
                    )
                ),

                notes=(
                    requirement_data.get(
                        "notes"
                    )
                ),

                requirement_type=(
                    requirement_data.get(
                        "type"
                    )
                ),

                status=(
                    requirement_data.get(
                        "status"
                    )
                ),

                decision=(
                    result.get(
                        "decision"
                    )
                ),

                decision_reason=(
                    result.get(
                        "decision_reason"
                    )
                ),

                review_flags=(
                    result.get(
                        "review_flags"
                    )
                ),

                recommended_action=(
                    result.get(
                        "recommended_action"
                    )
                ),

                review_priority=(
                    result.get(
                        "review_priority"
                    )
                ),
            )

            db.add(requirement)

            db.flush()


            # =============================================
            # BEST MATCH IDENTIFICATION
            # =============================================

            best_match = (
                result.get(
                    "best_match"
                )
            )


            best_traceability_id = None


            if best_match:

                best_traceability_id = (
                    best_match.get(
                        "traceability_id"
                    )
                )


            # =============================================
            # STANDARD MATCHES
            # =============================================

            for match_data in result.get(
                "all_matches",
                [],
            ):

                matched_keywords = (
                    match_data.get(
                        "matched_keywords"
                    )
                )


                # Fallback:
                # some older result formats stored
                # matched_keywords inside evidence.

                if matched_keywords is None:

                    matched_keywords = (
                        match_data.get(
                            "evidence",
                            {},
                        ).get(
                            "matched_keywords",
                            [],
                        )
                    )


                standard_match = (
                    StandardMatch(

                        requirement_id=(
                            requirement.id
                        ),

                        traceability_id=(
                            match_data.get(
                                "traceability_id"
                            )
                        ),

                        standard_id=(
                            match_data.get(
                                "standard_id"
                            )
                        ),

                        standard_number=(
                            match_data.get(
                                "standard_number"
                            )
                        ),

                        title=(
                            match_data.get(
                                "title"
                            )
                        ),

                        # Legacy keyword matcher field
                        match_score=(
                            match_data.get(
                                "match_score"
                            )
                        ),

                        # Hybrid confidence
                        confidence=(
                            match_data.get(
                                "confidence"
                            )
                        ),

                        confidence_level=(
                            match_data.get(
                                "confidence_level"
                            )
                        ),

                        evidence_strength=(
                            match_data.get(
                                "evidence_strength"
                            )
                        ),

                        verified=(
                            match_data.get(
                                "verified",
                                False,
                            )
                        ),

                        needs_human_review=(
                            match_data.get(
                                "needs_human_review",
                                True,
                            )
                        ),

                        source_verification_status=(
                            match_data.get(
                                "source_verification_status"
                            )
                        ),

                        source_name=(
                            match_data.get(
                                "source_name"
                            )
                        ),

                        source_url=(
                            match_data.get(
                                "source_url"
                            )
                        ),

                        evidence_type=(
                            match_data.get(
                                "evidence_type"
                            )
                        ),

                        match_method=(
                            match_data.get(
                                "match_method"
                            )
                        ),

                        evidence=(
                            match_data.get(
                                "evidence"
                            )
                        ),

                        # =================================
                        # HYBRID AI FIELDS
                        # =================================

                        keyword_score=(
                            match_data.get(
                                "keyword_score"
                            )
                        ),

                        semantic_score=(
                            match_data.get(
                                "semantic_score"
                            )
                        ),

                        hybrid_score=(
                            match_data.get(
                                "hybrid_score"
                            )
                        ),

                        model_name=(
                            match_data.get(
                                "model_name"
                            )
                        ),

                        matched_keywords=(
                            matched_keywords
                        ),

                        # =================================
                        # BEST MATCH FLAG
                        # =================================

                        is_best_match=(
                            match_data.get(
                                "traceability_id"
                            )
                            ==
                            best_traceability_id
                        ),
                    )
                )

                db.add(
                    standard_match
                )


        # =================================================
        # COMMIT
        # =================================================

        db.commit()


        return {
            "saved": True,

            "document_id": (
                document.id
            ),

            "analysis_db_id": (
                analysis.id
            ),
        }


    except Exception:

        db.rollback()

        raise


    finally:

        db.close()


# =========================================================
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

            reports.append(
                {
                    "analysis_id": (
                        analysis.analysis_id
                    ),

                    "filename": (
                        analysis.document.filename
                    ),

                    "analysis_timestamp": (
                        analysis.analysis_timestamp.isoformat()
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
                }
            )


        return {
            "count": len(
                reports
            ),

            "reports": (
                reports
            ),
        }


    finally:

        db.close()


# =========================================================
# SERIALIZE STANDARD MATCH
# =========================================================

def serialize_match(
    match,
):

    return {

        "traceability_id": (
            match.traceability_id
        ),

        "standard_id": (
            match.standard_id
        ),

        "standard_number": (
            match.standard_number
        ),

        "title": (
            match.title
        ),

        # Legacy matcher
        "match_score": (
            match.match_score
        ),

        # =============================================
        # HYBRID AI SCORES
        # =============================================

        "keyword_score": (
            match.keyword_score
        ),

        "semantic_score": (
            match.semantic_score
        ),

        "hybrid_score": (
            match.hybrid_score
        ),

        "confidence": (
            match.confidence
        ),

        "confidence_level": (
            match.confidence_level
        ),

        "evidence_strength": (
            match.evidence_strength
        ),

        "matched_keywords": (
            match.matched_keywords
            if match.matched_keywords
            else []
        ),

        "verified": (
            match.verified
        ),

        "needs_human_review": (
            match.needs_human_review
        ),

        "source_verification_status": (
            match.source_verification_status
        ),

        "source_name": (
            match.source_name
        ),

        "source_url": (
            match.source_url
        ),

        "evidence_type": (
            match.evidence_type
        ),

        "match_method": (
            match.match_method
        ),

        "model_name": (
            match.model_name
        ),

        "evidence": (
            match.evidence
        ),

        "is_best_match": (
            match.is_best_match
        ),
    }


# =========================================================
# GET ONE COMPLETE REPORT
# =========================================================

def get_report_from_database(
    analysis_id,
):

    db = SessionLocal()

    try:

        analysis = (
            db.query(Analysis)
            .filter(
                Analysis.analysis_id
                == analysis_id
            )
            .first()
        )


        if analysis is None:
            return None


        results = []


        for requirement in (
            analysis.requirements
        ):

            all_matches = [
                serialize_match(
                    match
                )
                for match
                in requirement.matches
            ]


            # Highest score first
            all_matches.sort(
                key=lambda item: (
                    item.get(
                        "hybrid_score"
                    )
                    or
                    item.get(
                        "confidence"
                    )
                    or 0
                ),
                reverse=True,
            )


            best_match = None


            for match in (
                requirement.matches
            ):

                if match.is_best_match:

                    best_match = (
                        serialize_match(
                            match
                        )
                    )

                    break


            match_method = (
                analysis.matcher_version
            )


            if best_match:

                match_method = (
                    best_match.get(
                        "match_method"
                    )
                    or
                    analysis.matcher_version
                )


            elif all_matches:

                match_method = (
                    all_matches[
                        0
                    ].get(
                        "match_method"
                    )
                    or
                    analysis.matcher_version
                )


            results.append(
                {

                    "requirement": {

                        "id": (
                            requirement.requirement_code
                        ),

                        "requirement": (
                            requirement.requirement_name
                        ),

                        "value": (
                            requirement.value
                        ),

                        "notes": (
                            requirement.notes
                        ),

                        "type": (
                            requirement.requirement_type
                        ),

                        "status": (
                            requirement.status
                        ),
                    },


                    "decision": (
                        requirement.decision
                    ),

                    "decision_reason": (
                        requirement.decision_reason
                    ),

                    "review_flags": (
                        requirement.review_flags
                    ),

                    "recommended_action": (
                        requirement.recommended_action
                    ),

                    "review_priority": (
                        requirement.review_priority
                    ),

                    "best_match": (
                        best_match
                    ),

                    "all_matches": (
                        all_matches
                    ),

                    "match_method": (
                        match_method
                    ),
                }
            )


        # =================================================
        # SORT REQUIREMENTS BY PRIORITY
        # =================================================

        priority_order = {
            "HIGH": 1,
            "MEDIUM": 2,
            "LOW": 3,
        }


        results.sort(
            key=lambda item: (
                priority_order.get(
                    item[
                        "review_priority"
                    ],
                    4,
                )
            )
        )


        # =================================================
        # FINAL DATABASE REPORT
        # =================================================

        return {

            "filename": (
                analysis.document.filename
            ),

            "status": (
                "PDF processed successfully"
            ),

            "characters_extracted": (
                analysis.document.characters_extracted
            ),

            "ocr_required": (
                analysis.document.ocr_required
            ),

            "analysis_id": (
                analysis.analysis_id
            ),

            "analysis_timestamp": (
                analysis.analysis_timestamp.isoformat()
            ),

            "matcher_version": (
                analysis.matcher_version
            ),

            "matching_engine": (
                "Hybrid Keyword + Semantic AI"
                if analysis.matcher_version
                == "HYBRID_KEYWORD_SEMANTIC_V1"
                else "Legacy Matching Engine"
            ),

            "document_status": (
                analysis.document_status
            ),

            "review_risk_score": (
                analysis.review_risk_score
            ),

            "review_risk_level": (
                analysis.review_risk_level
            ),

            "document_review_reasons": (
                analysis.document_review_reasons
            ),

            "top_priority_issues": (
                analysis.top_priority_issues
            ),

            "analysis_completion_percentage": (
                analysis.analysis_completion_percentage
            ),

            "summary": (
                analysis.summary
            ),

            "results": (
                results
            ),

            "database": {

                "saved": True,

                "document_id": (
                    analysis.document_id
                ),

                "analysis_db_id": (
                    analysis.id
                ),
            },
        }


    finally:

        db.close()


# =========================================================
# DELETE REPORT
# =========================================================

def delete_report_from_database(
    analysis_id,
):

    db = SessionLocal()

    try:

        analysis = (
            db.query(Analysis)
            .filter(
                Analysis.analysis_id
                == analysis_id
            )
            .first()
        )


        if analysis is None:
            return False


        document_id = (
            analysis.document_id
        )


        analysis_count = (
            db.query(
                func.count(
                    Analysis.id
                )
            )
            .filter(
                Analysis.document_id
                == document_id
            )
            .scalar()
        )


        # Current PROCURAI workflow creates
        # one document per uploaded analysis.
        # If this is the only analysis,
        # deleting Document cascades everything.

        if analysis_count == 1:

            document = (
                db.query(Document)
                .filter(
                    Document.id
                    == document_id
                )
                .first()
            )

            if document:

                db.delete(
                    document
                )


        else:

            db.delete(
                analysis
            )


        db.commit()

        return True


    except Exception:

        db.rollback()

        raise


    finally:

        db.close()