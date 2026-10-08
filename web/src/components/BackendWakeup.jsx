import { useEffect, useState } from "react";
import "../CSS/BackendWakeup.css";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const HEALTH_URL = `${API_BASE_URL}/api/v1/health`;

const MAX_WAIT_TIME = 120000; // 2 minutes
const INITIAL_RETRY_DELAY = 1500;
const MAX_RETRY_DELAY = 5000;

export default function BackendWakeup({ children }) {
  const [status, setStatus] = useState("checking");
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  useEffect(() => {
    let cancelled = false;
    let retryTimer = null;
    let elapsedTimer = null;
    let startTime = Date.now();

    const checkBackend = async () => {
      if (cancelled) return;

      try {
        const controller = new AbortController();

        const timeout = setTimeout(() => {
          controller.abort();
        }, 8000);

        const response = await fetch(HEALTH_URL, {
          method: "GET",
          cache: "no-store",
          signal: controller.signal,
        });

        clearTimeout(timeout);

        if (!response.ok) {
          throw new Error(`Health check failed: ${response.status}`);
        }

        const data = await response.json();

        if (
          data?.status === "healthy" &&
          data?.nlp_loaded === true &&
          data?.embedder_loaded === true
        ) {
          if (!cancelled) {
            setStatus("ready");
          }

          return;
        }

        throw new Error("Backend is still initializing.");
      } catch (error) {
        if (cancelled) return;

        const elapsed = Date.now() - startTime;

        if (elapsed >= MAX_WAIT_TIME) {
          setStatus("failed");
          return;
        }

        setStatus("waking");

        const retryDelay = Math.min(
          INITIAL_RETRY_DELAY + Math.floor(elapsed / 10000) * 500,
          MAX_RETRY_DELAY,
        );

        retryTimer = setTimeout(checkBackend, retryDelay);
      }
    };

    elapsedTimer = setInterval(() => {
      if (!cancelled) {
        setElapsedSeconds(Math.floor((Date.now() - startTime) / 1000));
      }
    }, 1000);

    checkBackend();

    return () => {
      cancelled = true;

      if (retryTimer) {
        clearTimeout(retryTimer);
      }

      if (elapsedTimer) {
        clearInterval(elapsedTimer);
      }
    };
  }, []);

  if (status === "ready") {
    return children;
  }

  if (status === "failed") {
    return (
      <div className="backend-wakeup">
        <div className="backend-wakeup-card">
          <div className="backend-wakeup-logo">S</div>

          <div className="backend-wakeup-icon backend-wakeup-icon-error">!</div>

          <h1>SmartHire is taking longer than expected</h1>

          <p>
            We're having trouble connecting to the SmartHire backend. Please try
            again.
          </p>

          <button
            className="backend-wakeup-button"
            onClick={() => window.location.reload()}
          >
            Try again
          </button>

          <span className="backend-wakeup-time">
            Connection attempt: {elapsedSeconds}s
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="backend-wakeup">
      <div className="backend-wakeup-card">
        <div className="backend-wakeup-logo">S</div>

        <div className="backend-wakeup-spinner">
          <span />
        </div>

        <h1>
          {status === "checking"
            ? "Connecting to SmartHire"
            : "Getting things ready"}
        </h1>

        <p>
          {status === "checking"
            ? "Checking the SmartHire AI workspace..."
            : "SmartHire's AI backend is waking up. This usually takes a few seconds after a period of inactivity."}
        </p>

        <div className="backend-wakeup-status">
          <div className="backend-status-item completed">
            <span className="backend-status-dot">✓</span>
            <span>Connecting to SmartHire</span>
          </div>

          <div
            className={`backend-status-item ${
              status === "waking" ? "active" : ""
            }`}
          >
            <span className="backend-status-dot">
              {status === "waking" ? <span className="mini-spinner" /> : "○"}
            </span>

            <span>Starting AI services</span>
          </div>

          <div className="backend-status-item">
            <span className="backend-status-dot">○</span>

            <span>Preparing your workspace</span>
          </div>
        </div>

        <div className="backend-wakeup-progress">
          <div className="backend-wakeup-progress-bar" />
        </div>

        <span className="backend-wakeup-time">
          {elapsedSeconds > 0 ? `${elapsedSeconds}s` : "Connecting..."}
        </span>
      </div>
    </div>
  );
}
