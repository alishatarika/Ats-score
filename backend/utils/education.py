"""
education.py — Structural education extraction + embedding-based scoring.

Degree name patterns are structural facts (finite, standardized worldwide).
Field-of-study / institution relevance is scored via embedding cosine similarity
with the JD — no hardcoded subject-matter lists.

If JD does not mention education requirements → extra-credit mode.
"""

import re
from typing import Dict, List, Optional, Tuple

from utils.embeddings import text_similarity, embed, pairwise_sim_matrix
import numpy as np


# ── Degree patterns (structural — these are standardized global degree names) ─
_DEGREE_PATTERNS: List[Tuple[str, str]] = [
    (r"\bb\.?\s*tech(?:nology)?\b",            "B.Tech"),
    (r"\bb\.?\s*e\.?\b",                        "B.E."),
    (r"\bb\.?\s*sc\.?\b",                       "B.Sc"),
    (r"\bb\.?\s*com\.?\b",                      "B.Com"),
    (r"\bb\.?\s*a(?:rts)?\b",                   "B.A."),
    (r"\bm\.?\s*tech(?:nology)?\b",             "M.Tech"),
    (r"\bm\.?\s*e\.?\b",                        "M.E."),
    (r"\bm\.?\s*sc\.?\b",                       "M.Sc"),
    (r"\bm\.?\s*b\.?\s*a\.?\b",                 "MBA"),
    (r"\bm\.?\s*a(?:rts)?\b",                   "M.A."),
    (r"\bm\.?\s*com\.?\b",                      "M.Com"),
    (r"\bph\.?\s*d\.?\b",                       "PhD"),
    (r"\bd\.?\s*phil\.?\b",                     "D.Phil"),
    (r"\bbachelor(?:'s)?(?:\s+of\s+[\w\s]{2,40})?\b", "Bachelor's"),
    (r"\bmaster(?:'s)?(?:\s+of\s+[\w\s]{2,40})?\b",   "Master's"),
    (r"\bdoctor(?:ate|al)?(?:\s+of\s+[\w\s]{2,40})?\b", "Doctorate"),
    (r"\bassociate(?:'s)?(?:\s+(?:of|in)\s+[\w\s]{2,40})?\b", "Associate's"),
    (r"\bdiploma(?:\s+in\s+[\w\s]{2,40})?\b",   "Diploma"),
    (r"\bcertificate(?:\s+in\s+[\w\s]{2,40})?\b", "Certificate"),
    (r"\bhigh\s+school\b",                      "High School"),
    (r"\bhigher\s+secondary\b",                 "Higher Secondary"),
    (r"\b12th\b|\bhsc\b|\bintermediate\b",       "12th / HSC"),
    (r"\b10th\b|\bssc\b|\bmatriculation\b",      "10th / SSC"),
]

_COMPILED_DEGREES = [
    (re.compile(pat, re.IGNORECASE), label)
    for pat, label in _DEGREE_PATTERNS
]

_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
_GPA_RE  = re.compile(
    r"(?:cgpa|gpa|grade\s+point\s+average|percentage|marks?)\s*[:\-]?\s*"
    r"([\d]+(?:\.[\d]+)?)\s*(?:/\s*[\d]+(?:\.[\d]+)?)?",
    re.IGNORECASE,
)
_INSTITUTION_RE = re.compile(
    r"\b(?:university|college|institute(?:\s+of\s+technology)?|school|"
    r"academy|polytechnic|iit|nit|bits|iiit|iim)\b",
    re.IGNORECASE,
)

# Ordinal degree quality tier (standardised educational hierarchy — not a DB)
_DEGREE_TIER: Dict[str, int] = {
    "PhD": 5,       "D.Phil": 5,     "Doctorate": 5,
    "Master's": 4,  "M.Tech": 4,     "M.E.": 4,  "M.Sc": 4,
    "MBA": 4,       "M.A.": 4,       "M.Com": 4,
    "Bachelor's": 3,"B.Tech": 3,     "B.E.": 3,  "B.Sc": 3,
    "B.Com": 3,     "B.A.": 3,
    "Associate's": 2, "Diploma": 2,
    "12th / HSC": 1, "Higher Secondary": 1, "Certificate": 1,
    "10th / SSC": 0, "High School": 0,
}


def _detect_degree(text: str) -> Optional[Tuple[str, int, int]]:
    for compiled, label in _COMPILED_DEGREES:
        m = compiled.search(text)
        if m:
            return label, m.start(), m.end()
    return None


def extract_education(text: str) -> List[Dict]:
    """
    Extract structured education entries from section text.
    Returns list of dicts: degree, field_of_study, institution, years, gpa.
    """
    if not text.strip():
        return []

    raw_blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]

    if len(raw_blocks) >= 2:
        blocks = raw_blocks
    else:
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        blocks, current_block = [], []
        for line in lines:
            if _detect_degree(line) and current_block:
                blocks.append("\n".join(current_block))
                current_block = [line]
            else:
                current_block.append(line)
        if current_block:
            blocks.append("\n".join(current_block))

    entries: List[Dict] = []

    for block in blocks:
        result = _detect_degree(block)
        if not result:
            continue
        degree_label, _, deg_end = result

        # Field of study: text immediately after degree token
        after  = block[deg_end:].strip()
        fos_m  = re.match(
            r"(?:in|of|–|-|:)?\s*([A-Za-z\s&/]{3,60}?)(?:\n|,|\d{4}|$)", after
        )
        field_of_study: Optional[str] = None
        if fos_m:
            candidate = fos_m.group(1).strip()
            stopwords = {"the", "and", "of", "in", "at", "to", "from"}
            words = [w for w in candidate.lower().split() if w not in stopwords]
            if candidate and not _YEAR_RE.match(candidate) and len(words) >= 1:
                field_of_study = candidate

        # Institution: line with institution keyword
        institution: Optional[str] = None
        for line in block.split("\n"):
            if _INSTITUTION_RE.search(line):
                institution = line.strip()
                break
        if not institution:
            for line in block.split("\n"):
                s = line.strip()
                if s and not _detect_degree(s) and len(s) > 5:
                    institution = s
                    break

        # Year range
        years_found = _YEAR_RE.findall(block)
        year_range: Optional[str] = None
        if len(years_found) >= 2:
            year_range = f"{years_found[0]} – {years_found[-1]}"
        elif len(years_found) == 1:
            year_range = years_found[0]

        gpa_m = _GPA_RE.search(block)
        gpa: Optional[str] = gpa_m.group(0).strip() if gpa_m else None

        entries.append({
            "degree":         degree_label,
            "field_of_study": field_of_study,
            "institution":    institution,
            "years":          year_range,
            "gpa":            gpa,
        })

    # Deduplicate by (degree, institution)
    seen_keys: set = set()
    deduped = []
    for e in entries:
        key = (e["degree"], e.get("institution", ""))
        if key not in seen_keys:
            seen_keys.add(key)
            deduped.append(e)

    return deduped


def score_education(
    entries: List[Dict],
    jd_text: str,
    jd_mentions_education: bool = True,
) -> Tuple[float, str]:
    """
    Score education section out of 100.

    Factors:
    - Highest degree tier (50 pts, uses standard educational hierarchy)
    - Field-of-study relevance to JD (30 pts, embedding cosine similarity)
    - Completeness of entries — institution + years present (20 pts)

    If jd_mentions_education = False → extra-credit mode (no penalty for absence).
    """
    if not jd_mentions_education:
        if not entries:
            return 50.0, "Education not required by JD — neutral score (no penalty)."
        max_tier = max((_DEGREE_TIER.get(e["degree"], 2) for e in entries), default=0)
        bonus = round(40.0 + max_tier * 3, 1)
        return min(bonus, 75.0), (
            f"Bonus: {len(entries)} education entry/entries (not required by JD)."
        )

    if not entries:
        return 20.0, "No education entries detected. ATS may flag this."

    max_tier     = max((_DEGREE_TIER.get(e["degree"], 2) for e in entries), default=0)
    degree_score = min((max_tier / 5) * 50, 50.0)

    # Field-of-study relevance via embedding (no keyword lists needed)
    all_fields = " ".join(
        e.get("field_of_study", "") or "" for e in entries
    ).strip()
    field_relevance = text_similarity(all_fields, jd_text) if all_fields else 0.0
    field_score     = min(field_relevance * 30, 30.0)

    # Completeness
    complete_count    = sum(1 for e in entries if e.get("institution") and e.get("years"))
    completeness_score = min(complete_count * 10, 20.0)

    score = min(degree_score + field_score + completeness_score, 100.0)
    explanation = (
        f"{len(entries)} education entry/entries. "
        f"Highest degree tier: {max_tier}/5. "
        f"Field relevance (embedding): {field_relevance:.2f}."
    )
    return round(score, 1), explanation