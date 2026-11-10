CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS document_categories (
    category_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS documents (
    document_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    category_id INT UNSIGNED NULL,

    document_name VARCHAR(255) NOT NULL,
    document_type VARCHAR(100) NULL,
    original_file_name VARCHAR(255) NOT NULL,
    file_extension VARCHAR(20) NOT NULL,
    mime_type VARCHAR(100),
    file_size_bytes BIGINT UNSIGNED NOT NULL,

    storage_provider VARCHAR(50) NOT NULL DEFAULT 'backblaze_b2',
    bucket_name VARCHAR(100) NOT NULL,
    object_key VARCHAR(500) NOT NULL,

    upload_status ENUM('pending', 'completed', 'failed')
        NOT NULL DEFAULT 'pending',

    processing_status ENUM('pending', 'processing', 'completed', 'failed')
        NOT NULL DEFAULT 'pending',

    indexing_status ENUM('pending', 'processing', 'completed', 'failed')
        NOT NULL DEFAULT 'pending',

    classification_status ENUM('pending', 'completed', 'failed', 'needs_review')
        NOT NULL DEFAULT 'pending',

    classification_confidence DECIMAL(5,4) NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_documents_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_documents_category
        FOREIGN KEY (category_id)
        REFERENCES document_categories(category_id)
        ON DELETE SET NULL,

    CONSTRAINT uq_bucket_object
        UNIQUE (bucket_name, object_key),

    CONSTRAINT chk_classification_confidence
        CHECK (
            classification_confidence IS NULL
            OR classification_confidence BETWEEN 0 AND 1
        ),

    INDEX idx_documents_user (user_id),
    INDEX idx_documents_category (category_id),
    INDEX idx_documents_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS extracted_data (
    extraction_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    document_id BIGINT UNSIGNED NOT NULL UNIQUE,

    extracted_text LONGTEXT,
    structured_data JSON,

    extraction_status ENUM('pending', 'processing', 'completed', 'failed')
        NOT NULL DEFAULT 'pending',

    error_message TEXT,
    extracted_at DATETIME NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_extracted_document
        FOREIGN KEY (document_id)
        REFERENCES documents(document_id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS reminders (
    reminder_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    document_id BIGINT UNSIGNED NOT NULL,

    reminder_title VARCHAR(255) NOT NULL,
    reminder_type ENUM('warranty', 'expiry', 'renewal', 'custom')
        NOT NULL DEFAULT 'custom',

    due_date DATE NOT NULL,
    notify_at DATETIME NOT NULL,

    status ENUM('pending', 'sent', 'completed', 'cancelled')
        NOT NULL DEFAULT 'pending',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_reminder_document
        FOREIGN KEY (document_id)
        REFERENCES documents(document_id)
        ON DELETE CASCADE,

    INDEX idx_reminders_document (document_id),
    INDEX idx_reminders_schedule (status, notify_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- =========================================
-- AI-GENERATED REMINDER SUGGESTIONS
-- Suggestions remain separate from actual reminders until approved.
-- =========================================

CREATE TABLE IF NOT EXISTS reminder_suggestions (
    suggestion_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    user_id BIGINT UNSIGNED NOT NULL,
    document_id BIGINT UNSIGNED NOT NULL,

    reminder_title VARCHAR(255) NOT NULL,
    reminder_type ENUM('warranty', 'expiry', 'renewal', 'custom')
        NOT NULL DEFAULT 'custom',

    due_date DATE NOT NULL,
    notify_at DATETIME NOT NULL,

    -- Supporting excerpt from the extracted document text.
    evidence VARCHAR(2000) NOT NULL,

    -- AI confidence is stored as a value from 0.0000 to 1.0000.
    confidence DECIMAL(5,4) NOT NULL DEFAULT 0.5000,

    status ENUM('pending', 'approved', 'rejected')
        NOT NULL DEFAULT 'pending',

    -- Populated when the user approves the suggestion.
    reminder_id BIGINT UNSIGNED NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_reminder_suggestions_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_reminder_suggestions_document
        FOREIGN KEY (document_id)
        REFERENCES documents(document_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_reminder_suggestions_reminder
        FOREIGN KEY (reminder_id)
        REFERENCES reminders(reminder_id)
        ON DELETE SET NULL,

    CONSTRAINT chk_reminder_suggestion_confidence
        CHECK (confidence BETWEEN 0 AND 1),

    INDEX idx_reminder_suggestions_user_status
        (user_id, status),

    INDEX idx_reminder_suggestions_document_status
        (document_id, status),

    INDEX idx_reminder_suggestions_created
        (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS chat_history (
    chat_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    conversation_id CHAR(36) NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    document_id BIGINT UNSIGNED NULL,

    message_role ENUM('user', 'assistant') NOT NULL,
    message_content LONGTEXT NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_chat_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_chat_document
        FOREIGN KEY (document_id)
        REFERENCES documents(document_id)
        ON DELETE SET NULL,

    INDEX idx_chat_conversation (conversation_id),
    INDEX idx_chat_user (user_id),
    INDEX idx_chat_document (document_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- =========================================
-- USER SESSIONS TABLE
-- =========================================

CREATE TABLE IF NOT EXISTS user_sessions (
    session_id CHAR(36) PRIMARY KEY,

    user_id BIGINT UNSIGNED NOT NULL,

    expires_at DATETIME NOT NULL,

    revoked_at DATETIME NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_sessions_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    INDEX idx_sessions_user (user_id),

    INDEX idx_sessions_expiry (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
