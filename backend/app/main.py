from fastapi import FastAPI, UploadFile, File, HTTPException
import os
import shutil

from app.services.pdf_service import extract_pdf_text
from app.services.requirement_service import extract_requirements
from app.services.standards_service import load_standards
from app.services.matching_service import match_requirement_to_standards

app = FastAPI()

UPLOAD_FOLDER = "app/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


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


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    file_path = os.path.join(
        UPLOAD_FOLDER,
        file.filename
    )

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    extracted_text = extract_pdf_text(file_path)

    requirements = extract_requirements(extracted_text)

    standards = load_standards()

    results = []

    for requirement in requirements:

        matches = match_requirement_to_standards(
            requirement,
            standards
        )

        results.append({
            "requirement": requirement,
            "matched_standards": matches
        })

    return {
        "filename": file.filename,
        "status": "PDF processed successfully",
        "characters_extracted": len(extracted_text),
        "requirements_found": len(requirements),
        "results": results
    }