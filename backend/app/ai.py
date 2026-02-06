from __future__ import annotations

import re
from functools import lru_cache
from typing import List, Dict, Any

import spacy
from sentence_transformers import SentenceTransformer, util


@lru_cache(maxsize=1)
def _nlp():
    return spacy.load("en_core_web_sm")


@lru_cache(maxsize=1)
def _embedder():
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


_STOP = {
    "and", "or", "to", "with", "in", "of", "for", "a", "an", "the",
    "using", "experience", "strong", "skills", "knowledge", "ability",
    "responsible", "responsibilities", "requirements", "preferred",
    "must", "should", "role", "position", "job"
}

# extra JD/resume junk words (helps reduce noise)
_JUNK_PHRASES = {
    "job title", "location", "type", "requirements", "must have", "job description",
    "responsibilities", "requirement", "the job poster", "can start immediately",
    "remote setting", "fte", "full time", "contract", "internship"
}

_SKILL_PATTERNS = [
    "aws", "azure", "gcp", "google cloud", "kubernetes", "docker", "jenkins", "github actions",
    "gitlab ci", "terraform", "ansible", "helm", "argocd", "gitops", "prometheus", "grafana",
    "linux", "nginx", "apache", "vault",
    "python", "pytorch", "tensorflow", "scikit-learn", "nlp", "llm", "rag", "langchain",
    "postgresql", "mysql", "mongodb", "redis",
]

_MULTIWORD_RE = re.compile(r"[a-zA-Z0-9\+\#\.\-]{2,}(?:\s+[a-zA-Z0-9\+\#\.\-]{2,}){0,3}")


def _norm_term(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def _unique_keep_order(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for x in items:
        nx = _norm_term(x)
        if not nx or nx in seen:
            continue
        seen.add(nx)
        out.append(nx)
    return out


def _is_junk_line(s: str) -> bool:
    low = s.lower()
    if len(low) < 3:
        return True
    if low in {"resume", "curriculum vitae"}:
        return True
    # reject pure headers
    if low in {"skills", "experience", "education", "summary", "projects"}:
        return True
    # reject obvious boilerplate
    for jp in _JUNK_PHRASES:
        if jp in low:
            return True
    return False


def _resume_lines(text: str) -> List[str]:
    """
    Keep lines that are useful for semantic matching:
    - bullet lines
    - tool lists
    - short-but-meaningful lines (>=3 chars)
    """
    lines: List[str] = []
    for ln in (text or "").splitlines():
        s = ln.strip()
        if not s:
            continue

        # keep bullet lines even if short
        is_bullet = s.startswith(("-", "•", "*"))

        # clean bullet prefix for matching readability
        if is_bullet:
            s = s.lstrip("-•*").strip()

        if _is_junk_line(s):
            continue

        # allow shorter lines if they look technical
        if len(s) < 10:
            if any(tok in s.lower() for tok in ["aws", "gcp", "ci", "cd", "sql", "git", "k8", "docker", "terraform"]):
                lines.append(s)
            continue

        lines.append(s)

    # fallback: if filtering removed too much, keep raw split lines
    if len(lines) < 8:
        raw = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
        lines = raw[:200]

    return lines[:260]


def extract_skills(text: str, max_terms: int = 80) -> List[str]:
    t = text or ""
    low = t.lower()

    found: List[str] = []

    for p in _SKILL_PATTERNS:
        if p in low:
            found.append(p)

    nlp = _nlp()
    doc = nlp(t)

    for ent in doc.ents:
        cand = _norm_term(ent.text)
        if 2 <= len(cand) <= 40 and cand not in _STOP:
            if len(cand.split()) <= 3:
                found.append(cand)

    for chunk in doc.noun_chunks:
        cand = _norm_term(chunk.text)
        if 2 <= len(cand) <= 40 and cand not in _STOP:
            if len(cand.split()) <= 4:
                found.append(cand)

    for m in _MULTIWORD_RE.findall(low):
        cand = _norm_term(m)
        if 2 <= len(cand) <= 40 and cand not in _STOP:
            if any(x in cand for x in ["+", "#", ".", "-", "ci", "sql", "cloud", "kube", "docker", "git"]):
                found.append(cand)

    found = _unique_keep_order(found)

    cleaned = []
    for x in found:
        if x in _STOP:
            continue
        if len(x) < 2:
            continue
        if all(w in _STOP for w in x.split()):
            continue
        if any(j in x for j in _JUNK_PHRASES):
            continue
        cleaned.append(x)

    return cleaned[:max_terms]


def exact_keyword_match(resume_text: str, jd_keywords: List[str]) -> Dict[str, Any]:
    rt = (resume_text or "").lower()
    present: List[str] = []
    missing: List[str] = []

    for kw in jd_keywords or []:
        k = _norm_term(kw)
        if not k:
            continue

        if " " in k:
            hit = k in rt
        else:
            hit = re.search(rf"\b{re.escape(k)}\b", rt) is not None

        if hit:
            present.append(k)
        else:
            missing.append(k)

    present = _unique_keep_order(present)
    missing = _unique_keep_order(missing)

    total = len(present) + len(missing)
    coverage = round((len(present) / total) * 100.0, 2) if total > 0 else 0.0

    return {"present": present, "missing": missing, "coverage": coverage}


def semantic_match(
    jd_terms: List[str],
    resume_text: str,
    threshold: float = 0.62,
) -> Dict[str, Any]:
    jd_terms = _unique_keep_order([_norm_term(x) for x in (jd_terms or []) if _norm_term(x)])
    if not jd_terms:
        return {"semantic_hits": [], "semantic_misses": [], "semantic_matches": [], "semantic_coverage": 0.0}

    lines = _resume_lines(resume_text or "")
    if not lines:
        return {"semantic_hits": [], "semantic_misses": jd_terms, "semantic_matches": [], "semantic_coverage": 0.0}

    model = _embedder()

    jd_emb = model.encode(jd_terms, convert_to_tensor=True, normalize_embeddings=True)
    line_emb = model.encode(lines, convert_to_tensor=True, normalize_embeddings=True)

    sims = util.cos_sim(jd_emb, line_emb)

    semantic_hits: List[str] = []
    semantic_misses: List[str] = []
    semantic_matches: List[Dict[str, Any]] = []

    for i, term in enumerate(jd_terms):
        best_score = float(sims[i].max())
        best_idx = int(sims[i].argmax())
        best_line = lines[best_idx] if 0 <= best_idx < len(lines) else ""

        if best_score >= float(threshold):
            semantic_hits.append(term)
            semantic_matches.append(
                {"keyword": term, "score": round(best_score, 4), "best_line": best_line}
            )
        else:
            semantic_misses.append(term)

    semantic_hits = _unique_keep_order(semantic_hits)
    semantic_misses = _unique_keep_order(semantic_misses)

    total = len(semantic_hits) + len(semantic_misses)
    semantic_coverage = round((len(semantic_hits) / total) * 100.0, 2) if total > 0 else 0.0

    semantic_matches.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)

    return {
        "semantic_hits": semantic_hits,
        "semantic_misses": semantic_misses,
        "semantic_matches": semantic_matches,
        "semantic_coverage": semantic_coverage,
    }
