CREATE DATABASE IF NOT EXISTS SPM;
USE SPM;

CREATE TABLE IF NOT EXISTS tasks (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  task_details  TEXT,
  deadline DATETIME, 
  notes TEXT,
  ################## collaborators 
  
  creator_id INT NOT NULL,
  assigned_to_id INT NULL,

  status ENUM('Unassigned', 'Ongoing', 'Under Review', 'Completed') NOT NULL DEFAULT 'Unassigned',
  
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);