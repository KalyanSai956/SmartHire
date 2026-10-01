import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Search, Sparkles } from "lucide-react";

import { getHistory, deleteHistory } from "../services/api";

import { useAuth } from "../context/AuthContext";
import { normalizeHistory } from "../utils/analysis";
import AnalysisTable from "../components/AnalysisTable";

export default function History() {
  const { accessToken } = useAuth();

  const [history, setHistory] = useState([]);
  const [query, setQuery] = useState("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [deletingId, setDeletingId] = useState(null);

  /* =====================================================
     LOAD HISTORY
     ===================================================== */

  useEffect(() => {
    let cancelled = false;

    async function loadHistory() {
      try {
        setLoading(true);
        setError("");

        const data = await getHistory(accessToken);

        if (!cancelled) {
          setHistory(normalizeHistory(data));
        }
      } catch (err) {
        console.error("Failed to load history:", err);

        if (!cancelled) {
          setError(err.message || "Could not load analysis history.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadHistory();

    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  /* =====================================================
     SEARCH
     ===================================================== */

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();

    if (!q) {
      return history;
    }

    return history.filter((item) =>
      String(item.filename || "")
        .toLowerCase()
        .includes(q),
    );
  }, [history, query]);

  /* =====================================================
     DELETE
     ===================================================== */

  async function handleDelete(analysisId) {
    const item = history.find(
      (entry) => String(entry.id) === String(analysisId),
    );

    const filename = item?.filename || "this analysis";

    const confirmed = window.confirm(
      `Delete "${filename}"?\n\nThis analysis will be permanently removed from your history.`,
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeletingId(analysisId);
      setError("");

      await deleteHistory(analysisId, accessToken);

      /*
       * Remove it immediately from UI.
       * No need to reload the whole page.
       */
      setHistory((current) =>
        current.filter((entry) => String(entry.id) !== String(analysisId)),
      );
    } catch (err) {
      console.error("Failed to delete analysis:", err);

      setError(err.message || "Failed to delete analysis.");
    } finally {
      setDeletingId(null);
    }
  }

  /* =====================================================
     RENDER
     ===================================================== */

  return (
    <div className="mx-auto max-w-4xl px-6 py-5 page-shell">
      {/* =================================================
          HEADER
      ================================================= */}

      <section className="page-heading">
        <div>
          <p className="eyebrow">ANALYSIS HISTORY</p>
        </div>

        <Link to="/analyze" className="button secondary">
          New Analysis
        </Link>
      </section>

      {/* =================================================
          SEARCH
      ================================================= */}

      <div className="history-toolbar">
        <div className="search-field">
          <Search size={17} />

          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search resumes..."
          />
        </div>
      </div>

      {/* =================================================
          ERROR
      ================================================= */}

      {error && <div className="inline-error history-error">{error}</div>}

      {/* =================================================
          TABLE
      ================================================= */}

      <div className="mx-auto max-w-4xl px-6 py-5 panel table-panel history-panel">
        {loading ? (
          <div className="loading-state">
            <span className="loading-spinner" />
            Loading history...
          </div>
        ) : (
          <AnalysisTable
            items={filtered}
            emptyText={
              query
                ? "No resumes match your search."
                : "Upload your first resume to create an analysis."
            }
            onDelete={handleDelete}
            deletingId={deletingId}
          />
        )}
      </div>
    </div>
  );
}
