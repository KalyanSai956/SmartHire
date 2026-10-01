import { useEffect, useMemo, useState } from "react";
import {
  ArrowUpRight,
  Bookmark,
  BookmarkCheck,
  BriefcaseBusiness,
  Building2,
  ChevronDown,
  Clock3,
  ExternalLink,
  MapPin,
  RefreshCw,
  Search,
  Target,
  X,
} from "lucide-react";

import { useAuth } from "../context/AuthContext";
import {
  getJobRecommendations,
  getJobs,
  getSavedJobs,
  saveJob,
  removeSavedJob,
} from "../services/api";

import "../CSS/Jobs.css";

function normalizeScore(value) {
  const number = Number(value);

  if (!Number.isFinite(number)) {
    return 0;
  }

  return number <= 1 ? Math.round(number * 100) : Math.round(number);
}

function normalizeArray(value) {
  return Array.isArray(value) ? value.filter(Boolean) : [];
}

function normalizeJob(item) {
  const job = item?.job || item;
  const company =
    job?.company && typeof job.company === "object" ? job.company : null;

  return {
    ...job,
    id: job?.id || job?.job_id || item?.job_id,
    title: job?.title || "Untitled Position",
    company:
      company?.name ||
      job?.company_name ||
      (typeof job?.company === "string" ? job.company : null) ||
      "Company",
    company_data: company,
    location: job?.location_display || job?.location || "India",
    remote_type: job?.remote_type || "",
    employment_type: job?.employment_type || "",
    experience_level:
      job?.classified_experience_level || job?.experience_level || "",
    description: job?.description || "",
    application_url: job?.application_url || job?.source_url || "#",
    match_score: normalizeScore(
      item?.match_score ?? job?.match_score ?? item?.score ?? job?.score,
    ),
    role_score: normalizeScore(item?.role_score ?? job?.role_score),
    required_skill_score: normalizeScore(
      item?.required_skill_score ?? job?.required_skill_score,
    ),
    semantic_score: normalizeScore(item?.semantic_score ?? job?.semantic_score),
    experience_score: normalizeScore(
      item?.experience_score ?? job?.experience_score,
    ),
    preferred_skill_score: normalizeScore(
      item?.preferred_skill_score ?? job?.preferred_skill_score,
    ),
    freshness_score: normalizeScore(
      item?.freshness_score ?? job?.freshness_score,
    ),
    matched_skills: normalizeArray(item?.matched_skills ?? job?.matched_skills),
    missing_required_skills: normalizeArray(
      item?.missing_required_skills ?? job?.missing_required_skills,
    ),
    missing_preferred_skills: normalizeArray(
      item?.missing_preferred_skills ?? job?.missing_preferred_skills,
    ),
    missing_skills: normalizeArray(
      item?.missing_skills ??
        job?.missing_skills ??
        item?.missing_required_skills ??
        job?.missing_required_skills,
    ),
    skills: normalizeArray(job?.skills),
    required_skills: normalizeArray(job?.required_skills),
    preferred_skills: normalizeArray(job?.preferred_skills),
    match_reasons: normalizeArray(item?.match_reasons ?? job?.match_reasons),
    posted_at: job?.posted_at || job?.first_seen_at || null,
  };
}

function normalizeRecommendationResponse(data) {
  if (Array.isArray(data)) {
    return data.map(normalizeJob);
  }

  if (Array.isArray(data?.results)) {
    return data.results.map(normalizeJob);
  }

  if (Array.isArray(data?.recommendations)) {
    return data.recommendations.map(normalizeJob);
  }

  if (Array.isArray(data?.jobs)) {
    return data.jobs.map(normalizeJob);
  }

  return [];
}

function normalizeSavedResponse(data) {
  if (Array.isArray(data)) {
    return data.map(normalizeJob);
  }

  if (Array.isArray(data?.jobs)) {
    return data.jobs.map(normalizeJob);
  }

  if (Array.isArray(data?.results)) {
    return data.results.map(normalizeJob);
  }

  if (Array.isArray(data?.saved_jobs)) {
    return data.saved_jobs.map(normalizeJob);
  }

  return [];
}

function formatDate(date) {
  if (!date) {
    return "";
  }

  const parsed = new Date(date);

  if (Number.isNaN(parsed.getTime())) {
    return "";
  }

  const diff = Date.now() - parsed.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));

  if (days <= 0) {
    return "Posted today";
  }

  if (days === 1) {
    return "Posted yesterday";
  }

  if (days < 30) {
    return `Posted ${days} days ago`;
  }

  return parsed.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function getMatchClass(score) {
  if (score >= 80) {
    return "job-match-high";
  }

  if (score >= 60) {
    return "job-match-medium";
  }

  return "job-match-low";
}

function getCompanyInitials(name) {
  if (!name) {
    return "CO";
  }

  const words = name.trim().split(/\s+/).filter(Boolean);

  if (words.length === 1) {
    return words[0].slice(0, 2).toUpperCase();
  }

  return `${words[0][0]}${words[1][0]}`.toUpperCase();
}

function CompanyLogo({ job, large = false }) {
  const logo = job?.company_data?.logo_url;
  const brandColor = job?.company_data?.brand_color;
  const company = job?.company || "Company";

  return (
    <div
      className={`job-company-logo ${large ? "large" : ""}`}
      style={
        brandColor
          ? {
              "--company-brand": brandColor,
            }
          : undefined
      }
    >
      {logo ? (
        <img
          src={logo}
          alt={`${company} logo`}
          onError={(event) => {
            event.currentTarget.style.display = "none";
            event.currentTarget.parentElement?.classList.add("fallback");
          }}
        />
      ) : (
        <span>{getCompanyInitials(company)}</span>
      )}

      <span className="job-company-logo-fallback">
        {getCompanyInitials(company)}
      </span>
    </div>
  );
}

function ScoreBreakdown({ job }) {
  const scores = [
    ["Role compatibility", job.role_score],
    ["Required skills", job.required_skill_score],
    ["Semantic match", job.semantic_score],
    ["Experience", job.experience_score],
    ["Preferred skills", job.preferred_skill_score],
    ["Freshness", job.freshness_score],
  ];

  return (
    <div className="job-score-breakdown">
      {scores.map(([label, value]) => (
        <div className="job-score-item" key={label}>
          <div className="job-score-label">
            <span>{label}</span>
            <strong>{value}%</strong>
          </div>

          <div className="job-score-track">
            <span
              style={{
                width: `${Math.min(Math.max(value, 0), 100)}%`,
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function JobCard({ job, saved, saving, onToggleSave, onOpenDetails }) {
  const score = job.match_score;

  return (
    <article className="job-card">
      <div className="job-card-top">
        <CompanyLogo job={job} />

        <div className="job-card-heading">
          <h3 title={job.title}>{job.title}</h3>

          <p>{job.company}</p>
        </div>

        <button
          type="button"
          className={`job-save-button ${saved ? "saved" : ""}`}
          onClick={() => onToggleSave(job)}
          disabled={saving}
          aria-label={saved ? "Remove saved job" : "Save job"}
        >
          {saved ? <BookmarkCheck size={18} /> : <Bookmark size={18} />}
        </button>
      </div>

      <div className="job-match-row">
        <div
          className={`job-match-badge ${score > 0 ? getMatchClass(score) : "job-match-neutral"}`}
        >
          <Target size={14} />
          <strong>{score > 0 ? `${score}%` : "—"}</strong>
          <span>{score > 0 ? "match" : "match pending"}</span>
        </div>

        {job.role_score > 0 && (
          <span className="job-match-detail">Role {job.role_score}%</span>
        )}

        {job.required_skill_score > 0 && (
          <span className="job-match-detail">
            Skills {job.required_skill_score}%
          </span>
        )}
      </div>

      <div className="job-meta">
        <span>
          <MapPin size={14} />
          {job.location}
        </span>

        {job.remote_type && (
          <span>
            <BriefcaseBusiness size={14} />
            {job.remote_type}
          </span>
        )}

        {job.employment_type && (
          <span>
            <Clock3 size={14} />
            {job.employment_type}
          </span>
        )}

        {job.experience_level && <span>{job.experience_level}</span>}
      </div>

      {job.description && <p className="job-description">{job.description}</p>}

      {job.matched_skills.length > 0 && (
        <div className="job-skills-section">
          <span className="job-skills-label">Matching skills</span>

          <div className="job-skills">
            {job.matched_skills.slice(0, 8).map((skill) => (
              <span key={skill} className="job-skill matched">
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      {job.missing_required_skills.length > 0 && (
        <div className="job-skills-section">
          <span className="job-skills-label missing">
            Required skills to improve
          </span>

          <div className="job-skills">
            {job.missing_required_skills.slice(0, 5).map((skill) => (
              <span key={skill} className="job-skill missing">
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="job-card-footer">
        <span className="job-posted">{formatDate(job.posted_at)}</span>

        <div className="job-card-actions">
          <button
            type="button"
            className="job-details-button"
            onClick={() => onOpenDetails(job)}
          >
            Details
          </button>

          <a
            href={job.application_url}
            target="_blank"
            rel="noopener noreferrer"
            className="job-apply-button"
          >
            View Job
            <ArrowUpRight size={15} />
          </a>
        </div>
      </div>
    </article>
  );
}

function JobDetails({ job, saved, saving, onClose, onToggleSave }) {
  if (!job) {
    return null;
  }

  return (
    <div className="job-drawer-backdrop" onClick={onClose}>
      <aside
        className="job-drawer"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="job-drawer-header">
          <button
            type="button"
            className="job-drawer-close"
            onClick={onClose}
            aria-label="Close details"
          >
            <X size={18} />
          </button>

          <CompanyLogo job={job} large />

          <div className="job-drawer-company">
            <span>{job.company}</span>

            {job.company_data?.website_url && (
              <a
                href={job.company_data.website_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                Company website
                <ExternalLink size={12} />
              </a>
            )}
          </div>
        </div>

        <div className="job-drawer-content">
          <div className="job-drawer-title">
            <span className="jobs-eyebrow">Job opportunity</span>

            <h2>{job.title}</h2>

            <div
              className={`job-drawer-match ${job.match_score > 0 ? getMatchClass(job.match_score) : "job-match-neutral"}`}
            >
              <Target size={16} />
              <strong>
                {job.match_score > 0 ? `${job.match_score}%` : "—"}
              </strong>
              <span>
                {job.match_score > 0 ? "resume match" : "match pending"}
              </span>
            </div>
          </div>

          <div className="job-meta job-drawer-meta">
            <span>
              <MapPin size={14} />
              {job.location}
            </span>

            {job.remote_type && (
              <span>
                <BriefcaseBusiness size={14} />
                {job.remote_type}
              </span>
            )}

            {job.employment_type && (
              <span>
                <Clock3 size={14} />
                {job.employment_type}
              </span>
            )}

            {job.experience_level && <span>{job.experience_level}</span>}
          </div>

          <section className="job-drawer-section">
            <h3>Match breakdown</h3>
            <ScoreBreakdown job={job} />
          </section>

          {job.matched_skills.length > 0 && (
            <section className="job-drawer-section">
              <h3>Matched skills</h3>

              <div className="job-skills">
                {job.matched_skills.map((skill) => (
                  <span key={skill} className="job-skill matched">
                    {skill}
                  </span>
                ))}
              </div>
            </section>
          )}

          {job.missing_required_skills.length > 0 && (
            <section className="job-drawer-section">
              <h3>Required skills to improve</h3>

              <div className="job-skills">
                {job.missing_required_skills.map((skill) => (
                  <span key={skill} className="job-skill missing">
                    {skill}
                  </span>
                ))}
              </div>
            </section>
          )}

          {job.missing_preferred_skills.length > 0 && (
            <section className="job-drawer-section">
              <h3>Preferred skills to improve</h3>

              <div className="job-skills">
                {job.missing_preferred_skills.map((skill) => (
                  <span key={skill} className="job-skill preferred">
                    {skill}
                  </span>
                ))}
              </div>
            </section>
          )}

          {job.match_reasons.length > 0 && (
            <section className="job-drawer-section">
              <h3>Why this matches</h3>

              <ul className="job-reasons">
                {job.match_reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            </section>
          )}

          {job.description && (
            <section className="job-drawer-section">
              <h3>About the role</h3>
              <p className="job-drawer-description">{job.description}</p>
            </section>
          )}
        </div>

        <div className="job-drawer-footer">
          <button
            type="button"
            className={`job-drawer-save ${saved ? "saved" : ""}`}
            onClick={() => onToggleSave(job)}
            disabled={saving}
          >
            {saved ? <BookmarkCheck size={16} /> : <Bookmark size={16} />}

            {saved ? "Saved" : "Save Job"}
          </button>

          <a
            href={job.application_url}
            target="_blank"
            rel="noopener noreferrer"
            className="job-drawer-apply"
          >
            View Job
            <ArrowUpRight size={16} />
          </a>
        </div>
      </aside>
    </div>
  );
}

export default function Jobs() {
  const { accessToken } = useAuth();

  const [jobs, setJobs] = useState([]);
  const [allJobs, setAllJobs] = useState([]);
  const [savedJobs, setSavedJobs] = useState([]);
  const [activeTab, setActiveTab] = useState("recommended");
  const [search, setSearch] = useState("");
  const [locationFilter, setLocationFilter] = useState("");
  const [remoteType, setRemoteType] = useState("");
  const [employmentType, setEmploymentType] = useState("");
  const [experienceFilter, setExperienceFilter] = useState("");
  const [companyFilter, setCompanyFilter] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [sortBy, setSortBy] = useState("match");
  const [loading, setLoading] = useState(true);
  const [savedLoading, setSavedLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [savingId, setSavingId] = useState(null);
  const [error, setError] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [selectedJob, setSelectedJob] = useState(null);

  async function loadRecommendations({
    refresh = false,
    remote = remoteType,
    employment = employmentType,
  } = {}) {
    if (!accessToken) {
      return;
    }

    try {
      if (refresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setError("");

      const data = await getJobRecommendations({
        token: accessToken,
        matchThreshold: 0.25,
        candidateCount: 50,
        resultCount: 20,
        remoteType: remote,
        employmentType: employment,
      });

      setJobs(normalizeRecommendationResponse(data));
    } catch (err) {
      console.error("Job recommendations error:", err);

      setError(err?.message || "Unable to load recommended jobs.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  async function loadAllJobs({ refresh = false } = {}) {
    if (!accessToken) {
      return;
    }

    try {
      if (refresh && activeTab === "all") {
        setRefreshing(true);
      }

      const data = await getJobs({
        token: accessToken,
        page: 1,
        limit: 50,
      });

      setAllJobs(normalizeRecommendationResponse(data));
    } catch (err) {
      console.error("All jobs error:", err);
      setError(err?.message || "Unable to load available jobs.");
    } finally {
      if (refresh && activeTab === "all") {
        setRefreshing(false);
      }
    }
  }

  async function loadSavedJobs() {
    if (!accessToken) {
      return;
    }

    try {
      setSavedLoading(true);

      const data = await getSavedJobs(accessToken);

      setSavedJobs(normalizeSavedResponse(data));
    } catch (err) {
      console.error("Saved jobs error:", err);
    } finally {
      setSavedLoading(false);
    }
  }

  useEffect(() => {
    if (!accessToken) {
      return;
    }

    loadRecommendations();
    loadAllJobs();
    loadSavedJobs();
  }, [accessToken]);

  async function handleToggleSave(job) {
    if (!accessToken || !job.id) {
      return;
    }

    try {
      setSavingId(job.id);

      const isSaved = savedJobs.some((saved) => saved.id === job.id);

      if (isSaved) {
        await removeSavedJob(job.id, accessToken);

        setSavedJobs((current) =>
          current.filter((saved) => saved.id !== job.id),
        );
      } else {
        await saveJob(job.id, accessToken);

        setSavedJobs((current) => [...current, job]);
      }

      if (selectedJob && selectedJob.id === job.id) {
        setSelectedJob({
          ...job,
        });
      }
    } catch (err) {
      console.error("Save job error:", err);

      setError(err?.message || "Unable to update saved job.");
    } finally {
      setSavingId(null);
    }
  }

  const companies = useMemo(() => {
    const source =
      activeTab === "recommended"
        ? jobs
        : activeTab === "all"
          ? allJobs
          : savedJobs;

    return [
      ...new Map(
        source
          .filter((job) => job.company)
          .map((job) => [job.company, job.company]),
      ).values(),
    ].sort();
  }, [activeTab, jobs, allJobs, savedJobs]);

  const roles = useMemo(() => {
    const source =
      activeTab === "recommended"
        ? jobs
        : activeTab === "all"
          ? allJobs
          : savedJobs;

    return [...new Set(source.map((job) => job.title).filter(Boolean))].sort();
  }, [activeTab, jobs, allJobs, savedJobs]);

  const visibleJobs = useMemo(() => {
    const source =
      activeTab === "recommended"
        ? jobs
        : activeTab === "all"
          ? allJobs
          : savedJobs;

    const query = search.trim().toLowerCase();

    const location = locationFilter.trim().toLowerCase();

    const company = companyFilter.trim().toLowerCase();

    const role = roleFilter.trim().toLowerCase();

    const filtered = source.filter((job) => {
      const searchable = [
        job.title,
        job.company,
        job.description,
        job.location,
        ...job.skills,
      ]
        .join(" ")
        .toLowerCase();

      const matchesSearch = !query || searchable.includes(query);

      const matchesLocation =
        !location || job.location.toLowerCase().includes(location);

      const matchesCompany =
        !company || job.company.toLowerCase().includes(company);

      const matchesRole = !role || job.title.toLowerCase().includes(role);

      const matchesRemote =
        !remoteType ||
        job.remote_type.toLowerCase() === remoteType.toLowerCase();

      const matchesEmployment =
        !employmentType ||
        job.employment_type
          .toLowerCase()
          .includes(employmentType.toLowerCase());

      const matchesExperience =
        !experienceFilter ||
        job.experience_level
          .toLowerCase()
          .includes(experienceFilter.toLowerCase());

      return (
        matchesSearch &&
        matchesLocation &&
        matchesCompany &&
        matchesRole &&
        matchesRemote &&
        matchesEmployment &&
        matchesExperience
      );
    });

    return filtered.sort((a, b) => {
      if (sortBy === "recent") {
        return new Date(b.posted_at || 0) - new Date(a.posted_at || 0);
      }

      if (sortBy === "skills") {
        return b.required_skill_score - a.required_skill_score;
      }

      return b.match_score - a.match_score;
    });
  }, [
    activeTab,
    jobs,
    savedJobs,
    search,
    locationFilter,
    companyFilter,
    roleFilter,
    remoteType,
    employmentType,
    experienceFilter,
    sortBy,
  ]);

  function handleTabChange(tab) {
    setActiveTab(tab);
    setSelectedJob(null);
    setError("");
  }

  function handleRefresh() {
    if (activeTab === "all") {
      loadAllJobs({ refresh: true });
      return;
    }

    if (activeTab === "saved") {
      loadSavedJobs();
      return;
    }

    loadRecommendations({ refresh: true });
  }

  function clearFilters() {
    setSearch("");
    setLocationFilter("");
    setRemoteType("");
    setEmploymentType("");
    setExperienceFilter("");
    setCompanyFilter("");
    setRoleFilter("");
    setSortBy("match");
  }

  const hasFilters = Boolean(
    search ||
    locationFilter ||
    remoteType ||
    employmentType ||
    experienceFilter ||
    companyFilter ||
    roleFilter,
  );

  const isSaved = selectedJob
    ? savedJobs.some((saved) => saved.id === selectedJob.id)
    : false;

  if (loading) {
    return (
      <div className="jobs-page">
        <div className="jobs-loading">
          <h2>Finding jobs for you</h2>

          <p>Matching your resume against available opportunities...</p>

          <div className="jobs-loading-bar">
            <span />
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="mx-auto max-w-7xl jobs-page">
        <section className="jobs-header">
          <div>
            <div className="jobs-eyebrow">Jobs matched to your resume</div>
          </div>

          <button
            type="button"
            className="jobs-refresh-button"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            <RefreshCw size={15} className={refreshing ? "jobs-spin" : ""} />

            {refreshing ? "Refreshing..." : "Refresh"}
          </button>
        </section>

        {error && (
          <div className="jobs-error">
            <div>
              <strong>Unable to complete the request</strong>
              <span>{error}</span>
            </div>

            <button type="button" onClick={() => setError("")}>
              <X size={16} />
            </button>
          </div>
        )}

        <div className="jobs-tabs">
          <button
            type="button"
            className={activeTab === "recommended" ? "active" : ""}
            onClick={() => handleTabChange("recommended")}
          >
            Recommended
            <span>{jobs.length}</span>
          </button>

          <button
            type="button"
            className={activeTab === "saved" ? "active" : ""}
            onClick={() => setActiveTab("saved")}
          >
            <Bookmark size={15} />
            Saved
            <span>{savedJobs.length}</span>
          </button>
        </div>

        <section className="jobs-toolbar">
          <div className="jobs-search">
            <Search size={17} />

            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search jobs, companies, skills..."
            />

            {search && (
              <button
                type="button"
                onClick={() => setSearch("")}
                aria-label="Clear search"
              >
                <X size={15} />
              </button>
            )}
          </div>

          <button
            type="button"
            className={`jobs-filter-toggle ${showFilters ? "active" : ""}`}
            onClick={() => setShowFilters((current) => !current)}
          >
            Filters
            <ChevronDown size={15} />
          </button>
        </section>

        {showFilters && (
          <section className="jobs-filter-panel">
            <div className="jobs-filter-field">
              <label>Role</label>

              <select
                value={roleFilter}
                onChange={(event) => setRoleFilter(event.target.value)}
              >
                <option value="">All roles</option>

                {roles.map((role) => (
                  <option key={role} value={role}>
                    {role}
                  </option>
                ))}
              </select>
            </div>

            <div className="jobs-filter-field">
              <label>Company</label>

              <select
                value={companyFilter}
                onChange={(event) => setCompanyFilter(event.target.value)}
              >
                <option value="">All companies</option>

                {companies.map((company) => (
                  <option key={company} value={company}>
                    {company}
                  </option>
                ))}
              </select>
            </div>

            <div className="jobs-filter-field">
              <label>Location</label>

              <input
                value={locationFilter}
                onChange={(event) => setLocationFilter(event.target.value)}
                placeholder="India, Bengaluru..."
              />
            </div>

            <div className="jobs-filter-field">
              <label>Work arrangement</label>

              <select
                value={remoteType}
                onChange={(event) => {
                  const value = event.target.value;

                  setRemoteType(value);

                  if (activeTab === "recommended") {
                    loadRecommendations({
                      remote: value,
                      employment: employmentType,
                    });
                  }
                }}
              >
                <option value="">Any</option>
                <option value="remote">Remote</option>
                <option value="hybrid">Hybrid</option>
                <option value="onsite">On-site</option>
              </select>
            </div>

            <div className="jobs-filter-field">
              <label>Employment</label>

              <select
                value={employmentType}
                onChange={(event) => {
                  const value = event.target.value;

                  setEmploymentType(value);

                  if (activeTab === "recommended") {
                    loadRecommendations({
                      remote: remoteType,
                      employment: value,
                    });
                  }
                }}
              >
                <option value="">Any</option>
                <option value="full-time">Full-time</option>
                <option value="part-time">Part-time</option>
                <option value="internship">Internship</option>
                <option value="contract">Contract</option>
              </select>
            </div>

            <div className="jobs-filter-field">
              <label>Experience</label>

              <select
                value={experienceFilter}
                onChange={(event) => setExperienceFilter(event.target.value)}
              >
                <option value="">Any level</option>
                <option value="fresher">Fresher</option>
                <option value="intern">Intern</option>
                <option value="entry">Entry level</option>
                <option value="mid">Mid level</option>
                <option value="senior">Senior</option>
              </select>
            </div>

            <div className="jobs-filter-field">
              <label>Sort</label>

              <select
                value={sortBy}
                onChange={(event) => setSortBy(event.target.value)}
              >
                <option value="match">Best match</option>
                <option value="recent">Most recent</option>
                <option value="skills">Skill match</option>
              </select>
            </div>

            {hasFilters && (
              <button
                type="button"
                className="jobs-clear-filters"
                onClick={clearFilters}
              >
                Clear filters
              </button>
            )}
          </section>
        )}

        <div className="jobs-result-heading">
          {savedLoading && <span>Updating saved jobs...</span>}
        </div>

        {visibleJobs.length === 0 ? (
          <div className="jobs-empty">
            <div className="jobs-empty-icon">
              {activeTab === "saved" ? (
                <Bookmark size={22} />
              ) : (
                <BriefcaseBusiness size={22} />
              )}
            </div>

            <h2>
              {activeTab === "saved"
                ? "No saved jobs yet"
                : activeTab === "all"
                  ? "No jobs found"
                  : "No matching jobs found"}
            </h2>

            <p>
              {activeTab === "saved"
                ? "Save opportunities you want to come back to later."
                : hasFilters
                  ? "Try changing your search or filters."
                  : activeTab === "all"
                    ? "There are no active jobs available right now."
                    : "We couldn't find recommendations for your current resume."}
            </p>

            {hasFilters && (
              <button
                type="button"
                className="jobs-empty-button"
                onClick={clearFilters}
              >
                Clear filters
              </button>
            )}
          </div>
        ) : (
          <div className="jobs-grid">
            {visibleJobs.map((job) => (
              <JobCard
                key={job.id}
                job={job}
                saved={savedJobs.some((saved) => saved.id === job.id)}
                saving={savingId === job.id}
                onToggleSave={handleToggleSave}
                onOpenDetails={setSelectedJob}
              />
            ))}
          </div>
        )}
      </div>

      {selectedJob && (
        <JobDetails
          job={selectedJob}
          saved={isSaved}
          saving={savingId === selectedJob.id}
          onClose={() => setSelectedJob(null)}
          onToggleSave={handleToggleSave}
        />
      )}
    </>
  );
}
