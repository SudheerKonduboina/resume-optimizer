from __future__ import annotations
import re
from typing import Dict, Any

ACTION_VERBS = [
    "built","developed","implemented","designed","optimized","improved","reduced","increased",
    "deployed","integrated","automated","led","owned","created","delivered","tested","fine-tuned"
]

def content_signals(resume_text: str) -> Dict[str, Any]:
    t = resume_text.lower()

    bullets = sum(1 for ln in resume_text.splitlines() if ln.strip().startswith(("-", "•", "*")))
    has_numbers = bool(re.search(r"\b\d+(\.\d+)?%?\b", t))
    action_verb_hits = sum(1 for v in ACTION_VERBS if re.search(rf"\b{re.escape(v)}\b", t))

    return {
        "bullet_lines": bullets,
        "has_numbers": has_numbers,
        "action_verb_hits": action_verb_hits,
    }

def compute_scores(keyword_cov: float, semantic_hit_count: int, fmt_flags: dict, signals: dict) -> Dict[str, Any]:
    # Keywords (45)
    kw_score = min(45, round(keyword_cov * 40 + min(semantic_hit_count, 10) * 0.5, 1))

    # Formatting (25)
    fmt_score = 25.0
    if fmt_flags.get("possible_multi_column_layout"):
        fmt_score -= 8
    missing_core = fmt_flags.get("section_presence", {}).get("missing_core_sections", [])
    fmt_score -= min(8, len(missing_core) * 2)

    contact = fmt_flags.get("contact_info", {})
    if not contact.get("email_detected"):
        fmt_score -= 3
    if not contact.get("phone_detected"):
        fmt_score -= 2
    fmt_score = max(0, round(fmt_score, 1))

    # Content (30)
    content_score = 30.0
    if signals["bullet_lines"] < 6:
        content_score -= 6
    if not signals["has_numbers"]:
        content_score -= 6
    if signals["action_verb_hits"] < 6:
        content_score -= 6
    content_score = max(0, round(content_score, 1))

    total = round(kw_score + fmt_score + content_score, 1)
    total = min(100.0, total)

    return {
        "total": total,
        "breakdown": {
            "keywords": kw_score,
            "formatting": fmt_score,
            "content": content_score,
        }
    }

def build_suggestions(fmt_flags: dict, kw_missing: list, semantic_misses: list, signals: dict) -> Dict[str, Any]:
    suggestions = []

    if fmt_flags.get("possible_multi_column_layout"):
        suggestions.append({
            "type": "formatting",
            "title": "Avoid multi-column layout",
            "detail": "ATS systems can misread columns. Use a single-column layout with simple headings."
        })

    missing_core = fmt_flags.get("section_presence", {}).get("missing_core_sections", [])
    if missing_core:
        suggestions.append({
            "type": "structure",
            "title": "Add core sections",
            "detail": f"Consider adding: {', '.join(missing_core)} with clear headings."
        })

    if signals["bullet_lines"] < 6:
        suggestions.append({
            "type": "content",
            "title": "Add more bullet points with impact",
            "detail": "Use 3–6 bullets per role/project focusing on outcomes, tools, and measurable results."
        })

    if not signals["has_numbers"]:
        suggestions.append({
            "type": "content",
            "title": "Quantify impact",
            "detail": "Add metrics: latency reduced, accuracy improved, cost reduced, users served, requests/day, etc."
        })

    if len(kw_missing) > 0:
        top_missing = kw_missing[:12]
        suggestions.append({
            "type": "keywords",
            "title": "Add missing keywords (exact matches)",
            "detail": f"Try adding where true: {', '.join(top_missing)}"
        })

    if len(semantic_misses) > 0:
        top_sem = semantic_misses[:10]
        suggestions.append({
            "type": "keywords",
            "title": "Add related skills/terms (semantic misses)",
            "detail": f"These appear in JD but not in resume context: {', '.join(top_sem)}"
        })

    return {"items": suggestions}
