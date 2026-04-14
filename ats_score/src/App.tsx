"use client";
import { useState } from "react";

// ── Types ──────────────────────────────────────────────────────────────────────

interface ExpBreakdown {
  block_preview: string;
  start: string;
  end: string;
  years: number;
  is_current: boolean;
}

interface ExpRequirement {
  years: number;
  context: string;
}

interface ProjectInfo {
  title: string;
  description: string;
  tech_used: string[];
  impact: string[];
}

interface SummaryInsights {
  raw_text: string;
  key_points: string[];
  stated_role: string | null;
  experience_mentioned: number | null;
  relevance_to_jd: number;
  quality_score: number;
  suggestions: string[];
}

interface EducationInfo {
  degree: string;
  field_of_study: string | null;
  institution: string | null;
  years: string | null;
  gpa: string | null;
}

interface ATSResult {
  match_score: number;
  grade: string;
  overall_summary: string;
  score_breakdown: Record<string, number>;
  section_scores: Record<string, number>;
  jd_requirements: Record<string, boolean>;
  active_weights: Record<string, number>;
  skills_matched: string[];
  missing_skills: string[];
  all_resume_skills: string[];
  experience_years: number;
  experience_breakdown: ExpBreakdown[];
  required_experience: number | null;
  experience_requirements: ExpRequirement[];
  certifications_found: string[];
  certifications_matched: string[];
  certifications_required: string[];
  education: EducationInfo[];
  projects: ProjectInfo[];
  summary_insights: SummaryInsights;
}

// ── Colour helpers ─────────────────────────────────────────────────────────────

const scoreColor   = (s: number) => s >= 70 ? "#22c55e" : s >= 45 ? "#f59e0b" : "#ef4444";
const scoreBg      = (s: number) =>
  s >= 70 ? "bg-emerald-50 border-emerald-100"
: s >= 45 ? "bg-amber-50 border-amber-100"
: "bg-red-50 border-red-100";
const gradeRingCol = (s: number) =>
  s >= 80 ? "#22c55e" : s >= 60 ? "#3b82f6" : s >= 40 ? "#f59e0b" : "#ef4444";

const gradeBg = (g: string) =>
  g === "Excellent" ? "bg-emerald-100 text-emerald-700 border-emerald-200"
: g === "Good"      ? "bg-blue-100 text-blue-700 border-blue-200"
: g === "Fair"      ? "bg-amber-100 text-amber-700 border-amber-200"
:                     "bg-red-100 text-red-700 border-red-200";

// ── Score ring ────────────────────────────────────────────────────────────────

function ScoreRing({ score, grade }: { score: number; grade: string }) {
  const r      = 54;
  const circ   = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color  = gradeRingCol(score);
  return (
    <div className="flex flex-col items-center gap-3">
      <svg width="150" height="150" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r={r} fill="none" stroke="#e5e7eb" strokeWidth="12" />
        <circle
          cx="70" cy="70" r={r} fill="none"
          stroke={color} strokeWidth="12"
          strokeDasharray={circ} strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 70 70)"
          style={{ transition: "stroke-dashoffset 1.2s ease" }}
        />
        <text x="70" y="64" textAnchor="middle" fontSize="26" fontWeight="bold" fill={color}>{score}</text>
        <text x="70" y="80" textAnchor="middle" fontSize="11" fill="#9ca3af">/ 100</text>
      </svg>
      <span className={`text-sm font-semibold px-3 py-1 rounded-full border ${gradeBg(grade)}`}>{grade}</span>
    </div>
  );
}

// ── JD badge ──────────────────────────────────────────────────────────────────

function JDBadge({ required, weight }: { required: boolean; weight: number }) {
  if (!required)
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-purple-100 text-purple-700 border border-purple-200">
        <span>✦</span> extra
      </span>
    );
  return (
    <span className="inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-sky-100 text-sky-700 border border-sky-200">
      {Math.round(weight * 100)}% weight
    </span>
  );
}

// ── Section meter (percentage only) ───────────────────────────────────────────

function SectionMeter({
  label, icon, score100, contribution, required, weight,
}: {
  label: string; icon: string; score100: number;
  contribution: number; required: boolean; weight: number;
}) {
  const color = scoreColor(score100);
  const bg    = scoreBg(score100);

  return (
    <div className={`border rounded-xl p-4 ${bg} ${!required ? "opacity-80" : ""}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-base">{icon}</span>
          <span className="text-sm font-semibold text-gray-800">{label}</span>
          <JDBadge required={required} weight={weight} />
        </div>
        {/* ── percentage only ── */}
        <span className="text-lg font-bold" style={{ color }}>
          {score100.toFixed(0)}%
        </span>
      </div>

      <div className="h-2 bg-white rounded-full overflow-hidden border border-gray-100">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${Math.min(score100, 100)}%`, backgroundColor: color }}
        />
      </div>

      <div className="flex items-center justify-between mt-1.5">
        {required
          ? <span className="text-xs text-gray-500">Counted in ATS score</span>
          : <span className="text-xs text-purple-600">Bonus — not penalised if absent</span>
        }
        <span className="text-xs text-gray-500">+{contribution.toFixed(1)} pts</span>
      </div>
    </div>
  );
}

// ── Tag ────────────────────────────────────────────────────────────────────────

function Tag({ text, v }: { text: string; v: "green" | "red" | "blue" | "gray" | "purple" | "orange" }) {
  const cls: Record<string, string> = {
    green:  "bg-emerald-100 text-emerald-800 border-emerald-200",
    red:    "bg-red-100 text-red-800 border-red-200",
    blue:   "bg-sky-100 text-sky-800 border-sky-200",
    gray:   "bg-gray-100 text-gray-700 border-gray-200",
    purple: "bg-purple-100 text-purple-800 border-purple-200",
    orange: "bg-orange-100 text-orange-800 border-orange-200",
  };
  return (
    <span className={`inline-block border text-xs px-2 py-0.5 rounded-full mr-1 mb-1 ${cls[v]}`}>
      {text}
    </span>
  );
}

// ── Education card ─────────────────────────────────────────────────────────────

function EducationCard({ edu, i }: { edu: EducationInfo; i: number }) {
  const bg = i % 2 === 0 ? "bg-indigo-50 border-indigo-100" : "bg-blue-50 border-blue-100";
  return (
    <div className={`flex items-start gap-3 border rounded-xl p-4 ${bg}`}>
      <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 flex-shrink-0 mt-0.5">
        🎓
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between flex-wrap gap-1">
          <p className="text-sm font-bold text-gray-800">{edu.degree}</p>
          {edu.years && (
            <span className="text-xs text-gray-500 bg-white border border-gray-200 px-2 py-0.5 rounded-full">
              📅 {edu.years}
            </span>
          )}
        </div>
        {edu.field_of_study && (
          <p className="text-xs text-indigo-700 font-medium mt-0.5">{edu.field_of_study}</p>
        )}
        {edu.institution && (
          <p className="text-xs text-gray-500 mt-0.5">🏫 {edu.institution}</p>
        )}
        {edu.gpa && <div className="mt-1.5"><Tag text={edu.gpa} v="purple" /></div>}
      </div>
    </div>
  );
}

// ── JD requirements legend ─────────────────────────────────────────────────────

function JDLegend({ jdReq }: { jdReq: Record<string, boolean> }) {
  const required = Object.entries(jdReq).filter(([, v]) => v).map(([k]) => k);
  return (
    <div className="rounded-xl border border-gray-100 bg-gray-50 p-4 text-xs">
      <p className="font-semibold text-gray-600 mb-2">📋 JD Analysis — what this job description asks for:</p>
      <div className="flex flex-wrap gap-1.5">
        {required.map(k => (
          <span key={k} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-sky-100 text-sky-700 border border-sky-200 font-medium">
            ✓ {k}
          </span>
        ))}
      </div>
    </div>
  );
}

// ── Combined Result card ───────────────────────────────────────────────────────

function CombinedResult({ result }: { result: ATSResult }) {
  const rows = Object.entries(SECTION_META)
    .filter(([key]) => result.jd_requirements?.[key] !== false)
    .map(([key, { icon, label }]) => ({
      key,
      icon,
      label,
      score: result.section_scores?.[key] ?? 0,
      pts:   result.score_breakdown?.[key] ?? 0,
    }));

  const total = result.match_score;

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div>
          <h2 className="text-sm font-bold text-gray-700">Combined ATS Result</h2>
          <p className="text-xs text-gray-400 mt-0.5">weighted sum of all required sections</p>
        </div>
        <div className="text-right">
          <div className="text-3xl font-extrabold" style={{ color: scoreColor(total) }}>
            {Math.round(total)}
          </div>
          <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${gradeBg(result.grade)}`}>
            {result.grade}
          </span>
        </div>
      </div>

      {/* Per-section breakdown rows */}
      <div className="space-y-2">
        {rows.map(r => (
          <div
            key={r.key}
            className="flex items-center gap-3 py-2 border-b border-gray-50 last:border-0 text-xs"
          >
            <span className="w-4 text-center text-sm">{r.icon}</span>
            <span className="flex-1 font-medium text-gray-700 capitalize">{r.label}</span>
            {/* percentage */}
            <span className="w-10 text-right" style={{ color: scoreColor(r.score) }}>
              {r.score.toFixed(0)}%
            </span>
            {/* mini bar */}
            <div className="w-20 h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{
                  width: `${Math.min(r.score, 100)}%`,
                  backgroundColor: scoreColor(r.score),
                }}
              />
            </div>
            {/* points contributed */}
            <span
              className="w-14 text-right font-semibold"
              style={{ color: scoreColor(r.score) }}
            >
              +{r.pts.toFixed(1)} pts
            </span>
          </div>
        ))}
      </div>

      {/* Total */}
      <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between text-sm font-bold">
        <span className="text-gray-600">Final ATS Score</span>
        <span style={{ color: scoreColor(total) }}>{total.toFixed(1)} / 100</span>
      </div>
    </div>
  );
}

// ── Section meta ───────────────────────────────────────────────────────────────

const SECTION_META: Record<string, { icon: string; label: string }> = {
  skills:         { icon: "🧠", label: "Skills" },
  experience:     { icon: "💼", label: "Experience" },
  projects:       { icon: "📂", label: "Projects" },
  certifications: { icon: "🏅", label: "Certifications" },
  education:      { icon: "🎓", label: "Education" },
  summary:        { icon: "📝", label: "Summary" },
};

// ── Main page ──────────────────────────────────────────────────────────────────

export default function ATSPage() {
  const [file,    setFile]    = useState<File | null>(null);
  const [jd,      setJd]      = useState("");
  const [result,  setResult]  = useState<ATSResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState("");

  const handleAnalyze = async () => {
    if (!file || !jd.trim()) {
      setError("Please upload a resume and paste a job description.");
      return;
    }
    setError(""); setLoading(true); setResult(null);
    try {
      const form = new FormData();
      form.append("resume", file);
      form.append("job_description", jd);
      const res = await fetch("http://localhost:8000/api/ats-score", { method: "POST", body: form });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error((err as any).detail || `Server error ${res.status}`);
      }
      setResult(await res.json());
    } catch (e: any) {
      setError(e.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 py-10 px-4">
      <div className="max-w-5xl mx-auto">

        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight">
            ATS Resume Analyzer
          </h1>
        </div>

        {/* Input */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 mb-6">
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Job Description
              </label>
              <textarea
                className="w-full p-3 border border-gray-200 rounded-xl h-44 text-sm text-gray-800 resize-none focus:outline-none focus:ring-2 focus:ring-blue-400"
                placeholder="Paste the full job description here…"
                value={jd}
                onChange={e => setJd(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Resume (PDF / DOCX)
              </label>
              <label className="flex flex-col items-center justify-center h-44 border-2 border-dashed border-gray-200 rounded-xl cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-colors">
                <svg className="w-8 h-8 text-gray-300 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M4 16v1a2 2 0 002 2h12a2 2 0 002-2v-1M12 12V4m0 0L8 8m4-4l4 4" />
                </svg>
                <span className="text-sm text-gray-400">{file ? file.name : "Click to upload or drag & drop"}</span>
                <span className="text-xs text-gray-300 mt-1">PDF · DOCX</span>
                <input type="file" accept=".pdf,.docx" className="hidden"
                  onChange={e => setFile(e.target.files?.[0] || null)} />
              </label>
            </div>
          </div>

          {error && <p className="text-red-500 text-sm mt-3">{error}</p>}

          <button
            onClick={handleAnalyze} disabled={loading}
            className="mt-5 w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-semibold py-3 rounded-xl transition-colors text-sm"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                Analysing…
              </span>
            ) : "Analyse ATS Score"}
          </button>
        </div>

        {/* Results */}
        {result && (
          <div className="space-y-5">

            {/* JD analysis legend */}
            <JDLegend jdReq={result.jd_requirements} />

            {/* Score ring + quick stats */}
            <div className="grid md:grid-cols-2 gap-5">
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 flex flex-col items-center justify-center gap-4">
                <ScoreRing score={result.match_score} grade={result.grade} />
                <div className="w-full grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="bg-gray-50 rounded-lg p-2">
                    <div className="font-bold text-gray-800">
                      {result.skills_matched.length}/{result.skills_matched.length + result.missing_skills.length}
                    </div>
                    <div className="text-gray-400">Skills</div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-2">
                    <div className="font-bold text-gray-800">{result.experience_years}y</div>
                    <div className="text-gray-400">Experience</div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-2">
                    <div className="font-bold text-gray-800">{result.certifications_found.length}</div>
                    <div className="text-gray-400">Certs</div>
                  </div>
                </div>
              </div>

              {/* Section scores */}
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-sm font-bold text-gray-700">Section Scores</h2>
                  <span className="text-xs text-gray-400">
                    dynamic weights → <strong>{result.match_score.toFixed(1)}</strong> final
                  </span>
                </div>
                <div className="space-y-3">
                  {Object.entries(SECTION_META).map(([key, { icon, label }]) => {
                    const score100 = result.section_scores?.[key] ?? 0;
                    const contrib  = result.score_breakdown?.[key] ?? 0;
                    const required = result.jd_requirements?.[key] ?? true;
                    const weight   = result.active_weights?.[key] ?? 0;
                    if (!required) return null;
                    return (
                      <SectionMeter
                        key={key}
                        label={label} icon={icon}
                        score100={score100} contribution={contrib}
                        required={required} weight={weight}
                      />
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Skills */}
            <div className="grid md:grid-cols-2 gap-5">
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <h2 className="text-sm font-bold text-emerald-700 mb-3">
                  ✓ Matched Skills ({result.skills_matched.length})
                </h2>
                <div className="flex flex-wrap">
                  {result.skills_matched.length > 0
                    ? result.skills_matched.map(s => <Tag key={s} text={s} v="green" />)
                    : <p className="text-xs text-gray-400">No matching skills found</p>}
                </div>
              </div>
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <h2 className="text-sm font-bold text-red-600 mb-3">
                  ✗ Missing Skills ({result.missing_skills.length})
                </h2>
                <div className="flex flex-wrap">
                  {result.missing_skills.length > 0
                    ? result.missing_skills.map(s => <Tag key={s} text={s} v="red" />)
                    : <p className="text-xs text-gray-400">All required skills present 🎉</p>}
                </div>
              </div>
            </div>

            {/* Experience */}
            {result.jd_requirements?.experience && (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <div className="flex items-center justify-between mb-3">
                  <h2 className="text-sm font-bold text-gray-700">💼 Work Experience</h2>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 border">
                      {result.section_scores?.experience?.toFixed(0)}%
                    </span>
                    {result.required_experience !== null && (
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium border ${
                        result.experience_years >= result.required_experience
                          ? "bg-emerald-50 border-emerald-200 text-emerald-700"
                          : "bg-red-50 border-red-200 text-red-600"
                      }`}>
                        {result.experience_years >= result.required_experience ? "✓" : "✗"} {result.required_experience}y required
                      </span>
                    )}
                  </div>
                </div>

                {result.experience_requirements.length > 0 && (
                  <div className="flex flex-col gap-1 mb-4">
                    {result.experience_requirements.map((req, i) => (
                      <div key={i} className={`flex items-center gap-2 text-xs px-2 py-1 rounded-lg border ${
                        result.experience_years >= req.years
                          ? "bg-emerald-50 border-emerald-200 text-emerald-700"
                          : "bg-red-50 border-red-200 text-red-600"
                      }`}>
                        <span>{result.experience_years >= req.years ? "✓" : "✗"}</span>
                        <span>{req.years}y — {req.context}</span>
                      </div>
                    ))}
                  </div>
                )}

                {result.experience_breakdown.length > 0 ? (
                  <div className="space-y-2">
                    {result.experience_breakdown.map((r, i) => (
                      <div key={i} className="flex items-start gap-3 text-xs">
                        <div className={`w-2 h-2 rounded-full mt-1 flex-shrink-0 ${
                          r.is_current ? "bg-emerald-500" : "bg-blue-400"
                        }`} />
                        <div>
                          <p className="text-gray-700 font-medium">{r.block_preview}</p>
                          <p className="text-gray-400">{r.start} – {r.is_current ? "Present" : r.end} · {r.years}y</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-gray-400">
                    {result.experience_years === 0
                      ? "No work experience detected — this may be a student/fresher resume."
                      : "Experience detected but no date ranges found."}
                  </p>
                )}
              </div>
            )}

            {/* Education */}
            {result.education && result.education.length > 0 && (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <div className="flex items-center gap-2 mb-4">
                  <h2 className="text-sm font-bold text-gray-700">🎓 Education</h2>
                  <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 border">
                    {result.section_scores?.education?.toFixed(0)}%
                  </span>
                  <JDBadge required={result.jd_requirements?.education ?? true} weight={result.active_weights?.education ?? 0} />
                  <span className="ml-auto text-xs px-2 py-0.5 rounded-full font-medium bg-indigo-50 border border-indigo-200 text-indigo-600">
                    {result.education.length} {result.education.length === 1 ? "entry" : "entries"}
                  </span>
                </div>
                <div className="space-y-3">
                  {result.education.map((edu, i) => <EducationCard key={i} edu={edu} i={i} />)}
                </div>
              </div>
            )}

            {/* Certifications */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center gap-2 mb-4">
                <h2 className="text-sm font-bold text-gray-700">🏅 Certifications</h2>
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 border">
                  {result.section_scores?.certifications?.toFixed(0)}%
                </span>
                <JDBadge required={result.jd_requirements?.certifications ?? true} weight={result.active_weights?.certifications ?? 0} />
                {!result.jd_requirements?.certifications && (
                  <span className="ml-auto text-xs text-purple-600 bg-purple-50 border border-purple-200 px-2 py-0.5 rounded-full">
                    Not required · Full marks
                  </span>
                )}
              </div>

              {result.jd_requirements?.certifications ? (
                <div className="grid md:grid-cols-3 gap-4">
                  <div>
                    <p className="text-xs font-semibold text-gray-500 mb-2 flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-blue-400 inline-block" />
                      Found in Resume ({result.certifications_found.length})
                    </p>
                    <div className="flex flex-wrap">
                      {result.certifications_found.length > 0
                        ? result.certifications_found.map(c => <Tag key={c} text={c} v="blue" />)
                        : <span className="text-xs text-gray-400">None detected</span>}
                    </div>
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-gray-500 mb-2 flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-gray-400 inline-block" />
                      Required by JD ({result.certifications_required.length})
                    </p>
                    <div className="flex flex-wrap">
                      {result.certifications_required.length > 0
                        ? result.certifications_required.map(c => <Tag key={c} text={c} v="gray" />)
                        : <span className="text-xs text-gray-400">None specified</span>}
                    </div>
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-gray-500 mb-2 flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" />
                      Matched ({result.certifications_matched.length}/{result.certifications_required.length || result.certifications_found.length})
                    </p>
                    <div className="flex flex-wrap">
                      {result.certifications_matched.length > 0
                        ? result.certifications_matched.map(c => <Tag key={c} text={c} v="green" />)
                        : <span className="text-xs text-gray-400">None matched</span>}
                    </div>
                  </div>
                </div>
              ) : (
                <div>
                  <p className="text-xs text-gray-400 mb-2">
                    These certifications were found in your resume. They're not required by this JD but may strengthen your application.
                  </p>
                  <div className="flex flex-wrap">
                    {result.certifications_found.length > 0
                      ? result.certifications_found.map(c => <Tag key={c} text={c} v="blue" />)
                      : <span className="text-xs text-gray-400">No certifications detected</span>}
                  </div>
                </div>
              )}
            </div>

            {/* Projects */}
            {result.projects.length > 0 && (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <div className="flex items-center gap-2 mb-3">
                  <h2 className="text-sm font-bold text-gray-700">📂 Projects ({result.projects.length})</h2>
                  <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 border">
                    {result.section_scores?.projects?.toFixed(0)}%
                  </span>
                  <JDBadge required={result.jd_requirements?.projects ?? true} weight={result.active_weights?.projects ?? 0} />
                </div>
                <div className="space-y-3">
                  {result.projects.map((p, i) => (
                    <div key={i} className="border border-gray-100 rounded-xl p-4 hover:border-gray-200 transition-colors">
                      <p className="text-xs font-semibold text-gray-800 mb-1">{p.title}</p>
                      <p className="text-xs text-gray-500 mb-2 leading-relaxed">{p.description}</p>
                      <div className="flex flex-wrap">
                        {p.tech_used.slice(0, 12).map(t => <Tag key={t} text={t} v="blue" />)}
                      </div>
                      {p.impact.length > 0 && (
                        <p className="text-xs text-emerald-600 mt-1.5 font-medium">
                          📈 {p.impact.join(" · ")}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Summary */}
            {result.summary_insights.raw_text && (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <h2 className="text-sm font-bold text-gray-700">📝 Summary Quality</h2>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 border">
                      {result.section_scores?.summary?.toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400">
                      JD relevance: <strong>{(result.summary_insights.relevance_to_jd * 100).toFixed(0)}%</strong>
                    </span>
                    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                      result.summary_insights.quality_score >= 70 ? "bg-emerald-100 text-emerald-700"
                      : result.summary_insights.quality_score >= 40 ? "bg-amber-100 text-amber-700"
                      : "bg-red-100 text-red-700"
                    }`}>
                      {result.summary_insights.quality_score}%
                    </span>
                  </div>
                </div>

                <p className="text-xs text-gray-600 leading-relaxed mb-3 bg-gray-50 rounded-lg p-3 border border-gray-100">
                  {result.summary_insights.raw_text}
                </p>

                {result.summary_insights.suggestions.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-gray-500 mb-2">Suggestions to improve:</p>
                    <ul className="space-y-1">
                      {result.summary_insights.suggestions.map((s, i) => (
                        <li key={i} className="text-xs text-amber-700 flex gap-1.5 items-start">
                          <span className="mt-0.5">→</span><span>{s}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* ── Combined Result (always last) ── */}
            <CombinedResult result={result} />

          </div>
        )}
      </div>
    </div>
  );
}