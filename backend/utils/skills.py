import re
import json
import sys
from pathlib import Path
from typing import List, Tuple, Dict

import numpy as np
from utils.embeddings import embed, pairwise_sim_matrix

# ── Load taxonomy ─────────────────────────────────────────────────────────────

_DATA = Path(__file__).parent.parent / "data"

try:
    with open(_DATA / "skills.json") as f:
        _TAXONOMY: dict = json.load(f)
    _ALL_SKILLS = sorted(
        {s.lower() for group in _TAXONOMY.values() for s in group},
        key=len, reverse=True
    )
except FileNotFoundError:
    _ALL_SKILLS = []

# Compile one regex from taxonomy (longest match first = greedy, no partial matches)
_SKILLS_RE = re.compile(
    r'(?<![a-z0-9])(' + '|'.join(re.escape(s) for s in _ALL_SKILLS) + r')(?![a-z0-9])',
    re.IGNORECASE
) if _ALL_SKILLS else None

# Tech symbols not easily in a word list: C++, C#, .NET, Node.js, etc.
_TECH_SYMBOL_RE = re.compile(
    r'\b(?:'
    r'[A-Za-z][A-Za-z0-9]*(?:\+\+|\#|\.js|\.NET|\.net|\.py|\.rb|\.go|\.ts)'
    r'|[A-Z]{2,8}'          # AWS, GCP, SQL, HTML, CSS, API …
    r')\b'
)

# Words that look like skills but are noise — articles, prepositions, common verbs
_NOISE = {
    "a", "an", "the", "and", "or", "of", "in", "for", "to", "with", "on",
    "at", "by", "as", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "can",
    "could", "should", "may", "might", "must", "shall", "not", "no",
    "we", "you", "they", "he", "she", "it", "i", "me", "us", "them",
    "this", "that", "these", "those", "each", "all", "any", "both",
    "such", "own", "per", "via", "etc", "also", "just", "only", "very",
    "more", "most", "some", "many", "much", "few", "new", "good", "best",
    "strong", "key", "role", "team", "work", "world", "real", "based",
    "related", "relevant", "required", "preferred", "including", "using",
    "build", "built", "develop", "developed", "design", "designed",
    "manage", "managed", "create", "created", "write", "written",
    "use", "used", "make", "made", "ensure", "maintain", "provide",
    "overview", "responsibilities", "requirements", "candidate", "candidates",
    "bonus", "points", "weight", "criteria", "evaluation", "statement",
    "education", "degree", "bachelor", "master", "field", "equivalent",
    "practical", "hands", "on", "cross", "functional", "driven",
    "clean", "efficient", "scalable", "testable", "reusable", "complex",
    "existing", "current", "multiple", "various", "different", "specific",
    "following", "above", "below", "within", "across", "between",
}

# Minimum character length for a skill to be valid
_MIN_LEN = 3


def extract_skills(text: str) -> List[str]:
    """
    Extract skills from text.
    Returns sorted, deduplicated, noise-free list of lowercase skill strings.
    """
    if not text.strip():
        return []

    found = set()

    # Layer 1: taxonomy match (most reliable)
    if _SKILLS_RE:
        for m in _SKILLS_RE.finditer(text):
            skill = m.group().lower().strip()
            if skill not in _NOISE and len(skill) >= _MIN_LEN:
                found.add(skill)

    # Layer 2: tech symbols (C++, AWS, HTML5, etc.)
    for m in _TECH_SYMBOL_RE.finditer(text):
        skill = m.group().lower().strip()
        if skill not in _NOISE and len(skill) >= _MIN_LEN:
            found.add(skill)

    return sorted(found)


def skill_match_score(
    resume_skills: List[str],
    jd_skills: List[str],
    threshold: float = 0.80,   # tighter threshold = fewer false positives
) -> Tuple[float, List[str], List[str]]:
    """
    Match resume skills to JD skills using embedding cosine similarity.
    Returns (score 0-1, matched_jd_skills, unmatched_jd_skills).
    """
    if not jd_skills:
        return 1.0, [], []
    if not resume_skills:
        return 0.0, [], list(jd_skills)

    all_terms = resume_skills + jd_skills
    all_vecs  = embed(all_terms)

    n_res    = len(resume_skills)
    res_vecs = all_vecs[:n_res]
    jd_vecs  = all_vecs[n_res:]

    sim_matrix = pairwise_sim_matrix(jd_vecs, res_vecs)

    matched:   List[str] = []
    unmatched: List[str] = []

    for i, jd_skill in enumerate(jd_skills):
        best = float(sim_matrix[i].max()) if sim_matrix.shape[1] > 0 else 0.0
        (matched if best >= threshold else unmatched).append(jd_skill)

    score = len(matched) / max(len(jd_skills), 1)
    return round(score, 4), matched, unmatched


def categorize_skills(skills: List[str]) -> Dict[str, List[str]]:
    """
    Group a list of skills by their taxonomy category.
    Skills not found in any category go into 'other'.
    """
    result: Dict[str, List[str]] = {}
    skill_set = set(skills)

    for category, items in _TAXONOMY.items():
        matched = sorted(s for s in items if s.lower() in skill_set)
        if matched:
            result[category] = matched

    # anything not in taxonomy
    categorized = {s for group in result.values() for s in group}
    other = sorted(skill_set - {s.lower() for s in categorized})
    if other:
        result["other"] = other

    return result
