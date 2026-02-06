from __future__ import annotations
import re
from typing import List, Dict, Any, Tuple

from keybert import KeyBERT
from sentence_transformers import SentenceTransformer, util

_kw_model = None
_emb_model = None

def _norm(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9+#.\-/ ]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s

def get_models() -> Tuple[KeyBERT, SentenceTransformer]:
    global _kw_model, _emb_model
    if _emb_model is None:
        _emb_model = SentenceTransformer("all-MiniLM-L6-v2")
    if _kw_model is None:
        _kw_model = KeyBERT(model=_emb_model)
    return _kw_model, _emb_model

def extract_jd_keywords(job_description: str, top_n: int = 25) -> List[str]:
    jd = _norm(job_description)
    if not jd:
        return []

    kw_model, _ = get_models()
    phrases = kw_model.extract_keywords(
        jd,
        keyphrase_ngram_range=(1, 3),
        stop_words="english",
        top_n=top_n,
        use_mmr=True,
        diversity=0.5,
    )
    # keep only phrase text
    kws = []
    for p, _score in phrases:
        p = _norm(p)
        if len(p) >= 2 and p not in kws:
            kws.append(p)
    return kws

def keyword_match(resume_text: str, jd_keywords: List[str]) -> Dict[str, Any]:
    rt = _norm(resume_text)
    present = []
    missing = []

    for k in jd_keywords:
        if k and re.search(rf"\b{re.escape(k)}\b", rt):
            present.append(k)
        else:
            missing.append(k)

    coverage = 0.0 if not jd_keywords else len(present) / len(jd_keywords)

    return {
        "present": present,
        "missing": missing,
        "coverage": round(coverage, 3),
    }

def semantic_match(resume_text: str, jd_keywords: List[str], threshold: float = 0.58) -> Dict[str, Any]:
    _, emb_model = get_models()
    resume_lines = [ln.strip() for ln in resume_text.splitlines() if ln.strip()]
    resume_lines = resume_lines[:220]  # limit

    if not resume_lines or not jd_keywords:
        return {"semantic_hits": [], "semantic_misses": jd_keywords}

    line_emb = emb_model.encode(resume_lines, convert_to_tensor=True, normalize_embeddings=True)
    kw_emb = emb_model.encode(jd_keywords, convert_to_tensor=True, normalize_embeddings=True)

    sims = util.cos_sim(kw_emb, line_emb)  # [kws, lines]
    semantic_hits = []
    semantic_misses = []

    for i, kw in enumerate(jd_keywords):
        best_score, best_idx = float(sims[i].max()), int(sims[i].argmax())
        if best_score >= threshold:
            semantic_hits.append({
                "keyword": kw,
                "best_line": resume_lines[best_idx][:180],
                "score": round(best_score, 3),
            })
        else:
            semantic_misses.append(kw)

    return {"semantic_hits": semantic_hits, "semantic_misses": semantic_misses}
