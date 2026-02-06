from __future__ import annotations

import uuid
import asyncio
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core import MAX_FILE_BYTES, ALLOWED_EXT, AnalyzeResponse, StatusResponse, JobResult
from app.models import Job
from app.services.parse import parse_resume
from app.services.keywords import extract_jd_keywords, keyword_match, semantic_match
from app.services.scoring import content_signals, compute_scores, build_suggestions
from app.services.report import render_html_report

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=[])

app = FastAPI(
    title="ATS Resume Optimizer (Open-Source)",
    version="0.1.0",
)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# CORS for Next.js local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store (OK for demo assignment)
jobs: dict[str, Job] = {}


@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"status": False, "message": "Rate limit exceeded: 5 free uses/day per IP."},
    )


def set_status(job: Job, state: str, progress: int, message: str, error: Optional[str] = None):
    job.status = {"state": state, "progress": progress, "message": message, "error": error}


def _jd_is_too_short(jd: Optional[str]) -> bool:
    if not jd:
        return True
    # basic guard against "string" or tiny JD
    return len(jd.strip().split()) < 12


async def run_analysis(job: Job, file_path: str, jd: Optional[str]):
    try:
        set_status(job, "parsing", 10, "Parsing resume...")
        resume_text, fmt_flags = parse_resume(file_path)

        set_status(job, "analyzing", 35, "Analyzing keywords...")
        jd_keywords = []
        kw = {"present": [], "missing": [], "coverage": 0.0}
        sem = {"semantic_hits": [], "semantic_misses": []}

        if jd and not _jd_is_too_short(jd):
            jd_keywords = extract_jd_keywords(jd)
            if jd_keywords:
                kw = keyword_match(resume_text, jd_keywords)
                sem = semantic_match(resume_text, jd_keywords)

        set_status(job, "analyzing", 60, "Scoring resume...")
        signals = content_signals(resume_text)
        scores = compute_scores(kw["coverage"], len(sem.get("semantic_hits", [])), fmt_flags, signals)

        set_status(job, "generating_report", 80, "Generating report...")
        suggestions = build_suggestions(fmt_flags, kw.get("missing", []), sem.get("semantic_misses", []), signals)

        # If JD was provided but too short, add a nice hint
        if jd and _jd_is_too_short(jd):
            suggestions["items"].insert(
                0,
                {
                    "type": "keywords",
                    "title": "Job description too short",
                    "detail": "Paste a full job description (at least 2–3 paragraphs) to get accurate keyword matching.",
                },
            )

        payload = {
            "job_id": job.job_id,
            "filename": job.filename,
            "resume_text_preview": resume_text[:1200],
            "job_description_preview": (jd[:600] if jd else None),
            "scores": scores,
            "keyword_analysis": {
                "present": kw.get("present", []),
                "missing": kw.get("missing", []),
                "coverage": kw.get("coverage", 0.0),
                "jd_keywords": jd_keywords,
                "semantic_hits": sem.get("semantic_hits", []),
                "semantic_misses": sem.get("semantic_misses", []),
            },
            "formatting_flags": fmt_flags,
            "suggestions": suggestions,
        }

        job.report_html = render_html_report(payload)
        job.result = payload
        set_status(job, "done", 100, "Done")

    except Exception as e:
        set_status(job, "error", 100, "Failed", error=str(e))


# -------------------------
# Routes
# -------------------------

@app.get("/", tags=["default"])
def root():
    return {"status": "ok", "service": "ATS Resume Optimizer", "docs": "/docs"}


@app.get("/health", tags=["default"])
def health():
    return {"ok": True}


# IMPORTANT:
# Keep response_model=None here to avoid UploadFile/Pydantic edge issues on some setups.
@app.post("/api/analyze", response_model=None, tags=["default"])
@limiter.limit("5/day")
async def analyze(
    request: Request,
    resume: UploadFile = File(...),
    job_description: Optional[str] = Form(None),
):
    # Validate extension
    ext = Path(resume.filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="Only PDF or DOCX supported.")

    # Validate size
    contents = await resume.read()
    if len(contents) > MAX_FILE_BYTES:
        raise HTTPException(status_code=400, detail="File too large (max 10MB).")

    # Save to disk
    job_id = str(uuid.uuid4())
    safe_name = f"{job_id}{ext}"
    file_path = str(UPLOAD_DIR / safe_name)

    with open(file_path, "wb") as f:
        f.write(contents)

    # Create job
    job = Job(job_id=job_id, filename=resume.filename)
    jobs[job_id] = job
    set_status(job, "queued", 5, "Queued")

    # Run in background task
    asyncio.create_task(run_analysis(job, file_path, job_description))

    return AnalyzeResponse(status=True, job_id=job_id).model_dump()


@app.get("/api/status/{job_id}", response_model=StatusResponse, tags=["default"])
def status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return StatusResponse(status=True, job_id=job_id, **job.status)


@app.get("/api/result/{job_id}", response_model=JobResult, tags=["default"])
def result(job_id: str):
    job = jobs.get(job_id)
    if not job or not job.result:
        raise HTTPException(status_code=404, detail="Result not found")

    return JobResult(**job.result)


from app.services.report_pdf import build_pdf

@app.get("/api/download/{job_id}", tags=["default"])
def download(job_id: str):
    job = jobs.get(job_id)
    if not job or not job.result:
        raise HTTPException(status_code=404, detail="Report not found")

    pdf_bytes = build_pdf(job.result)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="ATS_Report_{job_id}.pdf"'
        },
    )

import os

ENV = os.getenv("ENV", "dev")
if ENV != "dev":
    enforce_rate_limit(ip)
    
print("ENV =", os.getenv("ENV"))
