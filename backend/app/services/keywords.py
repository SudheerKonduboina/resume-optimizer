from __future__ import annotations
from typing import List, Dict, Any

from app.ai import extract_skills, exact_keyword_match, semantic_match as ai_semantic_match


def extract_jd_keywords(jd_text: str) -> List[str]:
    if not jd_text or not jd_text.strip():
        return []
    return extract_skills(jd_text, max_terms=80)


def keyword_match(resume_text: str, jd_keywords: List[str]) -> Dict[str, Any]:
    return exact_keyword_match(resume_text, jd_keywords)


def semantic_match(resume_text: str, jd_keywords: List[str]) -> Dict[str, Any]:
    # ai expects (jd_terms, resume_text)
    return ai_semantic_match(jd_keywords, resume_text, threshold=0.62)
