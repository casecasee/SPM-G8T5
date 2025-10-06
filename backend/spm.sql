-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3306
-- Generation Time: Oct 06, 2025 at 01:50 PM
-- Server version: 8.2.0
-- PHP Version: 8.2.13

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `spm`
--

-- --------------------------------------------------------

--
-- Table structure for table `projects`
--

DROP TABLE IF EXISTS `projects`;
CREATE TABLE IF NOT EXISTS `projects` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `owner` varchar(255) DEFAULT NULL,
  `owner_id` int DEFAULT NULL,
  `status` varchar(50) NOT NULL,
  `tasks_done` int NOT NULL,
  `tasks_total` int NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_projects_owner_id` (`owner_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `project_members`
--

DROP TABLE IF EXISTS `project_members`;
CREATE TABLE IF NOT EXISTS `project_members` (
  `project_id` int NOT NULL,
  `staff_id` int NOT NULL,
  PRIMARY KEY (`project_id`,`staff_id`),
  KEY `staff_id` (`staff_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `staff`
--

DROP TABLE IF EXISTS `staff`;
CREATE TABLE IF NOT EXISTS `staff` (
  `employee_id` int NOT NULL AUTO_INCREMENT,
  `employee_name` varchar(100) NOT NULL,
  `email` varchar(255) NOT NULL,
  `department` varchar(100) NOT NULL,
  `role` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `team` varchar(100) NOT NULL,
  PRIMARY KEY (`employee_id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=48 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `staff`
--

INSERT INTO `staff` (`employee_id`, `employee_name`, `email`, `department`, `role`, `password`, `team`) VALUES
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
(47, 'James Connor', 'james.connor@company.com', 'Admin', 'manager', 'scrypt:32768:8:1$Igd0teMCNnB1nXDD$7f1aa55a12b1988f2918f00a65d1d29c560f03ea1d549be12f765ac398842263e5eb01294cb831079c68a922c51f223de8b7d52f14a94b0287cdb253c82d4909', 'F');

-- --------------------------------------------------------

--
-- Table structure for table `task`
--

DROP TABLE IF EXISTS `task`;
CREATE TABLE IF NOT EXISTS `task` (
  `task_id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `description` text NOT NULL,
  `attachment` varchar(512) DEFAULT NULL,
  `priority` int DEFAULT NULL,
  `start_date` datetime DEFAULT NULL,
  `deadline` datetime DEFAULT NULL,
  `completed_date` datetime DEFAULT NULL,
  `status` varchar(32) NOT NULL,
  `owner` int NOT NULL,
  `project_id` int DEFAULT NULL,
  `parent_id` int DEFAULT NULL,
  PRIMARY KEY (`task_id`),
  KEY `parent_id` (`parent_id`),
  KEY `ix_Task_owner` (`owner`),
  KEY `ix_Task_project_id` (`project_id`),
  KEY `ix_Task_deadline` (`deadline`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `task`
--

INSERT INTO `task` (`task_id`, `title`, `description`, `attachment`, `priority`, `start_date`, `deadline`, `completed_date`, `status`, `owner`, `project_id`, `parent_id`) VALUES
(1, 'task', 'TASKKKKKKKKKKKKKKKKKKKK', NULL, 4, NULL, '2025-10-06 00:00:00', '2025-10-04 14:04:46', 'under review', 1, NULL, NULL),
(6, 'this is another new task', '', NULL, 5, NULL, '2025-10-04 06:39:30', NULL, 'ongoing', 2, NULL, NULL),
(12, 'test status update', 'test', '[]', 5, NULL, '2025-10-26 16:00:00', '2025-10-06 21:28:49', 'done', 1, NULL, NULL),
(13, 'test status update', 'test', '[]', 5, '2025-10-06 21:28:43', '2025-10-26 16:00:00', NULL, 'under review', 1, NULL, NULL),
(14, 'Prepare weekly team report', 'Summarize key achievements, blockers, and next steps for this week’s activities.', '[]', 6, '2025-10-06 21:48:45', '2025-10-08 16:00:00', '2025-10-06 21:49:00', 'done', 1, NULL, NULL),
(15, 'Review design mockups', 'Go over the latest UI designs and provide feedback before the next iteration.', '[]', 3, '2025-10-06 21:38:11', '2025-10-20 16:00:00', NULL, 'ongoing', 1, NULL, NULL),
(16, 'Update client presentation', 'Incorporate the new performance metrics and refresh the visuals before tomorrow’s meeting.', '[]', 7, NULL, '2025-10-06 16:00:00', NULL, 'ongoing', 34, NULL, NULL),
(18, 'Schedule performance reviews', 'Coordinate one-on-one meetings with each team member for quarterly evaluations.', '[]', 7, NULL, '2025-10-07 16:00:00', NULL, 'unassigned', 35, NULL, NULL),
(19, 'Conduct customer feedback survey', 'Prepare and send out the feedback form to recent users, then collect responses.', '[]', 8, NULL, '2025-10-14 16:00:00', NULL, 'ongoing', 34, NULL, NULL),
(20, 'Optimize website SEO', 'Review page titles, metadata, and keywords to improve search visibility.', '[]', 2, NULL, '2025-10-20 16:00:00', NULL, 'ongoing', 34, NULL, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `task_collaborators`
--

DROP TABLE IF EXISTS `task_collaborators`;
CREATE TABLE IF NOT EXISTS `task_collaborators` (
  `task_id` int NOT NULL,
  `staff_id` int NOT NULL,
  PRIMARY KEY (`task_id`,`staff_id`),
  KEY `staff_id` (`staff_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `task_collaborators`
--

INSERT INTO `task_collaborators` (`task_id`, `staff_id`) VALUES
(1, 1),
(12, 1),
(13, 1),
(14, 1),
(15, 1),
(6, 2),
(20, 2),
(14, 34),
(16, 34),
(19, 34),
(20, 34),
(14, 35),
(18, 35);

--
-- Constraints for dumped tables
--

--
-- Constraints for table `projects`
--
ALTER TABLE `projects`
  ADD CONSTRAINT `projects_ibfk_1` FOREIGN KEY (`owner_id`) REFERENCES `staff` (`employee_id`) ON DELETE SET NULL;

--
-- Constraints for table `project_members`
--
ALTER TABLE `project_members`
  ADD CONSTRAINT `project_members_ibfk_1` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `project_members_ibfk_2` FOREIGN KEY (`staff_id`) REFERENCES `staff` (`employee_id`) ON DELETE CASCADE;

--
-- Constraints for table `task`
--
ALTER TABLE `task`
  ADD CONSTRAINT `task_ibfk_1` FOREIGN KEY (`owner`) REFERENCES `staff` (`employee_id`) ON DELETE RESTRICT,
  ADD CONSTRAINT `task_ibfk_2` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `task_ibfk_3` FOREIGN KEY (`parent_id`) REFERENCES `task` (`task_id`) ON DELETE CASCADE;

--
-- Constraints for table `task_collaborators`
--
ALTER TABLE `task_collaborators`
  ADD CONSTRAINT `task_collaborators_ibfk_1` FOREIGN KEY (`task_id`) REFERENCES `task` (`task_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `task_collaborators_ibfk_2` FOREIGN KEY (`staff_id`) REFERENCES `staff` (`employee_id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
