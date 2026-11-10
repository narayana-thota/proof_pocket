
from app.database.connection import get_db_connection


def create_reminder_suggestions_table():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
        CREATE TABLE IF NOT EXISTS reminder_suggestions (
            suggestion_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT UNSIGNED NOT NULL,
            document_id BIGINT UNSIGNED NOT NULL,
            reminder_title VARCHAR(255) NOT NULL,
            reminder_type ENUM(
                'warranty', 'expiry', 'renewal', 'custom'
            ) NOT NULL DEFAULT 'custom',
            due_date DATE NOT NULL,
            notify_at DATETIME NOT NULL,
            evidence TEXT NOT NULL,
            confidence DECIMAL(4,3) NOT NULL DEFAULT 0.500,
            status ENUM(
                'pending', 'approved', 'rejected'
            ) NOT NULL DEFAULT 'pending',
            reminder_id BIGINT UNSIGNED NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

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

            INDEX idx_reminder_suggestions_user_status
                (user_id, status),

            INDEX idx_reminder_suggestions_document
                (document_id),

            INDEX idx_reminder_suggestions_due_date
                (due_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """

        cursor.execute(query)
        connection.commit()

        print("Reminder suggestions table created successfully!")

        cursor.execute(
            "SHOW TABLES LIKE 'reminder_suggestions'"
        )

        if cursor.fetchone():
            print("Verification successful: table exists.")

    except Exception as error:
        if connection:
            connection.rollback()

        print("Migration failed:", error)

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()


if __name__ == "__main__":
    create_reminder_suggestions_table()
