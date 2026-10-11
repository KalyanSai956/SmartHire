import { CheckCircle2 } from "lucide-react";
import "../CSS/Analysis.css";

/**
 * The "Your Score" skeleton + animated steps screen.
 * Reuses the existing loading-* classes from Analysis.css.
 */
export default function AnalysisLoading() {
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
