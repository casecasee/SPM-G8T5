-- backend/database/schema.sql
CREATE DATABASE IF NOT EXISTS SPM;
USE SPM;

-- Drop existing tables (clean slate)
SET FOREIGN_KEY_CHECKS=0;
DROP TABLE IF EXISTS comment_attachments;
DROP TABLE IF EXISTS comment_mentions;
DROP TABLE IF EXISTS task_comments;
DROP TABLE IF EXISTS task_collaborators;
DROP TABLE IF EXISTS project_members;
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS task;
DROP TABLE IF EXISTS staff;
SET FOREIGN_KEY_CHECKS=1;

-- Create staff table (EXACT match to your current)
CREATE TABLE staff (
  employee_id INT PRIMARY KEY AUTO_INCREMENT,
  employee_name VARCHAR(100) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  department VARCHAR(100) NOT NULL,
  role VARCHAR(50) NOT NULL,
  password VARCHAR(255) NOT NULL,
  team VARCHAR(100) NOT NULL
) ENGINE=InnoDB;

-- Create projects table (FIXED: added proper defaults)
CREATE TABLE projects (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  owner VARCHAR(255) DEFAULT NULL,
  owner_id INT DEFAULT NULL,
  status VARCHAR(50) NOT NULL,
  tasks_done INT NOT NULL,
  tasks_total INT NOT NULL,
  due_date DATETIME DEFAULT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX ix_projects_owner_id (owner_id)
) ENGINE=InnoDB;

-- Create task table (EXACT match to your current - lowercase 'task')
CREATE TABLE task (
  task_id INT PRIMARY KEY AUTO_INCREMENT,
  title VARCHAR(255) NOT NULL,
  description TEXT NOT NULL,
  attachment VARCHAR(512) DEFAULT NULL,
  priority INT DEFAULT NULL,
  recurrence INT DEFAULT NULL,
  start_date DATETIME DEFAULT NULL,
  deadline DATETIME DEFAULT NULL,
  completed_date DATETIME DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status VARCHAR(32) NOT NULL,
  owner INT NOT NULL,
  project_id INT DEFAULT NULL,
  parent_id INT DEFAULT NULL,
  INDEX parent_id (parent_id),
  INDEX ix_Task_owner (owner),
  INDEX ix_Task_project_id (project_id),
  INDEX ix_Task_deadline (deadline)
) ENGINE=InnoDB;

-- Create project_members table (EXACT match)
CREATE TABLE project_members (
  project_id INT NOT NULL,
  staff_id INT NOT NULL,
  PRIMARY KEY (project_id, staff_id),
  KEY staff_id (staff_id)
) ENGINE=InnoDB;

-- Create task_collaborators table (EXACT match)
CREATE TABLE task_collaborators (
  task_id INT NOT NULL,
  staff_id INT NOT NULL,
  PRIMARY KEY (task_id, staff_id),
  KEY staff_id (staff_id)
) ENGINE=InnoDB;

-- Create task_comments table (EXACT match)
CREATE TABLE task_comments (
  id INT PRIMARY KEY AUTO_INCREMENT,
  task_id INT NOT NULL,
  author_id INT NOT NULL,
  content TEXT NOT NULL,
  created_at DATETIME NOT NULL,
  updated_at DATETIME DEFAULT NULL,
  INDEX ix_task_comments_created_at (created_at),
  INDEX ix_task_comments_task_id (task_id),
  INDEX ix_task_comments_author_id (author_id)
) ENGINE=InnoDB;

-- Create comment_mentions table (EXACT match)
CREATE TABLE comment_mentions (
  id INT PRIMARY KEY AUTO_INCREMENT,
  comment_id INT NOT NULL,
  mentioned_id INT NOT NULL,
  INDEX ix_comment_mentions_mentioned_id (mentioned_id),
  INDEX ix_comment_mentions_comment_id (comment_id)
) ENGINE=InnoDB;

-- Create comment_attachments table (EXACT match)
CREATE TABLE comment_attachments (
  id INT PRIMARY KEY AUTO_INCREMENT,
  comment_id INT NOT NULL,
  filename VARCHAR(255) NOT NULL,
  original_name VARCHAR(255) DEFAULT NULL,
  mime_type VARCHAR(100) DEFAULT NULL,
  size INT DEFAULT NULL,
  uploaded_at DATETIME NOT NULL,
  INDEX ix_comment_attachments_comment_id (comment_id)
) ENGINE=InnoDB;
