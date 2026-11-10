import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  AlertCircle,
  ArrowRight,
  Check,
  ChevronDown,
  Clock3,
  FileText,
  LoaderCircle,
  Menu,
  MessageSquare,
  Plus,
  Send,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";

import api from "../services/api";
import "./Chat.css";

function getErrorMessage(error, fallback = "Something went wrong. Please try again.") {
  const detail = error?.response?.data?.detail;

  if (Array.isArray(detail)) {
    return detail.map((item) => item?.msg || String(item)).join(", ");
  }

  if (typeof detail === "string") return detail;
  return error?.message || fallback;
}

function formatDate(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";

  return date.toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
  });
}

function formatTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";

  return date.toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getMessageText(message) {
  if (typeof message === "string") return message;
  return (
    message?.message_content ||
    message?.content ||
    message?.text ||
    message?.answer ||
    ""
  );
}

function getMessageRole(message) {
  const role = (message?.message_role || message?.role || "").toLowerCase();
  return role === "assistant" || role === "ai" ? "assistant" : "user";
}

/*
 * context_builder.py currently returns these exact source fields.
 * It does not return original filenames or page numbers, so the UI
 * deliberately displays document/chunk identifiers instead.
 */
function getSources(result) {
  const sources = Array.isArray(result?.sources) ? result.sources : [];

  return sources.map((source, index) => ({
    id: `${source?.source_number ?? index + 1}-${source?.chunk_id ?? "unknown"}`,
    sourceNumber: source?.source_number ?? index + 1,
    chunkId: source?.chunk_id,
    documentId: source?.document_id,
    chunkIndex: source?.chunk_index,
    sourceType: source?.source_type,
    retrievalScore: source?.retrieval_score,
    denseScore: source?.dense_score,
    sparseScore: source?.sparse_score,
    crossEncoderScore: source?.cross_encoder_score,
    rerankRank: source?.rerank_rank,
  }));
}

function getAnswer(result) {
  if (typeof result?.answer === "string") return result.answer;
  if (typeof result?.response === "string") return result.response;
  if (typeof result?.message === "string") return result.message;
  return "I couldn't generate an answer for that question.";
}

function makeConversationTitle(conversation) {
  const date = formatDate(conversation?.last_message_at);
  const count = Number(conversation?.message_count || 0);
  return `Conversation${date ? ` · ${date}` : ""}${count ? ` · ${count} messages` : ""}`;
}

function isProcessed(document) {
  return String(document?.processing_status || "").toLowerCase() === "completed";
}

function getDocumentName(document) {
  return (
    document?.original_file_name ||
    document?.document_name ||
    `Document ${document?.document_id}`
  );
}

function isAmbiguousSingleDocumentSummary(question) {
  const text = question.toLowerCase();
  const asksForSummary =
    /\b(summarize|summarise|summary|overview)\b/.test(text);
  const refersToOneUnspecifiedDocument =
    /\b(my|the|this|that)\s+document\b/.test(text) ||
    /\bmy file\b/.test(text);
  const explicitlyRequestsAll =
    /\b(all|every)\s+(of\s+)?(my\s+)?(documents|files)\b/.test(text);

  return asksForSummary && refersToOneUnspecifiedDocument && !explicitlyRequestsAll;
}

function formatScore(value) {
  if (typeof value !== "number" || !Number.isFinite(value)) return null;
  return value.toFixed(3);
}

export default function Chat() {
  const [conversations, setConversations] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [selectedDocumentId, setSelectedDocumentId] = useState("");
  const [loadingConversations, setLoadingConversations] = useState(true);
  const [loadingDocuments, setLoadingDocuments] = useState(true);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [sending, setSending] = useState(false);
  const [pageError, setPageError] = useState("");
  const [chatError, setChatError] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [summaryClarification, setSummaryClarification] = useState(false);

  const textareaRef = useRef(null);
  const messagesEndRef = useRef(null);

  const processedDocuments = useMemo(
    () => documents.filter(isProcessed),
    [documents]
  );

  const selectedDocument = useMemo(
    () =>
      documents.find(
        (document) => String(document.document_id) === String(selectedDocumentId)
      ) || null,
    [documents, selectedDocumentId]
  );

  const loadConversations = useCallback(async () => {
    try {
      setLoadingConversations(true);
      setPageError("");
      const response = await api.get("/api/chat/conversations");
      setConversations(
        Array.isArray(response.data?.conversations)
          ? response.data.conversations
          : []
      );
    } catch (error) {
      setPageError(getErrorMessage(error, "Unable to load your conversations."));
    } finally {
      setLoadingConversations(false);
    }
  }, []);

  const loadDocuments = useCallback(async () => {
    try {
      setLoadingDocuments(true);
      const response = await api.get("/api/documents/");
      setDocuments(
        Array.isArray(response.data?.documents) ? response.data.documents : []
      );
    } catch (error) {
      setDocuments([]);
      setChatError(getErrorMessage(error, "Unable to load your documents."));
    } finally {
      setLoadingDocuments(false);
    }
  }, []);

  const loadHistory = useCallback(async (conversationId) => {
    if (!conversationId) return;

    try {
      setLoadingHistory(true);
      setChatError("");
      setSummaryClarification(false);

      const response = await api.get(
        `/api/chat/history/${encodeURIComponent(conversationId)}`
      );
      const history = Array.isArray(response.data?.messages)
        ? response.data.messages
        : [];

      setMessages(
        history.map((message) => ({
          id: message.chat_id ?? `${message.message_role}-${message.created_at}`,
          role: getMessageRole(message),
          content: getMessageText(message),
          createdAt: message.created_at,
          // The history endpoint currently returns message text, not source metadata.
          sources: [],
        }))
      );

      setActiveConversationId(conversationId);

      const conversation = conversations.find(
        (item) => String(item.conversation_id) === String(conversationId)
      );
      setSelectedDocumentId(
        conversation?.document_id != null ? String(conversation.document_id) : ""
      );
    } catch (error) {
      setChatError(getErrorMessage(error, "Unable to load this conversation."));
    } finally {
      setLoadingHistory(false);
    }
  }, [conversations]);

  useEffect(() => {
    loadConversations();
    loadDocuments();
  }, [loadConversations, loadDocuments]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, sending, loadingHistory, summaryClarification]);

  const startNewChat = () => {
    setActiveConversationId(null);
    setMessages([]);
    setQuestion("");
    setChatError("");
    setPageError("");
    setSelectedDocumentId("");
    setSummaryClarification(false);
    setSidebarOpen(false);
    window.setTimeout(() => textareaRef.current?.focus(), 0);
  };

  const handleSelectConversation = async (conversationId) => {
    setSidebarOpen(false);
    await loadHistory(conversationId);
  };

  const sendQuestion = async (questionText, documentId = selectedDocumentId) => {
    const trimmedQuestion = questionText.trim();
    if (!trimmedQuestion || sending) return;

    const temporaryId = `temp-${Date.now()}`;
    const userMessage = {
      id: temporaryId,
      role: "user",
      content: trimmedQuestion,
      createdAt: new Date().toISOString(),
      sources: [],
    };

    setMessages((previous) => [...previous, userMessage]);
    setQuestion("");
    setChatError("");
    setSummaryClarification(false);
    setSending(true);

    try {
      const payload = {
        question: trimmedQuestion,
        ...(activeConversationId
          ? { conversation_id: activeConversationId }
          : {}),
        ...(documentId ? { document_id: Number(documentId) } : {}),
      };

      const response = await api.post("/api/chat/ask", payload);
      const result = response.data || {};

      if (result.conversation_id) {
        setActiveConversationId(result.conversation_id);
      }

      setMessages((previous) => [
        ...previous,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: getAnswer(result),
          createdAt: new Date().toISOString(),
          sources: getSources(result),
        },
      ]);

      const conversationsResponse = await api.get("/api/chat/conversations");
      setConversations(
        Array.isArray(conversationsResponse.data?.conversations)
          ? conversationsResponse.data.conversations
          : []
      );
    } catch (error) {
      setChatError(getErrorMessage(error, "Unable to send your question."));
    } finally {
      setSending(false);
      textareaRef.current?.focus();
    }
  };

  const handleSend = async (event) => {
    event?.preventDefault();
    const trimmedQuestion = question.trim();

    if (!trimmedQuestion || sending) return;

    if (trimmedQuestion.length > 2000) {
      setChatError("Your question must be 2,000 characters or fewer.");
      return;
    }

    if (!selectedDocumentId && isAmbiguousSingleDocumentSummary(trimmedQuestion)) {
      if (activeConversationId || messages.length > 0) {
        setChatError(
          "This conversation is already using all indexed documents. Start a new conversation and select one document to summarize it individually."
        );
        return;
      }

      if (processedDocuments.length === 0) {
        setChatError(
          "There are no processed documents available yet. Upload and process a document before requesting a summary."
        );
        return;
      }

      if (processedDocuments.length > 1) {
        setSummaryClarification(true);
        setChatError("");
        return;
      }

      // Exactly one processed document: the intended document is unambiguous.
      const onlyDocumentId = String(processedDocuments[0].document_id);
      setSelectedDocumentId(onlyDocumentId);
      await sendQuestion(trimmedQuestion, onlyDocumentId);
      return;
    }

    if (selectedDocumentId && !isProcessed(selectedDocument)) {
      setChatError("The selected document has not finished processing yet.");
      return;
    }

    if (!selectedDocumentId && processedDocuments.length === 0) {
      setChatError("Upload and process a document before asking questions.");
      return;
    }

    await sendQuestion(trimmedQuestion);
  };

  const handleChooseSummaryDocument = async (documentId) => {
    if (activeConversationId || messages.length > 0) {
      setChatError("Start a new conversation to choose a different document.");
      setSummaryClarification(false);
      return;
    }

    const document = processedDocuments.find(
      (item) => String(item.document_id) === String(documentId)
    );
    if (!document) return;

    setSelectedDocumentId(String(documentId));
    setSummaryClarification(false);
    await sendQuestion(question.trim() || "Summarize my document", String(documentId));
  };

  const handleComposerKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend(event);
    }
  };

  const suggestedQuestions = [
    "Summarize my document",
    "What are the important dates?",
    "Explain the key terms",
  ];

  const scopeLabel = selectedDocument
    ? getDocumentName(selectedDocument)
    : "All my indexed documents";

  return (
    <div className="pp-chat-page">
      {sidebarOpen && (
        <button
          type="button"
          className="pp-chat-backdrop"
          aria-label="Close conversation sidebar"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside className={`pp-chat-sidebar ${sidebarOpen ? "is-open" : ""}`}>
        <div className="pp-chat-sidebar-top">
          <div className="pp-chat-sidebar-brand">
            <div className="pp-chat-brand-icon"><Sparkles size={18} /></div>
            <div>
              <strong>ProofPocket AI</strong>
              <span>Document assistant</span>
            </div>
          </div>
          <button
            type="button"
            className="pp-chat-close-sidebar"
            aria-label="Close sidebar"
            onClick={() => setSidebarOpen(false)}
          >
            <X size={19} />
          </button>
        </div>

        <button type="button" className="pp-chat-new-button" onClick={startNewChat}>
          <Plus size={18} />
          New conversation
        </button>

        <div className="pp-chat-history-heading">
          <span>RECENT CONVERSATIONS</span>
          <button
            type="button"
            title="Refresh conversations"
            onClick={loadConversations}
            disabled={loadingConversations}
          >
            {loadingConversations ? (
              <LoaderCircle size={15} className="pp-chat-spin" />
            ) : (
              <Clock3 size={15} />
            )}
          </button>
        </div>

        <div className="pp-chat-conversation-list">
          {loadingConversations ? (
            <div className="pp-chat-sidebar-state">
              <LoaderCircle size={17} className="pp-chat-spin" />
              Loading conversations...
            </div>
          ) : conversations.length === 0 ? (
            <div className="pp-chat-sidebar-empty">
              <MessageSquare size={22} />
              <span>No conversations yet</span>
              <small>Your chats will appear here.</small>
            </div>
          ) : (
            conversations.map((conversation) => {
              const id = String(conversation.conversation_id);
              const active = id === String(activeConversationId);
              return (
                <button
                  type="button"
                  key={id}
                  className={`pp-chat-conversation ${active ? "active" : ""}`}
                  onClick={() => handleSelectConversation(id)}
                >
                  <MessageSquare size={16} />
                  <span>{makeConversationTitle(conversation)}</span>
                </button>
              );
            })
          )}
        </div>

        <div className="pp-chat-sidebar-footer">
          <ShieldCheck size={17} />
          <span>Your conversations are private to your account.</span>
        </div>
      </aside>

      <section className="pp-chat-workspace">
        <header className="pp-chat-topbar">
          <div className="pp-chat-topbar-left">
            <button
              type="button"
              className="pp-chat-menu-button"
              aria-label="Open conversations"
              onClick={() => setSidebarOpen(true)}
            >
              <Menu size={20} />
            </button>
            <div>
              <span className="pp-chat-topbar-eyebrow">PROOFPOCKET ASSISTANT</span>
              <h1>AI Document Chat</h1>
              <span className="pp-chat-scope-indicator">
                <FileText size={12} />
                {scopeLabel}
              </span>
            </div>
          </div>
          <button type="button" className="pp-chat-top-new" onClick={startNewChat}>
            <Plus size={16} />
            <span>New chat</span>
          </button>
        </header>

        {pageError && (
          <div className="pp-chat-alert" role="alert">
            <AlertCircle size={17} />
            <span>{pageError}</span>
            <button type="button" onClick={loadConversations}>Retry</button>
          </div>
        )}

        <div className="pp-chat-message-area">
          {loadingHistory ? (
            <div className="pp-chat-loading">
              <LoaderCircle size={27} className="pp-chat-spin" />
              <span>Loading conversation...</span>
            </div>
          ) : messages.length === 0 ? (
            <div className="pp-chat-welcome">
              <div className="pp-chat-welcome-icon"><Sparkles size={27} /></div>
              <span className="pp-chat-welcome-kicker">YOUR DOCUMENTS, UNDERSTOOD</span>
              <h2>What would you like to know?</h2>
              <p>
                Ask questions about your uploaded documents. ProofPocket AI
                searches your document knowledge and helps you find the answers.
              </p>
              {loadingDocuments ? (
                <div className="pp-chat-document-loading">
                  <LoaderCircle size={15} className="pp-chat-spin" />
                  Loading your documents...
                </div>
              ) : processedDocuments.length === 0 ? (
                <div className="pp-chat-no-documents">
                  <FileText size={17} />
                  No processed documents found. Upload and process a document to start chatting.
                </div>
              ) : (
                <div className="pp-chat-suggestions">
                  {suggestedQuestions.map((suggestion) => (
                    <button
                      type="button"
                      key={suggestion}
                      onClick={() => {
                        setQuestion(suggestion);
                        textareaRef.current?.focus();
                      }}
                    >
                      <Sparkles size={14} />
                      {suggestion}
                      <ArrowRight size={14} />
                    </button>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="pp-chat-messages">
              {messages.map((message) => (
                <article
                  key={message.id}
                  className={`pp-chat-message ${message.role}`}
                >
                  <div className="pp-chat-message-avatar">
                    {message.role === "assistant" ? <Sparkles size={17} /> : <span>You</span>}
                  </div>

                  <div className="pp-chat-message-body">
                    <div className="pp-chat-message-meta">
                      <strong>{message.role === "assistant" ? "ProofPocket AI" : "You"}</strong>
                      {message.createdAt && <time>{formatTime(message.createdAt)}</time>}
                    </div>
                    <div className="pp-chat-message-content">{message.content}</div>

                    {message.sources?.length > 0 && (
                      <div className="pp-chat-sources">
                        <div className="pp-chat-sources-heading">
                          <FileText size={15} />
                          Sources used ({message.sources.length})
                        </div>
                        {message.sources.map((source) => {
                          const sourceDocument = documents.find(
                            (item) => String(item.document_id) === String(source.documentId)
                          );
                          const score = formatScore(source.retrievalScore);
                          return (
                            <div className="pp-chat-source" key={source.id}>
                              <div className="pp-chat-source-icon"><FileText size={14} /></div>
                              <div className="pp-chat-source-main">
                                <strong>Source {source.sourceNumber}</strong>
                                <span>
                                  {sourceDocument
                                    ? getDocumentName(sourceDocument)
                                    : `Document ID: ${source.documentId ?? "Unknown"}`}
                                </span>
                                <small>
                                  Chunk ID: {source.chunkId ?? "Unknown"}
                                  {source.chunkIndex != null ? ` · Chunk index: ${source.chunkIndex}` : ""}
                                  {source.sourceType ? ` · ${source.sourceType}` : ""}
                                  {score ? ` · RRF score: ${score}` : ""}
                                </small>
                              </div>
                              {source.rerankRank != null && (
                                <span className="pp-chat-source-rank">Rank {source.rerankRank}</span>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </article>
              ))}

              {sending && (
                <article className="pp-chat-message assistant">
                  <div className="pp-chat-message-avatar"><Sparkles size={17} /></div>
                  <div className="pp-chat-message-body">
                    <div className="pp-chat-message-meta"><strong>ProofPocket AI</strong></div>
                    <div className="pp-chat-thinking">
                      <span /><span /><span />
                      <small>Searching your document context...</small>
                    </div>
                  </div>
                </article>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        <div className="pp-chat-composer-wrap">
          {chatError && (
            <div className="pp-chat-inline-error" role="alert">
              <AlertCircle size={15} />
              <span>{chatError}</span>
              <button type="button" onClick={() => setChatError("")} aria-label="Dismiss error">
                <X size={15} />
              </button>
            </div>
          )}

          {summaryClarification && (
            <div className="pp-chat-clarification">
              <div className="pp-chat-clarification-heading">
                <div className="pp-chat-clarification-icon"><FileText size={17} /></div>
                <div>
                  <strong>Which document should I summarize?</strong>
                  <span>You have more than one processed document. Choose one to keep this conversation focused.</span>
                </div>
                <button
                  type="button"
                  aria-label="Close document selection"
                  onClick={() => setSummaryClarification(false)}
                >
                  <X size={17} />
                </button>
              </div>
              <div className="pp-chat-document-options">
                {processedDocuments.map((document) => (
                  <button
                    type="button"
                    key={document.document_id}
                    onClick={() => handleChooseSummaryDocument(document.document_id)}
                    disabled={sending}
                  >
                    <FileText size={16} />
                    <span>{getDocumentName(document)}</span>
                    <ArrowRight size={15} />
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="pp-chat-document-select">
            <label htmlFor="pp-chat-document">
              <FileText size={15} />
              Document scope
            </label>
            <div className="pp-chat-select-wrap">
              <select
                id="pp-chat-document"
                value={selectedDocumentId}
                onChange={(event) => {
                  setChatError("");
                  setSelectedDocumentId(event.target.value);
                }}
                disabled={
                  sending ||
                  loadingDocuments ||
                  messages.length > 0 ||
                  Boolean(activeConversationId)
                }
              >
                <option value="">All my indexed documents</option>
                {documents.map((document) => (
                  <option
                    key={document.document_id}
                    value={document.document_id}
                    disabled={!isProcessed(document)}
                  >
                    {getDocumentName(document)}
                    {!isProcessed(document) ? " (not processed)" : ""}
                  </option>
                ))}
              </select>
              <ChevronDown size={15} />
            </div>
            {selectedDocument && (
              <span className="pp-chat-selected-hint">
                <Check size={12} />
                This conversation is limited to the selected document.
              </span>
            )}
            {!selectedDocumentId && (
              <span className="pp-chat-selected-hint">
                Search scope includes all your processed documents.
              </span>
            )}
          </div>

          <form className="pp-chat-composer" onSubmit={handleSend}>
            <textarea
              ref={textareaRef}
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={handleComposerKeyDown}
              placeholder="Ask anything about your documents..."
              rows={1}
              maxLength={2000}
              disabled={sending || loadingHistory}
            />
            <div className="pp-chat-composer-bottom">
              <span>
                <ShieldCheck size={13} />
                Answers use your available document context.
                <span className="pp-chat-char-count">{question.length}/2000</span>
              </span>
              <button
                type="submit"
                disabled={!question.trim() || sending || loadingHistory}
                aria-label="Send message"
              >
                {sending ? <LoaderCircle size={17} className="pp-chat-spin" /> : <Send size={17} />}
              </button>
            </div>
          </form>
          <p className="pp-chat-disclaimer">
            AI can make mistakes. Verify important details against your original documents.
          </p>
        </div>
      </section>
    </div>
  );
}
