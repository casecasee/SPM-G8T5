-- backend/database/seeds/development.sql
USE SPM;

-- Insert staff data (EXACT match to your current data)
INSERT INTO staff (employee_id, employee_name, email, department, role, password, team) VALUES
(1, 'Emma Johnson', 'emma.johnson@company.com', 'Finance', 'manager', 'scrypt:32768:8:1$SV77TeLwRr1fVxrH$ae351de7bfd467efb9fad6935a663dd6f3b2011df9b98d83259dc8997c95ce16768c7bfa80e12e7f4c4d2e3784cebc1cae96f90b42249a673e5bf088c2820370', 'A'),
(2, 'Marcus Chen', 'marcus.chen@company.com', 'Finance', 'staff', 'scrypt:32768:8:1$CnHDtDgGgoavw8qU$e252e5968662617c4a5e72836b2327b38e843d5984f775316369c94100c3612bb332e05f50fff2258f0256844607564f8f48f56a45d5bb701bd693f215cde717', 'A'),
(33, 'Isabella Rossi', 'isabella.rossi@company.com', 'HR', 'staff', 'scrypt:32768:8:1$0fyuoPHe63RwHGBS$273d6b6b33578e08a13b1205727ab67b90f3cab32cf7a2675514fc5009ef15c442781b4e0a8154218458b61c05cc6d6be28185ceff5c5baf4470b7f0e819b253', 'B'),
(34, 'Natalie Foster', 'natalie.foster@company.com', 'Finance', 'staff', 'scrypt:32768:8:1$cHqEmDIPLVWA9lG3$8e2e9f48bd2ee1b8a8eb39033de7549d4559aa81f45fe458743e7b1e1fb7fee4d70dd177fda0bd11749f3e2565a26efbf633990b4bacb490d75dcd5d64274445', 'A'),
(35, 'David Yap', 'david.yap@company.com', 'Finance', 'director', 'scrypt:32768:8:1$dRgvEPVWwHaVUw3O$adfa0649109a2baa43df3eba483470fff7cb2d16227d83a34e9eee6e507ef034904261e0aa12e79f7041416168c3a60353e9013bbc641e2659076cf94ad7ec39', 'A'),
(36, 'Samuel Lee', 'samuel.lee@company.com', 'HR', 'manager', 'scrypt:32768:8:1$nsIBsoeaIhCHqNpz$014a0b5656dafc5d73462bdd14d235e47a09542f97cf0cca393e7ff83866e7bb73dda99da71a788a5f74e3ba35d3335f93b4ab6bcec636ccf516a123ed9fc48d', 'B'),
(37, 'Sally Loh', 'sally.loh@company.com', 'HR', 'director', 'scrypt:32768:8:1$syYOJpcehNngXNoj$e3e9c3ac14392e5c7cf8fad45839786d7eddeaed6cac242166f4cadd319bdda12e70745500a9b4dc14366441842c66159bf98146fcedf9f47c3cb742b6bb6520', 'B'),
(38, 'Priya Nair', 'priya.nair@company.com', 'HR', 'staff', 'scrypt:32768:8:1$jKYhtwBg3aUdrPH9$0aa7d16f5e00566d43bb0d3699b19f94057525046eea61ebeff0a7bffb423a58659705f196768559110790fbc3896ba4742166eff867b8bd32b757e9dbaeb0c6', 'B'),
(39, 'Peter Yap', 'peter.yap@company.com', 'IT', 'director', 'scrypt:32768:8:1$MUJLXSpFB7euQ9Kh$1a9e3cac49f326985c2e1c844546ae000ede91c573945a5a48dab4ae9dc44a8c5b0c788e8102bb2e92c88020b7ec62373315094c7ead79c1957868f96d8385d2', 'C'),
(40, 'Amelia Chen', 'amelia.chen@company.com', 'IT', 'staff', 'scrypt:32768:8:1$zX0EPZGkyN8EMZKv$39dad1896947554a99e20f4c056b1f897d070930d521a0a8cc5025005d63363e8ccfeb4a15c4651b49f0f9faaed75fceb5deaad27538061c43b3b279d1b95d1a', 'C'),
(41, 'Oliver Smith', 'oliver.smith@company.com', 'IT', 'staff', 'scrypt:32768:8:1$0czmvuyDv907N2Iu$ef5cc2b4b2187a3a76f9e74d8af7f9ba5935ac4a1ea58873b80253ee5c65c68e9493c58bacdfe59bb44306ea71afcde2d695b1a0d441eb876ca6ae629cc95d64', 'C'),
(42, 'Derek Tan', 'derek.tan@company.com', 'Sales', 'director', 'scrypt:32768:8:1$NWXtRbe0HP04wFFp$786ae3545ee81fd4a43e37b471845c98d806df6296a74cf3177a0836e05312832c2f24496b6601bde88a147a5cf2f3c04b8c0d920c57bfa5b5fcd4d41bb91909', 'D'),
(43, 'Sophia Ibrahim', 'sophia.ibrahim@company.com', 'Sales', 'manager', 'scrypt:32768:8:1$OZLenawTexGtPFOq$6a5c748b04cb75bf48b1c5a46bbe2e4eaaa84e6a13e60b2afc66d3c3654cda25d379eac1b5eba689d7cb3a224d9788cb1e1ab01d9dd11be2c42e02e03c80d569', 'D'),
(44, 'Grace Miller', 'grace.miller@company.com', 'Sales', 'staff', 'scrypt:32768:8:1$JLwA8MmDz3B0fnF7$4d9886d38db1cd7d4f59d2cec3f1724dec04860de2287c566445c9a3a3c57d374df60ab3b6d6815a4088223a0ee926daf4aee06e1d054bf17c5331a8d38993ea', 'D'),
(45, 'Ernest Sim', 'ernest.sim@company.com', 'Consultancy', 'director', 'scrypt:32768:8:1$LEsHQpVaJr5dyP8u$9de5ca1862a1c723ba7b198a472c0128b0c29fa73a3e9af14d1ef2f67adb725865debe10379f56f8d9187a42dda2feb4cf3a6f063be9ca946c84975a4676d92f', 'E'),
(46, 'Hannah Lim', 'hannah.lim@company.com', 'Consultancy', 'staff', 'scrypt:32768:8:1$StRIE6tjdvk9a2hY$d471004894080be2fe1ba794812a238e8622b53d9ee967ce060e4514b21f1aa33019de48a1b206170a7d86dac774bb542e03313998c84c1066b34e498ea29159', 'E'),
(47, 'Jack Sim', 'jack.sim@company.com', 'HR', 'director', 'scrypt:32768:8:1$Igd0teMCNnB1nXDD$7f1aa55a12b1988f2918f00a65d1d29c560f03ea1d549be12f765ac398842263e5eb01294cb831079c68a922c51f223de8b7d52f14a94b0287cdb253c82d4909', 'B'),
(48, 'Charlie Brown', 'charlie.brown@company.com', 'IT', 'manager', 'scrypt:32768:8:1$BmFXveMbkur5Hu8B$cef961434dbe6af61814eb73c9a5cb39103559c24620e5fa27924a734cf3c65725360fd10d38c8979abb1dc270b95cc475f84964177f76bbfc7f57371b83f263', 'C'),
(49, 'Alice Jane', 'alice.jane@company.com', 'IT', 'staff', 'scrypt:32768:8:1$MuLENhGEXpT3B9p2$e449d65e7cee1252f22323408dfd2f289d2bb2be23bbcaafdc762d2c38a4374d7edb91b6b7683f31ed6799ced255070e8f0bcec6bf7867e43460c30988f0afad', 'C'),
(50, 'Bob Ranger', 'bob.ranger@company.com', 'IT', 'staff', 'scrypt:32768:8:1$cfSyfBUSzaV9v3ep$5673592ec69cd8b6d3b5cb91ee90403f6b58a9335ff08a9931a3c8e4c90969fd32081a981c25da5b22ad5519fbafa5b806f449f3a283152e22304c667074c9d1', 'C'),
(51, 'Liam Patel','liam.patel@company.com','HR','manager','scrypt:32768:8:1$VilNsh9RytgaUNP4$af428cbb43132a9944d25cb69222e1b10b816d93fe90b1c776650e2a5ef5da5e2b4bd3a4204b67ab11d8edc4d156b34c4b354c3141b3754bb13528bb73a7aac7','B'),
(52, 'Aria Kim','aria.kim@company.com','HR','manager','scrypt:32768:8:1$ZDF71zqbJg6WauCV$6be9bd84232e0fc6c931f5cbff8aa1a9463fd3677a5237db66d39f571e62ab010f467d24e36cc5350dbc6b26cb96a15966e806580387be9d56fba831757aca3a','B'),
(53, 'Julian Herrera','julian.herrera@company.com','HR','staff','scrypt:32768:8:1$mIjuhTubEBglU7ng$b0c5ea5b967a36489f0d24dc3cdc99828ca8eb5e5bc8a87e98d8ad245e388952ee4c1268f7cc6c4863a49f71700d1a3ed1c29a551186b0966c01366a1f4b5579','B'),
(54, 'Freya Ahmed','freya.ahmed@company.com','Consultancy','manager','scrypt:32768:8:1$jCSQhncHWriQfG60$0d93d348e341fc8b33f3e52bd05d7e1b00be22d840ec94beafd85f1294ac3d32eaedef6559d517fa9d9b4ef10cc186cf192a41ca1ec3010c4e9ebccf63030f45','E'),
(55, 'Eric Loh','eric.loh@company.com','Systems','director','scrypt:32768:8:1$vQhtuHdZOSRVyE6b$ec01376f915ccbe9207c51bff8264d7251805cd7043a620867e75ea7d8edbcff13a39338ebb1df4483b61c2c932b19222892d12ed11d83db33573642e86ce0d6','F'),
(56, 'Ethan Rivera','ethan.rivera@company.com','Systems','manager','scrypt:32768:8:1$5WV4svbRDI4MwlSY$4c7897725de640b53a3e8529f4f23fa5e15e2e9ee78c7a6059eb48036a94fd84bee5aee55714bbd2264b1918df806fb199d0cdb8cd9f88c05f6c3cd06d5d6d1b','F'),
(57, 'Zoe Martinez','zoe.martinez@company.com','Systems','staff','scrypt:32768:8:1$1Ry7iPhpslTptvhL$3b7002abc31743e22f3673acaf271978e0345524e829095027711b4da0ff5d3ae285408e4afca46526ffa4576580dfa5c9df28433b3f403b8b0323eebb94e2f5','F'),
(58, 'Aiden Brooks','aiden.brooks@company.com','Systems','manager','scrypt:32768:8:1$XpBP5iNZGIUTep0G$24ddd0dcac97c97023c7e51ae5812a864a350b5676ea36584ebedfec9276837ed6c75dc092695ba219bbaea0a1acd8b9fcc6d1a763fab9965ad2e6190a1f638f','F'),
(59, 'Nathaniel Cruz','nathaniel.cruz@company.com','Systems','staff','scrypt:32768:8:1$w2UEjnTF4tGKOh0i$b18d2425dd86108fdf9c033b2ea90ab9675e1b6391145659323386f0666c81ccdd90433b873c6e7f94b6709c62eefe2777f1bbae1bb41959e49fe6bebd1e51e2','F'),
(60, 'Philip Lee','philip.lee@company.com','Engineering','director','scrypt:32768:8:1$lL8pfJMskc3Pe6KE$6c63960217db2a220dd978b861688266cacdd2bed2d04f322872592c892d0bcf3c96195b608982da74470e15006aa7c201e39e6cfc823adb31b707db99506ebb','G'),
(61, 'Mia Wilson','mia.wilson@company.com','Engineering','manager','scrypt:32768:8:1$g9Z7iUI6EsdPayrb$4d10add9c9353bdcc91c7f02c615ca6b9ad2730f350c2a5934889d5824babebb6feb5c2ed425454e97c93e099bafbd8e4dd04d571ff6d3c730a55a6bbde6ea20','G'),
(62, 'Gabriel Moreau','gabriel.moreau@company.com','Engineering','staff','scrypt:32768:8:1$73fATBIhCCxt2z6E$a63a216986f18f853fb743c517488957b9ba4fd829fec3d5e2ff66d7d4b55e75d89a1304da8c0ecbed87caa29809d682a0d619c65f696b044af2030d9363224f','G'),
(63, 'Chloe Garcia','chloe.garcia@company.com','Engineering','manager','scrypt:32768:8:1$iVtbYIMMTOee1B2Y$1766f07609cc08d711e0e31c05ed42a0e1c58280b32f409e6b61c61680d53fb9d757528262b370d1df8f8ac5cea4c86c3226387edae473edc1fb0c7352dc1d9d','G'),
(64, 'Madison Clark','madison.clark@company.com','Engineering','staff','scrypt:32768:8:1$soUqejqpdBTW0dUT$2d2f58d00de61c29b67cbdbfbd91bc1ffeab47404507e30e323668f56f10798cbad4bc2a021627816d0b23cb65bc7d635dc343a34f9e766761d966ef8a32bb5f','G'),
(65, 'Isaac Goldberg','isaac.goldberg@company.com','Engineering','manager','scrypt:32768:8:1$kYRvLi5o9Ny50deH$5f7492c52b41fe29ad59f7c463d66877c78fde2d0100eaa616a14df6856414711588b1108f8b50f38ab3eda321f4a3893bf79a4846cb6745e3c764f57423eb8a','G'),
(66, 'Scarlett Lewis','scarlett.lewis@company.com','Engineering','staff','scrypt:32768:8:1$CkDxzhm28hAJlG1o$64a58da66fc5b6500a377586da0d1ade9593bd22dc0d4aea64c9b51b6d343390e0b8167285a88e5c8bd1c61316cb3e9747b5c6c15169ff291daa13fc39c528ad','G');

-- Insert projects data (FIXED: will have proper updated_at timestamps)
INSERT INTO projects (id, name, owner, owner_id, tasks_done, tasks_total, due_date) VALUES
(1, 'Website Redesign', 'Emma Johnson', 1, 0, 0, '2025-12-15 00:00:00'),
(2, 'Marketing Launch', 'Marcus Chen', 2, 0, 0, '2025-12-20 00:00:00'),
(3, 'Data Migration', 'Jack Sim', 47, 0, 0, '2025-12-31 00:00:00'),
(4, 'admin project', 'Jack Sim' , 47, 0,0, '2025-12-31 00:00:00' ),
(5, 'finance project', 'David Yap', 35, 0,0, '2025-12-31 00:00:00' ),
(6, 'HR project', 'Samuel Lee', 36, 0,0, '2025-12-31 00:00:00' ),
(7, 'IT project', 'Charlie Brown', 48, 0,0, '2025-12-31 00:00:00' ),
(8, 'marketing project', 'Derek Tan', 42, 0,0, '2025-12-31 00:00:00' ),
(9, 'operations project', 'Ernest Sim', 45, 0,0, '2025-12-31 00:00:00' );

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

INSERT INTO task (task_id, title, description, attachment, priority, recurrence, start_date, deadline, completed_date, created_at, status, owner, project_id, parent_id) VALUES
-- Admin (33)
(13, 'Update Office Asset Register', 'Record all new office assets and ensure disposal of outdated equipment is logged properly.', '[]', 6, NULL, NULL, '2025-11-02 10:00:00', NULL, '2025-10-29 10:00:00', 'ongoing', 33, 4, NULL),
(14, 'Coordinate Meeting Room Bookings', 'Oversee scheduling of meeting rooms for upcoming departmental events and staff meetings.', '[]', 4, NULL, NULL, '2025-11-05 09:00:00', NULL, '2025-10-29 10:02:00', 'under review', 33, 4, NULL),
(15, 'Organize Office Supplies Inventory', 'Perform quarterly stocktake of stationery and raise purchase requests for low items.', '[]', 5, NULL, NULL, '2025-11-08 14:00:00', NULL, '2025-10-29 10:05:00', 'unassigned', 33, 4, NULL),

-- Finance (34–35)
(16, 'Quarterly Tax Filing Preparation', 'Compile all financial statements and ensure all tax documents are in order for submission.', '[]', 9, NULL, NULL, '2025-11-10 12:00:00', NULL, '2025-10-29 10:10:00', 'ongoing', 34, 5, NULL),
(17, 'Vendor Payment Schedule Update', 'Review and update the vendor payment calendar for upcoming month.', '[]', 7, NULL, NULL, '2025-11-06 17:00:00', NULL, '2025-10-29 10:12:00', 'done', 34, 5, NULL),
(18, 'Expense Audit Follow-up', 'Coordinate with departments to clarify flagged expenses during last internal audit.', '[]', 8, NULL, NULL, '2025-11-04 11:00:00', NULL, '2025-10-29 10:14:00', 'ongoing', 34, 5, NULL),

(19, 'Forecast Departmental Budgets', 'Analyze spending patterns and prepare Q1 2026 budget forecasts for each department.', '[]', 9, NULL, NULL, '2025-11-12 15:00:00', NULL, '2025-10-29 10:15:00', 'under review', 35, 5, NULL),
(20, 'Reconcile Corporate Credit Cards', 'Verify all corporate card statements for discrepancies and submit reconciliation reports.', '[]', 7, NULL, NULL, '2025-11-03 10:30:00', NULL, '2025-10-29 10:17:00', 'ongoing', 35, 5, NULL),
(21, 'Finance SOP Documentation', 'Update internal finance standard operating procedures for onboarding new staff.', '[]', 5, NULL, NULL, '2025-11-09 09:00:00', NULL, '2025-10-29 10:18:00', 'unassigned', 35, 5, NULL),

-- HR (36–38)
(22, 'Recruitment Drive Coordination', 'Plan and schedule interviews for upcoming graduate hiring round.', '[]', 8, NULL, NULL, '2025-11-07 10:00:00', NULL, '2025-10-29 10:19:00', 'ongoing', 36, 6, NULL),
(23, 'Employee Engagement Survey', 'Design and launch the annual employee satisfaction survey to all staff.', '[]', 6, NULL, NULL, '2025-11-10 13:00:00', NULL, '2025-10-29 10:21:00', 'under review', 36, 6, NULL),
(24, 'HR Compliance Checklist', 'Ensure HR policies align with latest labor law requirements.', '[]', 9, NULL, NULL, '2025-11-02 12:00:00', NULL, '2025-10-29 10:23:00', 'done', 36, 6, NULL),

(25, 'Performance Appraisal Tracking', 'Monitor completion status of mid-year performance appraisals.', '[]', 7, NULL, NULL, '2025-11-08 11:00:00', NULL, '2025-10-29 10:24:00', 'ongoing', 37, 6, NULL),
(26, 'Update Employee Database', 'Review and update employee records with recent promotions and role changes.', '[]', 5, NULL, NULL, '2025-11-04 17:00:00', NULL, '2025-10-29 10:26:00', 'unassigned', 37, 6, NULL),
(27, 'Training Needs Analysis', 'Identify departments that require training and create proposals for next quarter.', '[]', 6, NULL, NULL, '2025-11-11 09:30:00', NULL, '2025-10-29 10:27:00', 'under review', 37, 6, NULL),

(28, 'Onboarding Kit Preparation', 'Prepare welcome materials and access passes for incoming new hires.', '[]', 4, NULL, NULL, '2025-11-03 09:00:00', NULL, '2025-10-29 10:29:00', 'done', 38, 6, NULL),
(29, 'Exit Interview Reports', 'Summarize findings from recent employee exit interviews.', '[]', 5, NULL, NULL, '2025-11-05 15:00:00', NULL, '2025-10-29 10:30:00', 'ongoing', 38, 6, NULL),
(30, 'Wellness Program Planning', 'Design monthly wellness initiatives to promote employee health.', '[]', 7, NULL, NULL, '2025-11-09 16:00:00', NULL, '2025-10-29 10:31:00', 'unassigned', 38, 6, NULL),

-- IT (39–41, 48–50)
(31, 'Network Security Audit', 'Conduct a full audit of firewall configurations and access control lists.', '[]', 9, NULL, NULL, '2025-11-12 12:00:00', NULL, '2025-10-29 10:32:00', 'ongoing', 39, 7, NULL),
(32, 'Server Maintenance Schedule', 'Draft a new maintenance plan for quarterly server updates.', '[]', 6, NULL, NULL, '2025-11-06 14:00:00', NULL, '2025-10-29 10:33:00', 'done', 39, 7, NULL),
(33, 'Software License Renewal', 'Review software subscriptions and renew those expiring next month.', '[]', 8, NULL, NULL, '2025-11-10 09:00:00', NULL, '2025-10-29 10:34:00', 'unassigned', 39, 7, NULL),

(34, 'Database Optimization', 'Analyze query performance and apply necessary database indexing.', '[]', 7, NULL, NULL, '2025-11-05 13:00:00', NULL, '2025-10-29 10:35:00', 'ongoing', 40, 7, NULL),
(35, 'Helpdesk Ticket Review', 'Analyze recurring IT issues from the past month and identify patterns.', '[]', 5, NULL, NULL, '2025-11-08 11:00:00', NULL, '2025-10-29 10:36:00', 'under review', 40, 7, NULL),
(36, 'Deploy Security Patches', 'Install latest OS and software security updates across all systems.', '[]', 9, NULL, NULL, '2025-11-11 16:00:00', NULL, '2025-10-29 10:37:00', 'ongoing', 40, 7, NULL),

(37, 'Set Up Backup Server', 'Configure backup server and test disaster recovery procedures.', '[]', 8, NULL, NULL, '2025-11-07 14:00:00', NULL, '2025-10-29 10:38:00', 'under review', 41, 7, NULL),
(38, 'Asset Tagging for Laptops', 'Implement asset tags for all new laptops to enhance tracking.', '[]', 6, NULL, NULL, '2025-11-09 10:00:00', NULL, '2025-10-29 10:39:00', 'done', 41, 7, NULL),
(39, 'VPN Access Review', 'Revalidate VPN access permissions and remove inactive users.', '[]', 5, NULL, NULL, '2025-11-03 09:30:00', NULL, '2025-10-29 10:40:00', 'unassigned', 41, 7, NULL),

(40, 'IT Helpdesk Training', 'Conduct refresher training for helpdesk staff on incident management.', '[]', 6, NULL, NULL, '2025-11-06 09:00:00', NULL, '2025-10-29 10:41:00', 'ongoing', 48, 7, NULL),
(41, 'System Access Audit', 'Review user access rights to ensure compliance with IT policies.', '[]', 9, NULL, NULL, '2025-11-08 11:00:00', NULL, '2025-10-29 10:42:00', 'done', 48, 7, NULL),
(42, 'Software Deployment Testing', 'Run UAT for newly developed internal software tools.', '[]', 8, NULL, NULL, '2025-11-10 14:00:00', NULL, '2025-10-29 10:43:00', 'under review', 48, 7, NULL),

(43, 'Cloud Service Cost Analysis', 'Compare cloud provider costs and suggest optimization strategies.', '[]', 7, NULL, NULL, '2025-11-11 13:00:00', NULL, '2025-10-29 10:44:00', 'unassigned', 49, 7, NULL),
(44, 'Implement MFA for Staff', 'Roll out multi-factor authentication for all employee accounts.', '[]', 8, NULL, NULL, '2025-11-05 12:00:00', NULL, '2025-10-29 10:45:00', 'ongoing', 49, 7, NULL),
(45, 'IT Asset Disposal Plan', 'Prepare disposal strategy for obsolete devices following compliance protocols.', '[]', 6, NULL, NULL, '2025-11-09 16:00:00', NULL, '2025-10-29 10:46:00', 'done', 49, 7, NULL),

(46, 'Upgrade Internal Network', 'Coordinate with vendor to upgrade switches and routers for faster connectivity.', '[]', 9, NULL, NULL, '2025-11-12 10:00:00', NULL, '2025-10-29 10:47:00', 'ongoing', 50, 7, NULL),
(47, 'Data Backup Verification', 'Ensure backups are successfully completed and restorable from storage.', '[]', 7, NULL, NULL, '2025-11-08 15:00:00', NULL, '2025-10-29 10:48:00', 'under review', 50, 7, NULL),
(48, 'Support Ticket Response Time Review', 'Evaluate current support response times and propose efficiency improvements.', '[]', 5, NULL, NULL, '2025-11-06 09:30:00', NULL, '2025-10-29 10:49:00', 'done', 50, 7, NULL),

-- Marketing (42–44)
(49, 'Social Media Campaign Planning', 'Develop campaign ideas for upcoming open house event.', '[]', 7, NULL, NULL, '2025-11-09 10:00:00', NULL, '2025-10-29 10:50:00', 'ongoing', 42, 8, NULL),
(50, 'Content Calendar Update', 'Revise marketing content schedule for next month.', '[]', 4, NULL, NULL, '2025-11-05 11:00:00', NULL, '2025-10-29 10:51:00', 'unassigned', 42, 8, NULL),
(51, 'Email Newsletter Design', 'Create and test email layouts for upcoming campaign.', '[]', 6, NULL, NULL, '2025-11-10 09:00:00', NULL, '2025-10-29 10:52:00', 'under review', 42, 8, NULL),

(52, 'Market Research Report', 'Compile findings on competitor outreach and digital strategies.', '[]', 9, NULL, NULL, '2025-11-08 14:00:00', NULL, '2025-10-29 10:53:00', 'done', 43, 8, NULL),
(53, 'Event Poster Design', 'Design promotional materials for the year-end showcase.', '[]', 5, NULL, NULL, '2025-11-07 15:00:00', NULL, '2025-10-29 10:54:00', 'ongoing', 43, 8, NULL),
(54, 'Ad Performance Analysis', 'Review metrics from recent online ads to optimize targeting.', '[]', 8, NULL, NULL, '2025-11-11 09:30:00', NULL, '2025-10-29 10:55:00', 'under review', 43, 8, NULL),

(55, 'Update Branding Guidelines', 'Revise color palette and typography standards for new campaigns.', '[]', 6, NULL, NULL, '2025-11-06 10:00:00', NULL, '2025-10-29 10:56:00', 'ongoing', 44, 8, NULL),
(56, 'Collaborate with Influencers', 'Identify and reach out to potential influencers for partnership.', '[]', 7, NULL, NULL, '2025-11-09 11:00:00', NULL, '2025-10-29 10:57:00', 'done', 44, 8, NULL),
(57, 'Photography Session Planning', 'Arrange photoshoot logistics for campaign visuals.', '[]', 5, NULL, NULL, '2025-11-12 15:00:00', NULL, '2025-10-29 10:58:00', 'under review', 44, 8, NULL),

-- Operations (45–46)
(58, 'Facility Maintenance Check', 'Inspect key facilities for safety compliance and repair needs.', '[]', 8, NULL, NULL, '2025-11-05 09:00:00', NULL, '2025-10-29 10:59:00', 'ongoing', 45, 9, NULL),
(59, 'Supplier Contract Renewal', 'Negotiate contract extensions with main service vendors.', '[]', 7, NULL, NULL, '2025-11-08 10:00:00', NULL, '2025-10-29 11:00:00', 'unassigned', 45, 9, NULL),
(60, 'Inventory Control Audit', 'Conduct audit to ensure accurate stock levels and documentation.', '[]', 9, NULL, NULL, '2025-11-11 13:00:00', NULL, '2025-10-29 11:01:00', 'under review', 45, 9, NULL),

(61, 'Logistics Route Optimization', 'Evaluate transport routes to reduce operational costs.', '[]', 6, NULL, NULL, '2025-11-09 12:00:00', NULL, '2025-10-29 11:02:00', 'done', 46, 9, NULL),
(62, 'Warehouse Space Planning', 'Reorganize storage areas for improved accessibility and safety.', '[]', 5, NULL, NULL, '2025-11-06 14:00:00', NULL, '2025-10-29 11:03:00', 'ongoing', 46, 9, NULL),
(63, 'Vendor Delivery Review', 'Analyze vendor delivery performance metrics for the last quarter.', '[]', 4, NULL, NULL, '2025-11-10 11:00:00', NULL, '2025-10-29 11:04:00', 'unassigned', 46, 9, NULL),

-- Admin (47)
(64, 'Organize Digital File Archive', 'Reorganize shared drives and remove redundant documents.', '[]', 5, NULL, NULL, '2025-11-08 09:30:00', NULL, '2025-10-29 11:05:00', 'ongoing', 47, 4, NULL),
(65, 'Prepare Monthly Staff Attendance Report', 'Compile attendance summaries and report to HR.', '[]', 6, NULL, NULL, '2025-11-05 10:00:00', NULL, '2025-10-29 11:06:00', 'done', 47, 4, NULL),
(66, 'Office Layout Update Plan', 'Assist management in drafting new seating arrangement plans.', '[]', 7, NULL, NULL, '2025-11-11 12:00:00', NULL, '2025-10-29 11:07:00', 'under review', 47, 4, NULL);

-- Insert project members (from your current data)
INSERT INTO project_members (project_id, staff_id) VALUES
(1, 1), (1, 2),  -- Website Redesign team
(2, 34), (2, 2), -- Marketing Launch team  
(3, 47);         -- Data Migration team

-- Insert task collaborators (from your current data)
INSERT INTO task_collaborators (task_id, staff_id) VALUES
(7, 1),
(8, 1),
(9, 1),
(10, 1),
(11, 1),
(12, 1),
(13, 33),
(14, 33),
(15, 33),
(1, 34),
(2, 34),
(3, 34),
(4, 34),
(5, 34),
(6, 34),
(16, 34),
(17, 34),
(18, 34),
(11, 35),
(12, 35),
(19, 35),
(20, 35),
(21, 35),
(22, 36),
(23, 36),
(24, 36),
(25, 37),
(26, 37),
(27, 37),
(28, 38),
(29, 38),
(30, 38),
(31, 39),
(32, 39),
(33, 39),
(34, 40),
(35, 40),
(36, 40),
(37, 41),
(38, 41),
(39, 41),
(49, 42),
(50, 42),
(51, 42),
(52, 43),
(53, 43),
(54, 43),
(55, 44),
(56, 44),
(57, 44),
(58, 45),
(59, 45),
(60, 45),
(61, 46),
(62, 46),
(63, 46),
(64, 47),
(65, 47),
(66, 47),
(40, 48),
(41, 48),
(42, 48),
(67, 48),
(68, 48),
(43, 49),
(44, 49),
(45, 49),
(46, 50),
(47, 50),
(48, 50);


-- INSERT INTO task_collaborators (task_id, staff_id) VALUES
-- -- Finance (34–35)
-- (16, 34), (17, 34), (18, 34),
-- (19, 35), (20, 35), (21, 35),

-- -- HR (36–38)
-- (22, 36), (23, 36), (24, 36),
-- (25, 37), (26, 37), (27, 37),
-- (28, 38), (29, 38), (30, 38),

-- -- IT (39–41, 48–50)
-- (31, 39), (32, 39), (33, 39),
-- (34, 40), (35, 40), (36, 40),
-- (37, 41), (38, 41), (39, 41),
-- (40, 48), (41, 48), (42, 48),
-- (43, 49), (44, 49), (45, 49),
-- (46, 50), (47, 50), (48, 50),

-- -- Marketing (42–44)
-- (49, 42), (50, 42), (51, 42),
-- (52, 43), (53, 43), (54, 43),
-- (55, 44), (56, 44), (57, 44),

-- -- Operations (45–46)
-- (58, 45), (59, 45), (60, 45),
-- (61, 46), (62, 46), (63, 46),

-- -- Admin (47)
-- (64, 47), (65, 47), (66, 47);


-- Insert default preferences for existing staff members
INSERT IGNORE INTO `notification_preferences` (`staff_id`, `deadline_reminders`, `task_status_updates`, `due_date_changes`, `deadline_reminder_days`)
SELECT `employee_id`, 1, 1, 1, '7,3,1'
FROM `staff`
WHERE `employee_id` NOT IN (SELECT `staff_id` FROM `notification_preferences`);



INSERT INTO project_members (project_id, staff_id) VALUES
-- Admin Project
(4, 33), (4, 47),
-- Finance Project
(5, 34), (5, 35),
-- HR Project
(6, 36), (6, 37), (6, 38),
-- IT Project
(7, 39), (7, 40), (7, 41), (7, 48), (7, 49), (7, 50),
-- Marketing Project
(8, 42), (8, 43), (8, 44),
-- Operations Project
(9, 45), (9, 46);
