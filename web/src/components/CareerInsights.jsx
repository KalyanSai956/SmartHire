import { NavLink } from "react-router-dom";
import { BarChart3, Settings, BookOpen, Mic2 } from "lucide-react";

export default function CareerInsights() {
  return (
    <aside className="career-insights">
      {/* =====================================================
          NAVIGATION
          ===================================================== */}

      <div className="career-insights-header">
        <span className="career-insights-label">QUICK LINKS</span>
      </div>

      <nav className="career-insights-nav">
        <NavLink
          to="/jobs"
          className={({ isActive }) =>
            `career-insight-link ${isActive ? "active" : ""}`
          }
        >
          <BookOpen className="career-insight-icon" size={17} strokeWidth={2} />

          <div>
            <strong>Jobs</strong>
          </div>
        </NavLink>

        <NavLink
          to="/history"
          className={({ isActive }) =>
            `career-insight-link ${isActive ? "active" : ""}`
          }
        >
          <BarChart3
            className="career-insight-icon"
            size={17}
            strokeWidth={2}
          />
          <div>
            <strong>ATS Scores</strong>
          </div>
        </NavLink>

        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `career-insight-link ${isActive ? "active" : ""}`
          }
        >
          <Settings className="career-insight-icon" size={17} strokeWidth={2} />

          <div>
            <strong>AI Settings</strong>
          </div>
        </NavLink>
        <NavLink
          to="/interview-prep"
          className={({ isActive }) =>
            `career-insight-link ${isActive ? "active" : ""}`
          }
        >
          <Mic2 className="career-insight-icon" size={17} strokeWidth={2} />

          <div>
            <strong>Interview Prep</strong>
          </div>
        </NavLink>
      </nav>

      {/* =====================================================
          CAREER SIGNAL
          ===================================================== */}

      <div className="career-insights-divider" />
      <div className="insight-card">
        <div>
          <span>RESUME INTELLIGENCE</span>
          <strong>Keep improving</strong>
        </div>
      </div>

      <div className="insight-card">
        <div>
          <span>REAL TIME JOB AGENT</span>
          <strong>Build your baseline</strong>
        </div>
      </div>
    </aside>
  );
}
