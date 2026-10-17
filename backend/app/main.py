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
    extract_pdf_text_with_ocr,
    count_meaningful_characters,
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
# CONSTANTS
# =========================================================

MATCHER_VERSION = "HYBRID_KEYWORD_SEMANTIC_V1"

MIN_USABLE_TEXT_LENGTH = 50

MAX_FILE_SIZE = 10 * 1024 * 1024

UPLOAD_FOLDER = "app/uploads"

REPORT_FOLDER = "app/reports"


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="PROCURAI",
    description=(
        "AI-Powered Procurement Specification Analysis "
        "and Indian Standards Recommendation System"
    ),
    version="0.6.0",
)


os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True,
)

os.makedirs(
    REPORT_FOLDER,
    exist_ok=True,
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

        "pdf_processing": (
            "Native PDF text extraction "
            "+ automatic Tesseract OCR fallback"
        ),

        "ocr_engine": "Tesseract OCR",
    }


# =========================================================
# STANDARDS
# =========================================================

@app.get("/standards")
def get_standards():

    standards = load_standards()

    return {
        "count": len(standards),
        "standards": standards,
    }


# =========================================================
# REPORT LIST
# =========================================================

@app.get("/reports")
def list_reports():

    return (
        list_reports_from_database()
    )


# =========================================================
# GET REPORT
# =========================================================

@app.get("/reports/{analysis_id}")
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
# DELETE REPORT
# =========================================================

@app.delete("/reports/{analysis_id}")
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
# UPLOAD + ANALYSIS
# =========================================================

@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
):

    # =====================================================
    # 1. VALIDATE FILENAME
    # =====================================================

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Filename is missing",
        )


    # =====================================================
    # 2. VALIDATE EXTENSION
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


    # Avoid overwriting another upload
    stored_filename = (
        f"{uuid.uuid4()}_"
        f"{safe_filename}"
    )


    file_path = os.path.join(
        UPLOAD_FOLDER,
        stored_filename,
    )


    # =====================================================
    # 4. SAVE FILE
    # =====================================================

    try:

        with open(
            file_path,
            "wb",
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer,
            )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to save uploaded PDF: "
                f"{str(exc)}"
            ),
        )


    # =====================================================
    # 5. FILE SIZE
    # =====================================================

    file_size = (
        os.path.getsize(
            file_path
        )
    )


    if file_size == 0:

        if os.path.exists(
            file_path
        ):
            os.remove(
                file_path
            )

        raise HTTPException(
            status_code=400,
            detail=(
                "Uploaded PDF is empty"
            ),
        )


    if file_size > MAX_FILE_SIZE:

        if os.path.exists(
            file_path
        ):
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
    # 6. PDF SIGNATURE
    # =====================================================

    with open(
        file_path,
        "rb",
    ) as pdf_file:

        signature = (
            pdf_file.read(
                5
            )
        )


    if signature != b"%PDF-":

        if os.path.exists(
            file_path
        ):
            os.remove(
                file_path
            )

        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file",
        )


    # =====================================================
    # 7. SMART PDF EXTRACTION
    #
    # Native text pages:
    #   PyMuPDF
    #
    # Scanned pages:
    #   Tesseract OCR
    # =====================================================

    try:

        (
            extracted_text,
            extraction_info,
        ) = extract_pdf_text_with_ocr(
            file_path
        )

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unable to process PDF text/OCR: "
                f"{str(exc)}"
            ),
        )


    # =====================================================
    # 8. MEANINGFUL CHARACTER COUNT
    # =====================================================

    meaningful_character_count = (
        count_meaningful_characters(
            extracted_text
        )
    )


    ocr_used = (
        extraction_info.get(
            "ocr_used",
            False,
        )
    )


    ocr_pages = (
        extraction_info.get(
            "ocr_pages",
            [],
        )
    )


    native_text_pages = (
        extraction_info.get(
            "native_text_pages",
            [],
        )
    )


    total_pages = (
        extraction_info.get(
            "total_pages",
            0,
        )
    )


    # =====================================================
    # 9. STILL NO USABLE TEXT AFTER OCR
    # =====================================================

    if (
        meaningful_character_count
        <
        MIN_USABLE_TEXT_LENGTH
    ):

        return {
            "filename": (
                safe_filename
            ),

            "status": (
                "INSUFFICIENT_TEXT_AFTER_OCR"
            ),

            "message": (
                "The PDF contained too little "
                "usable text even after OCR processing."
            ),

            "characters_extracted": (
                meaningful_character_count
            ),

            "ocr_required": (
                ocr_used
            ),

            "ocr_used": (
                ocr_used
            ),

            "ocr_pages": (
                ocr_pages
            ),

            "native_text_pages": (
                native_text_pages
            ),

            "total_pages": (
                total_pages
            ),
        }


    # =====================================================
    # 10. REQUIREMENT EXTRACTION
    # =====================================================

    requirements = (
        extract_requirements(
            extracted_text
        )
    )


    # =====================================================
    # 11. NO REQUIREMENTS
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
                "Text was extracted successfully, "
                "but no supported technical "
                "requirements were detected."
            ),

            "characters_extracted": (
                meaningful_character_count
            ),

            "ocr_required": (
                ocr_used
            ),

            "ocr_used": (
                ocr_used
            ),

            "ocr_pages": (
                ocr_pages
            ),

            "native_text_pages": (
                native_text_pages
            ),

            "total_pages": (
                total_pages
            ),

            "requirements_detected": 0,
        }


    # =====================================================
    # 12. LOAD STANDARDS
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
    # 13. ANALYSIS METADATA
    # =====================================================

    analysis_id = str(
        uuid.uuid4()
    )


    analysis_timestamp = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )


    # =====================================================
    # 14. COUNTERS
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
    # 15. MATCH REQUIREMENTS
    # =====================================================

    for requirement in requirements:

        match_result = (
            hybrid_match_requirement(
                requirement,
                standards,
            )
        )


        decision = (
            match_result.get(
                "decision"
            )
        )


        if (
            requirement.get(
                "status"
            )
            ==
            "needs_clarification"
        ):

            needs_clarification_count += 1


        if decision == "MATCH_FOUND":

            match_found_count += 1


        elif (
            decision
            ==
            "HUMAN_REVIEW_REQUIRED"
        ):

            human_review_count += 1


        elif (
            decision
            ==
            "NO_MATCH_FOUND"
        ):

            no_match_count += 1


        review_priority = (
            match_result.get(
                "review_priority",
                "MEDIUM",
            )
        )


        if review_priority == "HIGH":

            high_priority_count += 1


        elif review_priority == "MEDIUM":

            medium_priority_count += 1


        elif review_priority == "LOW":

            low_priority_count += 1


        results.append(
            {
                "requirement": (
                    requirement
                ),

                "decision": (
                    decision
                ),

                "decision_reason": (
                    match_result.get(
                        "decision_reason"
                    )
                ),

                "review_flags": (
                    match_result.get(
                        "review_flags",
                        [],
                    )
                ),

                "recommended_action": (
                    match_result.get(
                        "recommended_action"
                    )
                ),

                "review_priority": (
                    review_priority
                ),

                "best_match": (
                    match_result.get(
                        "best_match"
                    )
                ),

                "all_matches": (
                    match_result.get(
                        "all_matches",
                        [],
                    )
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
    # 16. SORT RESULTS
    # =====================================================

    priority_order = {
        "HIGH": 1,
        "MEDIUM": 2,
        "LOW": 3,
    }


    results.sort(
        key=lambda item: (
            priority_order.get(
                item.get(
                    "review_priority"
                ),
                4,
            )
        )
    )


    # =====================================================
    # 17. DOCUMENT STATUS
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
    # 18. REVIEW RISK
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
    # 19. REVIEW REASONS
    # =====================================================

    document_review_reasons = (
        get_document_review_reasons(
            human_review_count,
            no_match_count,
            needs_clarification_count,
        )
    )


    # =====================================================
    # 20. TOP PRIORITY ISSUES
    # =====================================================

    top_priority_issues = []


    for item in results:

        if (
            item.get(
                "review_priority"
            )
            ==
            "HIGH"
        ):

            requirement_data = (
                item.get(
                    "requirement",
                    {},
                )
            )


            top_priority_issues.append(
                {
                    "requirement_id": (
                        requirement_data.get(
                            "id"
                        )
                    ),

                    "requirement": (
                        requirement_data.get(
                            "requirement"
                        )
                    ),

                    "reason": (
                        item.get(
                            "decision_reason"
                        )
                    ),

                    "recommended_action": (
                        item.get(
                            "recommended_action"
                        )
                    ),
                }
            )


    # =====================================================
    # 21. COMPLETION PERCENTAGE
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
                /
                len(requirements)
            )
            * 100,
            2,
        )
    )


    # =====================================================
    # 22. SUMMARY
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
    # 23. FINAL RESPONSE
    # =====================================================

    response_data = {

        "filename": (
            safe_filename
        ),

        "status": (
            "PDF processed successfully"
        ),

        "characters_extracted": (
            meaningful_character_count
        ),

        # True means OCR was needed for at least one page
        "ocr_required": (
            ocr_used
        ),

        "ocr_used": (
            ocr_used
        ),

        "ocr_pages": (
            ocr_pages
        ),

        "native_text_pages": (
            native_text_pages
        ),

        "total_pages": (
            total_pages
        ),

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
    # 24. POSTGRESQL
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
    # 25. JSON BACKUP
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
    # 26. RETURN
    # =====================================================

    return response_data