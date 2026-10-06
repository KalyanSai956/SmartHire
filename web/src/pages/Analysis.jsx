import { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Download,
  FileText,
  Sparkles,
} from "lucide-react";
import { Link, useLocation, useParams } from "react-router-dom";

import SkillValidation from "../components/SkillValidation";
import { getHistory, getHistoryPdf, generatePdfBlob } from "../services/api";
import { useAuth } from "../context/AuthContext";
import {
  getAtsScore,
  getJdMatch,
  normalizeHistory,
  scoreStatus,
} from "../utils/analysis";

import "../CSS/Analysis.css";
/* =========================================================
   HELPERS
   ========================================================= */

function text(value) {
  if (value === null || value === undefined) return "";

  if (typeof value === "string" || typeof value === "number") {
    return String(value).trim();
  }

  return "";
}

function firstText(object, keys) {
  if (!object || typeof object !== "object") return "";

  for (const key of keys) {
    const value = text(object[key]);

    if (value) return value;
  }

  return "";
}

function skillName(value, index = 0) {
  if (typeof value === "string") {
    return value.trim();
  }

  return (
    firstText(value, ["name", "skill", "title", "label", "requirement"]) ||
    `Skill ${index + 1}`
  );
}

function itemTitle(item, fallback = "") {
  if (typeof item === "string") {
    return item.trim();
  }

  return (
    firstText(item, [
      "title",
      "name",
      "heading",
      "label",
      "issue",
      "problem",
      "category",
      "area",
      "action",
      "recommendation",
      "recommendation_text",
      "recommendationText",
      "suggestion",
      "suggestion_text",
      "message",
    ]) || fallback
  );
}

function itemDescription(item) {
  if (typeof item === "string" || !item || typeof item !== "object") {
    return "";
  }

  return firstText(item, [
    "description",
    "message",
    "feedback",
    "text",
    "details",
    "explanation",
    "reason",
    "action_text",
    "actionText",
    "recommendation",
    "recommendation_text",
    "recommendationText",
    "suggestion",
    "suggestion_text",
  ]);
}

function normalizeItems(value) {
  if (!value) return [];

  if (Array.isArray(value)) {
    return value
      .map((item) => ({
        title: itemTitle(item),
        description: itemDescription(item),
        raw: item,
      }))
      .filter((item) => item.title || item.description);
  }

  if (typeof value === "string") {
    return value
      .split(/\r?\n|;|\|/)
      .map((item) => item.trim())
      .filter(Boolean)
      .map((item) => ({
        title: item,
        description: "",
        raw: item,
      }));
  }

  if (typeof value === "object") {
    const nested =
      value.items ??
      value.data ??
      value.results ??
      value.recommendations ??
      value.actions ??
      value.issues ??
      value.feedback;

    if (Array.isArray(nested)) {
      return normalizeItems(nested);
    }

    const title = itemTitle(value);
    const description = itemDescription(value);

    if (title || description) {
      return [
        {
          title,
          description,
          raw: value,
        },
      ];
    }
  }

  return [];
}

function normalizeIssueSummary(value) {
  if (Array.isArray(value) || (value && typeof value === "object")) {
    return normalizeItems(value);
  }

  const summary = text(value);

  if (!summary) return [];

  const knownIssues = [
    "Most Skills Lack Supporting Evidence",
    "No Quantifiable Achievements Found",
  ];

  const extracted = [];
  let remaining = summary;

  for (const issue of knownIssues) {
    if (remaining.toLowerCase().includes(issue.toLowerCase())) {
      extracted.push({
        title: issue,
        description: "",
        raw: issue,
      });

      remaining = remaining.replace(new RegExp(issue, "ig"), "");
    }
  }

  const rest = remaining
    .split(/\r?\n|;|\||•/)
    .map((item) => item.trim())
    .filter(Boolean)
    .map((item) => ({
      title: item,
      description: "",
      raw: item,
    }));

  return [...extracted, ...rest];
}

function collectionFrom(...values) {
  for (const value of values) {
    const result = normalizeItems(value);

    if (result.length) {
      return result;
    }
  }

  return [];
}

function percentage(value) {
  const number = Number(value);

  if (!Number.isFinite(number)) return 0;

  return number <= 1 ? number * 100 : number;
}

function formatPercent(value, decimals = 0) {
  const number = percentage(value);

  return `${number.toFixed(decimals)}%`;
}

function scoreLabel(score) {
  if (score >= 85) return "Strong Resume";
  if (score >= 70) return "Good Resume";
  if (score >= 55) return "Fair Resume";

  return "Needs Improvement";
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = filename;

  document.body.appendChild(link);
  link.click();
  link.remove();

  setTimeout(() => URL.revokeObjectURL(url), 100);
}

function extractRecommendations(item) {
  if (!item || typeof item !== "object") {
    return [];
  }

  const nested =
    item.recommendations ??
    item.actions ??
    item.action_items ??
    item.actionItems;

  return normalizeItems(nested);
}

function buildActionItems(analysis, detailedFeedback, criticalIssues) {
  const explicit = collectionFrom(
    analysis.action_items,
    analysis.actionItems,
    analysis.recommendations,
    analysis.recommendation,
    analysis.improvement_actions,
    analysis.improvementActions,
  );

  if (explicit.length) {
    return explicit;
  }

  const nested = [];

  for (const item of detailedFeedback) {
    for (const recommendation of extractRecommendations(item.raw)) {
      nested.push(recommendation);
    }
  }

  if (nested.length) {
    return nested;
  }

  const fromFeedback = detailedFeedback
    .filter((item) => item.description)
    .map((item) => ({
      title: item.title || "Improve this area",
      description: item.description,
      raw: item.raw,
    }));

  if (fromFeedback.length) {
    return fromFeedback;
  }

  return criticalIssues.map((item) => ({
    title: item.title,
    description:
      item.description ||
      "Review this issue in the corresponding resume section and add supporting evidence.",
    raw: item.raw,
  }));
}

/* =========================================================
   GRAMMAR HELPERS (display only)
   ========================================================= */

const GRAMMAR_SECTIONS = [
  {
    key: "critical",
    title: "Critical errors",
    description: "Fix these first. They hurt readability and recruiter trust.",
  },
  {
    key: "moderate",
    title: "Moderate errors",
    description: "Noticeable mistakes that are worth correcting.",
  },
  {
    key: "minor",
    title: "Minor suggestions",
    description: "Small polish items and style tweaks.",
  },
];

function grammarSeverity(item, fallback = "minor") {
  const label = firstText(item, [
    "severity",
    "level",
    "priority",
    "category",
    "type",
  ]).toLowerCase();

  if (/crit|high|major|severe/.test(label)) return "critical";
  if (/mod|medium|warn/.test(label)) return "moderate";
  if (label) return "minor";

  return fallback;
}

function grammarErrorItem(raw) {
  if (typeof raw === "string") {
    return { original: raw.trim(), suggestion: "", message: "", context: "" };
  }

  const firstSuggestion = Array.isArray(raw?.suggestions)
    ? text(raw.suggestions[0])
    : "";

  return {
    original: firstText(raw, [
      "original",
      "error",
      "incorrect",
      "word",
      "text",
      "phrase",
      "match",
    ]),
    suggestion:
      firstText(raw, [
        "suggestion",
        "correction",
        "replacement",
        "corrected",
        "fix",
        "correct",
      ]) || firstSuggestion,
    message: firstText(raw, [
      "message",
      "description",
      "explanation",
      "reason",
      "rule",
    ]),
    context: firstText(raw, ["context", "sentence"]),
  };
}

function normalizeGrammarErrors(grammar) {
  const buckets = { critical: [], moderate: [], minor: [] };

  if (!grammar || typeof grammar !== "object") return buckets;

  const flat =
    grammar.errors ??
    grammar.issues ??
    grammar.details ??
    grammar.matches ??
    grammar.error_list ??
    grammar.errorList;

  if (Array.isArray(flat)) {
    for (const raw of flat) {
      buckets[grammarSeverity(raw)].push(grammarErrorItem(raw));
    }
  } else if (flat && typeof flat === "object") {
    for (const key of Object.keys(buckets)) {
      if (Array.isArray(flat[key])) {
        buckets[key] = flat[key].map(grammarErrorItem);
      }
    }
  }

  const found = Object.values(buckets).some((list) => list.length);

  if (!found) {
    for (const key of Object.keys(buckets)) {
      const list =
        [
          grammar[`${key}_errors`],
          grammar[`${key}_issues`],
          grammar[`${key}Errors`],
          grammar[`${key}_list`],
          grammar[key],
        ].find((value) => Array.isArray(value)) || [];

      buckets[key] = list.map(grammarErrorItem);
    }
  }

  return buckets;
}

/* =========================================================
   COMPONENT
   ========================================================= */

export default function Analysis() {
  const { id } = useParams();
  const location = useLocation();
  const { accessToken } = useAuth();

  const initialAnalysis = location.state?.analysis || null;

  const initialFilename = location.state?.filename || "Resume";

  const [analysis, setAnalysis] = useState(initialAnalysis);

  const [filename, setFilename] = useState(initialFilename);

  const [loading, setLoading] = useState(!initialAnalysis);

  const [error, setError] = useState("");

  const [pdfBusy, setPdfBusy] = useState(false);

  /* =======================================================
     LOAD ANALYSIS
     ======================================================= */

  useEffect(() => {
    if (id === "new" && initialAnalysis) {
      setAnalysis(initialAnalysis);

      setFilename(initialFilename);

      setLoading(false);

      return;
    }

    if (!id || id === "new") {
      setLoading(false);
      return;
    }

    let cancelled = false;

    async function loadAnalysis() {
      try {
        setLoading(true);
        setError("");

        const response = await getHistory(accessToken);

        const history = Array.isArray(response)
          ? response
          : Array.isArray(response?.data)
            ? response.data
            : Array.isArray(response?.history)
              ? response.history
              : [];

        const rows = normalizeHistory(history);

        const selected = rows.find((item) => String(item.id) === String(id));

        if (!selected) {
          throw new Error(`Analysis with ID ${id} was not found.`);
        }

        if (!cancelled) {
          setAnalysis(selected.result);

          setFilename(selected.filename || "Resume");
        }
      } catch (err) {
        console.error("Failed to load analysis:", err);

        if (!cancelled) {
          setError(err.message || "Could not load analysis.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadAnalysis();

    return () => {
      cancelled = true;
    };
  }, [id, accessToken, initialAnalysis, initialFilename]);

  /* =========================================================
     DERIVED DATA
     ========================================================= */

  const data = useMemo(() => {
    if (!analysis) return null;

    /* -------------------------------------------------------
       NEW PHASE 3 DATA
       ------------------------------------------------------- */

    const advancedATS = analysis.advanced_ats || analysis.advancedATS || null;

    const resumeQuality =
      analysis.resume_quality || analysis.resumeQuality || null;

    const resumeProfile =
      analysis.resume_profile || analysis.resumeProfile || null;

    const jdIntelligence =
      analysis.jd_intelligence || analysis.jdIntelligence || null;

    /* -------------------------------------------------------
       LEGACY DATA
       ------------------------------------------------------- */

    const componentScores =
      analysis.component_scores || analysis.componentScores || {};

    const legacyJD =
      analysis.jd_comparison ||
      analysis.jd_match_analysis ||
      analysis.jdMatchAnalysis ||
      {};

    const skillValidation =
      analysis.skill_validation_details ||
      analysis.skillValidationDetails ||
      {};

    const grammar =
      analysis.grammar_analysis ||
      analysis.grammar_results ||
      analysis.grammar ||
      {};

    const atsCompatibility =
      analysis.ats_compatibility ||
      analysis.ats_compatibility_analysis ||
      analysis.atsCompatibility ||
      {};

    /* -------------------------------------------------------
       SKILL VALIDATION
       ------------------------------------------------------- */

    const validated =
      Array.isArray(skillValidation.validated) &&
      skillValidation.validated.length
        ? skillValidation.validated
        : Array.isArray(skillValidation.validated_skills)
          ? skillValidation.validated_skills
          : [];

    const unvalidated =
      Array.isArray(skillValidation.unvalidated) &&
      skillValidation.unvalidated.length
        ? skillValidation.unvalidated
        : Array.isArray(skillValidation.unvalidated_skills)
          ? skillValidation.unvalidated_skills
          : [];

    const totalSkills = Number(
      skillValidation.total ??
        skillValidation.total_skills ??
        validated.length + unvalidated.length,
    );

    const validatedCount = Number(
      skillValidation.validated_count ??
        skillValidation.validatedCount ??
        validated.length,
    );

    const validationRate = Number(
      skillValidation.validation_pct ??
        skillValidation.validation_rate ??
        (totalSkills ? (validatedCount / totalSkills) * 100 : 0),
    );

    /* -------------------------------------------------------
       FEEDBACK
       ------------------------------------------------------- */

    const detailedFeedback = collectionFrom(
      analysis.detailed_feedback,
      analysis.detailedFeedback,
      analysis.feedback,
    );

    const criticalIssues = collectionFrom(
      analysis.critical_issues,
      analysis.criticalIssues,
      analysis.issues,
      analysis.critical_feedback,
      analysis.criticalFeedback,
    );

    const normalizedCriticalIssues = criticalIssues.length
      ? criticalIssues
      : normalizeIssueSummary(
          analysis.issues_summary ?? analysis.issuesSummary,
        );

    const legacyStrengths = collectionFrom(
      analysis.strengths,
      analysis.resume_strengths,
      analysis.resumeStrengths,
    );

    const qualityStrengths = Array.isArray(resumeQuality?.strengths)
      ? resumeQuality.strengths.map((item) => ({
          title:
            typeof item === "string"
              ? item
              : itemTitle(item, "Resume strength"),
          description: typeof item === "string" ? "" : itemDescription(item),
          raw: item,
        }))
      : [];

    const strengths = qualityStrengths.length
      ? qualityStrengths
      : legacyStrengths;

    const qualityWeaknesses = Array.isArray(resumeQuality?.weaknesses)
      ? resumeQuality.weaknesses.map((item) => ({
          title:
            typeof item === "string"
              ? item
              : itemTitle(item, "Resume weakness"),
          description: typeof item === "string" ? "" : itemDescription(item),
          raw: item,
        }))
      : [];

    const actionItems = buildActionItems(
      analysis,
      detailedFeedback,
      normalizedCriticalIssues,
    );

    /* -------------------------------------------------------
       ADVANCED ATS SCORE
       ------------------------------------------------------- */

    const advancedBreakdown =
      advancedATS?.score_breakdown || advancedATS?.scoreBreakdown || {};

    const advancedScore = Number(
      advancedATS?.ats_score ?? advancedATS?.atsScore,
    );

    const legacyScore = Number(getAtsScore(analysis)) || 0;

    const score = Number.isFinite(advancedScore) ? advancedScore : legacyScore;

    /* -------------------------------------------------------
       ADVANCED JD MATCH
       ------------------------------------------------------- */

    const advancedJDMatch = Number(
      advancedATS?.jd_match ?? advancedATS?.jdMatch,
    );

    const legacyMatch = Number(getJdMatch(analysis)) || 0;

    const match = Number.isFinite(advancedJDMatch)
      ? advancedJDMatch
      : legacyMatch;

    /* -------------------------------------------------------
       ADVANCED KEYWORDS
       ------------------------------------------------------- */

    const keywordAnalysis =
      advancedATS?.keyword_analysis || advancedATS?.keywordAnalysis || {};

    const advancedMatchedKeywords = Array.isArray(
      keywordAnalysis.matched_keywords,
    )
      ? keywordAnalysis.matched_keywords
      : Array.isArray(keywordAnalysis.matchedKeywords)
        ? keywordAnalysis.matchedKeywords
        : [];

    const advancedMissingKeywords = Array.isArray(
      keywordAnalysis.missing_keywords,
    )
      ? keywordAnalysis.missing_keywords
      : Array.isArray(keywordAnalysis.missingKeywords)
        ? keywordAnalysis.missingKeywords
        : [];

    const matchedKeywords = advancedMatchedKeywords.length
      ? advancedMatchedKeywords
      : Array.isArray(legacyJD.matched_keywords)
        ? legacyJD.matched_keywords
        : Array.isArray(analysis.matched_keywords)
          ? analysis.matched_keywords
          : [];

    const missingKeywords = advancedMissingKeywords.length
      ? advancedMissingKeywords
      : Array.isArray(legacyJD.missing_keywords)
        ? legacyJD.missing_keywords
        : Array.isArray(analysis.missing_keywords)
          ? analysis.missing_keywords
          : [];

    /* -------------------------------------------------------
       ADVANCED SKILLS
       ------------------------------------------------------- */

    const advancedMatchedSkills = Array.isArray(advancedATS?.matched_skills)
      ? advancedATS.matched_skills
      : Array.isArray(advancedATS?.matchedSkills)
        ? advancedATS.matchedSkills
        : [];

    const advancedMissingSkills = Array.isArray(advancedATS?.missing_skills)
      ? advancedATS.missing_skills
      : Array.isArray(advancedATS?.missingSkills)
        ? advancedATS.missingSkills
        : [];

    /* -------------------------------------------------------
       FALLBACK SKILLS GAP
       ------------------------------------------------------- */

    const legacySkillsGap = Array.isArray(legacyJD.skills_gap)
      ? legacyJD.skills_gap
      : Array.isArray(analysis.skills_gap)
        ? analysis.skills_gap
        : [];

    const skillsGap = advancedMissingSkills.length
      ? advancedMissingSkills
      : legacySkillsGap;

    /* -------------------------------------------------------
       SCORE BREAKDOWN
       ------------------------------------------------------- */

    const scoreRows = advancedATS
      ? [
          [
            "Keyword Match",
            Number(
              advancedBreakdown.keyword_match ??
                advancedBreakdown.keywordMatch ??
                0,
            ),
            100,
          ],
          [
            "Semantic Match",
            Number(
              advancedBreakdown.semantic_match ??
                advancedBreakdown.semanticMatch ??
                0,
            ),
            100,
          ],
          [
            "Skills Match",
            Number(
              advancedBreakdown.skills_match ??
                advancedBreakdown.skillsMatch ??
                0,
            ),
            100,
          ],
          [
            "Experience Match",
            Number(
              advancedBreakdown.experience_match ??
                advancedBreakdown.experienceMatch ??
                0,
            ),
            100,
          ],
          [
            "Project Match",
            Number(
              advancedBreakdown.project_match ??
                advancedBreakdown.projectMatch ??
                0,
            ),
            100,
          ],
          [
            "Resume Quality",
            Number(
              advancedBreakdown.resume_quality ??
                advancedBreakdown.resumeQuality ??
                resumeQuality?.overall_score ??
                0,
            ),
            100,
          ],
        ]
      : [
          [
            "Formatting",
            componentScores.formatting ??
              componentScores.format_score ??
              atsCompatibility.formatting_score ??
              0,
            20,
          ],
          [
            "Content Quality",
            componentScores.content_quality ??
              componentScores.content_score ??
              atsCompatibility.content_quality_score ??
              0,
            25,
          ],
          [
            "ATS Compatibility",
            componentScores.ats_compatibility ??
              componentScores.ats_score ??
              atsCompatibility.score ??
              atsCompatibility.ats_compatibility_score ??
              0,
            15,
          ],
          [
            "Keywords & Skills",
            componentScores.keyword_skills ??
              componentScores.keywords ??
              componentScores.keyword_score ??
              0,
            25,
          ],
          [
            "Skill Validation",
            componentScores.skill_validation ??
              componentScores.skill_validation_score ??
              0,
            15,
          ],
        ];

    /* -------------------------------------------------------
       RESUME QUALITY
       ------------------------------------------------------- */

    const qualityScore = Number(
      resumeQuality?.overall_score ?? resumeQuality?.overallScore,
    );

    const normalizedQualityScore = Number.isFinite(qualityScore)
      ? qualityScore
      : null;

    /* -------------------------------------------------------
       JD INTELLIGENCE
       ------------------------------------------------------- */

    const requiredSkills = Array.isArray(jdIntelligence?.required_skills)
      ? jdIntelligence.required_skills
      : Array.isArray(jdIntelligence?.requiredSkills)
        ? jdIntelligence.requiredSkills
        : [];

    const preferredSkills = Array.isArray(jdIntelligence?.preferred_skills)
      ? jdIntelligence.preferred_skills
      : Array.isArray(jdIntelligence?.preferredSkills)
        ? jdIntelligence.preferredSkills
        : [];

    const responsibilities = Array.isArray(jdIntelligence?.responsibilities)
      ? jdIntelligence.responsibilities
      : [];

    const educationRequirements = Array.isArray(
      jdIntelligence?.education_requirements,
    )
      ? jdIntelligence.education_requirements
      : Array.isArray(jdIntelligence?.educationRequirements)
        ? jdIntelligence.educationRequirements
        : [];

    const experienceRequirement =
      jdIntelligence?.experience_requirement ||
      jdIntelligence?.experienceRequirement ||
      {};

    const jobTitle =
      text(jdIntelligence?.job_title) ||
      text(jdIntelligence?.jobTitle) ||
      text(analysis.job_title) ||
      text(analysis.jobTitle);

    const domain = text(jdIntelligence?.domain);

    const seniority = text(jdIntelligence?.seniority);

    /* -------------------------------------------------------
       GRAMMAR
       ------------------------------------------------------- */

    const totalGrammarErrors = Number(
      grammar.total_errors ?? grammar.total ?? 0,
    );

    const criticalGrammarErrors = Number(
      grammar.critical_errors ?? grammar.critical ?? 0,
    );

    const moderateGrammarErrors = Number(
      grammar.moderate_errors ?? grammar.moderate ?? 0,
    );

    const minorGrammarErrors = Number(
      grammar.minor_errors ?? grammar.minor ?? 0,
    );

    /* -------------------------------------------------------
       LEGACY ATS COMPATIBILITY
       ------------------------------------------------------- */

    const atsCompatibilityScore = Number(
      atsCompatibility.score ??
        atsCompatibility.ats_compatibility_score ??
        componentScores.ats_compatibility ??
        componentScores.ats_score ??
        0,
    );

    const formattingScore = Number(
      atsCompatibility.formatting_score ??
        componentScores.formatting ??
        componentScores.format_score ??
        0,
    );

    const contentQualityScore = Number(
      atsCompatibility.content_quality_score ??
        componentScores.content_quality ??
        componentScores.content_score ??
        0,
    );

    return {
      score,
      match,

      advancedATS,
      advancedBreakdown,

      resumeQuality,
      resumeProfile,
      jdIntelligence,

      jobTitle,
      domain,
      seniority,

      requiredSkills,
      preferredSkills,
      responsibilities,
      educationRequirements,
      experienceRequirement,

      componentScores,
      legacyJD,

      skillValidation,
      validated,
      unvalidated,
      totalSkills,
      validatedCount,
      validationRate,

      detailedFeedback,
      criticalIssues: normalizedCriticalIssues,

      strengths,
      qualityWeaknesses,

      actionItems,

      scoreRows,

      normalizedQualityScore,

      matchedKeywords,
      missingKeywords,

      advancedMatchedSkills,
      advancedMissingSkills,

      skillsGap,

      grammar,

      totalGrammarErrors,
      criticalGrammarErrors,
      moderateGrammarErrors,
      minorGrammarErrors,
      grammarErrors: normalizeGrammarErrors(grammar),

      atsCompatibilityScore,
      formattingScore,
      contentQualityScore,

      parsingFriendliness:
        text(atsCompatibility.parsing_friendliness) ||
        text(atsCompatibility.parsingFriendliness) ||
        "Uses clean, standard formatting readable by automated parser",

      interpretation: text(analysis.interpretation),

      hasAdvancedATS: Boolean(advancedATS),

      hasJDIntelligence: Boolean(jdIntelligence),
    };
  }, [analysis]);

  /* =========================================================
     LOADING / ERROR
     ========================================================= */

  if (loading) {
    return (
      <div className="mx-auto max-w-4xl analysis-loading-page">
        <div className="analysis-loading-container">
          <aside className="loading-score-card">
            <h2>Your Score</h2>

            <div className="loading-score-gauge" aria-hidden="true">
              <div className="loading-gauge-arc" />
              <div className="loading-gauge-needle" />
            </div>

            <div className="loading-score-lines" aria-hidden="true">
              <span />
              <span />
            </div>

            <div className="loading-score-sections" aria-hidden="true">
              <div>
                <span>CONTENT</span>
                <i />
              </div>
              <div>
                <span>SECTION</span>
                <i />
              </div>
              <div>
                <span>ATS ESSENTIALS</span>
                <i />
              </div>
            </div>

            <button type="button" disabled className="loading-unlock-button">
              Unlock Full Report
            </button>
          </aside>

          <main className="loading-analysis-card" aria-live="polite">
            <div className="loading-step loading-step-1">
              <div className="loading-step-icon">
                <CheckCircle2 size={21} />
              </div>
              <span>Parsing your resume</span>
            </div>

            <div className="loading-divider" />

            <div className="loading-step loading-step-2">
              <div className="loading-step-icon">
                <CheckCircle2 size={21} />
              </div>
              <span>Analyzing your experience</span>
            </div>

            <div className="loading-step loading-step-3">
              <div className="loading-step-icon">
                <CheckCircle2 size={21} />
              </div>
              <span>Extracting your skills</span>
            </div>

            <div className="loading-step loading-step-4">
              <div className="loading-step-icon">
                <CheckCircle2 size={21} />
              </div>
              <span>Generating recommendations</span>
            </div>
          </main>
        </div>
      </div>
    );
  }

  if (error && !analysis) {
    return (
      <div className="page-shell">
        <div className="inline-error">
          <strong>Unable to load analysis</strong>

          <br />

          {error}
        </div>

        <Link to="/history" className="button secondary">
          <ArrowLeft size={16} />
          Back to History
        </Link>
      </div>
    );
  }

  if (!analysis || !data) {
    return (
      <div className="page-shell">
        <div className="empty-state">
          <span className="empty-icon">
            <FileText size={18} />
          </span>

          <strong>No analysis data available.</strong>

          <span>The selected analysis could not be found.</span>

          <Link to="/history" className="text-link">
            Back to History
          </Link>
        </div>
      </div>
    );
  }

  /* =========================================================
     DOWNLOAD
     ========================================================= */

  async function downloadReport() {
    try {
      setPdfBusy(true);
      setError("");

      const blob =
        id && id !== "new"
          ? await getHistoryPdf(id, accessToken)
          : await generatePdfBlob(analysis, accessToken);

      const safeName = filename
        .replace(/\.[^/.]+$/, "")
        .replace(/[^\w.-]+/g, "_");

      downloadBlob(blob, `smarthire_${safeName}.pdf`);
    } catch (err) {
      console.error("PDF generation error:", err);

      setError(err.message || "Failed to generate PDF.");
    } finally {
      setPdfBusy(false);
    }
  }

  const score = data.score;

  const grammarSegments = [
    { key: "critical", label: "Critical", count: data.criticalGrammarErrors },
    { key: "moderate", label: "Moderate", count: data.moderateGrammarErrors },
    { key: "minor", label: "Minor", count: data.minorGrammarErrors },
  ];

  const grammarSegmentTotal = grammarSegments.reduce(
    (sum, item) => sum + (Number(item.count) || 0),
    0,
  );

  const hasGrammarDetails = GRAMMAR_SECTIONS.some(
    (section) => data.grammarErrors[section.key].length > 0,
  );

  return (
    <div className="mx-auto max-w-5xl px-6 page-shell analysis-page">
      {/* =====================================================
          TOP BAR
          ===================================================== */}

      <div className="result-topbar">
        <Link to="/history" className="back-link">
          <ArrowLeft size={15} />
          Back to History
        </Link>

        <div className="result-topbar-right">
          <p>{filename}</p>

          <button
            className="button secondary"
            onClick={downloadReport}
            disabled={pdfBusy}
          >
            <Download size={16} />

            {pdfBusy ? "Generating..." : "Download Report"}
          </button>
        </div>
      </div>

      {error && <div className="inline-error">{error}</div>}

      {/* =====================================================
          HEADER
          ===================================================== */}

      <section className="result-header">
        <span className={`success-pill ${scoreStatus(score)}`}>
          {score >= 70 ? <CheckCircle2 size={15} /> : <AlertCircle size={15} />}

          {scoreLabel(score)}
        </span>
      </section>

      {/* =====================================================
          ADVANCED JD PROFILE
          ===================================================== */}

      {data.hasJDIntelligence && (
        <section className="panel jd-profile-card">
          <div className="panel-header">
            <div>
              <span className="section-kicker">JOB INTELLIGENCE</span>

              <h2>{data.jobTitle || "Target Job"}</h2>

              <p>Structured understanding of the supplied job description.</p>
            </div>
          </div>

          <div className="jd-profile-meta">
            {data.domain && (
              <div>
                <span>Domain</span>

                <strong>{data.domain}</strong>
              </div>
            )}

            {data.seniority && (
              <div>
                <span>Seniority</span>

                <strong>{data.seniority}</strong>
              </div>
            )}

            {data.experienceRequirement?.minimum_years != null && (
              <div>
                <span>Minimum Experience</span>

                <strong>
                  {data.experienceRequirement.minimum_years} years
                </strong>
              </div>
            )}

            {data.requiredSkills.length > 0 && (
              <div>
                <span>Required Skills</span>

                <strong>{data.requiredSkills.length}</strong>
              </div>
            )}

            {data.preferredSkills.length > 0 && (
              <div>
                <span>Preferred Skills</span>

                <strong>{data.preferredSkills.length}</strong>
              </div>
            )}
          </div>

          {data.requiredSkills.length > 0 && (
            <div className="jd-skill-section">
              <h3>Required Skills</h3>

              <div className="chips">
                {data.requiredSkills.map((item, index) => (
                  <span className="chip danger" key={index}>
                    {skillName(item, index)}
                  </span>
                ))}
              </div>
            </div>
          )}

          {data.preferredSkills.length > 0 && (
            <div className="jd-skill-section">
              <h3>Preferred Skills</h3>

              <div className="chips">
                {data.preferredSkills.map((item, index) => (
                  <span className="chip neutral" key={index}>
                    {skillName(item, index)}
                  </span>
                ))}
              </div>
            </div>
          )}
        </section>
      )}

      {/* =====================================================
          SCORE SUMMARY
          ===================================================== */}

      <div className="result-summary">
        {/* OVERALL SCORE */}

        <section className="panel score-hero">
          <p className="stat-label">OVERALL ATS SCORE</p>

          <div
            className="score-ring"
            style={{
              "--score": `${Math.min(100, Math.max(0, score))}%`,
            }}
          >
            <div>
              <strong>{Math.round(score)}</strong>

              <span>/100</span>
            </div>
          </div>

          <span className={`score-caption ${scoreStatus(score)}`}>
            {score >= 85 ? (
              <CheckCircle2 size={14} />
            ) : (
              <AlertCircle size={14} />
            )}

            {score >= 85
              ? "Excellent score"
              : score >= 70
                ? "Some improvements needed"
                : score >= 55
                  ? "Below average"
                  : "Significant improvements needed"}
          </span>
        </section>

        {/* ADVANCED SCORE BREAKDOWN */}

        <section className="panel breakdown-card">
          <div className="panel-header">
            <div>
              <h2>
                {data.hasAdvancedATS ? "ATS Breakdown" : "Score Breakdown"}
              </h2>

              <p>
                {data.hasAdvancedATS
                  ? "How your resume matches the target role."
                  : "Your resume performance across key ATS areas."}
              </p>
            </div>
          </div>

          <div className="score-bars">
            {data.scoreRows.map(([label, value, max]) => {
              const numericValue = Number(value) || 0;

              const percent = max
                ? Math.min(100, (numericValue / max) * 100)
                : 0;

              return (
                <div className="score-bar-row" key={label}>
                  <span>{label}</span>

                  <div className="bar">
                    <i
                      className={percent >= 70 ? "green" : "orange"}
                      style={{
                        width: `${percent}%`,
                      }}
                    />
                  </div>

                  <strong>
                    {Math.round(numericValue)}/{max}
                  </strong>
                </div>
              );
            })}
          </div>
        </section>

        {/* JOB MATCH */}

        <section className="panel match-card">
          <p className="stat-label">JOB MATCH</p>

          <strong className="match-big">
            {data.match > 0 ? `${Math.round(data.match)}%` : "—"}
          </strong>

          <span className="good-pill">
            {data.match >= 80
              ? "Strong Match"
              : data.match > 0
                ? "Review JD Gaps"
                : "No JD Provided"}
          </span>

          <div className="match-mini">
            <div>
              <span>Matched Keywords</span>

              <strong>{data.matchedKeywords.length}</strong>
            </div>

            <div>
              <span>Missing Keywords</span>

              <strong className="orange-text">
                {data.missingKeywords.length}
              </strong>
            </div>

            <div>
              <span>Semantic Similarity</span>

              <strong>
                {data.hasAdvancedATS &&
                data.advancedBreakdown.semantic_match != null
                  ? `${Math.round(
                      Number(data.advancedBreakdown.semantic_match),
                    )}%`
                  : data.legacyJD.semantic_similarity != null
                    ? formatPercent(data.legacyJD.semantic_similarity)
                    : "—"}
              </strong>
            </div>
          </div>
        </section>
      </div>

      {/* =====================================================
          RESUME QUALITY
          ===================================================== */}

      {data.resumeQuality && (
        <section className="panel resume-quality-summary">
          <div className="panel-header">
            <div>
              <span className="section-kicker">RESUME INTELLIGENCE</span>

              <h2>Resume Quality</h2>

              <p>
                Deterministic quality analysis of your resume structure and
                content.
              </p>
            </div>

            {data.normalizedQualityScore !== null && (
              <strong className="quality-score-big">
                {data.normalizedQualityScore}
                /100
              </strong>
            )}
          </div>

          <div className="quality-metrics">
            {[
              ["Contact", data.resumeQuality.contact_score],
              ["Structure", data.resumeQuality.structure_score],
              ["Experience", data.resumeQuality.experience_score],
              ["Projects", data.resumeQuality.projects_score],
              ["Skills", data.resumeQuality.skills_score],
              ["Content", data.resumeQuality.content_score],
            ].map(([label, value]) => (
              <div key={label}>
                <span>{label}</span>

                <strong>{Number(value ?? 0)}</strong>
              </div>
            ))}
          </div>

          {data.resumeQuality.recommendations?.length > 0 && (
            <div className="quality-recommendations">
              <h3>Resume Quality Recommendations</h3>

              <div className="feedback-list">
                {data.resumeQuality.recommendations.map((item, index) => (
                  <div className="feedback-item" key={index}>
                    <CheckCircle2
                      size={18}
                      className="green-text feedback-icon"
                    />

                    <div className="feedback-content">
                      <strong>
                        {typeof item === "string"
                          ? item
                          : itemTitle(item, `Recommendation ${index + 1}`)}
                      </strong>

                      {typeof item !== "string" && itemDescription(item) && (
                        <p>{itemDescription(item)}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      )}

      {/* =====================================================
          STRENGTHS + ISSUES
          ===================================================== */}

      <div className="result-content-grid">
        <section className="panel">
          <div className="panel-header">
            <div>
              <span className="section-kicker">STRENGTHS</span>

              <h2>What You're Doing Well</h2>
            </div>
          </div>

          {data.strengths.length ? (
            <div className="feedback-list">
              {data.strengths.map((item, index) => (
                <div className="feedback-item" key={index}>
                  <CheckCircle2
                    size={18}
                    className="green-text feedback-icon"
                  />

                  <div className="feedback-content">
                    <strong>{item.title || `Strength ${index + 1}`}</strong>

                    {item.description && <p>{item.description}</p>}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-result-message">
              <Sparkles size={18} />

              <span>
                No explicit strengths were returned for this analysis.
              </span>
            </div>
          )}
        </section>

        <section className="panel">
          <div className="panel-header">
            <div>
              <span className="section-kicker">CRITICAL ISSUES</span>

              <h2>Issues to Address First</h2>
            </div>
          </div>

          {data.criticalIssues.length ? (
            <div className="issue-list">
              {data.criticalIssues.map((item, index) => (
                <div className="issue-card" key={index}>
                  <div className="issue-icon">
                    <AlertCircle size={17} />
                  </div>

                  <div className="issue-content">
                    <strong>{item.title || `Issue ${index + 1}`}</strong>

                    {item.description && <p>{item.description}</p>}
                  </div>
                </div>
              ))}
            </div>
          ) : data.qualityWeaknesses.length ? (
            <div className="issue-list">
              {data.qualityWeaknesses.map((item, index) => (
                <div className="issue-card" key={index}>
                  <div className="issue-icon">
                    <AlertCircle size={17} />
                  </div>

                  <div className="issue-content">
                    <strong>{item.title || `Improvement ${index + 1}`}</strong>

                    {item.description && <p>{item.description}</p>}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-result-message success-empty">
              <CheckCircle2 size={18} />

              <span>No critical issues were detected.</span>
            </div>
          )}
        </section>
      </div>

      {/* =====================================================
          SKILL VALIDATION
          ===================================================== */}

      <SkillValidation
        totalSkills={data.totalSkills}
        validatedSkills={data.validatedCount}
        validationRate={data.validationRate}
        matchedSkills={data.validated}
        missingSkills={data.unvalidated}
      />

      {/* =====================================================
          ADVANCED JD COMPARISON
          ===================================================== */}

      {(data.matchedKeywords.length ||
        data.missingKeywords.length ||
        data.advancedMatchedSkills.length ||
        data.advancedMissingSkills.length) > 0 && (
        <section className="panel jd-details-card">
          <div className="panel-header">
            <div>
              <span className="section-kicker">JOB DESCRIPTION MATCH</span>

              <h2>Resume vs Job Requirements</h2>

              <p>
                Compare your resume with the structured requirements detected
                from the job description.
              </p>
            </div>
          </div>

          <div className="jd-detail-grid">
            {/* MATCHED SKILLS */}

            {data.advancedMatchedSkills.length > 0 && (
              <div>
                <h3>Matched Required Skills</h3>

                <div className="chips">
                  {data.advancedMatchedSkills.map((item, index) => (
                    <span className="chip success" key={index}>
                      <CheckCircle2 size={12} />
                      {skillName(item, index)}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* MISSING SKILLS */}

            {data.advancedMissingSkills.length > 0 && (
              <div>
                <h3>Missing Required Skills</h3>

                <div className="chips">
                  {data.advancedMissingSkills.map((item, index) => (
                    <span className="chip danger" key={index}>
                      <AlertCircle size={12} />
                      {skillName(item, index)}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* MATCHED KEYWORDS */}

            {data.matchedKeywords.length > 0 && (
              <div>
                <h3>Matched Keywords</h3>

                <div className="chips">
                  {data.matchedKeywords.map((item, index) => (
                    <span className="chip success" key={index}>
                      <CheckCircle2 size={12} />
                      {skillName(item, index)}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* MISSING KEYWORDS */}

            {data.missingKeywords.length > 0 && (
              <div>
                <h3>Missing Keywords</h3>

                <div className="chips">
                  {data.missingKeywords.map((item, index) => (
                    <span className="chip danger" key={index}>
                      <AlertCircle size={12} />
                      {skillName(item, index)}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      {/* =====================================================
          RESPONSIBILITIES
          ===================================================== */}

      {data.responsibilities.length > 0 && (
        <section className="panel">
          <div className="panel-header">
            <div>
              <span className="section-kicker">TARGET ROLE</span>

              <h2>Job Responsibilities</h2>
            </div>
          </div>

          <div className="feedback-list">
            {data.responsibilities.map((item, index) => (
              <div className="feedback-item" key={index}>
                <CheckCircle2 size={18} className="green-text feedback-icon" />

                <div className="feedback-content">
                  <strong>Responsibility {index + 1}</strong>

                  <p>{item}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* =====================================================
          DETAILED FEEDBACK
          ===================================================== */}

      <section className="panel feedback-panel">
        <div className="panel-header">
          <div>
            <span className="section-kicker">DETAILED FEEDBACK</span>

            <h2>Resume Improvement Areas</h2>

            <p>
              {data.detailedFeedback.length
                ? `${data.detailedFeedback.length} issue(s) flagged.`
                : "No detailed feedback available."}
            </p>
          </div>
        </div>

        {data.detailedFeedback.length ? (
          <div className="recommendation-list">
            {data.detailedFeedback.map((item, index) => (
              <div className="recommendation-card" key={index}>
                <div className="recommendation-number">{index + 1}</div>

                <div className="recommendation-content">
                  <strong>
                    {item.title || `Improvement Area ${index + 1}`}
                  </strong>

                  {item.description && <p>{item.description}</p>}

                  {extractRecommendations(item.raw).length > 0 && (
                    <div className="nested-recommendations">
                      {extractRecommendations(item.raw).map(
                        (recommendation, recommendationIndex) => (
                          <div
                            className="nested-recommendation"
                            key={recommendationIndex}
                          >
                            <ArrowRight size={13} />

                            <span>
                              {recommendation.title ||
                                recommendation.description}
                            </span>
                          </div>
                        ),
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-result-message">
            No detailed feedback returned.
          </div>
        )}
      </section>

      {/* =====================================================
          ACTION ITEMS
          ===================================================== */}

      <section className="panel action-items-panel">
        <div className="panel-header">
          <div>
            <span className="section-kicker">ACTION ITEMS</span>

            <h2>Improve Your Resume</h2>

            <p>Concrete steps generated from the analysis findings.</p>
          </div>
        </div>

        {data.actionItems.length ? (
          <div className="action-items-list">
            {data.actionItems.map((item, index) => (
              <div className="action-item" key={index}>
                <span className="action-item-number">{index + 1}</span>

                <div>
                  <strong>{item.title || "Recommended action"}</strong>

                  {item.description && <p>{item.description}</p>}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-result-message">
            No action items were returned.
          </div>
        )}
      </section>

      {/* =====================================================
          GRAMMAR + LEGACY ATS COMPATIBILITY
          ===================================================== */}

      <div className="analysis-bottom-grid">
        {/* GRAMMAR */}

        <section className="analysis-card panel grammar-analysis-card">
          <div className="analysis-card-header">
            <div>
              <span className="section-kicker">GRAMMAR & SPELLING</span>

              <h2>Language Quality</h2>

              <p>
                {data.totalGrammarErrors === 0
                  ? "No grammar or spelling errors were found in your resume."
                  : `${data.totalGrammarErrors} issue${
                      data.totalGrammarErrors === 1 ? "" : "s"
                    } found across your resume.`}
              </p>
            </div>

            <span
              className={
                data.totalGrammarErrors === 0
                  ? "status-badge clean"
                  : "status-badge warning"
              }
            >
              {data.totalGrammarErrors === 0 ? "CLEAN" : "REVIEW"}
            </span>
          </div>

          <div className="grammar-grid">
            <div>
              <span>Total Errors</span>

              <strong>{data.totalGrammarErrors}</strong>
            </div>

            <div>
              <span>Critical</span>

              <strong className="grammar-critical-number">
                {data.criticalGrammarErrors}
              </strong>
            </div>

            <div>
              <span>Moderate</span>

              <strong className="grammar-moderate-number">
                {data.moderateGrammarErrors}
              </strong>
            </div>

            <div>
              <span>Minor</span>

              <strong className="grammar-minor-number">
                {data.minorGrammarErrors}
              </strong>
            </div>
          </div>

          {grammarSegmentTotal > 0 && (
            <div className="grammar-distribution">
              <div
                className="grammar-distribution-bar"
                role="img"
                aria-label="Error severity distribution"
              >
                {grammarSegments.map((item) =>
                  Number(item.count) > 0 ? (
                    <span
                      key={item.key}
                      className={item.key}
                      style={{
                        width: `${(Number(item.count) / grammarSegmentTotal) * 100}%`,
                      }}
                    />
                  ) : null,
                )}
              </div>

              <div className="grammar-distribution-legend">
                {grammarSegments.map((item) => (
                  <span key={item.key}>
                    <i className={item.key} />
                    {item.label}
                    <b>
                      {Math.round(
                        ((Number(item.count) || 0) / grammarSegmentTotal) * 100,
                      )}
                      %
                    </b>
                  </span>
                ))}
              </div>
            </div>
          )}

          {GRAMMAR_SECTIONS.map((section) => {
            const list = data.grammarErrors[section.key];

            if (!list.length) return null;

            return (
              <div className="grammar-error-section" key={section.key}>
                <div className={`grammar-error-section-header ${section.key}`}>
                  <div>
                    <h3>{section.title}</h3>

                    <p>{section.description}</p>
                  </div>

                  <span>{list.length}</span>
                </div>

                <div className="grammar-error-list">
                  {list.map((error, index) => (
                    <div
                      className={`grammar-error-item ${section.key}`}
                      key={index}
                    >
                      <div className="grammar-error-main">
                        <span className="grammar-error-number">
                          {index + 1}
                        </span>

                        <div className="grammar-error-content">
                          <div className="grammar-error-correction">
                            <strong>
                              {error.original ||
                                error.suggestion ||
                                error.message ||
                                `Issue ${index + 1}`}
                            </strong>

                            {error.original && error.suggestion && (
                              <>
                                <ArrowRight size={14} />

                                <strong className="grammar-suggestion">
                                  {error.suggestion}
                                </strong>
                              </>
                            )}
                          </div>

                          {error.message &&
                            error.message !== error.original && (
                              <p>{error.message}</p>
                            )}

                          {error.context && (
                            <blockquote className="grammar-error-context">
                              {error.context}
                            </blockquote>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}

          {data.totalGrammarErrors === 0 ? (
            <div className="grammar-clean-result">
              <CheckCircle2 size={20} />

              <div>
                <strong>All clear</strong>

                <p>No grammar or spelling errors detected.</p>
              </div>
            </div>
          ) : (
            !hasGrammarDetails && (
              <div className="analysis-status warning grammar-review-note">
                <AlertCircle size={18} />

                <div>
                  <strong>REVIEW REQUIRED</strong>

                  <p>Grammar or spelling issues were detected.</p>
                </div>
              </div>
            )
          )}
        </section>

        {/* LEGACY COMPATIBILITY */}

        <section className="analysis-card panel">
          <div className="analysis-card-header">
            <div>
              <span className="section-kicker">ATS COMPATIBILITY</span>
            </div>

            <span
              className={
                data.atsCompatibilityScore >= 13
                  ? "status-badge clean"
                  : data.atsCompatibilityScore >= 10
                    ? "status-badge warning"
                    : "status-badge danger"
              }
            >
              {data.atsCompatibilityScore >= 13
                ? "EXCELLENT"
                : data.atsCompatibilityScore >= 10
                  ? "GOOD"
                  : "NEEDS WORK"}
            </span>
          </div>

          <div className="compatibility-score">
            <div>
              <span>Score</span>

              <strong>{data.atsCompatibilityScore}/15</strong>
            </div>

            <div className="compatibility-progress">
              <span
                style={{
                  width: `${Math.min(
                    100,
                    Math.max(0, (data.atsCompatibilityScore / 15) * 100),
                  )}%`,
                }}
              />
            </div>
          </div>

          <div className="compatibility-metrics">
            <div>
              <span>Formatting Score</span>

              <strong>{data.formattingScore}/20</strong>
            </div>

            <div>
              <span>Legacy Content Quality</span>

              <strong>{data.contentQualityScore}/25</strong>
            </div>
          </div>

          <div className="parsing-info">
            <span>Parsing Friendliness</span>

            <p>
              <CheckCircle2 size={15} />

              {data.parsingFriendliness}
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
