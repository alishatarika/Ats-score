from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from services.text_extraction import extract_text
from services.scorer_extraction import calculate_ats_score

router = APIRouter()


@router.post("/ats-score")
async def ats_score(
    resume: UploadFile = File(..., description="Upload your resume (PDF or DOCX)"),
    job_description: str = Form(..., description="Paste the full job description here"),
):
    allowed_extensions = (".pdf", ".docx")
    if not resume.filename.lower().endswith(allowed_extensions):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Please upload a PDF or DOCX. Got: {resume.filename}",
        )
    if not job_description.strip():
        raise HTTPException(
            status_code=400,
            detail="Job description cannot be empty.",
        )

    resume_text = extract_text(resume)

    if not resume_text.strip():
        raise HTTPException(
            status_code=422,
            detail="Could not extract text from the resume. Make sure the file is not scanned/image-only.",
        )

    result = calculate_ats_score(resume_text, job_description)

    return result