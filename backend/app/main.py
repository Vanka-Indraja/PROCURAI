from fastapi import FastAPI, UploadFile, File, HTTPException
import os
import shutil
import uuid
import json
from datetime import datetime, timezone

from app.services.pdf_service import extract_pdf_text
from app.services.requirement_service import extract_requirements
from app.services.standards_service import load_standards
from app.services.matching_service import match_requirement_to_standards


def get_document_status(
    match_found_count,
    human_review_count,
    no_match_count,
    needs_clarification_count
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


def calculate_review_risk(
    total_requirements,
    human_review_count,
    no_match_count,
    needs_clarification_count
):
    if total_requirements == 0:
        return 0

    risk_points = (
        human_review_count * 2
        + no_match_count * 3
        + needs_clarification_count * 2
    )

    max_points = total_requirements * 7

    risk_score = round(
        (risk_points / max_points) * 100,
        2
    )

    return min(risk_score, 100)


def get_review_risk_level(review_risk_score):
    if review_risk_score >= 60:
        return "HIGH"

    if review_risk_score >= 30:
        return "MEDIUM"

    return "LOW"


def get_document_review_reasons(
    human_review_count,
    no_match_count,
    needs_clarification_count
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

    if not reasons:
        reasons.append(
            "No major review issues detected."
        )

    return reasons


app = FastAPI()

UPLOAD_FOLDER = "app/uploads"
REPORT_FOLDER = "app/reports"
MAX_FILE_SIZE = 10 * 1024 * 1024
MIN_TEXT_LENGTH = 50

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    REPORT_FOLDER,
    exist_ok=True
)


@app.get("/")
def home():
    return {
        "project": "PROCURAI",
        "status": "Backend is running"
    }


@app.get("/standards")
def get_standards():
    standards = load_standards()

    return {
        "count": len(standards),
        "standards": standards
    }


@app.get("/reports")
def list_reports():

    reports = []

    for filename in os.listdir(REPORT_FOLDER):

        if not filename.endswith(".json"):
            continue

        report_path = os.path.join(
            REPORT_FOLDER,
            filename
        )

        with open(
            report_path,
            "r",
            encoding="utf-8"
        ) as report_file:
            report_data = json.load(
                report_file
            )

        reports.append({
            "analysis_id": report_data.get("analysis_id"),
            "filename": report_data.get("filename"),
            "analysis_timestamp": report_data.get(
                "analysis_timestamp"
            ),
            "document_status": report_data.get(
                "document_status"
            ),
            "review_risk_level": report_data.get(
                "review_risk_level"
            )
        })

    reports.sort(
        key=lambda item: item.get(
            "analysis_timestamp",
            ""
        ),
        reverse=True
    )

    return {
        "count": len(reports),
        "reports": reports
    }


@app.get("/reports/{analysis_id}")
def get_report(analysis_id: str):

    report_path = os.path.join(
        REPORT_FOLDER,
        f"{analysis_id}.json"
    )

    if not os.path.exists(report_path):
        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )

    with open(
        report_path,
        "r",
        encoding="utf-8"
    ) as report_file:
        report_data = json.load(
            report_file
        )

    return report_data


@app.delete("/reports/{analysis_id}")
def delete_report(analysis_id: str):

    report_path = os.path.join(
        REPORT_FOLDER,
        f"{analysis_id}.json"
    )

    if not os.path.exists(report_path):
        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )

    os.remove(report_path)

    return {
        "status": "Report deleted successfully",
        "analysis_id": analysis_id
    }


@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    file_path = os.path.join(
        UPLOAD_FOLDER,
        file.filename
    )

    with open(
        file_path,
        "wb"
    ) as buffer:
        shutil.copyfileobj(
            file.file,
            buffer
        )

    file_size = os.path.getsize(
        file_path
    )

    if file_size == 0:
        os.remove(file_path)

        raise HTTPException(
            status_code=400,
            detail="Uploaded PDF is empty"
        )

    if file_size > MAX_FILE_SIZE:
        os.remove(file_path)

        raise HTTPException(
            status_code=400,
            detail="PDF file size exceeds 10 MB limit"
        )

    with open(
        file_path,
        "rb"
    ) as pdf_file:
        signature = pdf_file.read(5)

    if signature != b"%PDF-":
        os.remove(file_path)

        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file"
        )

    extracted_text = extract_pdf_text(
        file_path
    )

    clean_text = extracted_text.strip()

    if len(clean_text) < MIN_TEXT_LENGTH:
        return {
            "filename": file.filename,
            "status": "OCR_REQUIRED",
            "message": (
                "Very little or no selectable text was detected. "
                "This PDF may be scanned or image-based."
            ),
            "characters_extracted": len(clean_text),
            "ocr_required": True
        }

    requirements = extract_requirements(
        extracted_text
    )

    if len(requirements) == 0:
        return {
            "filename": file.filename,
            "status": "NO_REQUIREMENTS_DETECTED",
            "message": (
                "Text was extracted from the PDF, but no supported "
                "technical requirements were detected."
            ),
            "characters_extracted": len(extracted_text),
            "ocr_required": False,
            "requirements_detected": 0
        }

    standards = load_standards()

    analysis_timestamp = datetime.now(
        timezone.utc
    ).isoformat()

    analysis_id = str(
        uuid.uuid4()
    )

    results = []

    match_found_count = 0
    human_review_count = 0
    no_match_count = 0
    needs_clarification_count = 0

    high_priority_count = 0
    medium_priority_count = 0
    low_priority_count = 0

    for requirement in requirements:

        match_result = match_requirement_to_standards(
            requirement,
            standards
        )

        decision = match_result["decision"]

        if requirement["status"] == "needs_clarification":
            needs_clarification_count += 1

        if decision == "MATCH_FOUND":
            match_found_count += 1

        elif decision == "HUMAN_REVIEW_REQUIRED":
            human_review_count += 1

        elif decision == "NO_MATCH_FOUND":
            no_match_count += 1

        review_priority = match_result["review_priority"]

        if review_priority == "HIGH":
            high_priority_count += 1

        elif review_priority == "MEDIUM":
            medium_priority_count += 1

        elif review_priority == "LOW":
            low_priority_count += 1

        results.append({
            "requirement": requirement,
            "decision": decision,
            "decision_reason": match_result["decision_reason"],
            "review_flags": match_result["review_flags"],
            "recommended_action": match_result["recommended_action"],
            "review_priority": review_priority,
            "best_match": match_result["best_match"],
            "all_matches": match_result["all_matches"]
        })

    priority_order = {
        "HIGH": 1,
        "MEDIUM": 2,
        "LOW": 3
    }

    results.sort(
        key=lambda item: priority_order.get(
            item["review_priority"],
            4
        )
    )

    document_status = get_document_status(
        match_found_count,
        human_review_count,
        no_match_count,
        needs_clarification_count
    )

    review_risk_score = calculate_review_risk(
        len(requirements),
        human_review_count,
        no_match_count,
        needs_clarification_count
    )

    review_risk_level = get_review_risk_level(
        review_risk_score
    )

    document_review_reasons = get_document_review_reasons(
        human_review_count,
        no_match_count,
        needs_clarification_count
    )

    top_priority_issues = []

    for item in results:
        if item["review_priority"] == "HIGH":
            top_priority_issues.append({
                "requirement_id": item["requirement"]["id"],
                "requirement": item["requirement"]["requirement"],
                "reason": item["decision_reason"],
                "recommended_action": item["recommended_action"]
            })

    if len(requirements) == 0:
        analysis_completion_percentage = 0

    else:
        analyzed_count = (
            match_found_count
            + human_review_count
            + no_match_count
        )

        analysis_completion_percentage = round(
            (
                analyzed_count
                / len(requirements)
            ) * 100,
            2
        )

    summary = {
        "total_requirements": len(requirements),
        "match_found": match_found_count,
        "human_review_required": human_review_count,
        "no_match_found": no_match_count,
        "needs_clarification": needs_clarification_count,
        "high_priority": high_priority_count,
        "medium_priority": medium_priority_count,
        "low_priority": low_priority_count
    }

    response_data = {
        "filename": file.filename,
        "status": "PDF processed successfully",
        "characters_extracted": len(extracted_text),
        "ocr_required": False,
        "analysis_id": analysis_id,
        "analysis_timestamp": analysis_timestamp,
        "matcher_version": "baseline_keyword_v1",
        "document_status": document_status,
        "review_risk_score": review_risk_score,
        "review_risk_level": review_risk_level,
        "document_review_reasons": document_review_reasons,
        "top_priority_issues": top_priority_issues,
        "analysis_completion_percentage": analysis_completion_percentage,
        "summary": summary,
        "results": results
    }

    report_path = os.path.join(
        REPORT_FOLDER,
        f"{analysis_id}.json"
    )

    with open(
        report_path,
        "w",
        encoding="utf-8"
    ) as report_file:
        json.dump(
            response_data,
            report_file,
            indent=4,
            ensure_ascii=False
        )

    return response_data