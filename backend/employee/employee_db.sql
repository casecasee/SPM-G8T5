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
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


INSERT INTO `staff` (`employee_id`, `employee_name`, `email`, `department`, `role`, `password`, `team`) VALUES
(1, 'test', 'test1@gmail.com', 'Finance', 'manager', 'scrypt:32768:8:1$mtuy3ILZYT5Oo2xw$2eb0e684d977c87f6717f71a0bbf9d80eab1570be2beb2d0e647f47dd9895c0723fd6fa17d82b412f847d9c324e3ffea2a00455aef9191268bc2710b32397111', 'A'),
(2, 'test2', 'test2@gmail.com', 'Finance', 'staff', 'scrypt:32768:8:1$a0gACjpOas4zdj45$94d98382350366cc4e12c3dafb33bc3b89534c5cae74025274386bb44f9bd51ab9db0bfeaeb4e38fa05e2b204d64523a539afe648290d9713e456157041afca6', 'A');
COMMIT;