-- backend/database/seeds/development.sql
USE SPM;

-- Insert staff data (EXACT match to your current data)
INSERT INTO staff (employee_id, employee_name, email, department, role, password, team) VALUES
(1, 'test', 'test1@gmail.com', 'Finance', 'manager', 'scrypt:32768:8:1$mtuy3ILZYT5Oo2xw$2eb0e684d977c87f6717f71a0bbf9d80eab1570be2beb2d0e647f47dd9895c0723fd6fa17d82b412f847d9c324e3ffea2a00455aef9191268bc2710b32397111', 'A'),
(2, 'test2', 'test2@gmail.com', 'Finance', 'staff', 'scrypt:32768:8:1$a0gACjpOas4zdj45$94d98382350366cc4e12c3dafb33bc3b89534c5cae74025274386bb44f9bd51ab9db0bfeaeb4e38fa05e2b204d64523a539afe648290d9713e456157041afca6', 'A'),
(33, 'Isabella Rossi', 'isabella.rossi@company.com', 'Admin', 'staff', 'scrypt:32768:8:1$0fyuoPHe63RwHGBS$273d6b6b33578e08a13b1205727ab67b90f3cab32cf7a2675514fc5009ef15c442781b4e0a8154218458b61c05cc6d6be28185ceff5c5baf4470b7f0e819b253', 'F'),
(34, 'Natalie Foster', 'natalie.foster@company.com', 'Finance', 'staff', 'scrypt:32768:8:1$cHqEmDIPLVWA9lG3$8e2e9f48bd2ee1b8a8eb39033de7549d4559aa81f45fe458743e7b1e1fb7fee4d70dd177fda0bd11749f3e2565a26efbf633990b4bacb490d75dcd5d64274445', 'A'),
(35, 'David Tan', 'david.tan@company.com', 'Finance', 'senior manager', 'scrypt:32768:8:1$dRgvEPVWwHaVUw3O$adfa0649109a2baa43df3eba483470fff7cb2d16227d83a34e9eee6e507ef034904261e0aa12e79f7041416168c3a60353e9013bbc641e2659076cf94ad7ec39', 'A'),
(36, 'Samuel Lee', 'samuel.lee@company.com', 'HR', 'manager', 'scrypt:32768:8:1$nsIBsoeaIhCHqNpz$014a0b5656dafc5d73462bdd14d235e47a09542f97cf0cca393e7ff83866e7bb73dda99da71a788a5f74e3ba35d3335f93b4ab6bcec636ccf516a123ed9fc48d', 'B'),
(37, 'Elena Petrova', 'elena.petrova@company.com', 'HR', 'senior manager', 'scrypt:32768:8:1$syYOJpcehNngXNoj$e3e9c3ac14392e5c7cf8fad45839786d7eddeaed6cac242166f4cadd319bdda12e70745500a9b4dc14366441842c66159bf98146fcedf9f47c3cb742b6bb6520', 'B'),
(38, 'Priya Nair', 'priya.nair@company.com', 'HR', 'staff', 'scrypt:32768:8:1$jKYhtwBg3aUdrPH9$0aa7d16f5e00566d43bb0d3699b19f94057525046eea61ebeff0a7bffb423a58659705f196768559110790fbc3896ba4742166eff867b8bd32b757e9dbaeb0c6', 'B'),
(39, 'Daniel Wong', 'daniel.wong@company.com', 'IT', 'senior manager', 'scrypt:32768:8:1$MUJLXSpFB7euQ9Kh$1a9e3cac49f326985c2e1c844546ae000ede91c573945a5a48dab4ae9dc44a8c5b0c788e8102bb2e92c88020b7ec62373315094c7ead79c1957868f96d8385d2', 'C'),
(40, 'Amelia Chen', 'amelia.chen@company.com', 'IT', 'staff', 'scrypt:32768:8:1$zX0EPZGkyN8EMZKv$39dad1896947554a99e20f4c056b1f897d070930d521a0a8cc5025005d63363e8ccfeb4a15c4651b49f0f9faaed75fceb5deaad27538061c43b3b279d1b95d1a', 'C'),
(41, 'Oliver Smith', 'oliver.smith@company.com', 'IT', 'staff', 'scrypt:32768:8:1$0czmvuyDv907N2Iu$ef5cc2b4b2187a3a76f9e74d8af7f9ba5935ac4a1ea58873b80253ee5c65c68e9493c58bacdfe59bb44306ea71afcde2d695b1a0d441eb876ca6ae629cc95d64', 'C'),
(42, 'Michael Adams', 'michael.adams@company.com', 'Marketing', 'manager', 'scrypt:32768:8:1$NWXtRbe0HP04wFFp$786ae3545ee81fd4a43e37b471845c98d806df6296a74cf3177a0836e05312832c2f24496b6601bde88a147a5cf2f3c04b8c0d920c57bfa5b5fcd4d41bb91909', 'D'),
(43, 'Sophia Ibrahim', 'sophia.ibrahim@company.com', 'Marketing', 'staff', 'scrypt:32768:8:1$OZLenawTexGtPFOq$6a5c748b04cb75bf48b1c5a46bbe2e4eaaa84e6a13e60b2afc66d3c3654cda25d379eac1b5eba689d7cb3a224d9788cb1e1ab01d9dd11be2c42e02e03c80d569', 'D'),
(44, 'Grace Miller', 'grace.miller@company.com', 'Marketing', 'staff', 'scrypt:32768:8:1$JLwA8MmDz3B0fnF7$4d9886d38db1cd7d4f59d2cec3f1724dec04860de2287c566445c9a3a3c57d374df60ab3b6d6815a4088223a0ee926daf4aee06e1d054bf17c5331a8d38993ea', 'D'),
(45, 'Lucas Grant', 'lucas.grant@company.com', 'Operations', 'senior manager', 'scrypt:32768:8:1$LEsHQpVaJr5dyP8u$9de5ca1862a1c723ba7b198a472c0128b0c29fa73a3e9af14d1ef2f67adb725865debe10379f56f8d9187a42dda2feb4cf3a6f063be9ca946c84975a4676d92f', 'E'),
(46, 'Hannah Lim', 'hannah.lim@company.com', 'Operations', 'staff', 'scrypt:32768:8:1$StRIE6tjdvk9a2hY$d471004894080be2fe1ba794812a238e8622b53d9ee967ce060e4514b21f1aa33019de48a1b206170a7d86dac774bb542e03313998c84c1066b34e498ea29159', 'E'),
(47, 'James Connor', 'james.connor@company.com', 'Admin', 'manager', 'scrypt:32768:8:1$Igd0teMCNnB1nXDD$7f1aa55a12b1988f2918f00a65d1d29c560f03ea1d549be12f765ac398842263e5eb01294cb831079c68a922c51f223de8b7d52f14a94b0287cdb253c82d4909', 'F'),
(48, 'Charlie Owner', 'charlie@example.com', 'IT', 'manager', 'scrypt:32768:8:1$eMpXOUzFXG2kyq0z$b3837a17cd53ccbb57e5c29d26bde15b8031b50a93a6d8a78c8f4202208cb4517efaced6610146dbddfc3909b89db2674a8d84f4551a5acb328ca56175e8e9b7', 'C'),
(49, 'Alice Collaborator', 'alice@example.com', 'IT', 'staff', 'scrypt:32768:8:1$71i1rdw2L2MCaofW$28f43c0dfd74527dab7b5039ed6089ecf74a878fb459db9c0dd3e30706c509fcb9708cf7e20b798826d27571bd6fc2cd87f6efd4c3a02c8159a04473aac7c2ca', 'C'),
(50, 'Bob Collaborator', 'bob@example.com', 'IT', 'staff', 'scrypt:32768:8:1$IS001Gh20fO1Xowf$06e29eeba3634ae79981113a03b0f40e9395f83070a0504e4937357a8b120566f95f9a87c98c140033352c5bc91782fa4c9b373a5aff6043dc1345b46c350fb6', 'C');


-- Insert projects data (FIXED: will have proper updated_at timestamps)
INSERT INTO projects (id, name, owner, owner_id, tasks_done, tasks_total, due_date) VALUES
(1, 'Website Redesign', 'test', 1, 0, 0, '2025-12-15 00:00:00'),
(2, 'Marketing Launch', 'test2', 2, 0, 0, '2025-12-20 00:00:00'),
(3, 'Data Migration', 'James Connor', 47, 0, 0, '2025-12-31 00:00:00');

-- Insert tasks data (EXACT match to your current data)
INSERT INTO task (task_id, title, description, attachment, priority, recurrence, start_date, deadline, completed_date, created_at, status, owner, project_id, parent_id) VALUES
(1, 'Reconcile Bank Statements', 'Match company bank transactions with internal records to ensure accuracy.', '[]', 8, NULL, NULL, '2025-10-22 12:46:00', NULL, '2025-10-18 22:47:07', 'ongoing', 34, NULL, NULL),
(2, 'Process Vendor Invoices', 'Enter and verify vendor invoices for approval and payment scheduling.', '[]', 7, NULL, NULL, '2025-10-31 22:47:00', NULL, '2025-10-18 22:48:04', 'ongoing', 34, NULL, NULL),
(3, 'Expense Reports', 'Record employee expense claims and ensure compliance with policy.', '[]', 5, NULL, NULL, '2025-10-29 13:51:00', NULL, '2025-10-18 22:48:42', 'ongoing', 34, NULL, NULL),
(4, 'Maintain Financial Records', 'File and organize accounting documents for audit readiness.', '[]', 3, NULL, NULL, '2025-10-22 12:51:00', NULL, '2025-10-18 22:49:50', 'ongoing', 34, NULL, NULL),
(5, 'Entry for Budget Sheet', 'Input approved budget adjustments into the financial tracking', '[]', 6, NULL, NULL, '2025-10-20 23:52:00', NULL, '2025-10-18 22:51:57', 'ongoing', 34, NULL, NULL),
(6, 'Assist with Payroll Reconciliation', 'Verify employee timesheets and support payroll accuracy checks.', '[]', 9, NULL, NULL, '2025-10-19 12:54:00', NULL, '2025-10-18 22:52:30', 'ongoing', 34, NULL, NULL),
(7, 'Prepare Monthly Financial Report', 'Compile monthly financial performance data and present a summary to the director.', '[]', 9, NULL, NULL, '2025-10-30 13:00:00', NULL, '2025-10-18 22:57:15', 'unassigned', 1, NULL, NULL),
(8, 'Coordinate Internal Audit Schedule', 'Set and communicate the internal audit timeline to all relevant departments.', '[]', 5, NULL, NULL, '2025-10-22 12:59:00', NULL, '2025-10-18 22:57:49', 'unassigned', 1, NULL, NULL),
(9, 'Analyze Departmental Expenses', 'Review spending across departments to identify cost-saving', '[]', 7, NULL, NULL, '2025-10-23 12:59:00', NULL, '2025-10-18 22:58:16', 'unassigned', 1, NULL, NULL),
(10, 'Expense Policy Training', 'Conduct training for staff on updated expense reimbursement policies.', '[]', 3, NULL, NULL, '2025-11-07 12:00:00', NULL, '2025-10-18 22:58:45', 'unassigned', 1, NULL, NULL),
(11, 'Approve Capital Expenditure Requests', 'Evaluate all CAPEX requests exceeding department thresholds and approve or reject accordingly.', '[]', 9, NULL, NULL, '2025-10-23 14:03:00', NULL, '2025-10-18 23:00:14', 'unassigned', 35, NULL, NULL),
(12, 'Financial Policy Revision', 'Oversee the revision of internal finance policies to align with new regulatory standards.', '[]', 5, NULL, NULL, '2025-10-21 15:04:00', NULL, '2025-10-18 23:00:36', 'unassigned', 35, NULL, NULL);

-- Insert project members (from your current data)
INSERT INTO project_members (project_id, staff_id) VALUES
(1, 1), (1, 2),  -- Website Redesign team
(2, 34),         -- Marketing Launch team  
(3, 47);         -- Data Migration team

-- Insert task collaborators (from your current data)
INSERT INTO task_collaborators (task_id, staff_id) VALUES
(7, 1), (8, 1), (9, 1), (10, 1), (11, 1), (12, 1), (6, 34), (1, 34), (2, 34), (5, 34), (3, 34), (4, 34)
;

-- Insert default preferences for existing staff members
INSERT IGNORE INTO `notification_preferences` (`staff_id`, `deadline_reminders`, `task_status_updates`, `due_date_changes`, `deadline_reminder_days`)
SELECT `employee_id`, 1, 1, 1, '7,3,1'
FROM `staff`
WHERE `employee_id` NOT IN (SELECT `staff_id` FROM `notification_preferences`);