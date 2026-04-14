"""
projects.py — Extract and score projects from resume text.

Improvements:
  - Better title detection (handles "Project Name | Tech Stack" formats)
  - Per-project JD relevance score via embeddings
  - JD-matched skills highlighted per project
  - Duration extraction from project text
  - Team size / role detection
  - Richer impact detection (numbers, percentages, action verbs)
"""

import re
from typing import Dict, List, Tuple

from utils.skills import extract_skills
from utils.embeddings import text_similarity, embed, pairwise_sim_matrix

# ── Impact detection ──────────────────────────────────────────────────────────

_IMPACT_RE = re.compile(
    r"""
    \d+[\.,]?\d*\s*
    (%|percent|x\b|users?|ms\b|seconds?|minutes?|hours?|
     requests?|rpm|rps|k\b|million|billion|lines?|commits?|
     downloads?|stars?|forks?|clients?|customers?|records?)
    |
    (increased|reduced|improved|optimized|boosted|decreased|cut|
     saved|achieved|delivered|grew|scaled|shipped|launched|
     automated|eliminated|accelerated|enhanced|streamlined)
    \s[\w\s]{0,25}\d+
    """,
    re.VERBOSE | re.IGNORECASE,
)

# ── Duration extraction ───────────────────────────────────────────────────────

_DURATION_RE = re.compile(
    r'\b(\d+)\s*(week|month|year)s?\b'
    r'|\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{4}'
    r'\s*[-–]\s*'
    r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{4}\b',
    re.IGNORECASE
)

# ── Team / role detection ─────────────────────────────────────────────────────

_ROLE_RE = re.compile(
    r'\b(team\s+of\s+\d+|solo|individual|group\s+of\s+\d+|'
    r'lead|led|built\s+alone|collaborated\s+with\s+\d+)\b',
    re.IGNORECASE
)

# ── Project block splitter ────────────────────────────────────────────────────

def _split_project_blocks(text: str) -> List[str]:
    # Try blank-line split first
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if len(b.strip()) > 20]
    if len(blocks) > 1:
        return blocks

    # Numbered list: "1. Project" or "1) Project"
    numbered = re.split(r"(?=\b\d+[.)]\s+[A-Z])", text.strip())
    if len(numbered) > 1:
        return [b.strip() for b in numbered if len(b.strip()) > 20]

    # Bullet list
    bulleted = re.split(r"\n(?=[•\-\*►▪]\s+)", text.strip())
    if len(bulleted) > 1:
        return [b.strip() for b in bulleted if len(b.strip()) > 20]

    # Title-like lines (short, Title Case or ALL CAPS) as block separators
    lines = text.splitlines()
    blocks, current = [], []
    for line in lines:
        stripped = line.strip()
        words = stripped.split()
        is_title = (
            stripped
            and len(words) <= 8
            and (stripped.isupper() or all(w[0].isupper() for w in words if w))
            and not stripped.endswith(".")
        )
        if is_title and current:
            blocks.append("\n".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        blocks.append("\n".join(current))

    return [b.strip() for b in blocks if len(b.strip()) > 20] or ([text.strip()] if len(text.strip()) > 20 else [])


# ── Title extraction ──────────────────────────────────────────────────────────

def _extract_title(lines: List[str]) -> Tuple[str, int]:
    """
    Returns (title, lines_consumed).
    Handles formats:
      - "Project Name"
      - "Project Name | React, Node.js"
      - "Project Name — Description"
      - "Role: Project Name"
    """
    if not lines:
        return "Untitled Project", 0

    first = lines[0].strip().strip("•·-–—*►▪")

    # "Role: Title" pattern
    role_match = re.match(r'^(?:project|title|name)\s*[:\-]\s*(.+)', first, re.IGNORECASE)
    if role_match:
        return role_match.group(1).strip(), 1

    # "Title | Tech" or "Title — desc" — take only the part before separator
    sep_match = re.match(r'^([^|–—]{3,60})\s*[|–—]', first)
    if sep_match:
        return sep_match.group(1).strip(), 1

    # Short first line = title
    if len(first.split()) <= 10:
        return first, 1

    # Long first line — truncate
    return " ".join(first.split()[:8]) + "…", 0


# ── Per-project JD relevance ──────────────────────────────────────────────────

def _project_jd_relevance(project_text: str, jd_text: str) -> float:
    """Returns 0-100 relevance of a single project to the JD."""
    if not project_text.strip() or not jd_text.strip():
        return 0.0
    return round(text_similarity(project_text, jd_text) * 100, 1)


# ── Main extractor ────────────────────────────────────────────────────────────

def extract_projects(text: str, jd_text: str = "") -> List[Dict]:
    if not text.strip():
        return []

    jd_skills = extract_skills(jd_text) if jd_text else []
    projects  = []

    for block in _split_project_blocks(text):
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue

        title, consumed = _extract_title(lines)
        body_lines      = lines[consumed:]
        description     = " ".join(body_lines)[:600] if body_lines else title

        # Skills in this project
        tech_used = extract_skills(block)[:20]

        # Which of those skills are also in the JD
        jd_matched_tech = [t for t in tech_used if t in set(jd_skills)]

        # Impact sentences
        impact = [
            s.strip()
            for s in re.split(r"(?<=[.!?])\s+", description)
            if _IMPACT_RE.search(s)
        ]

        # Duration
        dur_match = _DURATION_RE.search(block)
        duration  = dur_match.group(0).strip() if dur_match else None

        # Team/role
        role_match = _ROLE_RE.search(block)
        team_info  = role_match.group(0).strip() if role_match else None

        # JD relevance score for this project
        relevance = _project_jd_relevance(block, jd_text) if jd_text else None

        projects.append({
            "title":           title,
            "description":     description,
            "tech_used":       tech_used,
            "jd_matched_tech": jd_matched_tech,
            "impact":          impact,
            "duration":        duration,
            "team_info":       team_info,
            "jd_relevance":    relevance,
        })

    return projects


# ── Scoring ───────────────────────────────────────────────────────────────────

def _summarize_projects(projects: List[Dict]) -> str:
    parts = []
    for p in projects:
        parts.extend([p["title"], p["description"]])
        parts.extend(p.get("tech_used", []))
        parts.extend(p.get("impact", []))
    return " ".join(filter(None, parts))


def score_projects(
    projects: List[Dict],
    jd_text: str,
    jd_mentions_projects: bool = True,
) -> Tuple[float, str]:
    if not jd_mentions_projects:
        return 100.0, "Not required by JD — full marks awarded"

    if not projects:
        return 0.0, "No projects detected — JD appears to require them"

    # Overall semantic relevance
    blob = _summarize_projects(projects)
    sim  = text_similarity(blob, jd_text)

    # Per-project relevance average
    relevances = [p["jd_relevance"] for p in projects if p.get("jd_relevance") is not None]
    avg_rel    = sum(relevances) / len(relevances) if relevances else sim * 100

    # Scoring components
    relevance_score = min(avg_rel * 0.70, 70.0)          # 0-70 pts
    count_score     = min(len(projects) * 10, 20.0)       # 0-20 pts (2+ projects = good)
    impact_score    = 10.0 if any(p.get("impact") for p in projects) else 0.0  # 0-10 pts

    score = min(relevance_score + count_score + impact_score, 100.0)

    explanation = (
        f"{len(projects)} project(s) · "
        f"avg JD relevance {avg_rel:.0f}% · "
        f"{'impact metrics found' if impact_score else 'no quantified impact'}"
    )
    return round(score, 1), explanation
