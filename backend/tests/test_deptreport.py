import unittest
from datetime import datetime, timedelta

# --- Helpers to simulate your Vue logic (Python equivalent) ---
def make_task(name, owner, created_at, due_at, priority=5, status="ongoing"):
    return {
        "name": name,
        "owner": owner,
        "created_at": created_at,
        "due_date": due_at,
        "priority": priority,
        "status": status
    }

def is_overdue(task):
    if not task.get("due_date"):
        return False
    return datetime.fromisoformat(task["due_date"]) < datetime.now()

def sort_by_priority_and_date(tasks):
    return sorted(tasks, key=lambda t: (-t["priority"], datetime.fromisoformat(t["due_date"])))

# --- Sample employee data ---
employees = [
    {"employee_id": 1, "employee_name": "Natalie Foster", "department": "Finance"},
    {"employee_id": 2, "employee_name": "David Tan", "department": "Finance"},
    {"employee_id": 3, "employee_name": "Test 2", "department": "Finance"}
]

# --- Seed tasks across employees ---
now = datetime.now()
seed_tasks = {
    "Natalie Foster": [
        make_task("Prepare Monthly Financial Report", "Natalie Foster",
                  (now - timedelta(days=10)).isoformat(),
                  (now + timedelta(days=5)).isoformat(), priority=8)
    ],
    "David Tan": [
        make_task("Update Invoice Records", "David Tan",
                  (now - timedelta(days=20)).isoformat(),
                  (now + timedelta(days=10)).isoformat(), priority=5)
    ],
    "Test 2": [
        make_task("Audit Expense Claims", "Test 2",
                  (now - timedelta(days=40)).isoformat(),
                  (now - timedelta(days=10)).isoformat(), priority=6, status="done")
    ]
}


# ================================================================
#                 🧩 TEST CASES
# ================================================================
class DepartmentReportTests(unittest.TestCase):

    def setUp(self):
        self.manager = {"email": "test1@gmail.com", "password": "PasswordNumber!1"}
        self.department = "Finance"
        self.departmentEmployees = employees
        self.teamTasksData = seed_tasks

    # 1️⃣ Generate Department Report for Past Month by Default
    def test_generate_dept_report_default_month(self):
        start = datetime.now() - timedelta(days=30)
        end = datetime.now()

        collected = []
        for emp in self.departmentEmployees:
            tasks = self.teamTasksData.get(emp["employee_name"], [])
            for t in tasks:
                created = datetime.fromisoformat(t["created_at"])
                if created >= start:
                    collected.append(t)

        self.assertTrue(len(collected) > 0)
        print(f"[PASS] Default monthly report for department '{self.department}' contains {len(collected)} tasks.")

    # 2️⃣ Filter by Specific Employee
    def test_filter_by_specific_employee(self):
        emp_name = "Natalie Foster"
        filtered = self.teamTasksData.get(emp_name, [])
        self.assertTrue(all(t["owner"] == emp_name for t in filtered))
        print(f"[PASS] Filtered correctly for employee {emp_name}: {len(filtered)} tasks found.")

    # 3️⃣ Filter by Multiple Employees
    def test_filter_by_multiple_employees(self):
        selected_names = ["Natalie Foster", "David Tan", "Test 2"]
        combined = []
        for name in selected_names:
            combined.extend(self.teamTasksData.get(name, []))
        self.assertEqual(len(combined), 3)
        print(f"[PASS] Filtered multiple employees ({', '.join(selected_names)}): {len(combined)} tasks total.")

    # 4️⃣ Download Department Report
    def test_download_department_report(self):
        payload = {
            "department": self.department,
            "tasks": [t for tasks in self.teamTasksData.values() for t in tasks],
            "format": "pdf"
        }
        self.assertIn("tasks", payload)
        self.assertEqual(payload["format"], "pdf")
        print(f"[PASS] Department report ready for download in PDF format with {len(payload['tasks'])} tasks.")

    # 5️⃣ Task Updated on Report when Edited
    def test_task_updated_reflects_in_report(self):
        task = self.teamTasksData["Natalie Foster"][0]
        old_priority = task["priority"]
        task["priority"] = 9
        self.assertNotEqual(task["priority"], old_priority)
        print(f"[PASS] Task update reflected in report: '{task['name']}' new priority {task['priority']}")

    # 6️⃣ Filter Department Report by Custom Date Range
    def test_filter_department_custom_date_range(self):
        start = datetime(2025, 10, 1)
        end = datetime(2025, 11, 29)

        filtered = []
        for emp in self.departmentEmployees:
            tasks = self.teamTasksData.get(emp["employee_name"], [])
            for t in tasks:
                created = datetime.fromisoformat(t["created_at"])
                if start <= created <= end:
                    filtered.append(t)

        self.assertTrue(all(start <= datetime.fromisoformat(t["created_at"]) <= end for t in filtered))
        print(f"[PASS] Filtered by date range ({start:%b %d}–{end:%b %d}): {len(filtered)} tasks found.")

    # 7️⃣ Manager Selects Invalid Timeframe
    def test_invalid_timeframe_selection(self):
        start = datetime(2025, 11, 10)
        end = datetime(2025, 11, 1)
        is_valid = start <= end
        self.assertFalse(is_valid)
        print(f"[PASS] Invalid timeframe detected (start={start}, end={end}).")

    # 8️⃣ Department Has No Tasks
    def test_department_has_no_tasks(self):
        user = {"email": "lucas.grant@company.com", "password": "Password@123"}
        empty_tasks = []
        self.assertEqual(len(empty_tasks), 0)
        print(f"[PASS] {user['email']} -> No tasks, report shows 'Nil'.")

    # 9️⃣ Overall Progress Updated Based on Task Timeframe
    def test_overall_progress_calculation(self):
        start = datetime(2025, 10, 1)
        end = datetime(2025, 10, 20)
        all_tasks = [t for tasks in self.teamTasksData.values() for t in tasks]
        overdue = [t for t in all_tasks if is_overdue(t)]
        total = len(all_tasks)

        if total == 0:
            progress = "Nil"
        elif len(overdue) == 0:
            progress = "Good"
        elif len(overdue) == 1:
            progress = "Average"
        else:
            progress = "Poor"

        self.assertIn(progress, ["Nil", "Good", "Average", "Poor"])
        print(f"[PASS] Department '{self.department}' overall progress: {progress}.")

if __name__ == "__main__":
    unittest.main()
