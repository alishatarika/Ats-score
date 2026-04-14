import re
from typing import Dict, List, Tuple

from services.section_extraction import extract_sections
from utils.skills import extract_skills, skill_match_score
from utils.certifications import extract_certifications, score_certifications, match_certs_to_jd
from utils.date_utils import (
    calculate_experience,
    get_experience_breakdown,
    parse_required_experience,
)
from utils.projects import extract_projects, score_projects
from utils.summary import extract_summary_insights
from utils.education import extract_education, score_education
from models.ats_score import (
    ATSAnalysis, ProjectInfo, SummaryInsights, EducationInfo
)


# ── JD requirement detection ──────────────────────────────────────────────────

def _analyze_jd(jd_text: str) -> Dict[str, bool]:
    t = jd_text.lower()
    return {
        # Skills are always relevant — every JD asks for something
        "skills": True,

        "experience": bool(re.search(
            r'\b(experience|year[s]?\s+of|worked|background|employment|history|proven)\b', t
        )),
        "education": bool(re.search(
            r'\b(degree|bachelor|master|phd|doctorate|education|qualification|'
            r'graduate|undergraduate|diploma|university|college)\b', t
        )),
        "certifications": bool(re.search(
            r'\b(certif|licensed?|credential|accredited|certified|certification)\b', t
        )),
        "projects": bool(re.search(
            r'\b(project|portfolio|built|developed|shipped|open.source|'
            r'github|case\s+study|implementation|side\s+project)\b', t
        )),
        # Summary is always measured (it anchors the candidate's pitch)
        "summary": True,
    }


# ── Weight computation ────────────────────────────────────────────────────────

# Base weights when section IS required by JD
_BASE_WEIGHTS: Dict[str, float] = {
    "skills":         0.45,
    "experience":     0.25,
    "education":      0.10,
    "certifications": 0.10,
    "projects":       0.15,
    "summary":        0.05,
}

_ALWAYS_ON = {"skills", "summary"}   # never zeroed out

# Bonus pool: max total bonus contribution from "extra" sections
_MAX_BONUS_PTS = 5.0      # max 5 pts bonus across all extra sections


def _compute_weights(jd_req: Dict[str, bool]) -> Dict[str, float]:
    active = {
        k: (_BASE_WEIGHTS[k] if (jd_req.get(k, False) or k in _ALWAYS_ON) else 0.0)
        for k in _BASE_WEIGHTS
    }
    total = sum(active.values())
    if total == 0:
        n = len(active)
        return {k: round(1.0 / n, 4) for k in active}
    return {k: round(v / total, 4) for k, v in active.items()}


# ── Experience scoring ────────────────────────────────────────────────────────

def _experience_score(exp_years: float, required_years: float | None) -> float:
    # JD specifies a requirement → score proportionally
    if required_years and required_years > 0:
        return round(min(exp_years / required_years, 1.0) * 100, 1)
    # JD has no experience requirement → full marks, no penalty
    return 100.0


# ── Grade ─────────────────────────────────────────────────────────────────────

def _grade(score: float) -> str:
    if score >= 80: return "Excellent"
    if score >= 60: return "Good"
    if score >= 40: return "Fair"
    return "Poor"


# ── Summary text builder ──────────────────────────────────────────────────────

def _build_summary(
    section_scores: Dict[str, float],
    weights: Dict[str, float],
    jd_req: Dict[str, bool],
    final_score: float,
    matched: List[str],
    missing: List[str],
    exp_years: float,
    certs: List[str],
    projects: List[dict],
    summary_quality: int,
    exp_breakdown: List[dict],
) -> str:
    grade = _grade(final_score)

    exp_detail = (
        ", ".join(
            f"{e['block_preview'][:40].rstrip('.')}… ({e['years']} yrs)"
            for e in exp_breakdown[:3]
        )
        if exp_breakdown
        else "No dated work periods detected"
    )

    lines = [
        f"ATS Score: {final_score:.1f} / 100  [{grade}]",
        "",
        "── Section Scores (weights are JD-driven) ──",
    ]

    for key in ["skills", "experience", "projects", "certifications", "education", "summary"]:
        w    = weights.get(key, 0.0)
        s    = section_scores.get(key, 0.0)
        req  = jd_req.get(key, False)
        tag  = f"{round(w * 100)}% weight" if req else "extra credit"
        lines.append(f"  {key.capitalize():16}  {s:5.1f}/100  [{tag}]")

    lines += [
        "",
        f"✅  Skills matched:   {len(matched)}  → {', '.join(matched[:6])}{'…' if len(matched) > 6 else ''}",
        f"❌  Skills missing:   {len(missing)}  → {', '.join(missing[:6])}{'…' if len(missing) > 6 else ''}",
        f"🗓️  Work experience:  {exp_years} yr(s)  [{exp_detail}]",
        f"🏅  Certifications:   {', '.join(certs) if certs else 'none found'}",
        f"📂  Projects:         {len(projects)} detected",
        f"📝  Summary quality:  {summary_quality}/100",
        "",
    ]

    if final_score >= 80:
        lines.append("👍 Strong match — your resume aligns well with this JD.")
    elif final_score >= 60:
        lines.append("📝 Good match — filling the missing skills will significantly help.")
    elif final_score >= 40:
        lines.append("⚠️  Fair match — notable skill gaps found. Highlight more relevant experience.")
    else:
        lines.append("🔴 Low match — significant gaps. Consider upskilling or a better-fit role.")

    return "\n".join(lines)


# ── Main pipeline ─────────────────────────────────────────────────────────────

def calculate_ats_score(resume_text: str, jd_text: str) -> ATSAnalysis:

    # ── 1. Section parsing ───────────────────────────────────────────────────
    sections = extract_sections(resume_text)

    skills_text  = sections.get("skills", "")   or resume_text
    exp_text     = sections.get("experience", "") or resume_text
    proj_text    = sections.get("projects", "")
    cert_text    = sections.get("certifications", "") or resume_text
    summary_text = sections.get("summary", "")
    edu_text     = sections.get("education", "")

    # ── 2. JD analysis ──────────────────────────────────────────────────────
    jd_req  = _analyze_jd(jd_text)
    weights = _compute_weights(jd_req)

    # ── 3. Data extraction ───────────────────────────────────────────────────
    resume_skills = extract_skills(skills_text)
    jd_skills     = extract_skills(jd_text)

    # Categorise resume skills by taxonomy group
    from utils.skills import categorize_skills
    skills_by_category  = categorize_skills(resume_skills)
    missing_by_category = categorize_skills([])   # filled after matching
    resume_only_skills  = sorted(set(resume_skills) - set(jd_skills))

    resume_certs   = extract_certifications(cert_text, cert_section=sections.get("certifications", ""))
    matched_certs, jd_required_certs = match_certs_to_jd(resume_certs, jd_text)
    exp_years      = calculate_experience(exp_text)
    exp_breakdown  = get_experience_breakdown(exp_text)
    req_years, exp_requirements = parse_required_experience(jd_text)
    raw_projects   = extract_projects(proj_text, jd_text=jd_text)
    summary_ins    = extract_summary_insights(summary_text, jd_text)
    edu_list       = extract_education(edu_text)

    # ── 4. Section scores (each 0-100) ───────────────────────────────────────
    skill_ratio, matched_skills, missing_skills = skill_match_score(
        resume_skills, jd_skills
    )
    skills_100 = round(skill_ratio * 100, 1)
    missing_by_category = categorize_skills(missing_skills)

    experience_100 = _experience_score(exp_years, req_years)

    projects_100, proj_expl = score_projects(
        raw_projects, jd_text, jd_mentions_projects=jd_req["projects"]
    )
    certs_100, cert_expl = score_certifications(
        resume_certs, jd_text, jd_mentions_certs=jd_req["certifications"]
    )
    edu_100, edu_expl = score_education(
        edu_list, jd_text, jd_mentions_education=jd_req["education"]
    )
    summary_100 = summary_ins["quality_score"]

    section_scores: Dict[str, float] = {
        "skills":         skills_100,
        "experience":     experience_100,
        "projects":       projects_100,
        "certifications": certs_100,
        "education":      edu_100,
        "summary":        summary_100,
    }

    # ── 5. Weighted final score + bonus pool ─────────────────────────────────
    core_score     = 0.0
    score_breakdown: Dict[str, float] = {}
    extra_keys     = [k for k in section_scores if not jd_req.get(k, False)]
    required_keys  = [k for k in section_scores if jd_req.get(k, False)]

    for key in required_keys:
        contrib = round(weights[key] * section_scores[key], 2)
        core_score += contrib
        score_breakdown[key] = contrib

    # Extra sections: bonus proportional to score, total capped
    bonus_total = 0.0
    for key in extra_keys:
        raw_bonus = (section_scores[key] / 100) * (_MAX_BONUS_PTS / max(len(extra_keys), 1))
        capped    = round(min(raw_bonus, _MAX_BONUS_PTS / max(len(extra_keys), 1)), 2)
        bonus_total += capped
        score_breakdown[key] = capped

    final_score = round(min(core_score + min(bonus_total, _MAX_BONUS_PTS), 100.0), 2)

    overall_summary = _build_summary(
        section_scores, weights, jd_req, final_score,
        matched_skills, missing_skills,
        exp_years, resume_certs, raw_projects,
        summary_ins["quality_score"], exp_breakdown,
    )

    return ATSAnalysis(
        match_score     = final_score,
        grade           = _grade(final_score),
        overall_summary = overall_summary,

        score_breakdown   = score_breakdown,
        section_scores    = section_scores,
        jd_requirements   = jd_req,
        active_weights    = weights,

        skills_matched       = matched_skills,
        missing_skills       = missing_skills,
        all_resume_skills    = sorted(resume_skills),
        skills_by_category   = skills_by_category,
        missing_by_category  = missing_by_category,
        resume_only_skills   = resume_only_skills,

        experience_years        = exp_years,
        experience_breakdown    = exp_breakdown,
        required_experience     = req_years,
        experience_requirements = exp_requirements,

        certifications_found   = resume_certs,
        certifications_matched = matched_certs,
        certifications_required = jd_required_certs,

        education = [
            EducationInfo(
                degree         = e["degree"],
                field_of_study = e.get("field_of_study"),
                institution    = e.get("institution"),
                years          = e.get("years"),
                gpa            = e.get("gpa"),
            )
            for e in edu_list
        ],

        projects = [
            ProjectInfo(
                title           = p["title"],
                description     = p["description"],
                tech_used       = p["tech_used"],
                jd_matched_tech = p.get("jd_matched_tech", []),
                impact          = p["impact"],
                duration        = p.get("duration"),
                team_info       = p.get("team_info"),
                jd_relevance    = p.get("jd_relevance"),
            )
            for p in raw_projects
        ],

        summary_insights = SummaryInsights(**summary_ins),
    )