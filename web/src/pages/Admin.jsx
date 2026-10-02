import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
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

function StatCard({ label, value, icon }) {
  return (
    <div className="admin-stat-card">
      <div className="admin-stat-top">
        <span>{label}</span>
        <div className="admin-stat-icon">{icon}</div>
      </div>

      <strong>{Number(value || 0).toLocaleString()}</strong>
    </div>
  );
}

function StatusRow({ label, status }) {
  return (
    <div className="admin-status-row">
      <div>
        <span
          className="admin-status-dot"
          data-status={status ? "online" : "offline"}
        />
        <span>{label}</span>
      </div>

      <strong data-status={status ? "online" : "offline"}>
        {status ? "Operational" : "Unavailable"}
      </strong>
    </div>
  );
}

function EmptyState({ text }) {
  return <div className="admin-empty">{text}</div>;
}

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

        <nav className="admin-nav">
          <button
            className={`admin-nav-item ${
              activeSection === "overview" ? "active" : ""
            }`}
            onClick={() => openSection("overview")}
          >
            <span>◈</span>
            Overview
          </button>

          <button
            className={`admin-nav-item ${
              activeSection === "users" ? "active" : ""
            }`}
            onClick={() => openSection("users")}
          >
            <span>◉</span>
            Users
          </button>

          <button
            className={`admin-nav-item ${
              activeSection === "jobs" ? "active" : ""
            }`}
            onClick={() => openSection("jobs")}
          >
            <span>▣</span>
            Jobs
          </button>

          <button
            className={`admin-nav-item ${
              activeSection === "sources" ? "active" : ""
            }`}
            onClick={() => openSection("sources")}
          >
            <span>◇</span>
            Job Sources
          </button>

          <button
            className={`admin-nav-item ${
              activeSection === "embeddings" ? "active" : ""
            }`}
            onClick={() => openSection("embeddings")}
          >
            <span>◌</span>
            Embeddings
          </button>

          <button
            className={`admin-nav-item ${
              activeSection === "llm" ? "active" : ""
            }`}
            onClick={() => openSection("llm")}
          >
            <span>△</span>
            LLM Usage
          </button>
        </nav>

        <div className="admin-sidebar-bottom">
          <button type="button" onClick={() => navigate("/dashboard")}>
            ← Back to SmartHire
          </button>
        </div>
      </aside>

      <main className="admin-main">
        <header className="admin-header">
          <div>
            <span className="admin-eyebrow">ADMINISTRATION</span>

            <h1>
              {activeSection === "overview" && "System Overview"}

              {activeSection === "users" && "Users"}

              {activeSection === "jobs" && "Jobs"}

              {activeSection === "sources" && "Job Sources"}

              {activeSection === "embeddings" && "Embeddings"}

              {activeSection === "llm" && "LLM Usage"}
            </h1>

            <p>
              {activeSection === "overview" &&
                "Monitor SmartHire platform activity and infrastructure status."}

              {activeSection === "users" &&
                "Monitor registered SmartHire accounts."}

              {activeSection === "jobs" &&
                "Monitor the current job inventory and application links."}

              {activeSection === "sources" &&
                "Monitor configured job ingestion sources."}

              {activeSection === "embeddings" &&
                "Monitor job embedding coverage and RAG readiness."}

              {activeSection === "llm" &&
                "Monitor platform and BYOK token usage."}
            </p>
          </div>

          <div className="admin-header-badge">
            <span />
            Admin Access
          </div>
        </header>

        {error && (
          <div className="admin-error">
            <span>!</span>

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
                    icon="U"
                  />

                  <StatCard
                    label="Active Jobs"
                    value={overview.stats.active_jobs}
                    icon="J"
                  />

                  <StatCard
                    label="Job Embeddings"
                    value={overview.stats.job_embeddings}
                    icon="E"
                  />

                  <StatCard
                    label="Resume Analyses"
                    value={overview.stats.resume_analyses}
                    icon="A"
                  />

                  <StatCard
                    label="Platform Tokens"
                    value={overview.stats.platform_tokens}
                    icon="P"
                  />

                  <StatCard
                    label="BYOK Tokens"
                    value={overview.stats.byok_tokens}
                    icon="B"
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

                    <div className="admin-status-list">
                      <StatusRow
                        label="API Server"
                        status={overview.system.api}
                      />

                      <StatusRow
                        label="Supabase"
                        status={overview.system.supabase}
                      />

                      <StatusRow label="Redis" status={overview.system.redis} />

                      <StatusRow
                        label="Embedding Model"
                        status={overview.system.embeddings}
                      />
                    </div>
                  </div>

                  <div className="admin-panel">
                    <div className="admin-panel-header">
                      <div>
                        <span className="admin-panel-kicker">SECURITY</span>

                        <h2>Access Control</h2>
                      </div>
                    </div>

                    <div className="admin-security-content">
                      <div className="admin-security-icon">✓</div>

                      <div>
                        <strong>Protected Admin API</strong>

                        <p>
                          Admin endpoints require a valid Supabase session and
                          an active admin_users record.
                        </p>
                      </div>
                    </div>
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
                  <EmptyState text="No registered users found." />
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
                              <strong>{user.email}</strong>
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
                  <EmptyState text="No jobs found." />
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

                            <td>{job.employment_type || "—"}</td>

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
                                  View Job ↗
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
                  <EmptyState text="No job sources configured." />
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
                <section className="admin-stats-grid">
                  <StatCard
                    label="Total Jobs"
                    value={embeddings.total_jobs}
                    icon="J"
                  />

                  <StatCard
                    label="Active Jobs"
                    value={embeddings.active_jobs}
                    icon="A"
                  />

                  <StatCard
                    label="Embeddings"
                    value={embeddings.total_embeddings}
                    icon="E"
                  />

                  <StatCard
                    label="Coverage"
                    value={`${embeddings.coverage}%`}
                    icon="%"
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

                  <div className="admin-progress">
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
                    icon="P"
                  />

                  <StatCard
                    label="BYOK Tokens"
                    value={llmUsage.byok_tokens}
                    icon="B"
                  />

                  <StatCard
                    label="Requests"
                    value={llmUsage.total_requests}
                    icon="R"
                  />
                </section>

                <section className="admin-panel">
                  <div className="admin-panel-header">
                    <div>
                      <span className="admin-panel-kicker">PROVIDERS</span>

                      <h2>Provider Usage</h2>
                    </div>
                  </div>

                  <div className="admin-provider-grid">
                    {Object.entries(llmUsage.provider_totals || {}).map(
                      ([provider, tokens]) => (
                        <div key={provider} className="admin-provider-card">
                          <span>{provider}</span>

                          <strong>{Number(tokens).toLocaleString()}</strong>

                          <small>tokens</small>
                        </div>
                      ),
                    )}
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
                    <EmptyState text="No LLM usage recorded." />
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
                              <td>{row.provider}</td>

                              <td>{row.model}</td>

                              <td>{row.feature}</td>

                              <td>
                                <span className="admin-pill neutral">
                                  {row.usage_source}
                                </span>
                              </td>

                              <td>
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
