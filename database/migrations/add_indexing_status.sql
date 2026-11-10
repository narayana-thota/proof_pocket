ALTER TABLE documents
ADD COLUMN indexing_status
ENUM('pending', 'processing', 'completed', 'failed')
NOT NULL DEFAULT 'pending'
AFTER processing_status;