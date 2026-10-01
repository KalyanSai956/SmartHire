import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { CheckCircle2, Upload } from "lucide-react";
import { analyzeResume } from "../services/api";
import { useAuth } from "../context/AuthContext";
import "../CSS/Analyze.css";

const MAX_SIZE = 5 * 1024 * 1024;

export default function Analyze() {
  const { accessToken } = useAuth();
  const navigate = useNavigate();
  const inputRef = useRef(null);

  const [file, setFile] = useState(null);
  const [jobDescription, setJobDescription] = useState("");
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  function selectFile(candidate) {
    setError("");

    if (!candidate) return;

    const allowed = [".pdf", ".doc", ".docx"];
    const name = candidate.name.toLowerCase();
    const valid = allowed.some((ext) => name.endsWith(ext));

    if (!valid) {
      setError("Please upload a PDF, DOC, or DOCX file.");
      return;
    }

    if (candidate.size > MAX_SIZE) {
      setError("The resume must be smaller than 5 MB.");
      return;
    }

    setFile(candidate);
  }

  async function submit() {
    setError("");

    if (!file) {
      setError("Please upload your resume first.");
      return;
    }

    setBusy(true);

    try {
      const activeProvider =
        localStorage.getItem("smarthire_active_provider") || "";

      const result = await analyzeResume({
        file,
        jobDescription,
        provider: activeProvider,
        token: accessToken,
      });

      navigate("/analysis/new", {
        state: {
          analysis: result,
          filename: file.name,
          isNew: true,
        },
      });
    } catch (err) {
      console.error("Resume analysis error:", err);

      const message =
        typeof err?.message === "string"
          ? err.message
          : typeof err?.detail === "string"
            ? err.detail
            : "";

      if (
        message === "[object Object]" ||
        message.toLowerCase().includes("free resume") ||
        message.toLowerCase().includes("resume analyses") ||
        message.toLowerCase().includes("quota") ||
        message.toLowerCase().includes("usage limit") ||
        message.toLowerCase().includes("limit reached")
      ) {
        setError(
          "Free resume analyses exhausted. Add your API key in AI Settings to continue.",
        );
      } else {
        setError(message || "Analysis failed.");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-7xl px-2 py-2 page-shell">
      <section className="center-heading">
        <p className="eyebrow">ANALYZE YOUR RESUME</p>
      </section>

      <div className="analyze-grid">
        <div
          className={`upload-card ${dragging ? "dragging" : ""}`}
          onDragOver={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            setDragging(false);
            selectFile(event.dataTransfer.files?.[0]);
          }}
          onClick={() => inputRef.current?.click()}
        >
          <div className="upload-visual">
            {file ? <CheckCircle2 size={25} /> : <Upload size={25} />}
          </div>

          <h2>{file ? file.name : "Upload your resume"}</h2>

          <p>
            {file
              ? "Your resume is ready for AI analysis."
              : "Drag & drop your PDF or DOCX here, or click to browse."}
          </p>

          <span className="upload-meta">Maximum 5 MB</span>

          <button
            type="button"
            className="button secondary browse-button"
            onClick={(event) => {
              event.stopPropagation();
              inputRef.current?.click();
            }}
          >
            Browse Files
          </button>

          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.doc,.docx"
            hidden
            onChange={(event) => selectFile(event.target.files?.[0])}
          />

          {file && (
            <div className="file-ready">
              <CheckCircle2 size={15} /> File selected
            </div>
          )}
        </div>

        <div className="jd-card">
          <div className="field-label">
            <span>Job Description</span>
            <span className="optional">Optional</span>
          </div>

          <textarea
            value={jobDescription}
            onChange={(event) => setJobDescription(event.target.value)}
            placeholder="Paste the job description here..."
            maxLength={5000}
          />

          <div className="textarea-footer">{jobDescription.length} / 5000</div>
        </div>
      </div>

      {error && <div className="analyze-error">{error}</div>}

      <div className="analyze-actions">
        <button
          className="button secondary large"
          onClick={submit}
          disabled={busy}
        >
          {busy ? "Analyzing resume..." : "Analyze Resume"}
        </button>
      </div>
    </div>
  );
}
