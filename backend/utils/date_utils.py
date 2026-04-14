
import re
from datetime import datetime
from dateutil import parser as dateparser   # pip install python-dateutil
from typing import List, Tuple, Dict, Optional

_MONTH = r"""
    (?:
        Jan(?:uary)? | Feb(?:ruary)? | Mar(?:ch)?  | Apr(?:il)? |
        May          | Jun(?:e)?     | Jul(?:y)?    | Aug(?:ust)? |
        Sep(?:tember)?| Oct(?:ober)? | Nov(?:ember)?| Dec(?:ember)?
    )
"""
_DATE_TOKEN = rf"""
    (?:
        {_MONTH} [\s,\-]+ \d{{4}}     |   # June 2021 / Jun-2021
        \d{{1,2}} [\/\-] \d{{4}}      |   # 06/2021 or 06-2021
        \d{{4}}   [\/\-] \d{{1,2}}    |   # 2021/06 or 2021-06
        \d{{4}}                            # bare year — only valid inside a range
    )
"""

# Separator between start and end dates
_SEP = r"[\s]*(?:–|—|--|-)[\s]*|\s+to\s+|\s+until\s+"

# "Present", "Current", "Now", "Till date", "Ongoing"
_PRESENT = r"(?:present|current|now|today|till\s+date|to\s+date|ongoing)"

# Full date-range pattern:  <date>  <sep>  (<date> | "present")
_RANGE_RE = re.compile(
    rf"({_DATE_TOKEN})\s*(?:{_SEP})\s*(?:({_DATE_TOKEN})|({_PRESENT}))",
    re.IGNORECASE | re.VERBOSE,
)

# ── Education noise filter ─────────────────────────────────────────────────────
# If a job block contains these words it's likely an education entry, not a job.
_EDUCATION_KEYWORDS = re.compile(
    r"\b(b\.?tech|b\.?e\.?|b\.?sc|m\.?tech|m\.?sc|m\.?b\.?a|ph\.?d|bachelor|"
    r"master|degree|diploma|university|college|institute|school|cgpa|gpa|"
    r"10th|12th|ssc|hsc|intermediate|matriculation)\b",
    re.IGNORECASE,
)


_JOB_BLOCK_START = re.compile(
    r"""
    ^(?:
        [\w\s]+ \s+ (?:at|@|,|\|) \s+ [\w\s]+ |

        # Company name line (ALL CAPS or Title Case, short, no sentence punctuation)
        [A-Z][A-Z\s&,\.]{3,50}$                  |

        # Bullet / numbered entry
        [\•\-\*\d]\s+\w                           |

        # Title Case short line (likely a job title or company)
        (?:[A-Z][a-z]+\s+){1,5}[A-Z][a-z]+\s*$
    )
    """,
    re.VERBOSE,
)



def _parse_date(text: str) -> Optional[datetime]:
    try:
        return dateparser.parse(text.strip(), default=datetime(2000, 1, 1))
    except Exception:
        return None


def _extract_one_date_range(text: str) -> Optional[Tuple[datetime, datetime]]:
    today = datetime.today()

    for match in _RANGE_RE.finditer(text):
        start_str  = match.group(1)
        end_str    = match.group(2)   # None if "present" matched
        is_present = match.group(3)   # e.g. "present"

        start_date = _parse_date(start_str)
        end_date   = today if (is_present or not end_str) else _parse_date(end_str)
        if (
            start_date and end_date
            and start_date < end_date
            and start_date.year >= 1970
            and (end_date - start_date).days >= 30
        ):
            return (start_date, end_date)

    return None


def _split_into_job_blocks(text: str) -> List[str]:
    # Strategy A: blank-line split
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]

    # Strategy B: if only one big blob, try line-by-line splitting
    if len(blocks) <= 1:
        lines = text.split("\n")
        current: List[str] = []
        blocks = []

        for line in lines:
            # A new job starts if this line looks like a header AND we already
            # have content in the current block
            if _JOB_BLOCK_START.match(line.strip()) and current:
                block_text = "\n".join(current).strip()
                if block_text:
                    blocks.append(block_text)
                current = [line]
            else:
                current.append(line)

        if current:
            blocks.append("\n".join(current).strip())

    # Drop very short fragments (fewer than 10 chars — probably noise)
    return [b for b in blocks if len(b) >= 10]


def _is_education_block(text: str) -> bool:
    return bool(_EDUCATION_KEYWORDS.search(text))


def _merge_overlapping_ranges(
    ranges: List[Tuple[datetime, datetime]]
) -> List[Tuple[datetime, datetime]]:
    
    if not ranges:
        return []

    sorted_ranges = sorted(ranges, key=lambda r: r[0])
    merged = [sorted_ranges[0]]

    for start, end in sorted_ranges[1:]:
        prev_start, prev_end = merged[-1]
        if start <= prev_end:
            # Overlapping — stretch the current merged range if needed
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))

    return merged


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Public API
# ══════════════════════════════════════════════════════════════════════════════

def calculate_experience(experience_section_text: str) -> float:
    
    if not experience_section_text.strip():
        return 0.0

    job_blocks = _split_into_job_blocks(experience_section_text)
    work_ranges: List[Tuple[datetime, datetime]] = []

    for block in job_blocks:
        # Skip if this looks like an education entry
        if _is_education_block(block):
            continue

        date_range = _extract_one_date_range(block)
        if date_range:
            work_ranges.append(date_range)

    if not work_ranges:
        return 0.0

    merged = _merge_overlapping_ranges(work_ranges)
    total_days = sum((end - start).days for start, end in merged)

    return round(total_days / 365.25, 1)   # 365.25 handles leap years


def get_experience_breakdown(experience_section_text: str) -> List[Dict]:
    if not experience_section_text.strip():
        return []

    today = datetime.today()
    job_blocks = _split_into_job_blocks(experience_section_text)
    breakdown = []

    for block in job_blocks:
        if _is_education_block(block):
            continue

        date_range = _extract_one_date_range(block)
        if not date_range:
            continue

        start, end = date_range
        years = round((end - start).days / 365.25, 1)

        breakdown.append({
            "block_preview": block[:80].replace("\n", " ").strip() + "...",
            "start":         start.strftime("%Y-%m-%d"),
            "end":           end.strftime("%Y-%m-%d"),
            "years":         years,
            "is_current":    (end.date() == today.date()),
        })

    return breakdown


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — JD Experience Requirement Parser
# ══════════════════════════════════════════════════════════════════════════════

_WORD_TO_NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}

_NUM_EXP_RE = re.compile(
    r"(?:minimum\s+of?|at\s+least\s+of?|minimum|at\s+least)?\s*"
    r"(\d+(?:\.\d+)?)\s*(?:\+|plus|or\s+more)?\s*(?:to\s*\d+\s*)?"
    r"years?\s+(?:of\s+)?([\w\s]{0,40}?experience[\w\s]{0,30})",
    re.IGNORECASE,
)

_WORD_EXP_RE = re.compile(
    r"\b(" + "|".join(_WORD_TO_NUM.keys()) + r")\s*(?:\+|plus|or\s+more)?\s*"
    r"years?\s+(?:of\s+)?([\w\s]{0,40}?experience[\w\s]{0,30})",
    re.IGNORECASE,
)


def parse_required_experience(jd_text: str) -> tuple:
    results = []
    seen = set()

    for m in _NUM_EXP_RE.finditer(jd_text):
        years = float(m.group(1))
        context = m.group(2).strip().rstrip(".,;")
        key = (years, context[:30].lower())
        if key not in seen:
            seen.add(key)
            results.append({"years": years, "context": context})

    for m in _WORD_EXP_RE.finditer(jd_text):
        years = float(_WORD_TO_NUM[m.group(1).lower()])
        context = m.group(2).strip().rstrip(".,;")
        key = (years, context[:30].lower())
        if key not in seen:
            seen.add(key)
            results.append({"years": years, "context": context})

    results.sort(key=lambda x: x["years"])
    max_years = max((r["years"] for r in results), default=None)
    return max_years, results
