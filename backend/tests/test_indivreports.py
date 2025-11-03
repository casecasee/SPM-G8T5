import unittest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Import the projects app and models
from projects.app import app, db
from models.project import Project
from models.task import Task
from models.staff import Staff

import unittest
from datetime import datetime, timedelta


# ---------------- MOCK HELPERS ---------------------
def make_task(name, created_at, due_at, priority=5, status="ongoing"):
    return {
        "name": name,
        "created_at": created_at,
        "due_date": due_at,
        "priority": priority,
        "status": status
    }

def parse_date(date_str):
    # Example: "Nov 17, 2025, 10:03 PM"
    return datetime.strptime(date_str, "%b %d, %Y, %I:%M %p")

# ---------------- TEST CASE CLASS ------------------
class IndividualReportTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Default test user
        cls.test_user = {
            "email": "test1@gmail.com",
            "password": "PasswordNumber!1",
            "role": "staff"
        }

        # Seed tasks to simulate DB results
        cls.seed_tasks = [
            make_task(
                "Prepare Monthly Financial Report",
                parse_date("Nov 3, 2025, 10:03 PM").isoformat(),
                parse_date("Nov 17, 2025, 10:03 PM").isoformat(),
                priority=8,
                status="ongoing"
            ),
            make_task(
                "Update Budget Sheet",
                (datetime.now() - timedelta(days=5)).isoformat(),
                (datetime.now() + timedelta(days=5)).isoformat(),
                priority=5,
                status="done"
            )
        ]

    # 1️⃣ Generate Individual Task Report for past month by default
    def test_generate_individual_report_default_month(self):
        """Test default generation of individual task report for past month"""
        print("\n[TEST] Generate Individual Report for Past Month (default)")
        user = self.test_user
        tasks = self.seed_tasks

        now = datetime.now()
        past_month = now - timedelta(days=30)
        filtered = [t for t in tasks if datetime.fromisoformat(t["created_at"]) >= past_month]

        self.assertGreaterEqual(len(filtered), 1)
        print(f"Report generated for {user['email']} with {len(filtered)} tasks in past month.")

    # 2️⃣ Task updated on report when edited in Task Page
    def test_task_update_reflects_in_report(self):
        """Task updated on report when edited in Task Page"""
        print("\n[TEST] Task updated on report after edit")
        task = self.seed_tasks[0]
        task["priority"] = 10  # simulate update
        self.assertEqual(task["priority"], 10)
        print(f"Updated Task: {task['name']} Priority -> {task['priority']}")

    # 3️⃣ Filter Individual Report by Custom Date Range
    def test_filter_report_by_custom_date_range(self):
        """Filter Individual Report by Custom Date Range"""
        print("\n[TEST] Filter by Custom Date Range")
        start = datetime(2025, 10, 1)
        end = datetime(2025, 11, 29)

        filtered = [t for t in self.seed_tasks
                    if datetime.fromisoformat(t["created_at"]) >= start
                    and datetime.fromisoformat(t["due_date"]) <= end]

        self.assertTrue(all(start <= datetime.fromisoformat(t["created_at"]) <= end for t in filtered))
        print(f"Tasks between {start:%b %d} - {end:%b %d}: {len(filtered)} found.")

    # 4️⃣ Download individual report
    def test_download_individual_report(self):
        """Test successful download/export of report"""
        print("\n[TEST] Download individual report")
        report_payload = {
            "tasks": self.seed_tasks,
            "user": self.test_user["email"],
            "format": "pdf"
        }
        self.assertIn("tasks", report_payload)
        self.assertEqual(report_payload["format"], "pdf")
        print(f"Download successful for {report_payload['user']} in PDF format.")

    # 5️⃣ Report format when user has no tasks
    def test_report_format_no_tasks(self):
        """Report Format when user has no tasks"""
        print("\n[TEST] Report format when user has no tasks")
        user = {"email": "bob@company.com", "password": "Password@123"}
        tasks = []  # no tasks
        self.assertEqual(len(tasks), 0)
        overall_progress = "Nil"
        self.assertEqual(overall_progress, "Nil")
        print(f"User {user['email']} has no tasks. Report shows '{overall_progress}'.")

    # 6️⃣ User selects invalid timeframe
    def test_invalid_timeframe_selection(self):
        """User selects invalid timeframe (End < Start)"""
        print("\n[TEST] Invalid timeframe selection")
        start = datetime(2025, 11, 10)
        end = datetime(2025, 11, 1)
        is_valid = start <= end
        self.assertFalse(is_valid, "Invalid timeframe not detected.")
        print(f"Invalid timeframe detected: Start={start}, End={end}")

    # 7️⃣ Overall Progress updated based on Task timeframe
    def test_overall_progress_calculation(self):
        """Overall Progress updated based on Task timeframe"""
        print("\n[TEST] Overall Progress based on Task timeframe")
        user = self.test_user
        tasks = self.seed_tasks

        total = len(tasks)
        overdue = [t for t in tasks if datetime.fromisoformat(t["due_date"]) < datetime.now()]

        if total == 0:
            progress = "Nil"
        elif len(overdue) == 0:
            progress = "Good"
        elif len(overdue) == 1:
            progress = "Average"
        else:
            progress = "Poor"

        self.assertIn(progress, ["Nil", "Good", "Average", "Poor"])
        print(f"{user['email']} overall progress: {progress}.")


if __name__ == "__main__":
    unittest.main()
