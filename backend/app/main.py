from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
)

import os
import shutil
import uuid
import json

from datetime import datetime, timezone


# =========================================================
# SERVICES
# =========================================================

from app.services.pdf_service import (
    extract_pdf_text,
)

from app.services.requirement_service import (
    extract_requirements,
)

from app.services.standards_service import (
    load_standards,
)

from app.services.hybrid_matching_service import (
    hybrid_match_requirement,
)

from app.services.database_service import (
    save_analysis_to_database,
    list_reports_from_database,
    get_report_from_database,
    delete_report_from_database,
)


# =========================================================
# MATCHER VERSION
# =========================================================

MATCHER_VERSION = (
    "HYBRID_KEYWORD_SEMANTIC_V1"
)


# =========================================================
# DOCUMENT STATUS
# =========================================================

def get_document_status(
    match_found_count,
    human_review_count,
    no_match_count,
    needs_clarification_count,
):
    if no_match_count > 0:
        return "INCOMPLETE_MATCHING"

    if (
        human_review_count > 0
        or needs_clarification_count > 0
    ):
        return "REVIEW_REQUIRED"

    if match_found_count > 0:
        return "READY"

    return "REVIEW_REQUIRED"


# =========================================================
# REVIEW RISK SCORE
# =========================================================

def calculate_review_risk(
    total_requirements,
    human_review_count,
    no_match_count,
    needs_clarification_count,
):
    if total_requirements == 0:
        return 0

    risk_points = (
        human_review_count * 2
        + no_match_count * 3
        + needs_clarification_count * 2
    )

    max_points = (
        total_requirements * 7
    )

    risk_score = round(
        (
            risk_points
            / max_points
        )
        * 100,
        2,
    )

    return min(
        risk_score,
        100,
    )


# =========================================================
# REVIEW RISK LEVEL
# =========================================================

def get_review_risk_level(
    review_risk_score,
):
    if review_risk_score >= 60:
        return "HIGH"

    if review_risk_score >= 30:
        return "MEDIUM"

    return "LOW"


# =========================================================
# DOCUMENT REVIEW REASONS
# =========================================================

def get_document_review_reasons(
    human_review_count,
    no_match_count,
    needs_clarification_count,
):
    reasons = []

    if human_review_count > 0:
        reasons.append(
            f"{human_review_count} "
            f"requirement(s) need human review."
        )

    if no_match_count > 0:
        reasons.append(
            f"{no_match_count} "
            f"requirement(s) have no matching standard."
        )

    if needs_clarification_count > 0:
        reasons.append(
            f"{needs_clarification_count} "
            f"requirement(s) are vague or incomplete."
        )

    if not reasons:
        reasons.append(
            "No major review issues detected."
        )

    return reasons


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="PROCURAI",
    description=(
        "AI-Powered Procurement Specification Analysis "
        "and Indian Standards Recommendation System"
    ),
    version="0.4.0",
)


# =========================================================
# CONFIGURATION
# =========================================================

UPLOAD_FOLDER = "app/uploads"

REPORT_FOLDER = "app/reports"

MAX_FILE_SIZE = (
    10 * 1024 * 1024
)

MIN_TEXT_LENGTH = 50


os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True,
)

os.makedirs(
    REPORT_FOLDER,
    exist_ok=True,
)


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():
    return {
        "project": "PROCURAI",
        "status": "Backend is running",
        "database": "PostgreSQL",
        "matching_engine": (
            "Hybrid Keyword + Semantic AI"
        ),
        "matcher_version": (
            MATCHER_VERSION
        ),
    }


# =========================================================
# GET STANDARDS FROM POSTGRESQL
# =========================================================

@app.get("/standards")
def get_standards():
    standards = (
        load_standards()
    )

    return {
        "count": len(standards),
        "standards": standards,
    }


# =========================================================
# GET ALL REPORTS FROM POSTGRESQL
# =========================================================

@app.get("/reports")
def list_reports():
    return (
        list_reports_from_database()
    )


# =========================================================
# GET ONE REPORT FROM POSTGRESQL
# =========================================================

@app.get(
    "/reports/{analysis_id}"
)
def get_report(
    analysis_id: str,
):
    report = (
        get_report_from_database(
            analysis_id
        )
    )

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    return report


# =========================================================
# DELETE REPORT FROM POSTGRESQL
# =========================================================

@app.delete(
    "/reports/{analysis_id}"
)
def delete_report(
    analysis_id: str,
):
    deleted = (
        delete_report_from_database(
            analysis_id
        )
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    # ---------------------------------------------
    # DELETE LOCAL JSON BACKUP ALSO
    # ---------------------------------------------

    report_path = os.path.join(
        REPORT_FOLDER,
        f"{analysis_id}.json",
    )

    if os.path.exists(
        report_path
    ):
        os.remove(
            report_path
        )

    return {
        "status": (
            "Report deleted successfully"
        ),
        "analysis_id": (
            analysis_id
        ),
    }


# =========================================================
# PDF UPLOAD + AI ANALYSIS
# =========================================================

@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
):

    # =====================================================
    # 1. CHECK FILENAME
    # =====================================================

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is missing",
        )


    # =====================================================
    # 2. PDF EXTENSION CHECK
    # =====================================================

    if not file.filename.lower().endswith(
        ".pdf"
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Only PDF files are allowed"
            ),
        )


    # =====================================================
    # 3. SAFE FILENAME
    # =====================================================

    safe_filename = (
        os.path.basename(
            file.filename
        )
    )


    file_path = os.path.join(
        UPLOAD_FOLDER,
        safe_filename,
    )


    # =====================================================
    # 4. SAVE UPLOADED PDF
    # =====================================================

    with open(
        file_path,
        "wb",
    ) as buffer:

        shutil.copyfileobj(
            file.file,
            buffer,
        )


    # =====================================================
    # 5. FILE SIZE
    # =====================================================

    file_size = (
        os.path.getsize(
            file_path
        )
    )


    # =====================================================
    # 6. EMPTY FILE CHECK
    # =====================================================

    if file_size == 0:

        os.remove(
            file_path
        )

        raise HTTPException(
            status_code=400,
            detail=(
                "Uploaded PDF is empty"
            ),
        )


    # =====================================================
    # 7. FILE SIZE LIMIT
    # =====================================================

    if file_size > MAX_FILE_SIZE:

        os.remove(
            file_path
        )

        raise HTTPException(
            status_code=400,
            detail=(
                "PDF file size exceeds "
                "10 MB limit"
            ),
        )


    # =====================================================
    # 8. PDF SIGNATURE CHECK
    # =====================================================

    with open(
        file_path,
        "rb",
    ) as pdf_file:

        signature = (
            pdf_file.read(5)
        )


    if signature != b"%PDF-":

        os.remove(
            file_path
        )

        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file",
        )


    # =====================================================
    # 9. EXTRACT PDF TEXT
    # =====================================================

    extracted_text = (
        extract_pdf_text(
            file_path
        )
    )


    clean_text = (
        extracted_text.strip()
    )


    # =====================================================
    # 10. OCR REQUIRED CHECK
    # =====================================================

    if (
        len(clean_text)
        < MIN_TEXT_LENGTH
    ):

        return {
            "filename": (
                safe_filename
            ),

            "status": (
                "OCR_REQUIRED"
            ),

            "message": (
                "Very little or no selectable "
                "text was detected. "
                "This PDF may be scanned "
                "or image-based."
            ),

            "characters_extracted": (
                len(clean_text)
            ),

            "ocr_required": True,
        }


    # =====================================================
    # 11. REQUIREMENT EXTRACTION
    # =====================================================

    requirements = (
        extract_requirements(
            extracted_text
        )
    )


    # =====================================================
    # 12. NO REQUIREMENTS FOUND
    # =====================================================

    if len(requirements) == 0:

        return {
            "filename": (
                safe_filename
            ),

            "status": (
                "NO_REQUIREMENTS_DETECTED"
            ),

            "message": (
                "Text was extracted from "
                "the PDF, but no supported "
                "technical requirements "
                "were detected."
            ),

            "characters_extracted": (
                len(extracted_text)
            ),

            "ocr_required": False,

            "requirements_detected": 0,
        }


    # =====================================================
    # 13. LOAD STANDARDS FROM POSTGRESQL
    # =====================================================

    standards = (
        load_standards()
    )


    if len(standards) == 0:
        raise HTTPException(
            status_code=500,
            detail=(
                "No standards are available "
                "in the PostgreSQL database."
            ),
        )


    # =====================================================
    # 14. ANALYSIS METADATA
    # =====================================================

    analysis_timestamp = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )


    analysis_id = str(
        uuid.uuid4()
    )


    # =====================================================
    # 15. RESULT COUNTERS
    # =====================================================

    results = []

    match_found_count = 0

    human_review_count = 0

    no_match_count = 0

    needs_clarification_count = 0

    high_priority_count = 0

    medium_priority_count = 0

    low_priority_count = 0


    # =====================================================
    # 16. ANALYZE EACH REQUIREMENT USING HYBRID AI
    # =====================================================

    for requirement in requirements:

        match_result = (
            hybrid_match_requirement(
                requirement,
                standards,
            )
        )


        decision = (
            match_result[
                "decision"
            ]
        )


        # -------------------------------------------------
        # REQUIREMENT CLARIFICATION COUNT
        # -------------------------------------------------

        if (
            requirement.get(
                "status"
            )
            == "needs_clarification"
        ):
            needs_clarification_count += 1


        # -------------------------------------------------
        # DECISION COUNTS
        # -------------------------------------------------

        if (
            decision
            == "MATCH_FOUND"
        ):
            match_found_count += 1


        elif (
            decision
            == "HUMAN_REVIEW_REQUIRED"
        ):
            human_review_count += 1


        elif (
            decision
            == "NO_MATCH_FOUND"
        ):
            no_match_count += 1


        # -------------------------------------------------
        # REVIEW PRIORITY
        # -------------------------------------------------

        review_priority = (
            match_result[
                "review_priority"
            ]
        )


        if (
            review_priority
            == "HIGH"
        ):
            high_priority_count += 1


        elif (
            review_priority
            == "MEDIUM"
        ):
            medium_priority_count += 1


        elif (
            review_priority
            == "LOW"
        ):
            low_priority_count += 1


        # -------------------------------------------------
        # ADD RESULT
        # -------------------------------------------------

        results.append(
            {
                "requirement": (
                    requirement
                ),

                "decision": (
                    decision
                ),

                "decision_reason": (
                    match_result[
                        "decision_reason"
                    ]
                ),

                "review_flags": (
                    match_result[
                        "review_flags"
                    ]
                ),

                "recommended_action": (
                    match_result[
                        "recommended_action"
                    ]
                ),

                "review_priority": (
                    review_priority
                ),

                "best_match": (
                    match_result[
                        "best_match"
                    ]
                ),

                "all_matches": (
                    match_result[
                        "all_matches"
                    ]
                ),

                "match_method": (
                    match_result.get(
                        "match_method",
                        MATCHER_VERSION,
                    )
                ),
            }
        )


    # =====================================================
    # 17. SORT RESULTS BY REVIEW PRIORITY
    # =====================================================

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


    # =====================================================
    # 18. DOCUMENT STATUS
    # =====================================================

    document_status = (
        get_document_status(
            match_found_count,
            human_review_count,
            no_match_count,
            needs_clarification_count,
        )
    )


    # =====================================================
    # 19. REVIEW RISK SCORE
    # =====================================================

    review_risk_score = (
        calculate_review_risk(
            len(requirements),
            human_review_count,
            no_match_count,
            needs_clarification_count,
        )
    )


    review_risk_level = (
        get_review_risk_level(
            review_risk_score
        )
    )


    # =====================================================
    # 20. DOCUMENT REVIEW REASONS
    # =====================================================

    document_review_reasons = (
        get_document_review_reasons(
            human_review_count,
            no_match_count,
            needs_clarification_count,
        )
    )


    # =====================================================
    # 21. TOP PRIORITY ISSUES
    # =====================================================

    top_priority_issues = []


    for item in results:

        if (
            item[
                "review_priority"
            ]
            == "HIGH"
        ):

            top_priority_issues.append(
                {
                    "requirement_id": (
                        item[
                            "requirement"
                        ]["id"]
                    ),

                    "requirement": (
                        item[
                            "requirement"
                        ][
                            "requirement"
                        ]
                    ),

                    "reason": (
                        item[
                            "decision_reason"
                        ]
                    ),

                    "recommended_action": (
                        item[
                            "recommended_action"
                        ]
                    ),
                }
            )


    # =====================================================
    # 22. ANALYSIS COMPLETION
    # =====================================================

    analyzed_count = (
        match_found_count
        + human_review_count
        + no_match_count
    )


    analysis_completion_percentage = (
        round(
            (
                analyzed_count
                / len(requirements)
            )
            * 100,
            2,
        )
    )


    # =====================================================
    # 23. SUMMARY
    # =====================================================

    summary = {

        "total_requirements": (
            len(requirements)
        ),

        "match_found": (
            match_found_count
        ),

        "human_review_required": (
            human_review_count
        ),

        "no_match_found": (
            no_match_count
        ),

        "needs_clarification": (
            needs_clarification_count
        ),

        "high_priority": (
            high_priority_count
        ),

        "medium_priority": (
            medium_priority_count
        ),

        "low_priority": (
            low_priority_count
        ),
    }


    # =====================================================
    # 24. FINAL RESPONSE
    # =====================================================

    response_data = {

        "filename": (
            safe_filename
        ),

        "status": (
            "PDF processed successfully"
        ),

        "characters_extracted": (
            len(extracted_text)
        ),

        "ocr_required": False,

        "analysis_id": (
            analysis_id
        ),

        "analysis_timestamp": (
            analysis_timestamp
        ),

        "matcher_version": (
            MATCHER_VERSION
        ),

        "matching_engine": (
            "Hybrid Keyword + Semantic AI"
        ),

        "document_status": (
            document_status
        ),

        "review_risk_score": (
            review_risk_score
        ),

        "review_risk_level": (
            review_risk_level
        ),

        "document_review_reasons": (
            document_review_reasons
        ),

        "top_priority_issues": (
            top_priority_issues
        ),

        "analysis_completion_percentage": (
            analysis_completion_percentage
        ),

        "summary": (
            summary
        ),

        "results": (
            results
        ),
    }


    # =====================================================
    # 25. SAVE ANALYSIS TO POSTGRESQL
    # =====================================================

    database_result = (
        save_analysis_to_database(
            response_data,
            file_size,
        )
    )


    response_data[
        "database"
    ] = database_result


    # =====================================================
    # 26. SAVE LOCAL JSON BACKUP
    # =====================================================

    report_path = os.path.join(
        REPORT_FOLDER,
        f"{analysis_id}.json",
    )


    with open(
        report_path,
        "w",
        encoding="utf-8",
    ) as report_file:

        json.dump(
            response_data,
            report_file,
            indent=4,
            ensure_ascii=False,
        )


    # =====================================================
    # 27. RETURN RESPONSE
    # =====================================================

    return response_data