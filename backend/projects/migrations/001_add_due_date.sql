-- Add project due date column if missing (MySQL-compatible)
SET @col := (SELECT COUNT(*) FROM information_schema.COLUMNS
             WHERE TABLE_SCHEMA = DATABASE()
               AND TABLE_NAME = 'projects'
               AND COLUMN_NAME = 'due_date');
SET @sql := IF(@col = 0,
  'ALTER TABLE projects ADD COLUMN due_date DATETIME NULL;',
  'SELECT 1;'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

