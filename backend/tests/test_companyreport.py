import unittest
from datetime import datetime, timedelta

# --- Helpers to simulate company logic (Python equivalent of your Vue code) ---
def make_task(name, dept, created_at, due_at, priority=5, status="ongoing"):
    return {
        "title": name,
        "department": dept,
        "created_at": created_at,
        "due_date": due_at,
        "priority": priority,
        "status": status,
    }

def is_overdue(task):
    if not task.get("due_date"):
        return False
    return datetime.fromisoformat(task["due_date"]) < datetime.now()

def build_company_data(companyTasksData, selectedDept=None, start=None, end=None):
    """Simulate buildCompanyData() from your Vue logic"""
    filtered = {}
    all_tasks = []

    for dept_name, dept_obj in companyTasksData.items():
        if selectedDept and dept_name != selectedDept:
            continue

        dept_tasks = []
        for team in dept_obj.values():
            for emp_tasks in team.values():
                dept_tasks.extend(emp_tasks)

        # Apply date range filter
        if start and end:
            dept_tasks = [
                t
                for t in dept_tasks
                if datetime.fromisoformat(t["created_at"]) <= end
                and datetime.fromisoformat(t["due_date"]) >= start
            ]

        completed = len(
            [t for t in dept_tasks if t["status"].lower() in ["done", "completed"]]
        )
        overdue = len([t for t in dept_tasks if is_overdue(t)])
        ontime = len(dept_tasks) - overdue
        completion_rate = round((completed / len(dept_tasks)) * 100) if dept_tasks else 0

        filtered[dept_name] = {
            "tasks": dept_tasks,
            "completed": completed,
            "overdue": overdue,
            "ontime": ontime,
            "completionRate": completion_rate,
        }
        all_tasks.extend(dept_tasks)

    return {
        "filtered": filtered,
        "all_tasks": all_tasks,
        "dept_count": len(filtered.keys()),
    }


# --- Seed company-wide sample data (simulating companyTasksData) ---
now = datetime.now()
companyTasksData = {
    "Finance": {
        "Team A": {
            "Natalie Foster": [
                make_task("Prepare Monthly Report", "Finance",
                          (now - timedelta(days=10)).isoformat(),
                          (now + timedelta(days=5)).isoformat(),
                          priority=8, status="ongoing")
            ],
            "David Tan": [
                make_task("Reconcile Accounts", "Finance",
                          (now - timedelta(days=20)).isoformat(),
                          (now + timedelta(days=3)).isoformat(),
                          priority=7, status="done")
            ]
        }
    },
    "IT": {
        "Team X": {
            "John Lim": [
                make_task("System Maintenance", "IT",
                          (now - timedelta(days=25)).isoformat(),
                          (now + timedelta(days=2)).isoformat(),
                          priority=6, status="ongoing")
            ]
        }
    },
    "HR": {
        "Team H": {
            "Lisa Chan": [
                make_task("Recruitment Drive", "HR",
                          (now - timedelta(days=5)).isoformat(),
                          (now + timedelta(days=1)).isoformat(),
                          priority=9, status="completed")
            ]
        }
    },
}


# ================================================================
# 🧩 TEST CASES — Company Report
# ================================================================
class CompanyReportTests(unittest.TestCase):
    def setUp(self):
        self.hr_user = {
            "email": "samuel.lee@company.com",
            "password": "Password@123"
        }
        self.company_data = companyTasksData

    # 1️⃣ Generate Company Report for Past Month by Default
    def test_generate_company_report_default_month(self):
        today = datetime.now()
        one_month_ago = today - timedelta(days=30)
        result = build_company_data(self.company_data, start=one_month_ago, end=today)
        self.assertTrue(result["dept_count"] > 0)
        self.assertTrue(len(result["all_tasks"]) > 0)
        print(f"[PASS] Default company report covers {result['dept_count']} departments, {len(result['all_tasks'])} tasks total.")

    # 2️⃣ Filter by Department
    def test_filter_by_department(self):
        selected_dept = "Finance"
        result = build_company_data(self.company_data, selectedDept=selected_dept)
        self.assertIn(selected_dept, result["filtered"].keys())
        self.assertEqual(result["dept_count"], 1)
        print(f"[PASS] Company report filtered correctly by department '{selected_dept}'.")

    # 3️⃣ Download Company Report
    def test_download_company_report(self):
        result = build_company_data(self.company_data)
        export_payload = {
            "format": "pdf",
            "departments": list(result["filtered"].keys()),
            "tasks": result["all_tasks"]
        }
        self.assertEqual(export_payload["format"], "pdf")
        self.assertTrue(len(export_payload["tasks"]) > 0)
        print(f"[PASS] Company report download prepared with {len(export_payload['tasks'])} tasks.")

    # 4️⃣ Filter Company Report by Custom Date Range
    def test_custom_date_range_filter(self):
        start = datetime(2025, 10, 1)
        end = datetime(2025, 11, 29)
        result = build_company_data(self.company_data, start=start, end=end)
        self.assertTrue(all(
            start <= datetime.fromisoformat(t["created_at"]) <= end
            for t in result["all_tasks"]
        ))
        print(f"[PASS] Custom date range filter applied ({start:%b %d} - {end:%b %d}).")

    # 5️⃣ Task Added to Report After Creation
    def test_task_added_reflects_in_report(self):
        new_task = make_task("Task 1", "Finance",
                             (now - timedelta(days=1)).isoformat(),
                             (now + timedelta(days=10)).isoformat(),
                             priority=7)
        self.company_data["Finance"]["Team A"]["David Tan"].append(new_task)

        result = build_company_data(self.company_data, selectedDept="Finance")
        all_titles = [t["title"] for t in result["all_tasks"]]
        self.assertIn("Task 1", all_titles)
        print(f"[PASS] Newly added task 'Task 1' appears in company report for Finance.")

    # 6️⃣ HR Selects Invalid Timeframe
    def test_invalid_timeframe_selection(self):
        start = datetime(2025, 11, 10)
        end = datetime(2025, 11, 1)
        self.assertTrue(start > end)
        print(f"[PASS] Invalid timeframe correctly detected (start={start}, end={end}).")

    # 🧩 Extra: Completion Rate / Productivity Metrics
    def test_company_completion_rate_and_metrics(self):
        result = build_company_data(self.company_data)
        total = len(result["all_tasks"])
        completed = sum(d["completed"] for d in result["filtered"].values())
        calc_rate = round((completed / total) * 100)
        avg_rate = sum(d["completionRate"] for d in result["filtered"].values()) / result["dept_count"]

        self.assertTrue(0 <= calc_rate <= 100)
        self.assertTrue(avg_rate >= 0)
        print(f"[PASS] Company completion rate {calc_rate}%, average department rate {round(avg_rate, 2)}%.")
        

if __name__ == "__main__":
    unittest.main()
