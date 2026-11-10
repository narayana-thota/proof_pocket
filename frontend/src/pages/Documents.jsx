
import { useEffect, useMemo, useRef, useState } from "react";
import {
  UploadCloud,
  FileText,
  FileSpreadsheet,
  FileImage,
  File,
  Download,
  Trash2,
  Search,
  RefreshCw,
  CheckCircle2,
  Clock3,
  AlertCircle,
  X,
  LoaderCircle,
  Sparkles,
} from "lucide-react";

import api from "../services/api";
import "./Documents.css";

const MAX_FILE_SIZE = 10 * 1024 * 1024;

const EXTRACTION_ENDPOINTS = {
  ".pdf": "extract",
  ".docx": "extract-docx",
  ".xlsx": "extract-excel",
  ".txt": "extract-txt",
};

function formatSize(bytes = 0) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function formatDate(date) {
  if (!date) return "Date unavailable";

  const parsed = new Date(date);

  if (Number.isNaN(parsed.getTime())) {
    return "Date unavailable";
  }

  return parsed.toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function getExtension(document) {
  return (
    document.file_extension ||
    document.original_file_name?.slice(
      document.original_file_name.lastIndexOf(".")
    ) ||
    ""
  ).toLowerCase();
}

function getFileIcon(document) {
  const extension = getExtension(document);

  if (extension === ".xlsx") return FileSpreadsheet;

  if ([".jpg", ".jpeg", ".png"].includes(extension)) {
    return FileImage;
  }

  if ([".pdf", ".docx", ".txt"].includes(extension)) {
    return FileText;
  }

  return File;
}

function getProcessingLabel(status) {
  const normalized = (status || "pending").toLowerCase();

  if (normalized === "completed") return "Processed";
  if (normalized === "processing") return "Processing";
  if (normalized === "failed") return "Failed";

  return "Pending";
}

function getErrorMessage(error, fallback) {
  return (
    error?.response?.data?.detail ||
    error?.message ||
    fallback
  );
}

export default function Documents() {
  const fileInputRef = useRef(null);

  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [processingId, setProcessingId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  const [selectedFile, setSelectedFile] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [notice, setNotice] = useState(null);

  const [uploadCategory, setUploadCategory] = useState("");
  const [documentType, setDocumentType] = useState("");

  // Load documents from the backend
  const loadDocuments = async () => {
    try {
      setLoading(true);

      const response = await api.get("/api/documents/");

      setDocuments(
        Array.isArray(response.data.documents)
          ? response.data.documents
          : []
      );
    } catch (error) {
      setNotice({
        type: "error",
        message: getErrorMessage(
          error,
          "Unable to load your documents."
        ),
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  // Search documents
  const filteredDocuments = useMemo(() => {
    const query = searchTerm.trim().toLowerCase();

    if (!query) return documents;

    return documents.filter((document) => {
      const name =
        document.original_file_name ||
        document.document_name ||
        "";

      const category = document.category_name || "";
      const type = document.document_type || "";

      return (
        name.toLowerCase().includes(query) ||
        category.toLowerCase().includes(query) ||
        type.toLowerCase().includes(query)
      );
    });
  }, [documents, searchTerm]);

  const processedCount = documents.filter(
    (document) =>
      document.processing_status === "completed"
  ).length;

  const pendingCount = documents.filter((document) =>
    ["pending", "processing"].includes(
      (document.processing_status || "pending").toLowerCase()
    )
  ).length;

  // Validate selected file
  const handleFileSelection = (event) => {
    const file = event.target.files?.[0];

    if (!file) return;

    const extension = file.name
      .slice(file.name.lastIndexOf("."))
      .toLowerCase();

    const allowedExtensions = [
      ".pdf",
      ".docx",
      ".xlsx",
      ".txt",
      ".jpg",
      ".jpeg",
      ".png",
    ];

    if (!allowedExtensions.includes(extension)) {
      setNotice({
        type: "error",
        message:
          "Unsupported file. Choose PDF, DOCX, XLSX, TXT, JPG or PNG.",
      });

      event.target.value = "";
      return;
    }

    if (file.size === 0) {
      setNotice({
        type: "error",
        message: "Empty files cannot be uploaded.",
      });

      event.target.value = "";
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setNotice({
        type: "error",
        message: "Maximum file size is 10 MB.",
      });

      event.target.value = "";
      return;
    }

    setSelectedFile(file);
    setNotice(null);
  };

  // Upload document and automatically extract supported formats
  const handleUpload = async (event) => {
    event.preventDefault();

    if (!selectedFile) {
      setNotice({
        type: "error",
        message: "Please select a document first.",
      });
      return;
    }

    const extension = selectedFile.name
      .slice(selectedFile.name.lastIndexOf("."))
      .toLowerCase();

    try {
      setUploading(true);
      setNotice(null);

      const formData = new FormData();

      formData.append("file", selectedFile);

      if (uploadCategory.trim()) {
        formData.append(
          "category_id",
          uploadCategory.trim()
        );
      }

      if (documentType.trim()) {
        formData.append(
          "document_type",
          documentType.trim()
        );
      }

      const response = await api.post(
        "/api/documents/upload",
        formData
      );

      const documentId = response.data.document_id;

      setSelectedFile(null);
      setUploadCategory("");
      setDocumentType("");

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      setNotice({
        type: "success",
        message: "Document uploaded successfully.",
      });

      await loadDocuments();

      // Start extraction and indexing for supported formats
      const extractionEndpoint =
        EXTRACTION_ENDPOINTS[extension];

      if (documentId && extractionEndpoint) {
        setProcessingId(documentId);

        try {
          await api.post(
            `/api/documents/${documentId}/${extractionEndpoint}`
          );

          setNotice({
            type: "success",
            message:
              "Document uploaded, extracted and indexed successfully.",
          });
        } catch (error) {
          setNotice({
            type: "error",
            message:
              "Document uploaded, but extraction failed: " +
              getErrorMessage(
                error,
                "Please retry extraction."
              ),
          });
        } finally {
          setProcessingId(null);
          await loadDocuments();
        }
      } else {
        setNotice({
          type: "success",
          message:
            "Image uploaded successfully. Text extraction for images is not available in V1.",
        });
      }
    } catch (error) {
      setNotice({
        type: "error",
        message: getErrorMessage(
          error,
          "Document upload failed."
        ),
      });
    } finally {
      setUploading(false);
    }
  };

  // Manually retry extraction
  const handleExtract = async (document) => {
    const extension = getExtension(document);

    const endpoint = EXTRACTION_ENDPOINTS[extension];

    if (!endpoint) {
      setNotice({
        type: "error",
        message:
          "Extraction is not supported for this file type.",
      });
      return;
    }

    try {
      setProcessingId(document.document_id);
      setNotice(null);

      await api.post(
        `/api/documents/${document.document_id}/${endpoint}`
      );

      setNotice({
        type: "success",
        message:
          "Document extracted and indexed successfully.",
      });

      await loadDocuments();
    } catch (error) {
      setNotice({
        type: "error",
        message: getErrorMessage(
          error,
          "Document extraction failed."
        ),
      });

      await loadDocuments();
    } finally {
      setProcessingId(null);
    }
  };

  // Generate download URL and open original document
  const handleDownload = async (document) => {
    try {
      const response = await api.get(
        `/api/documents/${document.document_id}/download`
      );

      const downloadUrl =
        response.data?.document?.download_url;

      if (!downloadUrl) {
        throw new Error(
          "Download URL was not returned by the server."
        );
      }

      window.open(
        downloadUrl,
        "_blank",
        "noopener,noreferrer"
      );
    } catch (error) {
      setNotice({
        type: "error",
        message: getErrorMessage(
          error,
          "Unable to download this document."
        ),
      });
    }
  };

  // Delete document
  const handleDelete = async (document) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${document.original_file_name}"? This will also remove associated AI indexing and related records.`
    );

    if (!confirmed) return;

    try {
      setDeletingId(document.document_id);
      setNotice(null);

      const response = await api.delete(
        `/api/documents/${document.document_id}`
      );

      setDocuments((previous) =>
        previous.filter(
          (item) =>
            item.document_id !== document.document_id
        )
      );

      setNotice({
        type: "success",
        message:
          response.data?.message ||
          "Document deleted successfully.",
      });
    } catch (error) {
      setNotice({
        type: "error",
        message: getErrorMessage(
          error,
          "Unable to delete document."
        ),
      });
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="documents-page">

      {/* Page heading */}
      <div className="documents-heading">
        <div>
          <span className="documents-eyebrow">
            YOUR PERSONAL LIBRARY
          </span>

          <h1>My Documents</h1>

          <p>
            Store, organize and access your important documents.
          </p>
        </div>

        <button
          className="documents-refresh"
          onClick={loadDocuments}
          disabled={loading}
          type="button"
        >
          <RefreshCw
            size={17}
            className={loading ? "spin" : ""}
          />
          Refresh
        </button>
      </div>

      {/* Notification */}
      {notice && (
        <div
          className={`documents-notice ${notice.type}`}
          role="status"
        >
          {notice.type === "success" ? (
            <CheckCircle2 size={18} />
          ) : (
            <AlertCircle size={18} />
          )}

          <span>{notice.message}</span>

          <button
            type="button"
            onClick={() => setNotice(null)}
            aria-label="Dismiss notification"
          >
            <X size={17} />
          </button>
        </div>
      )}

      {/* Statistics */}
      <div className="documents-stats">

        <div className="document-stat-card">
          <div className="document-stat-icon purple">
            <FileText size={21} />
          </div>

          <div>
            <span>Total documents</span>
            <strong>{documents.length}</strong>
          </div>
        </div>

        <div className="document-stat-card">
          <div className="document-stat-icon green">
            <CheckCircle2 size={21} />
          </div>

          <div>
            <span>Processed</span>
            <strong>{processedCount}</strong>
          </div>
        </div>

        <div className="document-stat-card">
          <div className="document-stat-icon orange">
            <Clock3 size={21} />
          </div>

          <div>
            <span>Pending / Processing</span>
            <strong>{pendingCount}</strong>
          </div>
        </div>

      </div>

      {/* Upload section */}
      <section className="document-upload-card">

        <div className="document-section-heading">
          <div>
            <h2>Upload a document</h2>
            <p>
              Add a document to your secure personal library.
            </p>
          </div>

          <div className="upload-heading-icon">
            <UploadCloud size={21} />
          </div>
        </div>

        <form onSubmit={handleUpload}>

          <label className="document-dropzone">

            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.xlsx,.txt,.jpg,.jpeg,.png"
              onChange={handleFileSelection}
              disabled={uploading}
            />

            <div className="upload-cloud-icon">
              <UploadCloud size={29} />
            </div>

            {selectedFile ? (
              <>
                <strong>{selectedFile.name}</strong>
                <span>
                  {formatSize(selectedFile.size)} · Selected
                </span>
              </>
            ) : (
              <>
                <strong>
                  Click to browse your files
                </strong>

                <span>
                  PDF, DOCX, XLSX, TXT, JPG and PNG · Maximum 10 MB
                </span>
              </>
            )}

          </label>

          <div className="document-upload-options">

            <div className="document-field">
              <label htmlFor="upload-category">
                Category ID (optional)
              </label>

              <input
                id="upload-category"
                type="number"
                min="1"
                placeholder="Enter category ID"
                value={uploadCategory}
                onChange={(event) =>
                  setUploadCategory(event.target.value)
                }
              />
            </div>

            <div className="document-field">
              <label htmlFor="upload-type">
                Document type (optional)
              </label>

              <input
                id="upload-type"
                type="text"
                placeholder="e.g. Warranty, Invoice"
                value={documentType}
                onChange={(event) =>
                  setDocumentType(event.target.value)
                }
              />
            </div>

          </div>

          <div className="document-upload-footer">

            <span>
              <CheckCircle2 size={15} />
              Secure storage powered by Backblaze B2
            </span>

            <button
              className="document-upload-button"
              type="submit"
              disabled={!selectedFile || uploading}
            >
              {uploading ? (
                <>
                  <LoaderCircle
                    className="spin"
                    size={17}
                  />
                  Uploading...
                </>
              ) : (
                <>
                  <UploadCloud size={17} />
                  Upload document
                </>
              )}
            </button>

          </div>
        </form>
      </section>

      {/* Document library */}
      <section className="document-library">

        <div className="document-library-heading">
          <div>
            <h2>All documents</h2>
            <p>
              {documents.length} documents in your library
            </p>
          </div>

          <div className="document-search">
            <Search size={18} />

            <input
              type="search"
              placeholder="Search documents..."
              value={searchTerm}
              onChange={(event) =>
                setSearchTerm(event.target.value)
              }
            />
          </div>
        </div>

        {loading ? (
          <div className="documents-state">
            <LoaderCircle size={28} className="spin" />
            <p>Loading your documents...</p>
          </div>
        ) : filteredDocuments.length === 0 ? (
          <div className="documents-state">

            <div className="empty-documents-icon">
              <FileText size={30} />
            </div>

            <h3>
              {searchTerm
                ? "No matching documents"
                : "No documents yet"}
            </h3>

            <p>
              {searchTerm
                ? "Try a different search term."
                : "Upload your first document to get started with ProofPocket."}
            </p>

          </div>
        ) : (

          <>
            {/* Desktop table */}
            <div className="document-table-wrap">
              <table className="document-table">

                <thead>
                  <tr>
                    <th>Document</th>
                    <th>Category</th>
                    <th>Size</th>
                    <th>Uploaded</th>
                    <th>AI status</th>
                    <th>Actions</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredDocuments.map((document) => {
                    const Icon = getFileIcon(document);

                    const status = getProcessingLabel(
                      document.processing_status
                    );

                    const extension = getExtension(document);

                    const canExtract = Boolean(
                      EXTRACTION_ENDPOINTS[extension]
                    );

                    return (
                      <tr key={document.document_id}>

                        <td>
                          <div className="document-name-cell">

                            <div className="document-file-icon">
                              <Icon size={20} />
                            </div>

                            <div>
                              <strong>
                                {document.original_file_name ||
                                  document.document_name}
                              </strong>

                              <span>
                                {extension
                                  .replace(".", "")
                                  .toUpperCase()}
                              </span>
                            </div>

                          </div>
                        </td>

                        <td>
                          {document.category_name ||
                            "Uncategorized"}
                        </td>

                        <td>
                          {formatSize(document.file_size_bytes)}
                        </td>

                        <td>
                          {formatDate(document.created_at)}
                        </td>

                        <td>
                          <span
                            className={`document-status ${status.toLowerCase()}`}
                          >
                            {status === "Processed" ? (
                              <CheckCircle2 size={14} />
                            ) : status === "Failed" ? (
                              <AlertCircle size={14} />
                            ) : (
                              <Clock3 size={14} />
                            )}

                            {status}
                          </span>
                        </td>

                        <td>
                          <div className="document-actions">

                            <button
                              type="button"
                              title="Download document"
                              aria-label="Download document"
                              onClick={() =>
                                handleDownload(document)
                              }
                            >
                              <Download size={17} />
                            </button>

                            {canExtract &&
                              document.processing_status !==
                                "completed" && (
                                <button
                                  type="button"
                                  title="Extract and index"
                                  aria-label="Extract and index document"
                                  disabled={
                                    processingId ===
                                    document.document_id
                                  }
                                  onClick={() =>
                                    handleExtract(document)
                                  }
                                >
                                  {processingId ===
                                  document.document_id ? (
                                    <LoaderCircle
                                      size={17}
                                      className="spin"
                                    />
                                  ) : (
                                    <Sparkles size={17} />
                                  )}
                                </button>
                              )}

                            <button
                              type="button"
                              className="delete-document-button"
                              title="Delete document"
                              aria-label="Delete document"
                              disabled={
                                deletingId === document.document_id
                              }
                              onClick={() =>
                                handleDelete(document)
                              }
                            >
                              {deletingId ===
                              document.document_id ? (
                                <LoaderCircle
                                  size={17}
                                  className="spin"
                                />
                              ) : (
                                <Trash2 size={17} />
                              )}
                            </button>

                          </div>
                        </td>

                      </tr>
                    );
                  })}
                </tbody>

              </table>
            </div>

            {/* Responsive mobile cards */}
            <div className="document-mobile-list">

              {filteredDocuments.map((document) => {
                const Icon = getFileIcon(document);

                const status = getProcessingLabel(
                  document.processing_status
                );

                const extension = getExtension(document);

                const canExtract = Boolean(
                  EXTRACTION_ENDPOINTS[extension]
                );

                return (
                  <article
                    className="document-mobile-card"
                    key={document.document_id}
                  >

                    <div className="document-mobile-top">

                      <div className="document-name-cell">
                        <div className="document-file-icon">
                          <Icon size={20} />
                        </div>

                        <div>
                          <strong>
                            {document.original_file_name ||
                              document.document_name}
                          </strong>

                          <span>
                            {formatSize(document.file_size_bytes)}
                            {" · "}
                            {formatDate(document.created_at)}
                          </span>
                        </div>
                      </div>

                      <span
                        className={`document-status ${status.toLowerCase()}`}
                      >
                        {status}
                      </span>

                    </div>

                    <div className="document-mobile-meta">
                      {document.category_name ||
                        "Uncategorized"}
                    </div>

                    <div className="document-mobile-actions">

                      <button
                        type="button"
                        onClick={() =>
                          handleDownload(document)
                        }
                      >
                        <Download size={16} />
                        Download
                      </button>

                      {canExtract &&
                        document.processing_status !==
                          "completed" && (
                          <button
                            type="button"
                            disabled={
                              processingId ===
                              document.document_id
                            }
                            onClick={() =>
                              handleExtract(document)
                            }
                          >
                            <Sparkles size={16} />
                            Extract
                          </button>
                        )}

                      <button
                        type="button"
                        className="mobile-delete-action"
                        disabled={
                          deletingId === document.document_id
                        }
                        onClick={() =>
                          handleDelete(document)
                        }
                      >
                        <Trash2 size={16} />
                        Delete
                      </button>

                    </div>
                  </article>
                );
              })}

            </div>
          </>
        )}

      </section>
    </div>
  );
}
