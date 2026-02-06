from __future__ import annotations

import re
from functools import lru_cache
from typing import List, Dict, Any

import spacy
from sentence_transformers import SentenceTransformer, util


@lru_cache(maxsize=1)
def _nlp():
    # Install: python -m spacy download en_core_web_sm
    return spacy.load("en_core_web_sm")


@lru_cache(maxsize=1)
def _embedder():
    # Install: pip install sentence-transformers
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


_STOP = {
    "and", "or", "to", "with", "in", "of", "for", "a", "an", "the",
    "using", "experience", "strong", "skills", "knowledge", "ability",
    "responsible", "responsibilities", "requirements", "preferred",
    "must", "should", "role", "position", "job"
}

_SKILL_PATTERNS = [
    # cloud/devops
    "aws", "azure", "gcp", "google cloud", "kubernetes", "docker", "jenkins", "github actions",
    "gitlab ci", "terraform", "ansible", "helm", "argocd", "gitops", "prometheus", "grafana",
    "linux", "nginx", "apache", "vault",
    # data/ai
    "python", "pytorch", "tensorflow", "scikit-learn", "nlp", "llm", "rag", "langchain",
    # db
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


def _clean_resume_lines(text: str) -> List[str]:
    """
    Create short, meaningful resume lines for best_line matching.
    """
    if not text:
        return []
    lines = []
    for ln in text.splitlines():
        s = re.sub(r"\s+", " ", (ln or "").strip())
        if len(s) < 18:
            continue
        # avoid lines that are just punctuation/headers
        if re.fullmatch(r"[-•*_=]{3,}", s):
            continue
        lines.append(s)
    # cap for performance
    return lines[:180]


def extract_skills(text: str, max_terms: int = 80) -> List[str]:
    """
    Extract skill/tool terms from free text (JD or resume).
    Hybrid:
      - curated pattern hits
      - spaCy noun chunks + entities filtered
      - regex candidates (backup)
    Returns normalized terms.
    """
    t = text or ""
    low = t.lower()
    found: List[str] = []

    # 1) curated pattern hits
    for p in _SKILL_PATTERNS:
        if p in low:
            found.append(p)

    # 2) spaCy entities & noun chunks
    doc = _nlp()(t)

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

    # 3) regex candidates (backup)
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
        cleaned.append(x)

    return cleaned[:max_terms]


def exact_keyword_match(resume_text: str, jd_keywords: List[str]) -> Dict[str, Any]:
    """
    Exact matching (case-insensitive) against resume text.
    Returns: present, missing, coverage (0..100)
    """
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

    return {"present": present, "missing": missing, "coverage": float(coverage)}


def semantic_match(jd_terms: List[str], resume_text: str, threshold: float = 0.62) -> Dict[str, Any]:
    """
    Semantic matching of JD terms vs resume text.
    We compute:
      - similarity of each JD term against:
        a) extracted resume skill terms
        b) resume lines (for best_line preview)
    Returns:
      semantic_matches: [{keyword, score (0..1), best_line}]
      semantic_hits: [keyword]
      semantic_misses: [keyword]
      semantic_coverage: 0..100
    """
    jd_terms = _unique_keep_order([_norm_term(x) for x in (jd_terms or []) if _norm_term(x)])
    if not jd_terms:
        return {
            "semantic_matches": [],
            "semantic_hits": [],
            "semantic_misses": [],
            "semantic_coverage": 0.0,
        }

    resume_terms = extract_skills(resume_text or "", max_terms=140)
    resume_lines = _clean_resume_lines(resume_text or "")

    if not resume_terms and not resume_lines:
        return {
            "semantic_matches": [],
            "semantic_hits": [],
            "semantic_misses": jd_terms,
            "semantic_coverage": 0.0,
        }

    model = _embedder()

    jd_emb = model.encode(jd_terms, convert_to_tensor=True, normalize_embeddings=True)

    # embeddings for terms (fast)
    term_emb = None
    if resume_terms:
        term_emb = model.encode(resume_terms, convert_to_tensor=True, normalize_embeddings=True)

    # embeddings for lines (for best_line)
    line_emb = None
    if resume_lines:
        line_emb = model.encode(resume_lines, convert_to_tensor=True, normalize_embeddings=True)

    matches: List[Dict[str, Any]] = []
    hits: List[str] = []
    misses: List[str] = []

    for i, term in enumerate(jd_terms):
        best_score = 0.0
        best_line = ""

        # 1) compare vs resume skill terms
        if term_emb is not None:
            sims_terms = util.cos_sim(jd_emb[i:i+1], term_emb)[0]
            bt = float(sims_terms.max())
            if bt > best_score:
                best_score = bt
                # we don't display term match text line, just score improvement

        # 2) compare vs resume lines (for context preview)
        if line_emb is not None:
            sims_lines = util.cos_sim(jd_emb[i:i+1], line_emb)[0]
            idx = int(sims_lines.argmax())
            bl = float(sims_lines[idx])
            if bl > best_score:
                best_score = bl
                best_line = resume_lines[idx]

        best_score = float(max(0.0, min(1.0, best_score)))

        if best_score >= float(threshold):
            hits.append(term)
        else:
            misses.append(term)

        matches.append(
            {
                "keyword": term,
                "score": best_score,           # 0..1
                "best_line": best_line or "",  # safe
            }
        )

    hits = _unique_keep_order(hits)
    misses = _unique_keep_order(misses)

    total = len(hits) + len(misses)
    coverage = (len(hits) / total) * 100.0 if total > 0 else 0.0
    coverage = float(round(coverage, 2))

    # return top matches for UI preview (highest score first)
    top_matches = sorted(matches, key=lambda x: x.get("score", 0.0), reverse=True)[:12]

    return {
        "semantic_matches": top_matches,
        "semantic_hits": hits,
        "semantic_misses": misses,
        "semantic_coverage": coverage,
    }
