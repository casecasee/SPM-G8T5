CREATE DATABASE IF NOT EXISTS SPM;
USE SPM;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS Task_Collaborators;
DROP TABLE IF EXISTS Task;

-- Create the Task table to match the model
CREATE TABLE Task (
    task_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    attachment VARCHAR(512) NULL,
    start_date DATETIME NULL,
    deadline DATETIME NULL,
    completed_date DATETIME NULL,
    status VARCHAR(32) NOT NULL,
    owner INT NOT NULL,
    project_id INT NULL,
    parent_id INT NULL,
    INDEX idx_task_deadline (deadline),
    INDEX idx_task_owner (owner),
    INDEX idx_task_project_id (project_id),
    CONSTRAINT fk_task_owner FOREIGN KEY (owner) REFERENCES staff(employee_id) ON DELETE RESTRICT,
    CONSTRAINT fk_task_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL,
    CONSTRAINT fk_task_parent FOREIGN KEY (parent_id) REFERENCES Task(task_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Create the Task_Collaborators junction table
CREATE TABLE Task_Collaborators (
    task_id INT NOT NULL,
    staff_id INT NOT NULL,
    PRIMARY KEY (task_id, staff_id),
    CONSTRAINT fk_tc_task FOREIGN KEY (task_id) REFERENCES Task(task_id) ON DELETE CASCADE,
    CONSTRAINT fk_tc_staff FOREIGN KEY (staff_id) REFERENCES staff(employee_id) ON DELETE CASCADE
) ENGINE=InnoDB;