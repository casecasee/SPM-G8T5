import os
import json
import unittest
from datetime import datetime, timedelta, timezone

# Import the Task service app & models
from employee.employee import Staff
from tasks.task import app, db  # type: ignore  # relies on your project structure
from models.staff import Staff  # type: ignore
from models.task import Task  # type: ignore
from models.comment import Comment  # type: ignore
from models.comment_mention import CommentMention  # type: ignore
from models.project import Project  # type: ignore

UTC = timezone.utc

class TaskApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        # Optional guard that also helps avoid attribute refreshes (not required since we only use IDs)
        app.config["SQLALCHEMY_SESSION_OPTIONS"] = {"expire_on_commit": False}

        cls.app = app
        cls.client = app.test_client()
        with app.app_context():
            db.create_all()

            # Seed 3 users: owner (employee), collaborator (employee), manager
            owner = Staff(employee_name="Owner One", email="owner@example.com", role="staff", department="Finance", team="A", password="Test123")
            collab = Staff(employee_name="Collab Two", email="collab@example.com", role="staff", department="Finance", team="A", password="Test123")
            manager = Staff(employee_name="Manager Three", email="manager@example.com", role="manager", department="Finance", team="A", password="Test123")
            
            db.session.add_all([owner, collab, manager])
            db.session.commit()

            # seed tasks

            # Capture their IDs (primitive ints only)
            cls.owner_id = owner.employee_id
            cls.collab_id = collab.employee_id
            cls.manager_id = manager.employee_id

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            db.drop_all()

    def login_as(self, employee_id, role):
        with self.client.session_transaction() as sess:
            sess["employee_id"] = employee_id
            sess["role"] = role

    def test_create_lonely_task(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Sample Task",
            "description": "This is a sample task for testing.",
            # "owner": self.owner_id,
            "priority": 2,
            "deadline": (datetime.now(UTC) + timedelta(days=5)).replace(microsecond=0).isoformat(),
            "collaborators": [self.collab_id],
            "attachments": [],
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 201, msg=f"Create task failed: {response.status_code} {response.get_data(as_text=True)}")

    def test_create_task_status_assignment_staff(self):
        # staff creates a task, should be "ongoing" by default
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Status Test Task (Staff)",
            "description": "Testing status assignment.",
            "priority": 2,
            "deadline": (datetime.now(UTC) + timedelta(days=5)).replace(microsecond=0).isoformat(),
            "collaborators": [self.collab_id],
            "attachments": [],
        }

        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 201, msg=f"Create task failed: {response.status_code} {response.get_data(as_text=True)}")
        data = response.get_json()
        task_id = data.get("task_id")
        self.assertIsNotNone(task_id, msg="Response missing task_id")

        # Fetch the created task directly from the database to verify status
        with self.app.app_context():
            task = Task.query.get(task_id)
            self.assertIsNotNone(task, msg="Task not found in database")
            self.assertEqual(task.status, "ongoing", msg=f"Expected status 'ongoing', got '{task.status}'")
            # TODO: also check start_date is set

    def test_create_task_status_assignment_manager(self):
        # manager creates a task, should be "unassigned" by default
        self.login_as(self.manager_id, "manager")
        payload = {
            "title": "Status Test Task (Manager)",
            "description": "Testing status assignment.",
            "priority": 2,
            "deadline": (datetime.now(UTC) + timedelta(days=5)).replace(microsecond=0).isoformat(),
            "collaborators": [self.collab_id],
            "attachments": [],
        }

        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 201, msg=f"Create task failed: {response.status_code} {response.get_data(as_text=True)}")
        data = response.get_json()
        task_id = data.get("task_id")
        self.assertIsNotNone(task_id, msg="Response missing task_id")

        # Fetch the created task directly from the database to verify status
        with self.app.app_context():
            task = Task.query.get(task_id)
            self.assertIsNotNone(task, msg="Task not found in database")
            self.assertEqual(task.status, "unassigned", msg=f"Expected status 'unassigned', got '{task.status}'")

    # def test_create_task_status_assignment_director(self):
    #     # director creates a task, should be "unassigned" by default
    #     self.login_as(self.manager_id, "manager")
    #     payload = {
    #         "title": "Status Test Task",
    #         "description": "Testing status assignment.",
    #         "priority": 2,
    #         "deadline": (datetime.now(UTC) + timedelta(days=5)).replace(microsecond=0).isoformat(),
    #         "collaborators": [self.collab_id],
    #         "attachments": [],
    #     }

    #     response = self.client.post("/tasks", json=payload)
    #     self.assertEqual(response.status_code, 201, msg=f"Create task failed: {response.status_code} {response.get_data(as_text=True)}")
    #     data = response.get_json()
    #     task_id = data.get("task_id")
    #     self.assertIsNotNone(task_id, msg="Response missing task_id")

    #     # Fetch the created task directly from the database to verify status
    #     with self.app.app_context():
    #         task = Task.query.get(task_id)
    #         self.assertIsNotNone(task, msg="Task not found in database")
    #         self.assertEqual(task.status, "unassigned", msg=f"Expected status 'unassigned', got '{task.status}'")

    def test_create_task_collaborators_list(self):
        # final collaborator list should include owner
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Collaborators test task",
            "description": "Testing status assignment.",
            "priority": 2,
            "deadline": (datetime.now(UTC) + timedelta(days=5)).replace(microsecond=0).isoformat(),
            "collaborators": [self.collab_id, self.manager_id],
            "attachments": [],
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 201, msg=f"Create task failed: {response.status_code} {response.get_data(as_text=True)}")
        data = response.get_json()
        task_id = data.get("task_id")
        self.assertIsNotNone(task_id, msg="Response missing task_id")
        with self.app.app_context():
            task = Task.query.get(task_id)
            self.assertIsNotNone(task, msg="Task not found in database")
            collab_ids = {c.employee_id for c in task.collaborators}
            self.assertIn(self.owner_id, collab_ids, msg="Owner not in collaborators")
            self.assertIn(self.collab_id, collab_ids, msg="Collaborator not in collaborators")
            self.assertIn(self.manager_id, collab_ids, msg="Manager not in collaborators")

    def test_create_task_date_invalid(self):
        pass

    def test_create_task_missing_fields(self):
        # idk if frontend doing, we should do it too i guess, not a priority
        pass

    def test_status_update_unassigned_to_ongoing(self):
        # unassigned -> ongoing should set start_date
        # unassigned, ongoing, under review, done
        pass

    def test_status_update_ongoing_to_under_review(self):
        # ongoing -> under review idt anything much happens
        pass

    def test_status_update_ongoing_to_done(self):
        # ongoing -> done should set completed_date
        pass

    def test_status_update_ongoing_to_done(self):
        # ongoing -> done should set completed_date
        pass

    def test_status_update_unassigned_to_under_review(self):
        # how would this even work? is it possible? KIV
        pass

    def test_status_update_unassigned_to_done(self):
        # TODO: idk
        pass

    def test_status_update_invalid_new_status(self):
        # dont think its an issue cuz frontend dropdown
        pass

    def test_status_update_task_not_found(self):
        # dont think its an issue cuz card will not exist, but error checking is implemented already
        pass

    def test_status_update_employee_not_collaborator(self):
        pass

    def test_metadata_update_by_owner(self):
        pass

    def test_metadata_update(self):
        pass

    def test_assign_tasks(self):
        pass

    











































































    

    # # ---------- helpers (API-only flow) ----------

    # def _login_as(self, employee_id, role):
    #     """Simulate login by setting session keys (no password/hash dependency)."""
    #     with self.client.session_transaction() as sess:
    #         sess["employee_id"] = employee_id
    #         sess["role"] = role

    # def _logout(self):
    #     with self.client.session_transaction() as sess:
    #         sess.clear()

    # def _iso_deadline(self, days=7):
    #     return (datetime.now(UTC) + timedelta(days=days)).replace(microsecond=0).isoformat()

    # def _create_task(self, owner_id=None, collaborators=None, title="Write docs"):
    #     if owner_id is None:
    #         owner_id = self.owner_id
    #     if collaborators is None:
    #         collaborators = [self.collab_id]

    #     payload = {
    #         "title": title,
    #         "description": "Do the docs",
    #         "owner": owner_id,
    #         "priority": 3,
    #         "deadline": self._iso_deadline(7),
    #         "collaborators": collaborators,
    #         "attachments": [],
    #         "parent_id": None,
    #         "project_id": None,
    #     }
    #     r = self.client.post("/tasks", json=payload)
    #     self.assertEqual(r.status_code, 201, msg=f"Create task failed: {r.status_code} {r.get_data(as_text=True)}")
    #     data = r.get_json()
    #     self.assertIn("task_id", data)
    #     return data["task_id"]

    # def _get_task(self, task_id):
    #     r = self.client.get(f"/task/{task_id}")
    #     self.assertEqual(r.status_code, 200, msg=r.get_data(as_text=True))
    #     return r.get_json()

    # # ---------- tests (API only) ----------

    # def test_status_patch_by_collaborator(self):
    #     # owner creates task
    #     self._login_as(self.owner_id, "staff")
    #     task_id = self._create_task(owner_id=self.owner_id, collaborators=[self.collab_id])
    #     self._logout()

    #     # collaborator moves to ongoing
    #     self._login_as(self.collab_id, "staff")
    #     r1 = self.client.patch(f"/task/status/{task_id}", json={"status": "ongoing"})
    #     self.assertEqual(r1.status_code, 200, msg=r1.get_data(as_text=True))

    #     t1 = self._get_task(task_id)
    #     self.assertEqual(t1["status"], "ongoing")
    #     self.assertIsNotNone(t1.get("start_date"))

    #     # collaborator marks done
    #     r2 = self.client.patch(f"/task/status/{task_id}", json={"status": "done"})
    #     self.assertEqual(r2.status_code, 200, msg=r2.get_data(as_text=True))

    #     t2 = self._get_task(task_id)
    #     self.assertEqual(t2["status"], "done")
    #     self.assertIsNotNone(t2.get("completed_date"))
    #     self._logout()

    # def test_status_patch_forbidden_if_not_collaborator(self):
    #     self._login_as(self.owner_id, "employee")
    #     task_id = self._create_task(owner_id=self.owner_id, collaborators=[self.collab_id])
    #     self._logout()

    #     # Login as a non-collaborator (manager OR create another employee)
    #     self._login_as(self.manager_id, "manager")
    #     r = self.client.patch(f"/task/status/{task_id}", json={"status": "ongoing"})
    #     self.assertIn(r.status_code, (401, 403), msg=f"Expected 401/403, got {r.status_code}: {r.get_data(as_text=True)}")
    #     self._logout()

    # def test_update_task_metadata_by_owner(self):
    #     self._login_as(self.owner_id, "employee")
    #     task_id = self._create_task(owner_id=self.owner_id, collaborators=[self.collab_id])

    #     payload = {
    #         "title": "Docs v2",
    #         "description": "Tighten docs",
    #         "priority": 2,
    #         "deadline": self._iso_deadline(14),
    #         "attachments": ["spec.pdf", "diagram.png"],
    #         "collaborators": [self.collab_id],  # ensure owner stays included on server-side
    #     }
    #     r = self.client.put(f"/task/{task_id}", json=payload)
    #     self.assertEqual(r.status_code, 200, msg=r.get_data(as_text=True))

    #     t = self._get_task(task_id)
    #     self.assertEqual(t["title"], "Docs v2")
    #     self.assertEqual(t["priority"], 2)
    #     self.assertEqual(t["attachments"], ["spec.pdf", "diagram.png"])
    #     # owner should still be owner
    #     self.assertEqual(t["owner"], self.owner_id)
    #     # collaborators reflect payload (owner is not duplicated here unless API returns all assignees)
    #     self._logout()

    # def test_non_owner_cannot_update_task(self):
    #     self._login_as(self.owner_id, "employee")
    #     task_id = self._create_task(owner_id=self.owner_id, collaborators=[self.collab_id])
    #     self._logout()

    #     self._login_as(self.collab_id, "employee")
    #     r = self.client.put(f"/task/{task_id}", json={"title": "Nope from collab"})
    #     self.assertIn(r.status_code, (401, 403), msg=f"Expected 401/403, got {r.status_code}: {r.get_data(as_text=True)}")
    #     self._logout()

    # def test_manager_can_reassign_owner(self):
    #     # Create task with owner=self.owner_id
    #     self._login_as(self.owner_id, "employee")
    #     task_id = self._create_task(owner_id=self.owner_id, collaborators=[self.collab_id])
    #     self._logout()

    #     # Manager reassigns to collaborator
    #     self._login_as(self.manager_id, "manager")
    #     r1 = self.client.put(f"/task/{task_id}", json={"owner": self.collab_id})
    #     self.assertEqual(r1.status_code, 200, msg=r1.get_data(as_text=True))

    #     t1 = self._get_task(task_id)
    #     self.assertEqual(t1["owner"], self.collab_id)

    #     # Manager tries to set unknown owner
    #     r2 = self.client.put(f"/task/{task_id}", json={"owner": 999999})
    #     # Your API might return 404 or 400; assert one of them
    #     self.assertIn(r2.status_code, (400, 404), msg=f"Expected 400/404, got {r2.status_code}: {r2.get_data(as_text=True)}")
    #     self._logout()

    # def test_comment_requires_auth_and_content(self):
    #     self._login_as(self.owner_id, "employee")
    #     task_id = self._create_task()
    #     self._logout()

    #     # No auth
    #     r1 = self.client.post(f"/task/{task_id}/comments", json={"content": "Hello"})
    #     self.assertIn(r1.status_code, (401, 403), msg=f"Expected 401/403, got {r1.status_code}")

    #     # With auth but missing content
    #     self._login_as(self.owner_id, "employee")
    #     r2 = self.client.post(f"/task/{task_id}/comments", json={})
    #     self.assertEqual(r2.status_code, 400, msg=r2.get_data(as_text=True))
    #     self._logout()

    # def test_comment_invalid_id_mention_rejected(self):
    #     self._login_as(self.owner_id, "employee")
    #     task_id = self._create_task()
    #     self._logout()

    #     self._login_as(self.collab_id, "employee")
    #     r = self.client.post(f"/task/{task_id}/comments", json={"content": "Ping @99999"})
    #     # Expect 400 per your spec
    #     self.assertEqual(r.status_code, 400, msg=r.get_data(as_text=True))
    #     self._logout()

    # def test_list_mentionable(self):
        # self._login_as(self.owner_id, "employee")
        # task_id = self._create_task(owner_id=self.owner_id, collaborators=[self.collab_id])

        # r = self.client.get(f"/task/{task_id}/mentionable")
        # self.assertEqual(r.status_code, 200, msg=r.get_data(as_text=True))
        # data = r.get_json()
        # # Expect owner + collaborators
        # id_set = {x["employee_id"] if isinstance(x, dict) else x for x in data}
        # self.assertIn(self.owner_id, id_set)
        # self.assertIn(self.collab_id, id_set)
        # self._logout()


if __name__ == "__main__":
    unittest.main()