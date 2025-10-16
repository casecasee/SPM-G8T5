USE SPM;

-- Notifications table
CREATE TABLE notifications (
    notification_id VARCHAR(36) PRIMARY KEY,
    staff_id VARCHAR(36) NOT NULL,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT,
    related_task_id VARCHAR(36),
    related_project_id VARCHAR(36),
    related_comment_id VARCHAR(36),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP NULL,
    INDEX idx_staff_created (staff_id, created_at),
    INDEX idx_staff_read (staff_id, is_read),
    FOREIGN KEY (staff_id) REFERENCES staff(employee_id) ON DELETE CASCADE
);

-- Notification preferences
CREATE TABLE notification_preferences (
    staff_id VARCHAR(36) PRIMARY KEY,
    deadline_reminders BOOLEAN DEFAULT TRUE,
    task_status_updates BOOLEAN DEFAULT TRUE,
    due_date_changes BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (staff_id) REFERENCES staff(employee_id) ON DELETE CASCADE
);

-- Deadline notification log (prevents duplicates)
CREATE TABLE deadline_notification_log (
    log_id VARCHAR(36) PRIMARY KEY,
    task_id VARCHAR(36) NOT NULL,
    staff_id VARCHAR(36) NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_deadline_notification (task_id, staff_id, notification_type),
    INDEX idx_task (task_id),
    FOREIGN KEY (staff_id) REFERENCES staff(employee_id) ON DELETE CASCADE
);