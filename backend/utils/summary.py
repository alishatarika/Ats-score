import re
from typing import Any, Dict, List, Optional

from utils.embeddings import text_similarity


_ROLE_RE = re.compile(
    r"\b(?:software|data|machine\s+learning|ml|ai|backend|front.?end|"
    r"full.?stack|devops|cloud|security|product|project|business|marketing|"
    r"hr|human\s+resources|financial|finance|senior|junior|mid.?level|"
    r"lead|principal|staff|associate|executive)\s+"
    r"(?:engineer|developer|analyst|scientist|manager|architect|consultant|"
    r"specialist|designer|administrator|officer|director|head|intern)\b",
    re.IGNORECASE,
)

_EXP_RE = re.compile(
    r"(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:experience|exp)",
    re.IGNORECASE,
)


def extract_summary_insights(summary_text: str, jd_text: str) -> Dict[str, Any]:
    raw = summary_text.strip()

    if not raw:
        return {
            "raw_text":             "",
            "key_points":           [],
            "stated_role":          None,
            "experience_mentioned": None,
            "relevance_to_jd":      0.0,
            "quality_score":        0,
            "suggestions": [
                "Add a professional summary section — ATS systems weight it.",
                "Mention your target role and total years of experience.",
                "Include 2-3 key skills that directly match the job description.",
            ],
        }

    sentences  = re.split(r"(?<=[.!?])\s+", raw)
    key_points = [s.strip() for s in sentences if len(s.strip()) > 20][:5]

    role_m    = _ROLE_RE.search(raw)
    stated_role: Optional[str] = role_m.group(0) if role_m else None

    exp_m = _EXP_RE.search(raw)
    experience_mentioned: Optional[int] = int(exp_m.group(1)) if exp_m else None

    # Embedding-based relevance to JD (not keyword overlap)
    relevance = text_similarity(raw, jd_text) if jd_text.strip() else 0.0
    relevance = min(max(relevance, 0.0), 1.0)

    # ── Quality scoring ───────────────────────────────────────────────────────
    word_count = len(raw.split())
    quality    = 0

    # Length bonus
    if word_count >= 40:
        quality += 25
    elif word_count >= 20:
        quality += 15
    else:
        quality += 5

    if stated_role:
        quality += 20

    if experience_mentioned:
        quality += 15

    # JD relevance → 0-30 pts
    quality += int(relevance * 30)

    # Multiple clear sentences
    if len(key_points) >= 2:
        quality += 10

    quality = min(quality, 100)

    # ── Improvement suggestions ───────────────────────────────────────────────
    suggestions: List[str] = []
    if word_count < 40:
        suggestions.append(
            "Expand your summary to at least 40 words — most ATS parsers reward longer summaries."
        )
    if not stated_role:
        suggestions.append(
            "State your target role explicitly (e.g., 'Senior Backend Engineer')."
        )
    if not experience_mentioned:
        suggestions.append(
            "Mention total years of experience (e.g., '4+ years of experience in…')."
        )
    if relevance < 0.20:
        suggestions.append(
            "Mirror more language from the job description — your summary has low semantic overlap with the JD."
        )

    return {
        "raw_text":             raw,
        "key_points":           key_points,
        "stated_role":          stated_role,
        "experience_mentioned": experience_mentioned,
        "relevance_to_jd":      round(relevance, 3),
        "quality_score":        quality,
        "suggestions":          suggestions,
    }