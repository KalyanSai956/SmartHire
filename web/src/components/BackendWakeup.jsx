import { useEffect, useState } from "react";
import "../CSS/BackendWakeup.css";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const HEALTH_URL = `${API_BASE_URL}/api/v1/health`;

const MAX_WAIT_TIME = 120000; // 2 minutes
const INITIAL_RETRY_DELAY = 1500;
const MAX_RETRY_DELAY = 5000;
const WARM_WINDOW = 10 * 60 * 1000; // treat backend as awake for 10 min
const STORAGE_KEY = "backendReadyAt";

// Steps are tied to elapsed seconds so progress looks real.
const STAGES = [
  { until: 8, label: "Connecting to SmartHire" },
  { until: 28, label: "Loading language models" },
  { until: 48, label: "Warming up resume analysis" },
  { until: Infinity, label: "Almost there" },
];

const TIPS = [
  "Recruiters spend only about 7 seconds on a first look at a resume.",
  "Quantified achievements get more attention than long task lists.",
  "SmartHire matches skills by meaning, not just exact keywords.",
  "Tailoring your resume to each job description improves your match score.",
  "Keep your resume to one or two pages. Clear beats long.",
];

const TIP_INTERVAL = 5000;

/**
 * Call this on your landing/login page (fire-and-forget) so the backend
 * starts waking up before the user ever reaches the app.
 *   useEffect(() => { warmBackend(); }, []);
 */
export function warmBackend() {
  fetch(HEALTH_URL, { mode: "no-cors", cache: "no-store" }).catch(() => {});
}

function wasRecentlyReady() {
  try {
    const t = Number(sessionStorage.getItem(STORAGE_KEY) || 0);
    return Date.now() - t < WARM_WINDOW;
  } catch {
    return false;
  }
}

function markReady() {
  try {
    sessionStorage.setItem(STORAGE_KEY, String(Date.now()));
  } catch {
    /* storage unavailable, ignore */
  }
}

export default function BackendWakeup({ children }) {
  const [status, setStatus] = useState(() =>
    wasRecentlyReady() ? "ready" : "checking",
  );
  const [elapsedMs, setElapsedMs] = useState(0);
  const [tipIndex, setTipIndex] = useState(0);

  // Health check loop
  useEffect(() => {
    if (status === "ready") return;

    let cancelled = false;
    let retryTimer = null;
    const startTime = Date.now();

    const tick = setInterval(() => {
      if (!cancelled) setElapsedMs(Date.now() - startTime);
    }, 250);

    const checkBackend = async () => {
      if (cancelled) return;

      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 8000);

      try {
        const response = await fetch(HEALTH_URL, {
          method: "GET",
          cache: "no-store",
          signal: controller.signal,
        });
        clearTimeout(timeout);

        if (!response.ok) throw new Error(`Health check: ${response.status}`);

        const data = await response.json();
        if (
          data?.status === "healthy" &&
          data?.nlp_loaded === true &&
          data?.embedder_loaded === true
        ) {
          if (cancelled) return;
          markReady();
          setStatus("finishing"); // let the bar reach 100% briefly
          retryTimer = setTimeout(() => !cancelled && setStatus("ready"), 450);
          return;
        }
        throw new Error("Backend is still initializing.");
      } catch {
        clearTimeout(timeout);
        if (cancelled) return;

        const elapsed = Date.now() - startTime;
        if (elapsed >= MAX_WAIT_TIME) {
          setStatus("failed");
          return;
        }

        setStatus("waking");
        const delay = Math.min(
          INITIAL_RETRY_DELAY + Math.floor(elapsed / 10000) * 500,
          MAX_RETRY_DELAY,
        );
        retryTimer = setTimeout(checkBackend, delay);
      }
    };

    checkBackend();

    return () => {
      cancelled = true;
      clearInterval(tick);
      if (retryTimer) clearTimeout(retryTimer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Rotating tips
  useEffect(() => {
    if (status === "ready" || status === "failed") return;
    const id = setInterval(
      () => setTipIndex((i) => (i + 1) % TIPS.length),
      TIP_INTERVAL,
    );
    return () => clearInterval(id);
  }, [status]);

  if (status === "ready") return children;

  const shell = (content) => (
    <div className="backend-wakeup">
      <div className="backend-wakeup-card">
        <div className="backend-wakeup-logo">S</div>
        {content}
      </div>
    </div>
  );

  if (status === "failed") {
    return shell(
      <>
        <h1>This is taking longer than usual</h1>
        <p>
          We couldn't reach SmartHire just yet. Check your connection and try
          again.
        </p>
        <button
          className="backend-wakeup-button"
          onClick={() => window.location.reload()}
        >
          Try again
        </button>
      </>,
    );
  }

  const seconds = elapsedMs / 1000;

  // Eases toward ~90% over ~50s, never stalls visibly, jumps to 100% on ready.
  const progress =
    status === "finishing" ? 100 : 92 * (1 - Math.exp(-seconds / 18));

  const activeStage =
    status === "finishing"
      ? STAGES.length
      : STAGES.findIndex((s) => seconds < s.until);

  // Only mention the delay if it's genuinely long.
  const slow = seconds > 60;

  return shell(
    <>
      <h1>Preparing your AI workspace</h1>
      <p>
        {slow
          ? "Still working on it. Thanks for your patience."
          : "Loading the models that analyze resumes and match candidates. The first load takes a moment."}
      </p>

      <div className="backend-wakeup-status" aria-live="polite">
        {STAGES.map((stage, i) => {
          if (
            i > Math.min(activeStage, STAGES.length - 1) &&
            status !== "finishing"
          ) {
            return null;
          }
          const done = i < activeStage;
          const active = i === activeStage;
          return (
            <div
              key={stage.label}
              className={`backend-status-item ${
                done ? "completed" : active ? "active" : ""
              }`}
            >
              <span className="backend-status-dot">
                {done ? "✓" : active ? <span className="mini-spinner" /> : "○"}
              </span>
              <span>{stage.label}</span>
            </div>
          );
        })}
      </div>

      <div
        className="backend-wakeup-progress"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(progress)}
      >
        <div
          className="backend-wakeup-progress-bar"
          style={{ width: `${progress}%` }}
        />
      </div>

      <p key={tipIndex} className="backend-wakeup-tip">
        {TIPS[tipIndex]}
      </p>
    </>,
  );
}
