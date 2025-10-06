USE SPM;

-- Drop project tables to start clean
SET FOREIGN_KEY_CHECKS=0;
DROP TABLE IF EXISTS project_members;
DROP TABLE IF EXISTS projects;
SET FOREIGN_KEY_CHECKS=1;

-- Recreate tables (must exist before inserts)
CREATE TABLE projects (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  owner VARCHAR(255),
  owner_id INT NULL,
  status VARCHAR(50) NOT NULL DEFAULT 'Active',
  tasks_done INT NOT NULL DEFAULT 0,
  tasks_total INT NOT NULL DEFAULT 0,
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

-- Sample projects (ensure owner_id exists in staff table)
INSERT INTO projects (name, owner, owner_id, status, tasks_done, tasks_total)
VALUES
  ('Website Redesign', 'test', 1, 'Active', 0, 0),
  ('Marketing Launch', 'test2', 2, 'On hold', 0, 0),
  ('Data Migration', 'James Connor', 47, 'Active', 0, 0);

-- Sample members (ensure these staff IDs exist)
INSERT INTO project_members (project_id, staff_id)
VALUES
  ((SELECT id FROM projects WHERE name='Website Redesign' LIMIT 1), 1),
  ((SELECT id FROM projects WHERE name='Website Redesign' LIMIT 1), 2),
  ((SELECT id FROM projects WHERE name='Marketing Launch' LIMIT 1), 34),
  ((SELECT id FROM projects WHERE name='Data Migration' LIMIT 1), 47);


