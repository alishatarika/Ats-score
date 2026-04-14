import re
from typing import Dict, List, Optional

# ── Section vocabulary (scored, not pattern-matched as single-regex) ──────────
SECTION_VOCAB: Dict[str, List[str]] = {
    "summary": [
        "summary", "profile", "objective", "about me", "career objective",
        "career summary", "personal statement", "professional statement",
        "overview", "executive summary", "personal profile", "biography", "bio",
        "professional summary", "professional profile",
    ],
    "skills": [
        "skills", "competencies", "competency", "expertise", "technologies",
        "tools", "core skills", "key skills", "technical expertise",
        "programming skills", "it skills", "languages", "frameworks",
        "technical proficiencies", "areas of expertise", "skill set",
        "tech stack", "technical skills", "tools and technologies",
    ],
    "experience": [
        "experience", "work experience", "professional experience",
        "employment", "work history", "employment history", "career history",
        "positions", "internship experience", "internships", "background",
        "professional background", "relevant experience", "industry experience",
    ],
    "education": [
        "education", "academic background", "qualifications", "academic history",
        "academic qualifications", "degrees", "training", "schooling",
        "university", "college", "educational background",
    ],
    "projects": [
        "projects", "personal projects", "academic projects", "key projects",
        "major projects", "notable projects", "selected projects",
        "relevant projects", "portfolio", "case studies", "project work",
        "side projects", "open source", "open-source contributions",
    ],
    "certifications": [
        "certifications", "certificates", "certification", "certificate",
        "licenses", "credentials", "accreditations", "professional development",
        "training and certifications", "courses and certifications",
        "professional certifications", "courses", "online courses",
    ],
    "achievements": [
        "achievements", "awards", "honors", "honours", "accomplishments",
        "recognition", "distinctions", "accolades", "prizes",
        "scholarships", "fellowships", "publications", "patents", "research",
    ],
}

# Flat lookup: vocab term → section key
_TERM_TO_SECTION: Dict[str, str] = {}
for _sec, _terms in SECTION_VOCAB.items():
    for _term in _terms:
        _TERM_TO_SECTION[_term.lower()] = _sec


def _detect_section_header(line: str) -> Optional[str]:
    stripped = line.strip()
    if not stripped or len(stripped) < 3:
        return None

    # Too long to be a header
    words = stripped.split()
    if len(words) > 7:
        return None

    # Clean decorative characters from edges
    cleaned = re.sub(r"^[\s\-_|•*#=►▶→>]+", "", stripped)
    cleaned = re.sub(r"[\s:–—\-_|•*#=]+$", "", cleaned).strip()

    if not cleaned:
        return None

    normalized = cleaned.lower()

    # Direct vocabulary lookup
    if normalized in _TERM_TO_SECTION:
        return _TERM_TO_SECTION[normalized]

    # Partial match: check if any known term is contained in this line
    for term, section in _TERM_TO_SECTION.items():
        if term in normalized and len(term) >= 5:
            return section

    # Signal: ALL CAPS short line
    if cleaned.isupper() and 3 <= len(cleaned.split()) <= 5:
        for term, section in _TERM_TO_SECTION.items():
            if term in normalized:
                return section

    return None


def extract_sections(text: str) -> Dict[str, str]:
    sections: Dict[str, List[str]] = {"header": []}
    current = "header"

    for line in text.split("\n"):
        detected = _detect_section_header(line)
        if detected:
            current = detected
            if current not in sections:
                sections[current] = []
        else:
            sections[current].append(line)

    return {k: "\n".join(v).strip() for k, v in sections.items() if v}
