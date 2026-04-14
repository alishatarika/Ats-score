
from pydantic import BaseModel
from typing import Dict, List, Optional


class ProjectInfo(BaseModel):
    title:           str
    description:     str
    tech_used:       List[str]
    jd_matched_tech: List[str]        # skills in this project that JD also wants
    impact:          List[str]
    duration:        Optional[str] = None
    team_info:       Optional[str] = None
    jd_relevance:    Optional[float] = None   # 0-100 relevance to JD


class EducationInfo(BaseModel):
    degree:         str
    field_of_study: Optional[str] = None
    institution:    Optional[str] = None
    years:          Optional[str] = None
    gpa:            Optional[str] = None


class SummaryInsights(BaseModel):
    raw_text:             str
    key_points:           List[str]
    stated_role:          Optional[str]
    experience_mentioned: Optional[int]
    relevance_to_jd:      float   # embedding cosine similarity 0-1
    quality_score:        int     # 0-100
    suggestions:          List[str]


class ATSAnalysis(BaseModel):
    # ── Core score ────────────────────────────────────────────────────────────
    match_score:     float   # final weighted score 0-100
    grade:           str     # Excellent / Good / Fair / Poor
    overall_summary: str

    # ── Score breakdown ───────────────────────────────────────────────────────
    score_breakdown: Dict[str, float]   # per-section weighted contribution
    section_scores:  Dict[str, float]   # per-section raw score out of 100

    # ── JD-driven config ──────────────────────────────────────────────────────
    jd_requirements: Dict[str, bool]    # which sections JD explicitly requires
    active_weights:  Dict[str, float]   # normalised weights used in final score

    # ── Skills ────────────────────────────────────────────────────────────────
    skills_matched:      List[str]
    missing_skills:      List[str]
    all_resume_skills:   List[str]
    skills_by_category:  Dict[str, List[str]] = {}   # resume skills grouped by category
    missing_by_category: Dict[str, List[str]] = {}   # missing skills grouped by category
    resume_only_skills:  List[str] = []               # skills in resume but NOT in JD

    # ── Experience ────────────────────────────────────────────────────────────
    experience_years:        float
    experience_breakdown:    List[Dict]
    required_experience:     Optional[float]
    experience_requirements: List[Dict]

    # ── Certifications ────────────────────────────────────────────────────────
    certifications_found:    List[str]   # all certs detected in resume
    certifications_matched:  List[str]   # resume certs that match JD requirements
    certifications_required: List[str]   # certs the JD asks for
    education:            List[EducationInfo]
    projects:             List[ProjectInfo]
    summary_insights:     SummaryInsights