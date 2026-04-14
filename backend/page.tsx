"use client";
import { useState } from "react";

// ── Types ─────────────────────────────────────────────────────────────────────

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
  section_scores: Record<string, number>;   // NEW: each section out of 100
  skills_matched: string[];
  missing_skills: string[];
  all_resume_skills: string[];
  experience_years: number;
  experience_breakdown: ExpBreakdown[];
  required_experience: number | null;
  experience_requirements: ExpRequirement[];
  certifications_found: string[];
  education: EducationInfo[];
  projects: ProjectInfo[];
  summary_insights: SummaryInsights;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function gradeColor(grade: string) {
  return grade === "Excellent" ? "text-green-600" :
         grade === "Good"      ? "text-blue-600"  :
         grade === "Fair"      ? "text-amber-600" :
                                 "text-red-600";
}

function gradeRing(score: number) {
  return score >= 80 ? "#22c55e" : score >= 60 ? "#3b82f6" : score >= 40 ? "#f59e0b" : "#ef4444";
}

function gradeBg(grade: string) {
  return grade === "Excellent" ? "bg-green-100 text-green-700 border-green-200" :
         grade === "Good"      ? "bg-blue-100 text-blue-700 border-blue-200"    :
         grade === "Fair"      ? "bg-amber-100 text-amber-700 border-amber-200" :
                                 "bg-red-100 text-red-700 border-red-200";
}

// ── UI Components ─────────────────────────────────────────────────────────────

function ScoreRing({ score, grade }: { score: number; grade: string }) {
  const r = 54;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color = gradeRing(score);

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width="150" height="150" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r={r} fill="none" stroke="#e5e7eb" strokeWidth="12" />
        <circle
          cx="70" cy="70" r={r} fill="none"
          stroke={color} strokeWidth="12"
          strokeDasharray={circ} strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 70 70)"
          style={{ transition: "stroke-dashoffset 1s ease" }}
        />
        <text x="70" y="65" textAnchor="middle" fontSize="26" fontWeight="bold" fill={color}>{score}</text>
        <text x="70" y="82" textAnchor="middle" fontSize="11" fill="#6b7280">/ 100</text>
      </svg>
      <span className={`text-sm font-semibold px-3 py-1 rounded-full border ${gradeBg(grade)}`}>{grade}</span>
    </div>
  );
}

// Section score meter — shows raw score out of 100 with color coding
function SectionMeter({
  label,
  score100,
  contribution,
  weight,
  icon,
}: {
  label: string;
  score100: number;
  contribution: number;
  weight: number;
  icon: string;
}) {
  const color = score100 >= 70 ? "#22c55e" : score100 >= 45 ? "#f59e0b" : "#ef4444";
  const bgColor = score100 >= 70 ? "bg-green-50 border-green-100" : score100 >= 45 ? "bg-amber-50 border-amber-100" : "bg-red-50 border-red-100";

  return (
    <div className={`border rounded-xl p-4 ${bgColor}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-lg">{icon}</span>
          <span className="text-sm font-semibold text-gray-800">{label}</span>
        </div>
        <div className="text-right">
          <span className="text-lg font-bold" style={{ color }}>{score100.toFixed(0)}</span>
          <span className="text-xs text-gray-400 ml-0.5">/100</span>
        </div>
      </div>
      <div className="h-2 bg-white rounded-full overflow-hidden border border-gray-100">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${Math.min(score100, 100)}%`, backgroundColor: color }}
        />
      </div>
      <div className="flex items-center justify-between mt-1.5">
        <span className="text-xs text-gray-500">Weight: {Math.round(weight * 100)}%</span>
        <span className="text-xs text-gray-500">Contributes {contribution.toFixed(1)} pts</span>
      </div>
    </div>
  );
}

function Tag({ text, variant }: { text: string; variant: "green" | "red" | "blue" | "gray" | "purple" }) {
  const cls = {
    green:  "bg-green-100 text-green-800 border-green-200",
    red:    "bg-red-100 text-red-800 border-red-200",
    blue:   "bg-blue-100 text-blue-800 border-blue-200",
    gray:   "bg-gray-100 text-gray-700 border-gray-200",
    purple: "bg-purple-100 text-purple-800 border-purple-200",
  }[variant];
  return <span className={`inline-block border text-xs px-2 py-0.5 rounded-full mr-1 mb-1 ${cls}`}>{text}</span>;
}

function EducationCard({ edu, index }: { edu: EducationInfo; index: number }) {
  const bgClass = index % 2 === 0 ? "bg-indigo-50 border-indigo-100" : "bg-blue-50 border-blue-100";
  return (
    <div className={`flex items-start gap-3 border rounded-xl p-4 ${bgClass}`}>
      <div className="flex-shrink-0 w-9 h-9 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className="w-5 h-5">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 14l9-5-9-5-9 5 9 5z" />
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 14l6.16-3.422A12.083 12.083 0 0112 21.5a12.083 12.083 0 01-6.16-10.922L12 14z" />
        </svg>
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2 flex-wrap">
          <p className="text-sm font-bold text-gray-800">{edu.degree}</p>
          {edu.years && (
            <span className="text-xs text-gray-500 bg-white border border-gray-200 px-2 py-0.5 rounded-full whitespace-nowrap">
              📅 {edu.years}
            </span>
          )}
        </div>
        {edu.field_of_study && <p className="text-xs text-indigo-700 font-medium mt-0.5">{edu.field_of_study}</p>}
        {edu.institution && (
          <p className="text-xs text-gray-600 mt-0.5 flex items-center gap-1">
            <svg viewBox="0 0 20 20" fill="currentColor" className="w-3 h-3 text-gray-400">
              <path fillRule="evenodd" d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4zm3 1h2v2H7V5zm2 4H7v2h2V9zm2-4h2v2h-2V5zm2 4h-2v2h2V9z" clipRule="evenodd" />
            </svg>
            {edu.institution}
          </p>
        )}
        {edu.gpa && <div className="mt-1.5"><Tag text={edu.gpa} variant="purple" /></div>}
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

const SECTION_META: Record<string, { icon: string; weight: number; label: string }> = {
  skills:          { icon: "🧠", weight: 0.40, label: "Skills" },
  experience:      { icon: "💼", weight: 0.25, label: "Experience" },
  projects:        { icon: "📂", weight: 0.15, label: "Projects" },
  certifications:  { icon: "🏅", weight: 0.10, label: "Certifications" },
  education:       { icon: "🎓", weight: 0.05, label: "Education" },
  summary:         { icon: "📝", weight: 0.05, label: "Summary" },
};

export default function ATSPage() {
  const [file, setFile]       = useState<File | null>(null);
  const [jd, setJd]           = useState("");
  const [result, setResult]   = useState<ATSResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");

  const handleAnalyze = async () => {
    if (!file || !jd.trim()) { setError("Please upload a resume and paste a job description."); return; }
    setError(""); setLoading(true); setResult(null);
    try {
      const form = new FormData();
      form.append("resume", file);
      form.append("job_description", jd);
      const res = await fetch("http://localhost:8000/api/ats-score", { method: "POST", body: form });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Server error ${res.status}`);
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
          <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight">ATS Resume Analyzer</h1>
          <p className="text-gray-500 mt-2 text-sm">
            Powered by TF-IDF semantic matching · Each section scored independently out of 100
          </p>
        </div>

        {/* Input Panel */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 mb-6">
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Job Description</label>
              <textarea
                className="w-full p-3 border border-gray-200 rounded-xl h-44 text-sm text-gray-800 resize-none focus:outline-none focus:ring-2 focus:ring-blue-400"
                placeholder="Paste the job description here..."
                value={jd}
                onChange={(e) => setJd(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Resume (PDF / DOCX)</label>
              <label className="flex flex-col items-center justify-center h-44 border-2 border-dashed border-gray-200 rounded-xl cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-colors">
                <svg className="w-8 h-8 text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16v1a2 2 0 002 2h12a2 2 0 002-2v-1M12 12V4m0 0L8 8m4-4l4 4" />
                </svg>
                <span className="text-sm text-gray-500">{file ? file.name : "Click to upload or drag & drop"}</span>
                <span className="text-xs text-gray-400 mt-1">PDF, DOCX supported</span>
                <input type="file" accept=".pdf,.docx" className="hidden" onChange={(e) => setFile(e.target.files?.[0] || null)} />
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
                Analyzing Resume…
              </span>
            ) : "Analyze ATS Score"}
          </button>
        </div>

        {/* Results */}
        {result && (
          <div className="space-y-5">

            {/* Score + Quick Stats */}
            <div className="grid md:grid-cols-2 gap-5">
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 flex flex-col items-center justify-center gap-4">
                <ScoreRing score={result.match_score} grade={result.grade} />
                <div className="w-full grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="bg-gray-50 rounded-lg p-2">
                    <div className="font-bold text-gray-800">{result.skills_matched.length}/{result.skills_matched.length + result.missing_skills.length}</div>
                    <div className="text-gray-500">Skills</div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-2">
                    <div className="font-bold text-gray-800">{result.experience_years}y</div>
                    <div className="text-gray-500">Experience</div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-2">
                    <div className="font-bold text-gray-800">{result.certifications_found.length}</div>
                    <div className="text-gray-500">Certs</div>
                  </div>
                </div>
              </div>

              {/* Section Scores — each out of 100 */}
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-sm font-bold text-gray-700">Section Scores (each /100)</h2>
                  <span className="text-xs text-gray-400">weighted → {result.match_score.toFixed(1)} final</span>
                </div>
                <div className="space-y-3">
                  {Object.entries(SECTION_META).map(([key, meta]) => {
                    const score100 = result.section_scores?.[key] ?? 0;
                    const contrib  = result.score_breakdown[`${key} (${Math.round(meta.weight * 100)}%)`] ?? 0;
                    return (
                      <SectionMeter
                        key={key}
                        label={meta.label}
                        score100={score100}
                        contribution={contrib}
                        weight={meta.weight}
                        icon={meta.icon}
                      />
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Skills */}
            <div className="grid md:grid-cols-2 gap-5">
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <h2 className="text-sm font-bold text-green-700 mb-3">✓ Matched Skills ({result.skills_matched.length})</h2>
                <div className="flex flex-wrap">
                  {result.skills_matched.length > 0
                    ? result.skills_matched.map((s) => <Tag key={s} text={s} variant="green" />)
                    : <p className="text-xs text-gray-400">No matching skills found</p>}
                </div>
              </div>
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <h2 className="text-sm font-bold text-red-600 mb-3">✗ Missing Skills ({result.missing_skills.length})</h2>
                <div className="flex flex-wrap">
                  {result.missing_skills.length > 0
                    ? result.missing_skills.map((s) => <Tag key={s} text={s} variant="red" />)
                    : <p className="text-xs text-gray-400">All required skills present 🎉</p>}
                </div>
              </div>
            </div>

            {/* Experience */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-sm font-bold text-gray-700">Work Experience</h2>
                <div className="flex items-center gap-2">
                  {result.section_scores?.experience !== undefined && (
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 border">
                      {result.section_scores.experience.toFixed(0)}/100
                    </span>
                  )}
                  {result.required_experience !== null && (
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium border ${
                      result.experience_years >= result.required_experience
                        ? "bg-green-50 border-green-200 text-green-700"
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
                        ? "bg-green-50 border-green-200 text-green-700"
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
                      <div className={`w-2 h-2 rounded-full mt-1 flex-shrink-0 ${r.is_current ? "bg-green-500" : "bg-blue-400"}`} />
                      <div className="flex-1">
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

            {/* Education */}
            {result.education && result.education.length > 0 && (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-lg">🎓</span>
                  <h2 className="text-sm font-bold text-gray-700">Education</h2>
                  <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 border ml-1">
                    {result.section_scores?.education?.toFixed(0) ?? "–"}/100
                  </span>
                  <span className="ml-auto text-xs px-2 py-0.5 rounded-full font-medium bg-indigo-50 border border-indigo-200 text-indigo-600">
                    {result.education.length} {result.education.length === 1 ? "entry" : "entries"}
                  </span>
                </div>
                <div className="space-y-3">
                  {result.education.map((edu, i) => <EducationCard key={i} edu={edu} index={i} />)}
                </div>
              </div>
            )}

            {/* Certifications */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center gap-2 mb-3">
                <h2 className="text-sm font-bold text-gray-700">Certifications</h2>
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 border">
                  {result.section_scores?.certifications?.toFixed(0) ?? "–"}/100
                </span>
              </div>
              <div className="flex flex-wrap">
                {result.certifications_found.length > 0
                  ? result.certifications_found.map((c) => <Tag key={c} text={c} variant="blue" />)
                  : <p className="text-xs text-gray-400">No certifications detected</p>}
              </div>
            </div>

            {/* Projects */}
            {result.projects.length > 0 && (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <div className="flex items-center gap-2 mb-3">
                  <h2 className="text-sm font-bold text-gray-700">Projects ({result.projects.length})</h2>
                  <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 border">
                    {result.section_scores?.projects?.toFixed(0) ?? "–"}/100
                  </span>
                </div>
                <div className="space-y-3">
                  {result.projects.map((p, i) => (
                    <div key={i} className="border border-gray-100 rounded-xl p-3">
                      <p className="text-xs font-semibold text-gray-800 mb-1">{p.title}</p>
                      <p className="text-xs text-gray-500 mb-2">{p.description}</p>
                      <div className="flex flex-wrap">
                        {p.tech_used.map((t) => <Tag key={t} text={t} variant="blue" />)}
                      </div>
                      {p.impact.length > 0 && (
                        <p className="text-xs text-green-600 mt-1">{p.impact.join(" · ")}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Summary Insights */}
            {result.summary_insights.raw_text && (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <h2 className="text-sm font-bold text-gray-700">Summary Quality</h2>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 border">
                      {result.section_scores?.summary?.toFixed(0) ?? "–"}/100
                    </span>
                  </div>
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                    result.summary_insights.quality_score >= 70 ? "bg-green-100 text-green-700" :
                    result.summary_insights.quality_score >= 40 ? "bg-amber-100 text-amber-700" :
                    "bg-red-100 text-red-700"
                  }`}>{result.summary_insights.quality_score}/100</span>
                </div>
                <p className="text-xs text-gray-600 leading-relaxed mb-3">{result.summary_insights.raw_text}</p>
                {result.summary_insights.suggestions.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-gray-500 mb-1">Suggestions to improve</p>
                    <ul className="space-y-1">
                      {result.summary_insights.suggestions.map((s, i) => (
                        <li key={i} className="text-xs text-amber-700 flex gap-1.5">
                          <span>→</span>{s}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

          </div>
        )}
      </div>
    </div>
  );
}
