"""
certifications.py — Extract and score certifications from resume text.

Three-layer extraction:
  1. Dataset match  — 200+ known certs from data/certifications.json
  2. Phrase pattern — catches "Certified X", "X Certification", "X Certificate"
  3. Section harvest — every clean line inside the certifications section

Scoring:
  - JD requires certs  → score based on how many JD certs the resume has
  - JD doesn't require → full 100 (no penalty)
"""

import re
import json
from pathlib import Path
from typing import List, Tuple

import numpy as np
from utils.embeddings import embed, pairwise_sim_matrix

# ── Load dataset ──────────────────────────────────────────────────────────────

_DATA = Path(__file__).parent.parent / "data"

try:
    with open(_DATA / "certifications.json") as f:
        _CERT_DATASET: dict = json.load(f)
    # Flatten all certs into one list, sorted longest first
    _ALL_CERTS: List[str] = sorted(
        {c for group in _CERT_DATASET.values() for c in group},
        key=len, reverse=True
    )
except FileNotFoundError:
    _ALL_CERTS = []

# Compile dataset regex (word-boundary aware, case-insensitive)
_DATASET_RE = re.compile(
    r'(?<![a-z])(' + '|'.join(re.escape(c) for c in _ALL_CERTS) + r')(?![a-z])',
    re.IGNORECASE
) if _ALL_CERTS else None

# Generic phrase pattern — catches anything the dataset might miss
_PHRASE_RE = re.compile(
    r'\b(?:'
    r'certified\s+[\w\s\-/]{2,50}|'          # "Certified Business Analyst"
    r'[\w\s\-/]{2,50}\s+certification|'       # "PMP Certification"
    r'[\w\s\-/]{2,50}\s+certificate|'         # "AWS Certificate"
    r'[\w\s\-/]{2,50}\s+certified|'           # "AWS Certified"
    r'[\w\s\-/]{2,50}\s+credential|'          # "Professional Credential"
    r'[\w\s\-/]{2,50}\s+nanodegree|'          # "Udacity Nanodegree"
    r'[\w\s\-/]{2,50}\s+specialization'       # "Coursera Specialization"
    r')\b',
    re.IGNORECASE
)

# Noise filter — phrases that match the pattern but aren't real certs
_NOISE_PHRASES = {
    "the certified", "a certified", "an certified",
    "not certified", "get certified", "become certified",
    "certification required", "certification preferred",
    "certifications required", "certifications preferred",
    "relevant certification", "relevant certifications",
    "any certification", "valid certification",
}

# Lines to skip in section harvest
_SKIP_LINE_RE = re.compile(
    r'^(education|experience|skills|summary|projects|work|employment|'
    r'jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|\d{4})',
    re.IGNORECASE
)


def extract_certifications(resume_text: str, cert_section: str = "") -> List[str]:
    """
    Extract all certifications from resume text.

    Args:
        resume_text:  Full resume text (for dataset + phrase matching)
        cert_section: Text of the certifications section only (for line harvest)

    Returns:
        Sorted, deduplicated list of certification strings.
    """
    found: set = set()

    # Layer 1: dataset match on full resume
    if _DATASET_RE:
        for m in _DATASET_RE.finditer(resume_text):
            cert = m.group().strip()
            if len(cert) >= 2:
                found.add(cert)

    # Layer 2: generic phrase pattern on full resume
    for m in _PHRASE_RE.finditer(resume_text):
        phrase = m.group().strip()
        phrase_lower = phrase.lower()
        if (
            4 < len(phrase) < 100
            and phrase_lower not in _NOISE_PHRASES
            and not re.search(r'\b(the|a|an)\s*$', phrase_lower)
        ):
            found.add(phrase)

    # Layer 3: every clean line in the cert section
    if cert_section:
        for line in cert_section.splitlines():
            line = line.strip().strip("•·-–—*►▪◆▸→")
            if (
                5 < len(line) < 150
                and not _SKIP_LINE_RE.match(line)
                and not line.isdigit()
            ):
                found.add(line)

    return sorted(found, key=str.lower)


def match_certs_to_jd(
    resume_certs: List[str],
    jd_text: str,
) -> Tuple[List[str], List[str]]:
    """
    Cross-match resume certs against JD using:
      1. Substring match (fast, exact)
      2. Embedding similarity (catches paraphrases)

    Returns:
        (matched_certs, jd_required_certs)
    """
    # Extract what the JD requires
    jd_certs = extract_certifications(jd_text)

    if not jd_certs or not resume_certs:
        return [], jd_certs

    matched = set()

    # Pass 1: substring match
    for rc in resume_certs:
        for jc in jd_certs:
            if rc.lower() in jc.lower() or jc.lower() in rc.lower():
                matched.add(rc)
                break

    # Pass 2: embedding similarity for remaining unmatched
    unmatched_resume = [c for c in resume_certs if c not in matched]
    if unmatched_resume and jd_certs:
        try:
            all_vecs = embed(unmatched_resume + jd_certs)
            res_vecs = all_vecs[:len(unmatched_resume)]
            jd_vecs  = all_vecs[len(unmatched_resume):]
            sim      = pairwise_sim_matrix(res_vecs, jd_vecs)  # (n_resume, n_jd)
            for i, rc in enumerate(unmatched_resume):
                if sim[i].max() >= 0.82:
                    matched.add(rc)
        except Exception:
            pass

    return sorted(matched), jd_certs


def score_certifications(
    resume_certs: List[str],
    jd_text: str,
    jd_mentions_certs: bool = True,
) -> Tuple[float, str]:
    """
    Score certifications 0-100.

    Rules:
      - JD doesn't mention certs → 100 (full marks, no penalty)
      - JD mentions certs + resume has matching ones → high score
      - JD mentions certs + resume has none → 0
    """
    if not jd_mentions_certs:
        return 100.0, "Not required by JD — full marks awarded"

    if not resume_certs:
        return 0.0, "No certifications found — JD appears to require them"

    matched, jd_certs = match_certs_to_jd(resume_certs, jd_text)

    if not jd_certs:
        # JD signals certs are needed but doesn't name specific ones
        # Score based on having any certs at all
        score = min(len(resume_certs) * 20, 100.0)
        return round(score, 1), f"{len(resume_certs)} cert(s) found — JD requires certs but doesn't specify which"

    score = round(len(matched) / len(jd_certs) * 100, 1)
    explanation = f"{len(matched)}/{len(jd_certs)} required cert(s) matched"
    return score, explanation
