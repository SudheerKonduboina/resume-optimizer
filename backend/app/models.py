from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import time

@dataclass
class Job:
    job_id: str
    filename: str
    created_at: float = field(default_factory=lambda: time.time())
    status: Dict[str, Any] = field(default_factory=lambda: {"state": "queued", "progress": 0, "message": "Queued"})
    result: Optional[Dict[str, Any]] = None
    report_html: Optional[str] = None
