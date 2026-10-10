import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  AlertCircle,
  ArrowRight,
  BriefcaseBusiness,
  CheckCircle2,
  FileText,
  GraduationCap,
  Sparkles,
  Target,
  TrendingUp,
  Trophy,
  Upload,
  UserRound,
  Zap,
} from "lucide-react";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { getHistory, getProfile, getUsageQuota } from "../services/api";
import { useAuth } from "../context/AuthContext";
import { getAtsScore, getJdMatch, normalizeHistory } from "../utils/analysis";

import "../CSS/Dashboard.css";

/* =========================================================
   SMALL COMPONENTS
   ========================================================= */

function StatCard({ label, value, suffix = "", helper, icon: Icon }) {
  return (
    <div className="stat-card">
      <div className="stat-top">
        <span className="stat-label">{label}</span>

        {Icon && (
          <span className="stat-icon">
            <Icon size={17} />
          </span>
        )}
      </div>

      <div className="stat-value">
        {value}
        {suffix && <span>{suffix}</span>}
      </div>

      <div className="stat-bottom">
        <span>{helper}</span>
      </div>
    </div>
  );
}

function ProfileTag({ children }) {
  return <span className="career-tag">{children}</span>;
}

function QuickAction({ icon: Icon, title, text, to, disabled = false }) {
  if (disabled) {
    return (
      <div className="quick-action disabled">
        <span className="quick-action-icon">
          <Icon size={18} />
        </span>

        <div>
          <strong>{title}</strong>
          <span>{text}</span>
        </div>

        <span className="coming-soon">Soon</span>
      </div>
    );
  }

  return (
    <Link to={to} className="quick-action">
      <span className="quick-action-icon">
        <Icon size={18} />
      </span>

      <div>
        <strong>{title}</strong>
        <span>{text}</span>
      </div>

      <ArrowRight size={16} className="quick-action-arrow" />
    </Link>
  );
}

/* =========================================================
   PROFILE COMPLETENESS
   ========================================================= */

function ProfileProgress({ profile }) {
  const checks = [
    {
      label: "Username",
      complete: Boolean(profile?.username?.trim()),
    },
    {
      label: "Career interests",
      complete:
        Array.isArray(profile?.career_interests) &&
        profile.career_interests.length > 0,
    },
    {
      label: "Specializations",
      complete:
        Array.isArray(profile?.specializations) &&
        profile.specializations.length > 0,
    },
    {
      label: "Skills",
      complete: Array.isArray(profile?.skills) && profile.skills.length > 0,
    },
    {
      label: "Target roles",
      complete:
        Array.isArray(profile?.target_roles) && profile.target_roles.length > 0,
    },
    {
      label: "Experience",
      complete: Boolean(profile?.experience?.trim()),
    },
    {
      label: "Graduation year",
      complete: Boolean(profile?.graduation_year),
    },
    {
      label: "Resume",
      complete: Boolean(profile?.resume_filename),
    },
  ];

  const completed = checks.filter((item) => item.complete).length;

  const percentage = Math.round((completed / checks.length) * 100);

  return {
    checks,
    completed,
    percentage,
  };
}

/* =========================================================
   PROFILE LIST
   ========================================================= */

function ProfileSection({ icon: Icon, title, children }) {
  return (
    <div className="profile-detail-block">
      <div className="profile-detail-heading">
        {Icon && <Icon size={15} />}
        <span>{title}</span>
      </div>

      {children}
    </div>
  );
}

function ProfileTags({ items, emptyText }) {
  if (!Array.isArray(items) || items.length === 0) {
    return <span className="muted">{emptyText}</span>;
  }

  return (
    <div className="career-tags">
      {items.map((item) => (
        <ProfileTag key={item}>{item}</ProfileTag>
      ))}
    </div>
  );
}

/* =========================================================
   DASHBOARD
   ========================================================= */

export default function Dashboard() {
  const { accessToken, user } = useAuth();
  const navigate = useNavigate();

  const [profile, setProfile] = useState(null);
  const [history, setHistory] = useState([]);
  const [usage, setUsage] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  /* =====================================================
     LOAD DASHBOARD DATA
     ===================================================== */

  useEffect(() => {
    let active = true;

    async function loadDashboard() {
      if (!accessToken) {
        setLoading(false);
        return;
      }

      setLoading(true);
      setError("");

      try {
        const [profileData, historyData, usageData] = await Promise.all([
          getProfile(accessToken),
          getHistory(accessToken),
          getUsageQuota(accessToken),
        ]);

        if (!active) {
          return;
        }

        setProfile(profileData);
        setHistory(normalizeHistory(historyData));
        setUsage(usageData);
      } catch (err) {
        if (active) {
          setError(err?.message || "Could not load your career workspace.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadDashboard();

    return () => {
      active = false;
    };
  }, [accessToken]);

  /* =====================================================
     DISPLAY DATA
     ===================================================== */

  const displayName =
    profile?.username ||
    user?.user_metadata?.full_name ||
    user?.user_metadata?.name ||
    user?.email?.split("@")[0] ||
    "there";

  const latest = history.length ? history[0] : null;

  const latestScore = latest ? getAtsScore(latest.result) : 0;

  const latestMatch = latest ? getJdMatch(latest.result) : 0;

  const bestScore = history.length
    ? Math.max(...history.map((item) => getAtsScore(item.result)))
    : 0;

  const averageScore = history.length
    ? Math.round(
        history.reduce((total, item) => total + getAtsScore(item.result), 0) /
          history.length,
      )
    : 0;

  /* =====================================================
     CHART
     ===================================================== */

  const chartData = useMemo(
    () =>
      history
        .slice(0, 7)
        .reverse()
        .map((item, index) => ({
          name: item.createdAt
            ? new Date(item.createdAt).toLocaleDateString(undefined, {
                month: "short",
                day: "numeric",
              })
            : `Scan ${index + 1}`,

          score: getAtsScore(item.result),
        })),
    [history],
  );

  /* =====================================================
     PROFILE PROGRESS
     ===================================================== */

  const profileProgress = ProfileProgress({
    profile,
  });

  /* =====================================================
     LOADING
     ===================================================== */

  if (loading) {
    return (
      <div className="page-shell dashboard-page">
        <div className="dashboard-loading">
          <span className="loading-spinner" />
          <span>Preparing your career workspace...</span>
        </div>
      </div>
    );
  }
  return (
    <div className="page-shell dashboard-page">
      <section className="career-profile-banner">
        <div className="career-profile-main">
          <div className="career-avatar">
            <UserRound size={23} />
          </div>

          <div className="career-profile-copy">
            <span className="career-greeting">Welcome back, {displayName}</span>

            <h2>
              {profile?.target_roles?.length
                ? profile.target_roles.join(" · ")
                : "Build your career profile"}
            </h2>

            <div className="career-meta">
              {profile?.experience && (
                <span>
                  <BriefcaseBusiness size={14} />
                  {profile.experience}
                </span>
              )}

              {profile?.graduation_year && (
                <span>
                  <GraduationCap size={14} />
                  Class of {profile.graduation_year}
                </span>
              )}

              {profile?.resume_filename && (
                <span>
                  <FileText size={14} />
                  Resume connected
                </span>
              )}
            </div>
          </div>
        </div>

        {/* PROFILE COMPLETENESS */}

        <div className="career-profile-progress">
          <div className="progress-copy">
            <span>Profile completeness</span>
            <strong>{profileProgress.percentage}%</strong>
          </div>

          <div className="progress-track">
            <div
              className="progress-fill"
              style={{
                width: `${profileProgress.percentage}%`,
              }}
            />
          </div>

          <span className="progress-helper">
            {profileProgress.completed}/8 profile sections complete
          </span>
        </div>
      </section>

      {/* =================================================
          ERROR
          ================================================= */}

      {error && (
        <div className="dashboard-error">
          <AlertCircle size={17} />
          <span>{error}</span>
        </div>
      )}

      {/* =================================================
          STATS
          ================================================= */}

      <section className="stats-grid">
        <StatCard
          label="LATEST ATS SCORE"
          value={latestScore || "—"}
          suffix={latestScore ? "/100" : ""}
          helper={
            latestScore ? "Most recent analysis" : "Run your first analysis"
          }
          // icon={Zap}
        />

        <StatCard
          label="BEST ATS SCORE"
          value={bestScore || "—"}
          suffix={bestScore ? "/100" : ""}
          helper="Your personal best"
          // icon={Trophy}
        />

        <StatCard
          label="TOTAL ANALYSES"
          value={history.length}
          helper="Saved resume analyses"
          // icon={FileText}
        />

        <StatCard
          label="AVERAGE ATS SCORE"
          value={averageScore || "—"}
          suffix={averageScore ? "/100" : ""}
          helper="Across your analyses"
          // icon={TrendingUp}
        />
      </section>
      {/* =================================================
    AI USAGE
    ================================================= */}

      {usage && (
        <section className="panel ai-usage-dashboard-panel">
          <div className="panel-header">
            <Link to="/settings" className="outline-button">
              AI Settings
              <ArrowRight size={15} />
            </Link>
          </div>

          <div className="ai-usage-dashboard-grid">
            <div className="ai-usage-stat">
              <span>Resume analyses</span>

              <strong>
                {usage.resume.used}
                <small>/{usage.resume.limit}</small>
              </strong>

              <p>{usage.resume.remaining} remaining</p>
            </div>

            <div className="ai-usage-stat">
              <span>Platform tokens</span>

              <strong>
                {Number(usage.tokens?.used || 0).toLocaleString()}

                <small>
                  /{Number(usage.tokens?.limit || 0).toLocaleString()}
                </small>
              </strong>

              <p>
                {Number(usage.tokens?.remaining || 0).toLocaleString()}{" "}
                remaining
              </p>
            </div>

            <div className="ai-usage-stat">
              <span>Input tokens</span>

              <strong>
                {Number(usage.tokens?.input_tokens || 0).toLocaleString()}
              </strong>

              <p>Platform usage</p>
            </div>

            <div className="ai-usage-stat">
              <span>Output tokens</span>

              <strong>
                {Number(usage.tokens?.output_tokens || 0).toLocaleString()}
              </strong>

              <p>Platform usage</p>
            </div>
          </div>

          {usage.byok?.connected && (
            <div className="byok-dashboard-note">
              <strong>BYOK active</strong>

              <span>
                {usage.byok.providers.length} provider
                {usage.byok.providers.length !== 1 ? "s" : ""} connected. BYOK
                usage is not deducted from your platform allowance.
              </span>
            </div>
          )}
        </section>
      )}
      {/* =================================================
          MAIN GRID
          ================================================= */}

      <section className="dashboard-main-grid">
        {/* =================================================
            RESUME PERFORMANCE
            ================================================= */}

        <div className="panel">
          <div className="panel-header">
            <div>
              <span className="section-kicker">RESUME INTELLIGENCE</span>
            </div>

            {history.length > 0 && (
              <span className="panel-badge">{history.length} scans</span>
            )}
          </div>

          <div className="chart-wrap">
            {chartData.length ? (
              <ResponsiveContainer width="100%" height={245}>
                <AreaChart
                  data={chartData}
                  margin={{
                    top: 10,
                    right: 4,
                    left: -22,
                    bottom: 0,
                  }}
                >
                  <defs>
                    <linearGradient id="scoreFill" x1="0" y1="0" x2="0" y2="1">
                      <stop
                        offset="0%"
                        stopColor="#0743eb"
                        stopOpacity={0.28}
                      />

                      <stop
                        offset="100%"
                        stopColor="#0744ed"
                        stopOpacity={0.02}
                      />
                    </linearGradient>
                  </defs>

                  <CartesianGrid stroke="#eef2f7" vertical={false} />

                  <XAxis
                    dataKey="name"
                    axisLine={false}
                    tickLine={false}
                    tick={{
                      fill: "#94a3b8",
                      fontSize: 12,
                    }}
                  />

                  <YAxis
                    domain={[0, 100]}
                    axisLine={false}
                    tickLine={false}
                    tick={{
                      fill: "#94a3b8",
                      fontSize: 12,
                    }}
                  />

                  <Tooltip
                    contentStyle={{
                      background: "#ffffff",
                      border: "1px solid #e5e7eb",
                      borderRadius: 10,
                      color: "#111827",
                      fontSize: 13,
                      boxShadow: "0 10px 30px rgba(15,23,42,0.08)",
                    }}
                    labelStyle={{
                      color: "#64748b",
                    }}
                    itemStyle={{
                      color: "#002a9d",
                    }}
                  />

                  <Area
                    type="monotone"
                    dataKey="score"
                    stroke="#002a9d"
                    strokeWidth={3}
                    fill="url(#scoreFill)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="chart-empty">
                <span className="empty-icon">
                  <TrendingUp size={18} />
                </span>

                <strong>Your score trend will appear here.</strong>

                <span>Analyze a resume to start tracking your progress.</span>

                <Link to="/analyze" className="outline-button">
                  Analyze Resume
                  <ArrowRight size={15} />
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* =================================================
            CAREER PROFILE
            ================================================= */}

        <div className="panel career-profile-panel">
          {/* CAREER INTERESTS */}

          <ProfileSection icon={Target} title="Career Interests">
            <ProfileTags
              items={profile?.career_interests}
              emptyText="No career interests added"
            />
          </ProfileSection>

          {/* SPECIALIZATIONS */}

          <ProfileSection icon={Sparkles} title="Specializations">
            <ProfileTags
              items={profile?.specializations}
              emptyText="No specializations added"
            />
          </ProfileSection>

          {/* TARGET ROLES */}

          <ProfileSection icon={BriefcaseBusiness} title="Target Roles">
            <ProfileTags
              items={profile?.target_roles}
              emptyText="No target roles added"
            />
          </ProfileSection>

          {/* SKILLS */}

          <ProfileSection icon={Zap} title="Skills">
            {profile?.skills?.length ? (
              <>
                <div className="career-tags">
                  {profile.skills.slice(0, 12).map((skill) => (
                    <ProfileTag key={skill}>{skill}</ProfileTag>
                  ))}
                </div>

                {profile.skills.length > 12 && (
                  <span className="profile-more">
                    +{profile.skills.length - 12} more
                  </span>
                )}
              </>
            ) : (
              <span className="muted">No skills added</span>
            )}
          </ProfileSection>

          {/* EXPERIENCE + GRADUATION */}

          <div className="profile-two-column">
            <div className="profile-detail-block">
              <div className="profile-detail-heading">
                <BriefcaseBusiness size={15} />
                <span>Experience</span>
              </div>

              <strong className="experience-value">
                {profile?.experience || "Not specified"}
              </strong>
            </div>

            <div className="profile-detail-block">
              <div className="profile-detail-heading">
                <GraduationCap size={15} />
                <span>Graduation</span>
              </div>

              <strong className="experience-value">
                {profile?.graduation_year || "Not specified"}
              </strong>
            </div>
          </div>

          {/* RESUME */}

          <div className="profile-resume-status">
            <div className="resume-status-icon">
              <CheckCircle2 size={17} />
            </div>

            <div>
              <strong>
                {profile?.resume_filename
                  ? "Resume connected"
                  : "Resume not connected"}
              </strong>

              <span>
                {profile?.resume_filename ||
                  "Upload your resume to unlock analysis."}
              </span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
