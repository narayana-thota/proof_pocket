
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  FileText,
  CheckCircle2,
  Clock3,
  AlertCircle,
  UploadCloud,
  MessageSquareText,
  BellRing,
  ArrowRight,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  FileSpreadsheet,
  FileImage,
  File,
} from "lucide-react";

import api from "../services/api";
import "./Dashboard.css";

function formatDate(value) {
  if (!value) return "Date unavailable";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return "Date unavailable";

  return date.toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function formatSize(bytes = 0) {
  if (!bytes) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;

  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function getFileIcon(extension = "") {
  const ext = extension.toLowerCase();

  if (ext === ".xlsx") return FileSpreadsheet;
  if ([".jpg", ".jpeg", ".png"].includes(ext)) return FileImage;
  if ([".pdf", ".docx", ".txt"].includes(ext)) return FileText;

  return File;
}

function getStatus(status) {
  const value = (status || "pending").toLowerCase();

  if (value === "completed") {
    return { label: "Processed", className: "success" };
  }

  if (value === "processing") {
    return { label: "Processing", className: "processing" };
  }

  if (value === "failed") {
    return { label: "Failed", className: "failed" };
  }

  return { label: "Pending", className: "pending" };
}

function getErrorMessage(error) {
  return (
    error?.response?.data?.detail ||
    error?.message ||
    "Unable to load dashboard information."
  );
}

export default function Dashboard() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadDashboard = useCallback(async () => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get("/api/documents/");
      const data = response.data;

      setDocuments(
        Array.isArray(data?.documents) ? data.documents : []
      );
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  const stats = useMemo(() => {
    const processed = documents.filter(
      (document) =>
        (document.processing_status || "").toLowerCase() === "completed"
    ).length;

    const failed = documents.filter(
      (document) =>
        (document.processing_status || "").toLowerCase() === "failed"
    ).length;

    const pending = documents.filter((document) =>
      ["pending", "processing"].includes(
        (document.processing_status || "pending").toLowerCase()
      )
    ).length;

    return {
      total: documents.length,
      processed,
      pending,
      failed,
    };
  }, [documents]);

  const recentDocuments = useMemo(() => {
    return [...documents]
      .sort((a, b) => {
        return (
          new Date(b.created_at || 0).getTime() -
          new Date(a.created_at || 0).getTime()
        );
      })
      .slice(0, 5);
  }, [documents]);

  return (
    <main className="pp-dashboard">
      {/* Page heading */}
      <section className="pp-dashboard-heading">
        <div>
          <span className="pp-dashboard-eyebrow">
            YOUR PERSONAL WORKSPACE
          </span>

          <h1>Dashboard</h1>

          <p>
            Everything important, organized in one secure place.
          </p>
        </div>

        <button
          type="button"
          className="pp-dashboard-refresh"
          onClick={loadDashboard}
          disabled={loading}
        >
          <RefreshCw
            size={16}
            className={loading ? "pp-spin" : ""}
          />
          <span>Refresh</span>
        </button>
      </section>

      {/* Welcome banner */}
      <section className="pp-welcome-banner">
        <div className="pp-welcome-content">
          <span className="pp-welcome-label">
            <Sparkles size={14} />
            WELCOME TO PROOFPOCKET
          </span>

          <h2>
            Your documents, in one
            <br />
            <span>secure pocket.</span>
          </h2>

          <p>
            Upload, organize, search and chat with your important
            documents. Keep everything accessible whenever you need it.
          </p>

          <div className="pp-welcome-actions">
            <Link to="/documents" className="pp-primary-action">
              <UploadCloud size={17} />
              Upload a document
            </Link>

            <Link to="/chat" className="pp-secondary-action">
              Explore AI chat
              <ArrowRight size={16} />
            </Link>
          </div>
        </div>

        <div className="pp-welcome-illustration" aria-hidden="true">
          <div className="pp-illustration-glow" />

          <div className="pp-illustration-card pp-illustration-back">
            <FileText size={29} />
          </div>

          <div className="pp-illustration-card pp-illustration-front">
            <div className="pp-illustration-shield">
              <ShieldCheck size={42} />
            </div>
            <span>Secure library</span>
            <small>Your files, protected</small>
          </div>

          <div className="pp-illustration-sparkle">
            <Sparkles size={19} />
          </div>
        </div>
      </section>

      {/* Error notice */}
      {error && (
        <div className="pp-dashboard-error" role="alert">
          <AlertCircle size={18} />
          <span>{error}</span>

          <button type="button" onClick={loadDashboard}>
            Try again
          </button>
        </div>
      )}

      {/* Statistics */}
      <section className="pp-dashboard-stats">
        <article className="pp-stat-card">
          <div className="pp-stat-top">
            <div className="pp-stat-icon purple">
              <FileText size={21} />
            </div>
            <span className="pp-stat-caption">YOUR LIBRARY</span>
          </div>

          <strong className="pp-stat-value">
            {loading ? "—" : stats.total}
          </strong>

          <span className="pp-stat-description">
            Total documents
          </span>
        </article>

        <article className="pp-stat-card">
          <div className="pp-stat-top">
            <div className="pp-stat-icon green">
              <CheckCircle2 size={21} />
            </div>
            <span className="pp-stat-caption">READY TO USE</span>
          </div>

          <strong className="pp-stat-value">
            {loading ? "—" : stats.processed}
          </strong>

          <span className="pp-stat-description">
            Successfully processed
          </span>
        </article>

        <article className="pp-stat-card">
          <div className="pp-stat-top">
            <div className="pp-stat-icon orange">
              <Clock3 size={21} />
            </div>
            <span className="pp-stat-caption">IN PROGRESS</span>
          </div>

          <strong className="pp-stat-value">
            {loading ? "—" : stats.pending}
          </strong>

          <span className="pp-stat-description">
            Pending or processing
          </span>
        </article>

        <article className="pp-stat-card">
          <div className="pp-stat-top">
            <div className="pp-stat-icon blue">
              <AlertCircle size={21} />
            </div>
            <span className="pp-stat-caption">NEEDS ATTENTION</span>
          </div>

          <strong className="pp-stat-value">
            {loading ? "—" : stats.failed}
          </strong>

          <span className="pp-stat-description">
            Documents with errors
          </span>
        </article>
      </section>

      {/* Main dashboard content */}
      <section className="pp-dashboard-main">
        <div className="pp-dashboard-panel pp-recent-panel">
          <div className="pp-panel-heading">
            <div>
              <h3>Recent documents</h3>
              <p>Your latest additions to ProofPocket.</p>
            </div>

            <Link to="/documents" className="pp-panel-link">
              View all
              <ArrowRight size={16} />
            </Link>
          </div>

          {loading ? (
            <div className="pp-dashboard-empty">
              <RefreshCw size={23} className="pp-spin" />
              <span>Loading your documents...</span>
            </div>
          ) : recentDocuments.length === 0 ? (
            <div className="pp-dashboard-empty">
              <div className="pp-empty-icon">
                <FileText size={26} />
              </div>

              <h4>Your library is waiting</h4>

              <p>
                Upload your first document to start building your
                personal library.
              </p>

              <Link to="/documents" className="pp-empty-link">
                Upload your first document
                <ArrowRight size={15} />
              </Link>
            </div>
          ) : (
            <div className="pp-recent-list">
              {recentDocuments.map((document) => {
                const Icon = getFileIcon(
                  document.file_extension ||
                    document.original_file_name?.slice(
                      document.original_file_name.lastIndexOf(".")
                    )
                );

                const status = getStatus(document.processing_status);

                return (
                  <article
                    className="pp-recent-document"
                    key={document.document_id}
                  >
                    <div className="pp-recent-file-icon">
                      <Icon size={20} />
                    </div>

                    <div className="pp-recent-file-info">
                      <strong title={document.original_file_name}>
                        {document.original_file_name ||
                          document.document_name ||
                          "Untitled document"}
                      </strong>

                      <span>
                        {formatSize(document.file_size_bytes)}
                        <span className="pp-meta-dot">·</span>
                        {formatDate(document.created_at)}
                      </span>
                    </div>

                    <span
                      className={`pp-document-status ${status.className}`}
                    >
                      <span className="pp-status-dot" />
                      {status.label}
                    </span>
                  </article>
                );
              })}
            </div>
          )}
        </div>

        {/* Quick actions */}
        <aside className="pp-dashboard-panel pp-quick-panel">
          <div className="pp-panel-heading">
            <div>
              <h3>Quick actions</h3>
              <p>Pick up where you left off.</p>
            </div>
          </div>

          <div className="pp-quick-actions">
            <Link to="/documents" className="pp-quick-action">
              <div className="pp-quick-icon purple">
                <UploadCloud size={20} />
              </div>

              <div>
                <strong>Upload document</strong>
                <span>Add a file to your library</span>
              </div>

              <ArrowRight size={17} className="pp-quick-arrow" />
            </Link>

            <Link to="/chat" className="pp-quick-action">
              <div className="pp-quick-icon blue">
                <MessageSquareText size={20} />
              </div>

              <div>
                <strong>Ask your documents</strong>
                <span>Get answers with AI chat</span>
              </div>

              <ArrowRight size={17} className="pp-quick-arrow" />
            </Link>

            <Link to="/reminders" className="pp-quick-action">
              <div className="pp-quick-icon orange">
                <BellRing size={20} />
              </div>

              <div>
                <strong>Manage reminders</strong>
                <span>Stay on top of deadlines</span>
              </div>

              <ArrowRight size={17} className="pp-quick-arrow" />
            </Link>
          </div>

          <div className="pp-security-note">
            <ShieldCheck size={19} />

            <div>
              <strong>Your documents stay protected</strong>
              <span>
                Your personal library is stored securely.
              </span>
            </div>
          </div>
        </aside>
      </section>

      {/* Bottom information */}
      <section className="pp-dashboard-footer">
        <div>
          <Sparkles size={17} />
          <span>
            Make your documents work smarter with ProofPocket AI.
          </span>
        </div>

        <Link to="/chat">
          Start a conversation
          <ArrowRight size={15} />
        </Link>
      </section>
    </main>
  );
}
