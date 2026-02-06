from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

MAX_FILE_MB = 10
MAX_FILE_BYTES = MAX_FILE_MB * 1024 * 1024

ALLOWED_EXT = {".pdf", ".docx"}


class AnalyzeResponse(BaseModel):
    status: bool = True
    job_id: str


class StatusResponse(BaseModel):
    status: bool = True
    job_id: str
    state: str
    progress: int = Field(ge=0, le=100)
    message: str
    error: Optional[str] = None


class JobResult(BaseModel):
    job_id: str
    filename: str
    resume_text_preview: str
    job_description_preview: Optional[str] = None

    scores: Dict[str, Any]
    keyword_analysis: Dict[str, Any]
    formatting_flags: Dict[str, Any]
    suggestions: Dict[str, Any]
