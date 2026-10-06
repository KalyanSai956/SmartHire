import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowUpRight,
  Briefcase,
  CheckCircle2,
  ChevronRight,
  Cpu,
  Database,
  ExternalLink,
  FileText,
  Inbox,
  KeyRound,
  Layers,
  LayoutDashboard,
  Percent,
  Rss,
  Server,
  ShieldCheck,
  Sparkles,
  Users,
  Zap,
} from "lucide-react";
import {
  getAdminOverview,
  getAdminUsers,
  getAdminJobs,
  getAdminSources,
  getAdminEmbeddings,
  getAdminLLMUsage,
} from "../services/api";
import { useAuth } from "../context/AuthContext";
import "../CSS/Admin.css";

const emptyData = {
  stats: {
    users: 0,
    active_jobs: 0,
    job_embeddings: 0,
    resume_analyses: 0,
    platform_tokens: 0,
    byok_tokens: 0,
  },
  system: {
    api: false,
    supabase: false,
    redis: false,
    embeddings: false,
  },
};

/* =========================================================
   NAVIGATION CONFIG (presentation only)
   ========================================================= */

const NAV_GROUPS = ["Platform", "Data", "Intelligence"];

const SECTIONS = [
  {
    id: "overview",
    group: "Platform",
    label: "Overview",
    icon: LayoutDashboard,
    title: "System Overview",
    description:
      "Monitor SmartHire platform activity and infrastructure status.",
  },
  {
    id: "users",
    group: "Data",
    label: "Users",
    icon: Users,
    title: "Users",
    description: "Monitor registered SmartHire accounts.",
    hint: "Accounts and verification status",
  },
  {
    id: "jobs",
    group: "Data",
    label: "Jobs",
    icon: Briefcase,
    title: "Jobs",
    description: "Monitor the current job inventory and application links.",
    hint: "Inventory and application links",
  },
  {
    id: "sources",
    group: "Data",
    label: "Job Sources",
    icon: Rss,
    title: "Job Sources",
    description: "Monitor configured job ingestion sources.",
    hint: "Configured ingestion sources",
  },
  {
    id: "embeddings",
    group: "Intelligence",
    label: "Embeddings",
    icon: Database,
    title: "Embeddings",
    description: "Monitor job embedding coverage and RAG readiness.",
    hint: "Coverage and RAG readiness",
  },
  {
    id: "llm",
    group: "Intelligence",
    label: "LLM Usage",
    icon: Sparkles,
    title: "LLM Usage",
    description: "Monitor platform and BYOK token usage.",
    hint: "Platform and BYOK tokens",
  },
];

/* =========================================================
   SMALL COMPONENTS
   ========================================================= */

function StatCard({ label, value, icon: Icon, tone = "blue", suffix = "" }) {
  return (
    <div className="admin-stat-card" data-tone={tone}>
      <div className="admin-stat-top">
        <span>{label}</span>

        <div className="admin-stat-icon">
          <Icon size={17} strokeWidth={2.2} />
        </div>
      </div>

      <strong>
        {Number(value || 0).toLocaleString()}
        {suffix}
      </strong>
    </div>
  );
}

function StatusRow({ label, status, icon: Icon }) {
  const state = status ? "online" : "offline";

  return (
    <div className="admin-status-row">
      <div>
        <span className="admin-status-icon" data-status={state}>
          <Icon size={16} />
        </span>

        <span>{label}</span>
      </div>

      <strong data-status={state}>
        <span className="admin-status-dot" data-status={state} />
        {status ? "Operational" : "Unavailable"}
      </strong>
    </div>
  );
}

function EmptyState({ text, icon: Icon = Inbox }) {
  return (
    <div className="admin-empty">
      <span className="admin-empty-icon">
        <Icon size={20} />
      </span>

      {text}
    </div>
  );
}

function getInitials(user) {
  const source = (user?.full_name || user?.email || "?").trim();
  const parts = source.split(/[\s@._-]+/).filter(Boolean);

  return ((parts[0]?.[0] || "?") + (parts[1]?.[0] || "")).toUpperCase();
}

/* =========================================================
   PAGE
   ========================================================= */

export default function Admin() {
  const { accessToken, loading: authLoading } = useAuth();

  const navigate = useNavigate();

  const [activeSection, setActiveSection] = useState("overview");

  const [overview, setOverview] = useState(emptyData);

  const [users, setUsers] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [sources, setSources] = useState([]);
  const [embeddings, setEmbeddings] = useState(null);
  const [llmUsage, setLlmUsage] = useState(null);

  const [loading, setLoading] = useState(true);

  const [sectionLoading, setSectionLoading] = useState(false);

  const [error, setError] = useState("");

  useEffect(() => {
    if (authLoading || !accessToken) {
      return;
    }

    let mounted = true;

    async function loadOverview() {
      try {
        setLoading(true);
        setError("");

        const result = await getAdminOverview(accessToken);

        if (mounted) {
          setOverview(result);
        }
      } catch (err) {
        if (!mounted) {
          return;
        }

        if (err?.message?.includes("Admin access")) {
          navigate("/dashboard", {
            replace: true,
          });

          return;
        }

        setError(err?.message || "Admin dashboard is temporarily unavailable.");
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    loadOverview();

    return () => {
      mounted = false;
    };
  }, [accessToken, authLoading, navigate]);

  async function openSection(section) {
    setActiveSection(section);
    setError("");

    if (section === "overview") {
      return;
    }

    setSectionLoading(true);

    try {
      if (section === "users") {
        const result = await getAdminUsers(accessToken);

        setUsers(result.users || []);
      }

      if (section === "jobs") {
        const result = await getAdminJobs(accessToken);

        setJobs(result.jobs || []);
      }

      if (section === "sources") {
        const result = await getAdminSources(accessToken);

        setSources(result.sources || []);
      }

      if (section === "embeddings") {
        const result = await getAdminEmbeddings(accessToken);

        setEmbeddings(result);
      }

      if (section === "llm") {
        const result = await getAdminLLMUsage(accessToken);

        setLlmUsage(result);
      }
    } catch (err) {
      setError(err?.message || "Admin data is temporarily unavailable.");
    } finally {
      setSectionLoading(false);
    }
  }

  if (authLoading || loading) {
    return (
      <div className="admin-loading">
        <div className="admin-spinner" />
        <span>Loading admin dashboard...</span>
      </div>
    );
  }

  /* ---------- Display-only derived values ---------- */

  const current =
    SECTIONS.find((section) => section.id === activeSection) || SECTIONS[0];

  const allSystemsOnline = Object.values(overview.system || {}).every(Boolean);

  const providerEntries = Object.entries(llmUsage?.provider_totals || {});

  const providerTotal = providerEntries.reduce(
    (sum, [, tokens]) => sum + (Number(tokens) || 0),
    0,
  );

  const platformTokens = Number(llmUsage?.platform_tokens || 0);
  const byokTokens = Number(llmUsage?.byok_tokens || 0);
  const tokenTotal = platformTokens + byokTokens;
  const platformShare = tokenTotal ? (platformTokens / tokenTotal) * 100 : 0;
  const byokShare = tokenTotal ? (byokTokens / tokenTotal) * 100 : 0;

  return (
    <div className="admin-page">
      <aside className="admin-sidebar">
        <div className="admin-brand">
          <div className="admin-brand-mark">S</div>

          <div>
            <strong>SmartHire</strong>

            <span>Admin Console</span>
          </div>
        </div>

        <nav className="admin-nav" aria-label="Admin sections">
          {NAV_GROUPS.map((group) => (
            <div className="admin-nav-group" key={group}>
              <span className="admin-nav-label">{group}</span>

              {SECTIONS.filter((section) => section.group === group).map(
                (section) => {
                  const Icon = section.icon;

                  return (
                    <button
                      type="button"
                      key={section.id}
                      className={`admin-nav-item ${
                        activeSection === section.id ? "active" : ""
                      }`}
                      aria-current={
                        activeSection === section.id ? "page" : undefined
                      }
                      onClick={() => openSection(section.id)}
                    >
                      <Icon size={17} strokeWidth={2.1} />
                      {section.label}
                    </button>
                  );
                },
              )}
            </div>
          ))}
        </nav>

        <div className="admin-sidebar-bottom">
          <button type="button" onClick={() => navigate("/dashboard")}>
            <ArrowLeft size={15} />
            Back to SmartHire
          </button>
        </div>
      </aside>

      <main className="admin-main">
        <header className="admin-header">
          <div>
            <div className="admin-breadcrumb">
              <span>Admin</span>
              <ChevronRight size={12} />
              <span>{current.label}</span>
            </div>

            <h1>{current.title}</h1>

            <p>{current.description}</p>
          </div>

          <div className="admin-header-badge">
            <i />
            Admin Access
          </div>
        </header>

        {error && (
          <div className="admin-error" role="alert">
            <span>
              <AlertTriangle size={14} />
            </span>

            <div>
              <strong>Dashboard unavailable</strong>

              <p>{error}</p>
            </div>
          </div>
        )}

        {sectionLoading ? (
          <div className="admin-section-loading">
            <div className="admin-spinner" />
            <span>Loading section...</span>
          </div>
        ) : (
          <>
            {activeSection === "overview" && (
              <>
                <section className="admin-stats-grid">
                  <StatCard
                    label="Users"
                    value={overview.stats.users}
                    icon={Users}
                    tone="blue"
                  />

                  <StatCard
                    label="Active Jobs"
                    value={overview.stats.active_jobs}
                    icon={Briefcase}
                    tone="green"
                  />

                  <StatCard
                    label="Job Embeddings"
                    value={overview.stats.job_embeddings}
                    icon={Database}
                    tone="violet"
                  />

                  <StatCard
                    label="Resume Analyses"
                    value={overview.stats.resume_analyses}
                    icon={FileText}
                    tone="amber"
                  />

                  <StatCard
                    label="Platform Tokens"
                    value={overview.stats.platform_tokens}
                    icon={Zap}
                    tone="cyan"
                  />

                  <StatCard
                    label="BYOK Tokens"
                    value={overview.stats.byok_tokens}
                    icon={KeyRound}
                    tone="slate"
                  />
                </section>

                <section className="admin-content-grid">
                  <div className="admin-panel">
                    <div className="admin-panel-header">
                      <div>
                        <span className="admin-panel-kicker">
                          INFRASTRUCTURE
                        </span>

                        <h2>System Status</h2>
                      </div>

                      <span className="admin-live">LIVE</span>
                    </div>

                    <div
                      className="admin-health-banner"
                      data-state={allSystemsOnline ? "ok" : "degraded"}
                    >
                      {allSystemsOnline ? (
                        <CheckCircle2 size={16} />
                      ) : (
                        <AlertTriangle size={16} />
                      )}

                      {allSystemsOnline
                        ? "All systems operational"
                        : "Some services are unavailable"}
                    </div>

                    <div className="admin-status-list">
                      <StatusRow
                        label="API Server"
                        status={overview.system.api}
                        icon={Server}
                      />

                      <StatusRow
                        label="Supabase"
                        status={overview.system.supabase}
                        icon={Database}
                      />

                      <StatusRow
                        label="Redis"
                        status={overview.system.redis}
                        icon={Layers}
                      />

                      <StatusRow
                        label="Embedding Model"
                        status={overview.system.embeddings}
                        icon={Cpu}
                      />
                    </div>
                  </div>

                  <div className="admin-panel admin-security-panel">
                    <div className="admin-panel-header">
                      <div>
                        <span className="admin-panel-kicker">SECURITY</span>

                        <h2>Access Control</h2>
                      </div>
                    </div>

                    <div className="admin-security-content">
                      <div className="admin-security-icon">
                        <ShieldCheck size={18} />
                      </div>

                      <div>
                        <strong>Protected Admin API</strong>

                        <p>
                          Admin endpoints require a valid Supabase session and
                          an active admin_users record.
                        </p>
                      </div>
                    </div>

                    <ul className="admin-check-list">
                      <li>
                        <CheckCircle2 size={16} />
                        Valid Supabase session required
                      </li>

                      <li>
                        <CheckCircle2 size={16} />
                        Active admin_users record required
                      </li>
                    </ul>
                  </div>
                </section>

                <section className="admin-panel">
                  <div className="admin-panel-header">
                    <div>
                      <span className="admin-panel-kicker">SHORTCUTS</span>

                      <h2>Quick Access</h2>
                    </div>
                  </div>

                  <div className="admin-quick-grid">
                    {SECTIONS.filter(
                      (section) => section.id !== "overview",
                    ).map((section) => {
                      const Icon = section.icon;

                      return (
                        <button
                          type="button"
                          key={section.id}
                          className="admin-quick-card"
                          onClick={() => openSection(section.id)}
                        >
                          <span className="admin-quick-icon">
                            <Icon size={17} />
                          </span>

                          <strong>
                            {section.label}
                            <ArrowUpRight size={14} />
                          </strong>

                          <span>{section.hint}</span>
                        </button>
                      );
                    })}
                  </div>
                </section>
              </>
            )}

            {activeSection === "users" && (
              <section className="admin-panel">
                <div className="admin-panel-header">
                  <div>
                    <span className="admin-panel-kicker">ACCOUNTS</span>

                    <h2>Registered Users</h2>
                  </div>

                  <span className="admin-count">{users.length} users</span>
                </div>

                {users.length === 0 ? (
                  <EmptyState text="No registered users found." icon={Users} />
                ) : (
                  <div className="admin-table-wrap">
                    <table className="admin-table">
                      <thead>
                        <tr>
                          <th>Email</th>
                          <th>Name</th>
                          <th>Verified</th>
                          <th>Created</th>
                          <th>Last Sign In</th>
                        </tr>
                      </thead>

                      <tbody>
                        {users.map((user) => (
                          <tr key={user.id}>
                            <td>
                              <div className="admin-user-cell">
                                <span className="admin-avatar">
                                  {getInitials(user)}
                                </span>

                                <strong>{user.email}</strong>
                              </div>
                            </td>

                            <td>{user.full_name || "—"}</td>

                            <td>
                              <span
                                className={
                                  user.email_confirmed
                                    ? "admin-pill success"
                                    : "admin-pill warning"
                                }
                              >
                                {user.email_confirmed ? "Verified" : "Pending"}
                              </span>
                            </td>

                            <td>
                              {user.created_at
                                ? new Date(user.created_at).toLocaleDateString()
                                : "—"}
                            </td>

                            <td>
                              {user.last_sign_in_at
                                ? new Date(
                                    user.last_sign_in_at,
                                  ).toLocaleString()
                                : "Never"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>
            )}

            {activeSection === "jobs" && (
              <section className="admin-panel">
                <div className="admin-panel-header">
                  <div>
                    <span className="admin-panel-kicker">JOB INVENTORY</span>

                    <h2>Latest Jobs</h2>
                  </div>

                  <span className="admin-count">{jobs.length} loaded</span>
                </div>

                {jobs.length === 0 ? (
                  <EmptyState text="No jobs found." icon={Briefcase} />
                ) : (
                  <div className="admin-table-wrap">
                    <table className="admin-table">
                      <thead>
                        <tr>
                          <th>Job</th>
                          <th>Company</th>
                          <th>Location</th>
                          <th>Type</th>
                          <th>Status</th>
                          <th>Application</th>
                        </tr>
                      </thead>

                      <tbody>
                        {jobs.map((job) => (
                          <tr key={job.id}>
                            <td>
                              <strong>{job.title}</strong>

                              <span className="admin-subtext">
                                {job.provider}
                              </span>
                            </td>

                            <td>{job.company}</td>

                            <td>{job.location_display || "India"}</td>

                            <td>
                              {job.employment_type ? (
                                <span className="admin-pill neutral">
                                  {job.employment_type}
                                </span>
                              ) : (
                                "—"
                              )}
                            </td>

                            <td>
                              <span
                                className={
                                  job.is_active
                                    ? "admin-pill success"
                                    : "admin-pill neutral"
                                }
                              >
                                {job.is_active ? "Active" : "Inactive"}
                              </span>
                            </td>

                            <td>
                              {job.application_url ? (
                                <a
                                  className="admin-link"
                                  href={job.application_url}
                                  target="_blank"
                                  rel="noreferrer"
                                >
                                  View Job
                                  <ExternalLink size={12} />
                                </a>
                              ) : (
                                "—"
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>
            )}

            {activeSection === "sources" && (
              <section className="admin-panel">
                <div className="admin-panel-header">
                  <div>
                    <span className="admin-panel-kicker">INGESTION</span>

                    <h2>Job Sources</h2>
                  </div>

                  <span className="admin-count">{sources.length} sources</span>
                </div>

                {sources.length === 0 ? (
                  <EmptyState text="No job sources configured." icon={Rss} />
                ) : (
                  <div className="admin-table-wrap">
                    <table className="admin-table">
                      <thead>
                        <tr>
                          <th>Source</th>
                          <th>Provider</th>
                          <th>Company</th>
                          <th>Status</th>
                        </tr>
                      </thead>

                      <tbody>
                        {sources.map((source) => (
                          <tr key={source.id}>
                            <td>
                              <strong>{source.name || source.id}</strong>
                            </td>

                            <td>{source.provider || "—"}</td>

                            <td>{source.company_id || "—"}</td>

                            <td>
                              <span
                                className={
                                  source.enabled
                                    ? "admin-pill success"
                                    : "admin-pill neutral"
                                }
                              >
                                {source.enabled ? "Enabled" : "Disabled"}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>
            )}

            {activeSection === "embeddings" && embeddings && (
              <>
                <section className="admin-stats-grid cols-4">
                  <StatCard
                    label="Total Jobs"
                    value={embeddings.total_jobs}
                    icon={Briefcase}
                    tone="blue"
                  />

                  <StatCard
                    label="Active Jobs"
                    value={embeddings.active_jobs}
                    icon={Zap}
                    tone="green"
                  />

                  <StatCard
                    label="Embeddings"
                    value={embeddings.total_embeddings}
                    icon={Database}
                    tone="violet"
                  />

                  <StatCard
                    label="Coverage"
                    value={embeddings.coverage}
                    suffix="%"
                    icon={Percent}
                    tone="amber"
                  />
                </section>

                <section className="admin-panel">
                  <div className="admin-panel-header">
                    <div>
                      <span className="admin-panel-kicker">RAG HEALTH</span>

                      <h2>Embedding Coverage</h2>
                    </div>

                    <span
                      className={
                        embeddings.healthy
                          ? "admin-pill success"
                          : "admin-pill warning"
                      }
                    >
                      {embeddings.healthy ? "Healthy" : "Needs Attention"}
                    </span>
                  </div>

                  <div
                    className={`admin-progress ${
                      embeddings.healthy ? "is-healthy" : "is-warning"
                    }`}
                  >
                    <div
                      style={{
                        width: `${Math.min(embeddings.coverage, 100)}%`,
                      }}
                    />
                  </div>

                  <p className="admin-progress-label">
                    {embeddings.coverage}% of jobs currently have an embedding.
                  </p>
                </section>
              </>
            )}

            {activeSection === "llm" && llmUsage && (
              <>
                <section className="admin-stats-grid">
                  <StatCard
                    label="Platform Tokens"
                    value={llmUsage.platform_tokens}
                    icon={Zap}
                    tone="blue"
                  />

                  <StatCard
                    label="BYOK Tokens"
                    value={llmUsage.byok_tokens}
                    icon={KeyRound}
                    tone="violet"
                  />

                  <StatCard
                    label="Requests"
                    value={llmUsage.total_requests}
                    icon={Sparkles}
                    tone="green"
                  />
                </section>

                <section className="admin-panel">
                  <div className="admin-panel-header">
                    <div>
                      <span className="admin-panel-kicker">DISTRIBUTION</span>

                      <h2>Token Mix</h2>
                    </div>
                  </div>

                  <div className="admin-split-bar">
                    <div
                      className="admin-split-platform"
                      style={{ width: `${platformShare}%` }}
                    />

                    <div
                      className="admin-split-byok"
                      style={{ width: `${byokShare}%` }}
                    />
                  </div>

                  <div className="admin-legend">
                    <span>
                      <i />
                      Platform <b>{platformShare.toFixed(1)}%</b>
                    </span>

                    <span>
                      <i className="byok" />
                      BYOK <b>{byokShare.toFixed(1)}%</b>
                    </span>
                  </div>
                </section>

                <section className="admin-panel">
                  <div className="admin-panel-header">
                    <div>
                      <span className="admin-panel-kicker">PROVIDERS</span>

                      <h2>Provider Usage</h2>
                    </div>
                  </div>

                  <div className="admin-provider-grid">
                    {providerEntries.map(([provider, tokens]) => {
                      const share = providerTotal
                        ? ((Number(tokens) || 0) / providerTotal) * 100
                        : 0;

                      return (
                        <div key={provider} className="admin-provider-card">
                          <div className="admin-provider-top">
                            <span>{provider}</span>

                            <em>{share.toFixed(1)}%</em>
                          </div>

                          <strong>{Number(tokens).toLocaleString()}</strong>

                          <small>tokens</small>

                          <div className="admin-mini-bar">
                            <div style={{ width: `${share}%` }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </section>

                <section className="admin-panel">
                  <div className="admin-panel-header">
                    <div>
                      <span className="admin-panel-kicker">REQUESTS</span>

                      <h2>Recent LLM Usage</h2>
                    </div>
                  </div>

                  {llmUsage.usage?.length === 0 ? (
                    <EmptyState text="No LLM usage recorded." icon={Sparkles} />
                  ) : (
                    <div className="admin-table-wrap">
                      <table className="admin-table">
                        <thead>
                          <tr>
                            <th>Provider</th>
                            <th>Model</th>
                            <th>Feature</th>
                            <th>Source</th>
                            <th>Tokens</th>
                            <th>Time</th>
                          </tr>
                        </thead>

                        <tbody>
                          {llmUsage.usage.slice(0, 100).map((row) => (
                            <tr key={row.id}>
                              <td>
                                <strong>{row.provider}</strong>
                              </td>

                              <td>{row.model}</td>

                              <td>{row.feature}</td>

                              <td>
                                <span className="admin-pill neutral">
                                  {row.usage_source}
                                </span>
                              </td>

                              <td className="admin-mono">
                                {Number(row.total_tokens || 0).toLocaleString()}
                              </td>

                              <td>
                                {row.created_at
                                  ? new Date(row.created_at).toLocaleString()
                                  : "—"}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </section>
              </>
            )}
          </>
        )}
      </main>
    </div>
  );
}
