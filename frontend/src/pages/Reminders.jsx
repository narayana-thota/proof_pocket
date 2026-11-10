import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  Bell,
  CalendarDays,
  Check,
  CheckCircle2,
  ChevronDown,
  Clock3,
  Edit3,
  FileText,
  LoaderCircle,
  Plus,
  Search,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import api from "../services/api";
import "./Reminders.css";
import "./Reminders_AI_Suggestions.css";

const REMINDER_TYPES = [
  { value: "warranty", label: "Warranty" },
  { value: "expiry", label: "Expiry" },
  { value: "renewal", label: "Renewal" },
  { value: "custom", label: "Custom" },
];

const EMPTY_FORM = {
  document_id: "",
  reminder_title: "",
  reminder_type: "custom",
  due_date: "",
  notify_at: "",
};

function getErrorMessage(error, fallback = "Something went wrong. Please try again.") {
  const detail = error?.response?.data?.detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item?.msg || String(item)).join(", ");
  }
  if (typeof detail === "string") return detail;
  return error?.message || fallback;
}

function dateOnly(value) {
  if (!value) return "";
  if (typeof value === "string") return value.slice(0, 10);
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function toLocalDateTimeInput(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value).slice(0, 16);
  const offset = date.getTimezoneOffset();
  const local = new Date(date.getTime() - offset * 60_000);
  return local.toISOString().slice(0, 16);
}

function toApiDateTime(value) {
  if (!value) return "";
  // datetime-local is interpreted in the user's local timezone.
  return new Date(value).toISOString();
}

function formatDate(value) {
  if (!value) return "No date";
  const date = new Date(`${dateOnly(value)}T00:00:00`);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function formatDateTime(value) {
  if (!value) return "Not set";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function documentName(document) {
  return (
    document?.original_file_name ||
    document?.document_name ||
    `Document ${document?.document_id}`
  );
}

function reminderStatus(reminder) {
  const status = String(reminder?.status || "pending").toLowerCase();
  if (status === "completed") return "completed";
  if (status === "cancelled") return "cancelled";

  const due = dateOnly(reminder?.due_date);
  const today = dateOnly(new Date());
  return due && due < today ? "overdue" : "upcoming";
}

function typeLabel(type) {
  return REMINDER_TYPES.find((item) => item.value === type)?.label || "Custom";
}

function makeFormData(reminder) {
  return {
    document_id: String(reminder?.document_id ?? ""),
    reminder_title: reminder?.reminder_title || "",
    reminder_type: reminder?.reminder_type || "custom",
    due_date: dateOnly(reminder?.due_date),
    notify_at: toLocalDateTimeInput(reminder?.notify_at),
  };
}

export default function Reminders() {
  const [reminders, setReminders] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [documentsLoading, setDocumentsLoading] = useState(true);
  const [pageError, setPageError] = useState("");
  const [actionError, setActionError] = useState("");
  const [search, setSearch] = useState("");
  const [activeFilter, setActiveFilter] = useState("all");
  const [modalOpen, setModalOpen] = useState(false);
  const [editingReminder, setEditingReminder] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [updatingId, setUpdatingId] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [suggestionsLoading, setSuggestionsLoading] = useState(true);
  const [suggestionActionId, setSuggestionActionId] = useState(null);

  const loadReminders = useCallback(async () => {
    try {
      setLoading(true);
      setPageError("");
      const response = await api.get("/api/reminders/");
      setReminders(Array.isArray(response.data?.reminders) ? response.data.reminders : []);
    } catch (error) {
      setPageError(getErrorMessage(error, "Unable to load reminders."));
    } finally {
      setLoading(false);
    }
  }, []);

  const loadSuggestions = useCallback(async () => {
    try {
      setSuggestionsLoading(true);
      const response = await api.get("/api/reminders/suggestions", {
        params: { status: "pending" },
      });
      setSuggestions(
        Array.isArray(response.data?.suggestions)
          ? response.data.suggestions
          : []
      );
    } catch (error) {
      setActionError(
        getErrorMessage(error, "Unable to load AI reminder suggestions.")
      );
    } finally {
      setSuggestionsLoading(false);
    }
  }, []);

  const loadDocuments = useCallback(async () => {
    try {
      setDocumentsLoading(true);
      const response = await api.get("/api/documents/");
      const docs = Array.isArray(response.data?.documents) ? response.data.documents : [];
      setDocuments(docs);
    } catch (error) {
      setActionError(getErrorMessage(error, "Unable to load your documents."));
    } finally {
      setDocumentsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadReminders();
    loadDocuments();
    loadSuggestions();
  }, [loadReminders, loadDocuments, loadSuggestions]);

  const documentMap = useMemo(() => {
    return new Map(documents.map((document) => [String(document.document_id), document]));
  }, [documents]);

  const counts = useMemo(() => {
    const result = { all: reminders.length, upcoming: 0, overdue: 0, completed: 0, cancelled: 0 };
    reminders.forEach((reminder) => {
      const status = reminderStatus(reminder);
      if (status in result) result[status] += 1;
    });
    return result;
  }, [reminders]);

  const filteredReminders = useMemo(() => {
    const query = search.trim().toLowerCase();

    return reminders
      .filter((reminder) => {
        const status = reminderStatus(reminder);
        const matchesFilter = activeFilter === "all" || status === activeFilter;
        const doc = documentMap.get(String(reminder.document_id));
        const text = [
          reminder.reminder_title,
          reminder.reminder_type,
          reminder.status,
          doc ? documentName(doc) : `document ${reminder.document_id}`,
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();

        return matchesFilter && (!query || text.includes(query));
      })
      .sort((a, b) => {
        const aDate = dateOnly(a.due_date);
        const bDate = dateOnly(b.due_date);
        return aDate.localeCompare(bDate);
      });
  }, [reminders, activeFilter, search, documentMap]);

  const openCreateModal = () => {
    setEditingReminder(null);
    setForm(EMPTY_FORM);
    setActionError("");
    setModalOpen(true);
  };

  const openEditModal = (reminder) => {
    setEditingReminder(reminder);
    setForm(makeFormData(reminder));
    setActionError("");
    setModalOpen(true);
  };

  const closeModal = () => {
    if (saving) return;
    setModalOpen(false);
    setEditingReminder(null);
    setForm(EMPTY_FORM);
  };

  const updateForm = (field, value) => {
    setForm((previous) => ({ ...previous, [field]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setActionError("");

    if (!form.document_id) {
      setActionError("Please select the document this reminder belongs to.");
      return;
    }
    if (!form.reminder_title.trim()) {
      setActionError("Please enter a reminder title.");
      return;
    }
    if (!form.due_date || !form.notify_at) {
      setActionError("Please provide both the due date and notification date/time.");
      return;
    }

    const due = new Date(`${form.due_date}T00:00:00`);
    const notify = new Date(form.notify_at);
    if (Number.isNaN(due.getTime()) || Number.isNaN(notify.getTime())) {
      setActionError("Please enter valid dates and times.");
      return;
    }

    const payload = {
      reminder_title: form.reminder_title.trim(),
      reminder_type: form.reminder_type,
      due_date: form.due_date,
      notify_at: toApiDateTime(form.notify_at),
    };

    try {
      setSaving(true);

      if (editingReminder) {
        await api.put(`/api/reminders/${editingReminder.reminder_id}`, payload);
      } else {
        await api.post("/api/reminders/", {
          ...payload,
          document_id: Number(form.document_id),
        });
      }

      setModalOpen(false);
      setEditingReminder(null);
      setForm(EMPTY_FORM);
      await loadReminders();
    } catch (error) {
      setActionError(getErrorMessage(error, "Unable to save this reminder."));
    } finally {
      setSaving(false);
    }
  };

  const approveSuggestion = async (suggestion) => {
    setActionError("");
    setSuggestionActionId(suggestion.suggestion_id);

    try {
      await api.post(
        `/api/reminders/suggestions/${suggestion.suggestion_id}/approve`,
        {}
      );
      await Promise.all([loadSuggestions(), loadReminders()]);
    } catch (error) {
      setActionError(
        getErrorMessage(error, "Unable to approve this AI suggestion.")
      );
    } finally {
      setSuggestionActionId(null);
    }
  };

  const rejectSuggestion = async (suggestion) => {
    setActionError("");
    setSuggestionActionId(suggestion.suggestion_id);

    try {
      await api.post(
        `/api/reminders/suggestions/${suggestion.suggestion_id}/reject`
      );
      await loadSuggestions();
    } catch (error) {
      setActionError(
        getErrorMessage(error, "Unable to reject this AI suggestion.")
      );
    } finally {
      setSuggestionActionId(null);
    }
  };

  const markCompleted = async (reminder) => {
    setActionError("");
    setUpdatingId(reminder.reminder_id);
    try {
      await api.put(`/api/reminders/${reminder.reminder_id}`, { status: "completed" });
      await loadReminders();
    } catch (error) {
      setActionError(getErrorMessage(error, "Unable to update reminder status."));
    } finally {
      setUpdatingId(null);
    }
  };

  const deleteReminder = async (reminder) => {
    const confirmed = window.confirm(
      `Delete "${reminder.reminder_title}"? This action cannot be undone.`
    );
    if (!confirmed) return;

    setActionError("");
    setDeletingId(reminder.reminder_id);
    try {
      await api.delete(`/api/reminders/${reminder.reminder_id}`);
      setReminders((previous) =>
        previous.filter((item) => item.reminder_id !== reminder.reminder_id)
      );
    } catch (error) {
      setActionError(getErrorMessage(error, "Unable to delete this reminder."));
    } finally {
      setDeletingId(null);
    }
  };

  const filters = [
    { value: "all", label: "All reminders", count: counts.all },
    { value: "upcoming", label: "Upcoming", count: counts.upcoming },
    { value: "overdue", label: "Overdue", count: counts.overdue },
    { value: "completed", label: "Completed", count: counts.completed },
  ];

  return (
    <div className="pp-reminders-page">
      <div className="pp-reminders-header">
        <div>
          <div className="pp-reminders-eyebrow"><Bell size={13} /> STAY AHEAD OF IMPORTANT DATES</div>
          <h1>Reminders</h1>
          <p>Keep warranties, expirations, renewals, and important dates on track.</p>
        </div>
        <button type="button" className="pp-reminders-primary" onClick={openCreateModal}>
          <Plus size={17} /> Create reminder
        </button>
      </div>

      {pageError && (
        <div className="pp-reminders-alert" role="alert">
          <AlertCircle size={17} />
          <span>{pageError}</span>
          <button type="button" onClick={loadReminders}>Retry</button>
        </div>
      )}

      {actionError && !modalOpen && (
        <div className="pp-reminders-alert" role="alert">
          <AlertCircle size={17} />
          <span>{actionError}</span>
          <button type="button" onClick={() => setActionError("")} aria-label="Dismiss"><X size={15} /></button>
        </div>
      )}

      <section className="pp-reminders-stats">
        <div className="pp-reminder-stat">
          <div className="pp-reminder-stat-icon total"><Bell size={18} /></div>
          <div><span>Total reminders</span><strong>{counts.all}</strong></div>
        </div>
        <div className="pp-reminder-stat">
          <div className="pp-reminder-stat-icon upcoming"><CalendarDays size={18} /></div>
          <div><span>Upcoming</span><strong>{counts.upcoming}</strong></div>
        </div>
        <div className="pp-reminder-stat">
          <div className="pp-reminder-stat-icon overdue"><Clock3 size={18} /></div>
          <div><span>Overdue</span><strong>{counts.overdue}</strong></div>
        </div>
        <div className="pp-reminder-stat">
          <div className="pp-reminder-stat-icon completed"><CheckCircle2 size={18} /></div>
          <div><span>Completed</span><strong>{counts.completed}</strong></div>
        </div>
      </section>

      <section className="pp-ai-suggestions-panel">
        <div className="pp-ai-suggestions-heading">
          <div className="pp-ai-suggestions-title">
            <span className="pp-ai-suggestions-icon"><Sparkles size={17} /></span>
            <div>
              <h2>AI-generated suggestions</h2>
              <p>Review dates identified from your uploaded documents before adding them to your reminders.</p>
            </div>
          </div>
          <span className="pp-ai-suggestions-count">
            {suggestions.length} pending
          </span>
        </div>

        {suggestionsLoading ? (
          <div className="pp-reminders-state">
            <LoaderCircle size={22} className="pp-reminders-spin" />
            <span>Checking AI suggestions...</span>
          </div>
        ) : suggestions.length === 0 ? (
          <div className="pp-ai-suggestions-empty">
            <Sparkles size={19} />
            <span>No pending AI suggestions. Upload and extract a document containing important dates to discover suggestions.</span>
          </div>
        ) : (
          <div className="pp-ai-suggestions-list">
            {suggestions.map((suggestion) => {
              const isBusy = suggestionActionId === suggestion.suggestion_id;
              const sourceName =
                suggestion.original_file_name ||
                suggestion.document_name ||
                `Document #${suggestion.document_id}`;
              const confidence = Number(suggestion.confidence);

              return (
                <article className="pp-ai-suggestion-card" key={suggestion.suggestion_id}>
                  <div className="pp-ai-suggestion-main">
                    <div className="pp-ai-suggestion-card-heading">
                      <h3>{suggestion.reminder_title}</h3>
                      <span className="pp-ai-suggestion-type">
                        {typeLabel(suggestion.reminder_type)}
                      </span>
                    </div>

                    <div className="pp-ai-suggestion-meta">
                      <span><FileText size={13} /> {sourceName}</span>
                      <span><CalendarDays size={13} /> Due {formatDate(suggestion.due_date)}</span>
                      <span><Clock3 size={13} /> Notify {formatDateTime(suggestion.notify_at)}</span>
                      {Number.isFinite(confidence) && (
                        <span>{Math.round(confidence * 100)}% confidence</span>
                      )}
                    </div>

                    {suggestion.evidence && (
                      <blockquote className="pp-ai-suggestion-evidence">
                        <strong>Evidence from document</strong>
                        <p>“{suggestion.evidence}”</p>
                      </blockquote>
                    )}
                  </div>

                  <div className="pp-ai-suggestion-actions">
                    <button
                      type="button"
                      className="pp-ai-suggestion-approve"
                      onClick={() => approveSuggestion(suggestion)}
                      disabled={isBusy}
                    >
                      {isBusy ? (
                        <LoaderCircle size={15} className="pp-reminders-spin" />
                      ) : <Check size={15} />}
                      Approve
                    </button>
                    <button
                      type="button"
                      className="pp-ai-suggestion-reject"
                      onClick={() => rejectSuggestion(suggestion)}
                      disabled={isBusy}
                    >
                      <X size={15} />
                      Reject
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>

      <section className="pp-reminders-panel">
        <div className="pp-reminders-toolbar">
          <div className="pp-reminders-filter-tabs">
            {filters.map((filter) => (
              <button
                type="button"
                key={filter.value}
                className={activeFilter === filter.value ? "active" : ""}
                onClick={() => setActiveFilter(filter.value)}
              >
                {filter.label}
                <span>{filter.count}</span>
              </button>
            ))}
          </div>

          <label className="pp-reminders-search">
            <Search size={16} />
            <input
              type="search"
              placeholder="Search reminders..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </label>
        </div>

        {loading ? (
          <div className="pp-reminders-state">
            <LoaderCircle size={25} className="pp-reminders-spin" />
            <span>Loading your reminders...</span>
          </div>
        ) : filteredReminders.length === 0 ? (
          <div className="pp-reminders-empty">
            <div className="pp-reminders-empty-icon"><CalendarDays size={25} /></div>
            <h3>{search || activeFilter !== "all" ? "No matching reminders" : "No reminders yet"}</h3>
            <p>
              {search || activeFilter !== "all"
                ? "Try another search or filter to find what you need."
                : "Create a reminder to keep track of an important date linked to one of your documents."}
            </p>
            {!search && activeFilter === "all" && (
              <button type="button" className="pp-reminders-primary" onClick={openCreateModal}>
                <Plus size={16} /> Create your first reminder
              </button>
            )}
          </div>
        ) : (
          <div className="pp-reminders-list">
            {filteredReminders.map((reminder) => {
              const status = reminderStatus(reminder);
              const doc = documentMap.get(String(reminder.document_id));
              const isBusy =
                deletingId === reminder.reminder_id ||
                updatingId === reminder.reminder_id;

              return (
                <article className="pp-reminder-card" key={reminder.reminder_id}>
                  <div className={`pp-reminder-card-icon ${status}`}>
                    {status === "completed" ? <CheckCircle2 size={19} /> : <CalendarDays size={19} />}
                  </div>

                  <div className="pp-reminder-card-content">
                    <div className="pp-reminder-card-heading">
                      <h3>{reminder.reminder_title}</h3>
                      <span className={`pp-reminder-status ${status}`}>
                        {status === "upcoming" ? "Upcoming" : status === "overdue" ? "Overdue" : status === "completed" ? "Completed" : "Cancelled"}
                      </span>
                    </div>
                    <div className="pp-reminder-card-meta">
                      <span className="pp-reminder-type">{typeLabel(reminder.reminder_type)}</span>
                      <span><FileText size={13} /> {doc ? documentName(doc) : `Document #${reminder.document_id}`}</span>
                      <span><CalendarDays size={13} /> Due {formatDate(reminder.due_date)}</span>
                      <span><Clock3 size={13} /> Notify {formatDateTime(reminder.notify_at)}</span>
                    </div>
                  </div>

                  <div className="pp-reminder-card-actions">
                    {status !== "completed" && status !== "cancelled" && (
                      <button
                        type="button"
                        className="pp-reminder-complete"
                        title="Mark as completed"
                        onClick={() => markCompleted(reminder)}
                        disabled={isBusy}
                      >
                        {updatingId === reminder.reminder_id ? (
                          <LoaderCircle size={16} className="pp-reminders-spin" />
                        ) : <Check size={16} />}
                        <span>Complete</span>
                      </button>
                    )}
                    <button
                      type="button"
                      className="pp-reminder-icon-action"
                      title="Edit reminder"
                      onClick={() => openEditModal(reminder)}
                      disabled={isBusy}
                    >
                      <Edit3 size={16} />
                    </button>
                    <button
                      type="button"
                      className="pp-reminder-icon-action danger"
                      title="Delete reminder"
                      onClick={() => deleteReminder(reminder)}
                      disabled={isBusy}
                    >
                      {deletingId === reminder.reminder_id ? (
                        <LoaderCircle size={16} className="pp-reminders-spin" />
                      ) : <Trash2 size={16} />}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>

      {modalOpen && (
        <div className="pp-reminders-modal-backdrop" onMouseDown={(event) => {
          if (event.target === event.currentTarget) closeModal();
        }}>
          <section
            className="pp-reminders-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="pp-reminders-modal-title"
          >
            <div className="pp-reminders-modal-header">
              <div>
                <span>{editingReminder ? "UPDATE YOUR SCHEDULE" : "PLAN AHEAD"}</span>
                <h2 id="pp-reminders-modal-title">
                  {editingReminder ? "Edit reminder" : "Create a reminder"}
                </h2>
              </div>
              <button type="button" onClick={closeModal} disabled={saving} aria-label="Close">
                <X size={19} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="pp-reminders-form">
              {actionError && (
                <div className="pp-reminders-alert modal-error" role="alert">
                  <AlertCircle size={16} />
                  <span>{actionError}</span>
                </div>
              )}

              <div className="pp-reminders-field">
                <label htmlFor="reminder-title">Reminder title <span>*</span></label>
                <input
                  id="reminder-title"
                  type="text"
                  maxLength={255}
                  placeholder="e.g. Laptop warranty expires"
                  value={form.reminder_title}
                  onChange={(event) => updateForm("reminder_title", event.target.value)}
                  required
                />
              </div>

              <div className="pp-reminders-form-grid">
                <div className="pp-reminders-field">
                  <label htmlFor="reminder-type">Reminder type</label>
                  <div className="pp-reminders-select">
                    <select
                      id="reminder-type"
                      value={form.reminder_type}
                      onChange={(event) => updateForm("reminder_type", event.target.value)}
                    >
                      {REMINDER_TYPES.map((type) => (
                        <option key={type.value} value={type.value}>{type.label}</option>
                      ))}
                    </select>
                    <ChevronDown size={15} />
                  </div>
                </div>

                <div className="pp-reminders-field">
                  <label htmlFor="reminder-document">Linked document <span>*</span></label>
                  <div className="pp-reminders-select">
                    <select
                      id="reminder-document"
                      value={form.document_id}
                      onChange={(event) => updateForm("document_id", event.target.value)}
                      disabled={documentsLoading || Boolean(editingReminder)}
                      required
                    >
                      <option value="">
                        {documentsLoading ? "Loading documents..." : "Select a document"}
                      </option>
                      {documents.map((document) => (
                        <option key={document.document_id} value={document.document_id}>
                          {documentName(document)}
                        </option>
                      ))}
                    </select>
                    <ChevronDown size={15} />
                  </div>
                  {editingReminder && (
                    <small>Reminder document cannot be changed after creation.</small>
                  )}
                </div>
              </div>

              <div className="pp-reminders-form-grid">
                <div className="pp-reminders-field">
                  <label htmlFor="reminder-due-date">Due date <span>*</span></label>
                  <input
                    id="reminder-due-date"
                    type="date"
                    value={form.due_date}
                    onChange={(event) => updateForm("due_date", event.target.value)}
                    required
                  />
                </div>

                <div className="pp-reminders-field">
                  <label htmlFor="reminder-notify-at">Notify at <span>*</span></label>
                  <input
                    id="reminder-notify-at"
                    type="datetime-local"
                    value={form.notify_at}
                    onChange={(event) => updateForm("notify_at", event.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="pp-reminders-form-note">
                <Bell size={15} />
                <span>
                  This saves a notification date and time in your reminder. Actual email,
                  push, or in-app delivery depends on your notification scheduler.
                </span>
              </div>

              <div className="pp-reminders-modal-actions">
                <button
                  type="button"
                  className="pp-reminders-secondary"
                  onClick={closeModal}
                  disabled={saving}
                >
                  Cancel
                </button>
                <button type="submit" className="pp-reminders-primary" disabled={saving}>
                  {saving ? (
                    <><LoaderCircle size={16} className="pp-reminders-spin" /> Saving...</>
                  ) : (
                    <><Check size={16} /> {editingReminder ? "Save changes" : "Create reminder"}</>
                  )}
                </button>
              </div>
            </form>
          </section>
        </div>
      )}
    </div>
  );
}
