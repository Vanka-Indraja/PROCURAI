import json
import os
import shutil
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.services.database_service import (
    delete_report_from_database,
    get_report_from_database,
    list_reports_from_database,
    save_analysis_to_database,
)
from app.services.hybrid_matching_service import (
    hybrid_match_requirement,
)
from app.services.pdf_service import (
    OCRPageLimitError,
    OCRUnavailableError,
    PDFPageLimitError,
    PDFProcessingError,
    count_meaningful_characters,
    extract_pdf_text_with_ocr,
)
from app.services.requirement_service import extract_requirements
from app.services.standards_service import load_standards


# =========================================================
# CONFIGURATION
# =========================================================

MATCHER_VERSION = "HYBRID_KEYWORD_SEMANTIC_V1"
MIN_USABLE_TEXT_LENGTH = 50
MAX_FILE_SIZE = 10 * 1024 * 1024
UPLOAD_FOLDER = "app/uploads"
REPORT_FOLDER = "app/reports"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)


app = FastAPI(
    title="PROCURAI",
    description=(
        "AI-Powered Procurement Specification Analysis "
        "and Indian Standards Recommendation System"
    ),
    version="0.7.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# REVIEW HELPERS
# =========================================================

def get_document_status(
    match_found_count,
    human_review_count,
    no_match_count,
    needs_clarification_count,
    ocr_review_required=False,
):
    if no_match_count > 0:
        return "INCOMPLETE_MATCHING"

    if (
        human_review_count > 0
        or needs_clarification_count > 0
        or ocr_review_required
    ):
        return "REVIEW_REQUIRED"

    if match_found_count > 0:
        return "READY"

    return "REVIEW_REQUIRED"


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

    max_points = total_requirements * 7

    return min(
        round((risk_points / max_points) * 100, 2),
        100,
    )


def get_review_risk_level(review_risk_score):
    if review_risk_score >= 60:
        return "HIGH"

    if review_risk_score >= 30:
        return "MEDIUM"

    return "LOW"


def get_document_review_reasons(
    human_review_count,
    no_match_count,
    needs_clarification_count,
    ocr_review_required=False,
    low_confidence_pages=None,
):
    reasons = []

    if human_review_count > 0:
        reasons.append(
            f"{human_review_count} requirement(s) need human review."
        )

    if no_match_count > 0:
        reasons.append(
            f"{no_match_count} requirement(s) have no matching standard."
        )

    if needs_clarification_count > 0:
        reasons.append(
            f"{needs_clarification_count} requirement(s) are vague or incomplete."
        )

    if ocr_review_required:
        pages = low_confidence_pages or []

        reasons.append(
            "OCR quality needs human review on page(s): "
            + ", ".join(str(page) for page in pages)
            + "."
        )

    if not reasons:
        reasons.append(
            "No major review issues detected."
        )

    return reasons


# =========================================================
# OCR METADATA HELPERS
# =========================================================

def extraction_fields(extraction_info):
    return {
        "ocr_required": extraction_info.get(
            "ocr_used",
            False,
        ),
        "ocr_used": extraction_info.get(
            "ocr_used",
            False,
        ),
        "ocr_pages": extraction_info.get(
            "ocr_pages",
            [],
        ),
        "native_text_pages": extraction_info.get(
            "native_text_pages",
            [],
        ),
        "total_pages": extraction_info.get(
            "total_pages",
            0,
        ),
        "ocr_confidence": extraction_info.get(
            "ocr_confidence"
        ),
        "low_confidence_pages": extraction_info.get(
            "low_confidence_pages",
            [],
        ),
        "ocr_review_required": extraction_info.get(
            "ocr_review_required",
            False,
        ),
        "ocr_quality_status": extraction_info.get(
            "ocr_quality_status",
            "NOT_APPLICABLE",
        ),
        "ocr_page_details": extraction_info.get(
            "ocr_page_details",
            [],
        ),
        "ocr_warnings": extraction_info.get(
            "ocr_warnings",
            [],
        ),
        "extraction_mode": extraction_info.get(
            "extraction_mode"
        ),
        "ocr_engine": extraction_info.get(
            "ocr_engine"
        ),
    }


def safe_remove(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


# =========================================================
# BASIC ENDPOINTS
# =========================================================

@app.get("/")
def home():
    return {
        "project": "PROCURAI",
        "status": "Backend is running",
        "database": "PostgreSQL",
        "matching_engine": "Hybrid Keyword + Semantic AI",
        "matcher_version": MATCHER_VERSION,
        "pdf_processing": (
            "Page-wise native text extraction + automatic "
            "Tesseract OCR + quality metadata"
        ),
        "ocr_engine": "Tesseract OCR",
        "api_version": "0.7.0",
    }


@app.get("/standards")
def get_standards():
    standards = load_standards()

    return {
        "count": len(standards),
        "standards": standards,
    }


@app.get("/reports")
def list_reports():
    return list_reports_from_database()


@app.get("/reports/{analysis_id}")
def get_report(analysis_id: str):
    report = get_report_from_database(
        analysis_id
    )

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    return report


@app.delete("/reports/{analysis_id}")
def delete_report(analysis_id: str):
    deleted = delete_report_from_database(
        analysis_id
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

    safe_remove(
        report_path
    )

    return {
        "status": "Report deleted successfully",
        "analysis_id": analysis_id,
    }


# =========================================================
# PDF ANALYSIS CORE
# =========================================================

def analyze_saved_pdf(
    file_path,
    safe_filename,
    file_size,
):
    # -----------------------------------------------------
    # PDF / OCR EXTRACTION
    # -----------------------------------------------------

    try:
        extracted_text, extraction_info = (
            extract_pdf_text_with_ocr(
                file_path
            )
        )

    except PDFPageLimitError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": (
                    "PDF_PAGE_LIMIT_EXCEEDED"
                ),
                "message": str(exc),
            },
        ) from exc

    except OCRPageLimitError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": (
                    "OCR_PAGE_LIMIT_EXCEEDED"
                ),
                "message": str(exc),
            },
        ) from exc

    except OCRUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "error_code": (
                    "OCR_ENGINE_UNAVAILABLE"
                ),
                "message": str(exc),
            },
        ) from exc

    except PDFProcessingError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": (
                    "OCR_OR_PDF_PROCESSING_FAILED"
                ),
                "message": str(exc),
            },
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "OCR_FAILED",
                "message": (
                    f"Unable to process PDF: {exc}"
                ),
            },
        ) from exc

    # -----------------------------------------------------
    # EXTRACTED TEXT VALIDATION
    # -----------------------------------------------------

    meaningful_character_count = (
        count_meaningful_characters(
            extracted_text
        )
    )

    ocr_fields = extraction_fields(
        extraction_info
    )

    if (
        meaningful_character_count
        < MIN_USABLE_TEXT_LENGTH
    ):
        return {
            "filename": safe_filename,
            "status": (
                "INSUFFICIENT_TEXT_AFTER_OCR"
            ),
            "error_code": (
                "INSUFFICIENT_TEXT_AFTER_OCR"
            ),
            "message": (
                "The PDF contained too little usable text "
                "after native extraction and OCR."
            ),
            "characters_extracted": (
                meaningful_character_count
            ),
            **ocr_fields,
        }

    # -----------------------------------------------------
    # REQUIREMENT EXTRACTION
    # -----------------------------------------------------

    requirements = extract_requirements(
        extracted_text
    )

    if not requirements:
        return {
            "filename": safe_filename,
            "status": (
                "NO_REQUIREMENTS_DETECTED"
            ),
            "error_code": (
                "NO_REQUIREMENTS_DETECTED"
            ),
            "message": (
                "Text was extracted successfully, "
                "but no supported technical requirements "
                "were detected."
            ),
            "characters_extracted": (
                meaningful_character_count
            ),
            "requirements_detected": 0,
            **ocr_fields,
        }

    # -----------------------------------------------------
    # LOAD STANDARDS
    # -----------------------------------------------------

    standards = load_standards()

    if not standards:
        raise HTTPException(
            status_code=500,
            detail=(
                "No standards are available in the "
                "PostgreSQL database."
            ),
        )

    # -----------------------------------------------------
    # ANALYSIS METADATA
    # -----------------------------------------------------

    analysis_id = str(
        uuid.uuid4()
    )

    analysis_timestamp = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    results = []

    match_found_count = 0
    human_review_count = 0
    no_match_count = 0
    needs_clarification_count = 0

    high_priority_count = 0
    medium_priority_count = 0
    low_priority_count = 0

    # -----------------------------------------------------
    # HYBRID MATCHING
    # -----------------------------------------------------

    for requirement in requirements:
        match_result = (
            hybrid_match_requirement(
                requirement,
                standards,
            )
        )

        decision = match_result.get(
            "decision"
        )

        if (
            requirement.get("status")
            == "needs_clarification"
        ):
            needs_clarification_count += 1

        if decision == "MATCH_FOUND":
            match_found_count += 1

        elif (
            decision
            == "HUMAN_REVIEW_REQUIRED"
        ):
            human_review_count += 1

        elif decision == "NO_MATCH_FOUND":
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
                "requirement": requirement,
                "decision": decision,
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

    # -----------------------------------------------------
    # SORT RESULTS BY REVIEW PRIORITY
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # OCR REVIEW STATUS
    # -----------------------------------------------------

    ocr_review_required = (
        ocr_fields[
            "ocr_review_required"
        ]
    )

    low_confidence_pages = (
        ocr_fields[
            "low_confidence_pages"
        ]
    )

    # -----------------------------------------------------
    # DOCUMENT STATUS
    # -----------------------------------------------------

    document_status = (
        get_document_status(
            match_found_count,
            human_review_count,
            no_match_count,
            needs_clarification_count,
            ocr_review_required=(
                ocr_review_required
            ),
        )
    )

    # -----------------------------------------------------
    # REVIEW RISK
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # REVIEW REASONS
    # -----------------------------------------------------

    document_review_reasons = (
        get_document_review_reasons(
            human_review_count,
            no_match_count,
            needs_clarification_count,
            ocr_review_required=(
                ocr_review_required
            ),
            low_confidence_pages=(
                low_confidence_pages
            ),
        )
    )

    # -----------------------------------------------------
    # TOP PRIORITY ISSUES
    # -----------------------------------------------------

    top_priority_issues = []

    for item in results:
        if (
            item.get(
                "review_priority"
            )
            != "HIGH"
        ):
            continue

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

    # -----------------------------------------------------
    # COMPLETION PERCENTAGE
    # -----------------------------------------------------

    analyzed_count = (
        match_found_count
        + human_review_count
        + no_match_count
    )

    analysis_completion_percentage = round(
        (
            analyzed_count
            / len(requirements)
        )
        * 100,
        2,
    )

    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # FINAL RESPONSE
    # -----------------------------------------------------

    response_data = {
        "filename": safe_filename,
        "status": (
            "PDF processed successfully"
        ),
        "characters_extracted": (
            meaningful_character_count
        ),
        **ocr_fields,
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
        "summary": summary,
        "results": results,
    }

    # -----------------------------------------------------
    # SAVE TO POSTGRESQL
    # -----------------------------------------------------

    database_result = (
        save_analysis_to_database(
            response_data,
            file_size,
        )
    )

    response_data[
        "database"
    ] = database_result

    # -----------------------------------------------------
    # OPTIONAL JSON REPORT COPY
    # -----------------------------------------------------

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

    return response_data


# =========================================================
# UPLOAD ENDPOINT
# =========================================================

@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
):
    # -----------------------------------------------------
    # BASIC FILE VALIDATION
    # -----------------------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is missing",
        )

    if not file.filename.lower().endswith(
        ".pdf"
    ):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed",
        )

    safe_filename = os.path.basename(
        file.filename
    )

    stored_filename = (
        f"{uuid.uuid4()}_"
        f"{safe_filename}"
    )

    file_path = os.path.join(
        UPLOAD_FOLDER,
        stored_filename,
    )

    # -----------------------------------------------------
    # SAVE TEMPORARY UPLOAD
    # -----------------------------------------------------

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
        safe_remove(
            file_path
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to save uploaded PDF: "
                f"{exc}"
            ),
        ) from exc

    try:
        # -------------------------------------------------
        # FILE SIZE
        # -------------------------------------------------

        file_size = os.path.getsize(
            file_path
        )

        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Uploaded PDF is empty"
                ),
            )

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=(
                    "PDF file size exceeds "
                    "10 MB limit"
                ),
            )

        # -------------------------------------------------
        # PDF SIGNATURE CHECK
        # -------------------------------------------------

        with open(
            file_path,
            "rb",
        ) as pdf_file:
            signature = (
                pdf_file.read(5)
            )

        if signature != b"%PDF-":
            raise HTTPException(
                status_code=400,
                detail="Invalid PDF file",
            )

        # -------------------------------------------------
        # RUN COMPLETE ANALYSIS
        # -------------------------------------------------

        return analyze_saved_pdf(
            file_path,
            safe_filename,
            file_size,
        )

    finally:
        # Database/report data is retained.
        # Temporary uploaded PDF is removed.
        safe_remove(
            file_path
        )