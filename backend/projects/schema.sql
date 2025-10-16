CREATE DATABASE IF NOT EXISTS SPM;
USE SPM;

DROP TABLE IF EXISTS project_members;
DROP TABLE IF EXISTS projects;

CREATE TABLE projects (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  owner VARCHAR(255),
  owner_id INT NULL,
  status VARCHAR(50) NOT NULL DEFAULT 'Active',
  tasks_done INT NOT NULL DEFAULT 0,
  tasks_total INT NOT NULL DEFAULT 0,
  due_date DATETIME NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX ix_projects_owner_id (owner_id),
  CONSTRAINT fk_projects_owner FOREIGN KEY (owner_id) REFERENCES staff(employee_id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE project_members (
  project_id INT NOT NULL,
  staff_id INT NOT NULL,
  PRIMARY KEY (project_id, staff_id),
  CONSTRAINT fk_pm_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
  CONSTRAINT fk_pm_staff   FOREIGN KEY (staff_id)   REFERENCES staff(employee_id) ON DELETE CASCADE
) ENGINE=InnoDB;