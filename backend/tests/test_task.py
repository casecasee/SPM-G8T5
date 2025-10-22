import os
import json
import unittest
from datetime import datetime, timedelta, timezone
import zoneinfo

# Import the Task service app & models
from employee.employee import Staff
from tasks.task import app, db  # type: ignore  # relies on your project structure
from models.staff import Staff  # type: ignore
from models.task import Task  # type: ignore
from models.comment import Comment  # type: ignore
from models.comment_mention import CommentMention  # type: ignore
from models.project import Project  # type: ignore

UTC = timezone.utc

def generate_deadline(days_ahead=5):
    deadline = (datetime.now(UTC) + timedelta(days=days_ahead)) \
        .replace(microsecond=0) \
        .isoformat() \
        .replace("+00:00", "Z")
    return deadline


def datetime_now():
    # replace 'America/New_York' with your actual IANA timezone name
    local_tz = zoneinfo.ZoneInfo("America/New_York")

    dt = datetime.now(local_tz)
    return dt


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
            different_dept = Staff(employee_name="Other Dept", email="other@example.com", role="staff", department="IT", team="B", password="Test123")

            db.session.add_all([owner, collab, manager, different_dept])
            db.session.commit()

            # seed tasks

            # Capture their IDs (primitive ints only)
            cls.owner_id = owner.employee_id
            cls.collab_id = collab.employee_id
            cls.manager_id = manager.employee_id
            cls.different_dept_id = different_dept.employee_id

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            db.drop_all()

    def login_as(self, employee_id, role):
        with self.client.session_transaction() as sess:
            sess["employee_id"] = employee_id
            sess["role"] = role
            sess["department"] = "Finance"
            sess["team"] = "A"

# ------------------------ CREATE TASKS TESTS --------------------------------------------------------

    def test_create_lonely_task(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Sample Task",
            "description": "This is a sample task for testing.",
            # "owner": self.owner_id,
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 201, msg=f"Create task failed: {response.status_code} {response.get_data(as_text=True)}")

    # test title empty
    def test_create_task_title_empty(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "",
            "description": "This is a sample task with empty title.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for empty title, got {response.status_code}")

        # test string with spaces too
        payload["title"] = "     "
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for empty title with spaces, got {response.status_code}")

    # test description empty
    def test_create_task_description_empty(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Task with empty description",
            "description": "",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for empty description, got {response.status_code}")

        # test string with spaces too
        payload["description"] = "     "
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for empty description with spaces, got {response.status_code}")

    # test deadline past
    def test_create_task_deadline_past(self):
        self.login_as(self.owner_id, "staff")
        past_deadline = generate_deadline(days_ahead=-1)
        payload = {
            "title": "Task with past deadline",
            "description": "This task has a past deadline.",
            "priority": 2,
            "deadline": past_deadline,
            "collaborators": [self.collab_id],
            "attachments": [],
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for past deadline, got {response.status_code}")

    # test deadline wrong format ?
    def test_create_task_deadline_wrong_format(self):
        self.login_as(self.owner_id, "staff")
        wrong_format_deadline = "2023/10/10 10:00:00"  # incorrect format
        payload = {
            "title": "Task with wrong format deadline",
            "description": "This task has a wrongly formatted deadline.",
            "priority": 2,
            "deadline": wrong_format_deadline,
            "collaborators": [self.collab_id],
            "attachments": [],
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for wrongly formatted deadline, got {response.status_code}")

    def test_create_task_status_assignment_staff(self):
        # staff creates a task, should be "ongoing" by default
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Status Test Task (Staff)",
            "description": "Testing status assignment.",
            "priority": 2,
            "deadline": generate_deadline(),
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
            "deadline": generate_deadline(),
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

    def test_create_task_status_assignment_director(self):
        # director creates a task, should be "unassigned" by default
        self.login_as(self.manager_id, "manager")
        payload = {
            "title": "Status Test Task",
            "description": "Testing status assignment.",
            "priority": 2,
            "deadline": generate_deadline(),
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

    # test priority invalid (out of range, non-int)
    def test_create_task_priority_invalid(self):
        self.login_as(self.owner_id, "staff")
        # test out of range
        payload = {
            "title": "Task with invalid priority",
            "description": "This task has an invalid priority.",
            "priority": 11,  # invalid priority
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for out of range priority, got {response.status_code}")

        # test non-int
        payload["priority"] = "high"  # invalid priority
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for non-integer priority, got {response.status_code}")

    # test project id (project does not exist)
    def test_create_task_project_id_invalid(self):
        # need to seed projects first
        pass 

    # test creator is set as owner
    def test_create_task_creator_set_as_owner(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Owner Test Task",
            "description": "Testing owner assignment.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
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
            # task.owner is a Staff object, need to get employee_id
            self.assertEqual(task.owner, self.owner_id, msg=f"Expected owner_id '{self.owner_id}', got '{task.owner}'")

    # test collaborators list for lonely tasks (collaborators must be same dept), must include owner
    def test_create_task_collaborators_lonely_task(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Collaborators Test Task",
            "description": "Testing collaborators assignment.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id, self.different_dept_id],
            "attachments": [],
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for collaborator from different department, got {response.status_code}")

    # test collaborators list for project tasks (project members only), must include owner
    def test_create_task_collaborators_project_task(self):
        # Need to seed a project first
        pass

    # test collaborators list for invalid ids
    def test_create_task_collaborators_invalid_ids(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Invalid Collaborators Test Task",
            "description": "Testing invalid collaborators assignment.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [999999],  # non-existent employee_id
            "attachments": [],
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 404, msg=f"Expected 400 for invalid collaborator IDs, got {response.status_code}")

    # test attachments ?

    # test comments ?

    # test recurrence ?

    # test subtasks title
    def test_create_subtask_title_empty(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "",
            "description": "Testing subtask with empty title.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
            "subtasks": [{
                "title": "",
                "description": "This is a subtask with empty title.",
                "priority": 2,
                "deadline": generate_deadline(),
                "collaborators": [self.collab_id],
                "attachments": [],
            }]
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for subtask with empty title, got {response.status_code}")

        # test string with spaces too
        payload["subtasks"][0]["title"] = "     "
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for subtask with empty title with spaces, got {response.status_code}")

    # test subtask desc
    def test_create_subtask_description_empty(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Task with Subtask",
            "description": "Testing subtask with empty description.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
            "subtasks": [{
                "title": "Subtask with empty description",
                "description": "",
                "priority": 2,
                "deadline": generate_deadline(),
                "collaborators": [self.collab_id],
                "attachments": [],
            }]
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for subtask with empty description, got {response.status_code}")

        # test string with spaces too
        payload["subtasks"][0]["description"] = "     "
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for subtask with empty description with spaces, got {response.status_code}")
     
    # test subtask deadline past
    def test_create_subtask_deadline_past(self):
        self.login_as(self.owner_id, "staff")
        past_deadline = generate_deadline(days_ahead=-1)
        payload = {
            "title": "Subtask with Past Deadline",
            "description": "Testing subtask with past deadline.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
            "subtasks": [{
                "title": "Subtask with Past Deadline",
                "description": "Testing subtask with past deadline.",
                "priority": 2,
                "deadline": past_deadline,
                "collaborators": [self.collab_id],
                "attachments": [],
            }]
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for subtask with past deadline, got {response.status_code}")

    # test subtask deadline wrong format
    def test_create_subtask_deadline_wrong_format(self):
        self.login_as(self.owner_id, "staff")
        wrong_format_deadline = "2023/10/10 10:00:00"  # incorrect format
        payload = {
            "title": "Subtask with Wrong Format Deadline",
            "description": "Testing subtask with wrongly formatted deadline.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
            "subtasks": [{
                "title": "Subtask with Wrong Format Deadline",
                "description": "Testing subtask with wrongly formatted deadline.",
                "priority": 2,
                "deadline": wrong_format_deadline,
                "collaborators": [self.collab_id],
                "attachments": [],
            }]
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for subtask with wrongly formatted deadline, got {response.status_code}")

    # test subtask owner (can be chosen, must be subset of parent collaborators)
    def test_create_subtask_owner_assignment(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Task with Subtask Owner",
            "description": "Testing subtask owner assignment.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
            "subtasks": [{
                "title": "Subtask with specific owner",
                "description": "This subtask has a specific owner.",
                "priority": 2,
                "deadline": generate_deadline(),
                "collaborators": [self.collab_id],
                "attachments": [],
                # specify owner as collab_id
                "owner": self.collab_id,
            }]
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 201, msg=f"Create task with subtask owner failed: {response.status_code} {response.get_data(as_text=True)}")
        data = response.get_json()
        task_id = data.get("task_id")
        self.assertIsNotNone(task_id, msg="Response missing task_id")

        # Fetch the created subtask directly from the database to verify owner
        with self.app.app_context():
            task = Task.query.get(task_id)
            self.assertIsNotNone(task, msg="Task not found in database")
            # self.assertEqual(len(task.subtasks), 1, msg="Expected 1 subtask")
            subtask = task.subtasks[0]
            self.assertEqual(subtask.owner, self.collab_id, msg=f"Expected subtask owner '{self.collab_id}', got '{subtask.owner}'")

    # test subtask status (staff/manager/director)


    # test subtask priority invalid (out of range, non-int)
    def test_create_subtask_priority_invalid(self):
        self.login_as(self.owner_id, "staff")
        # test out of range
        payload = {
            "title": "Task with Subtask",
            "description": "Testing subtask with invalid priority.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
            "subtasks": [{
                "title": "Subtask with invalid priority",
                "description": "This subtask has an invalid priority.",
                "priority": 11,  # invalid priority
                "deadline": generate_deadline(),
                "collaborators": [self.collab_id],
                "attachments": [],
            }]
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for subtask with out of range priority, got {response.status_code}")

        # test non-int
        payload["subtasks"][0]["priority"] = "high"  # invalid priority
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for subtask with non-integer priority, got {response.status_code}")

    # test subtask project id (should inherit from parent)
    def test_create_subtask_project_id_inherit(self):
        # Need to seed a project first
        pass

    # test subtask collaborators (must be subset of parent collaborators)
    def test_create_subtask_collaborators_subset(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Task with Subtask",
            "description": "Testing subtask collaborators assignment.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
            "subtasks": [{
                "title": "Subtask with invalid collaborators",
                "description": "This subtask has collaborators not in parent task.",
                "priority": 2,
                "deadline": generate_deadline(),
                "collaborators": [self.manager_id],  # not in parent collaborators
                "attachments": [],
            }]
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for subtask with collaborators not in parent task, got {response.status_code}")

    # test subtask attachments ?

    # test subtask comments ?

    # test subtask recurrence ? (subtasks cannot be recurrent)



# ----------------------------------------------------------------------------------------------------------


# ------------------------ UPDATE TASKS STATUS TESTS --------------------------------------------------------

    def update_task_status_task_not_found(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "status": "ongoing"}
        response = self.client.patch("/task/status/999999", json=payload)
        self.assertEqual(response.status_code, 404, msg=f"Expected 404 for non-existent task, got {response.status_code}")

    def test_status_update_unassigned_to_ongoing(self):
        # unassigned -> ongoing should set start_date
        # unassigned, ongoing, under review, done

        self.login_as(self.manager_id, "manager")
        payload = {
            "title": "Status Update Test Task (unassigned to ongoing)",
            "description": "Testing status update from unassigned to ongoing.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
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
            self.assertEqual(task.status, "unassigned", msg=f"Expected status 'unassigned', got '{task.status}'")
        self.login_as(self.collab_id, "staff")

        payload = {
            "status": "ongoing"}
        response = self.client.patch(f"/task/status/{task_id}", json=payload)
        self.assertEqual(response.status_code, 200, msg=f"Status update failed: {response.status_code} {response.get_data(as_text=True)}")
        data = response.get_json()
        with self.app.app_context():
            task = Task.query.get(task_id)
            # check start date is almost now
            self.assertIsNotNone(task.start_date, msg="start_date not set on status update to ongoing")
            now = datetime.now(UTC)
            # startdate = task.start_date
            self.assertTrue((now - task.start_date.replace(tzinfo=UTC)).total_seconds() < 10, msg="start_date not set correctly on status update to ongoing")

    def test_status_update_ongoing_to_under_review(self):
        # ongoing -> under review idt anything much happens

        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Status Update Test Task (ongoing to under review)",
            "description": "Testing status update from ongoing to under review.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
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
            self.assertEqual(task.status, "ongoing", msg=f"Expected status 'ongoing', got '{task.status}'")
        
        self.login_as(self.collab_id, "staff")
        payload = {
            "status": "under review"}
        response = self.client.patch(f"/task/status/{task_id}", json=payload)
        self.assertEqual(response.status_code, 200, msg=f"Status update failed: {response.status_code} {response.get_data(as_text=True)}")
        data = response.get_json()
        with self.app.app_context():
            task = Task.query.get(task_id)
            self.assertEqual(task.status, "under review", msg=f"Expected status 'under review', got '{task.status}'")

    def test_status_update_ongoing_to_done(self):
        # ongoing -> done should set completed_date

        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Status Update Test Task (ongoing to done)",
            "description": "Testing status update from ongoing to done.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
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
            self.assertEqual(task.status, "ongoing", msg=f"Expected status 'ongoing', got '{task.status}'")

        self.login_as(self.collab_id, "staff")
        payload = {
            "status": "done"}
        response = self.client.patch(f"/task/status/{task_id}", json=payload)
        self.assertEqual(response.status_code, 200, msg=f"Status update failed: {response.status_code} {response.get_data(as_text=True)}")
        data = response.get_json()
        with self.app.app_context():
            task = Task.query.get(task_id)
            self.assertEqual(task.status, "done", msg=f"Expected status 'done', got '{task.status}'")
            self.assertIsNotNone(task.completed_date, msg="completed_date not set on status update to done")
            now = datetime.now(UTC)
            # print("now:", now)
            # print("task.completed_date:", task.completed_date)
            # print('time taken: ', (now - task.completed_date).total_seconds())
            self.assertTrue((now - task.completed_date.replace(tzinfo=UTC)).total_seconds() < 10, msg="completed_date not set correctly on status update to done")

    def test_status_update_unassigned_to_under_review(self):
        # unassigned -> under review should set start_date
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Status Update Test Task (unassigned to under review)",
            "description": "Testing status update from unassigned to under review.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
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
            self.assertEqual(task.status, "ongoing", msg=f"Expected status 'ongoing', got '{task.status}'")
        self.login_as(self.collab_id, "staff")
        payload = {
            "status": "under review"}
        response = self.client.patch(f"/task/status/{task_id}", json=payload)
        self.assertEqual(response.status_code, 200, msg=f"Status update failed: {response.status_code} {response.get_data(as_text=True)}")
        data = response.get_json()
        with self.app.app_context():
            task = Task.query.get(task_id)
            self.assertIsNotNone(task.start_date, msg="start_date not set on status update to under review")
            now = datetime.now(UTC)
            self.assertTrue((now - task.start_date.replace(tzinfo=UTC)).total_seconds() < 10, msg="start_date not set correctly on status update to under review")

    def test_status_update_unassigned_to_done(self):
        # unassigned -> done should set start_date and completed_date
        self.login_as(self.manager_id, "manager")
        payload = {
            "title": "Status Update Test Task (unassigned to done)",
            "description": "Testing status update from unassigned to done.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
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
            self.assertEqual(task.status, "unassigned", msg=f"Expected status 'unassigned', got '{task.status}'")
        
        self.login_as(self.collab_id, "staff")
        payload = {"status": "done"}
        response = self.client.patch(f"/task/status/{task_id}", json=payload)
        self.assertEqual(response.status_code, 200, msg=f"Status update failed: {response.status_code} {response.get_data(as_text=True)}")
        data = response.get_json()
        with self.app.app_context():
            task = Task.query.get(task_id)
            self.assertIsNotNone(task.start_date, msg="start_date not set on status update to done")
            self.assertIsNotNone(task.completed_date, msg="completed_date not set on status update to done")
            now = datetime.now(UTC)
            self.assertTrue((now - task.start_date.replace(tzinfo=UTC)).total_seconds() < 10, msg="start_date not set correctly on status update to done")
            self.assertTrue((now - task.completed_date.replace(tzinfo=UTC)).total_seconds() < 10, msg="completed_date not set correctly on status update to done")

    def test_status_update_under_review_to_done(self):
        # under review -> done should set completed_date
        self.login_as(self.collab_id, "staff")
        payload = {
            "title": "Status Update Test Task (under review to done)",
            "description": "Testing status update from under review to done.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
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
            self.assertEqual(task.status, "ongoing", msg=f"Expected status 'ongoing', got '{task.status}'")
        
        self.login_as(self.collab_id, "staff")
        payload = {"status": "under review"} # first update to under review
        response = self.client.patch(f"/task/status/{task_id}", json=payload)
        self.assertEqual(response.status_code, 200, msg=f"Status update to under review failed: {response.status_code} {response.get_data(as_text=True)}")
        payload = {"status": "done"} # then update to done
        response = self.client.patch(f"/task/status/{task_id}", json=payload)
        self.assertEqual(response.status_code, 200, msg=f"Status update to done failed: {response.status_code} {response.get_data(as_text=True)}")
        data = response.get_json()
        with self.app.app_context():
            task = Task.query.get(task_id)
            self.assertIsNotNone(task.completed_date, msg="completed_date not set on status update to done")
            now = datetime.now(UTC)
            self.assertTrue((now - task.completed_date.replace(tzinfo=UTC)).total_seconds() < 10, msg="completed_date not set correctly on status update to done")

    def test_status_update_invalid_new_status(self):
        # dont think its an issue cuz frontend dropdown
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Status Update Test Task (invalid status)",
            "description": "Testing status update with invalid status.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 201, msg=f"Create task failed: {response.status_code} {response.get_data(as_text=True)}")
        data = response.get_json()
        task_id = data.get("task_id")
        self.assertIsNotNone(task_id, msg="Response missing task_id")

        payload = {
            "status": "invalid_status"
        }
        response = self.client.patch(f"/task/status/{task_id}", json=payload)
        self.assertEqual(response.status_code, 400, msg=f"Status update failed: {response.status_code} {response.get_data(as_text=True)}")
        
    def test_status_update_task_not_found(self):
        # dont think its an issue cuz card will not exist, but error checking is implemented already
        self.login_as(self.owner_id, "staff")
        response = self.client.patch("/task/status/999999", json={"status": "ongoing"})
        self.assertEqual(response.status_code, 404, msg=f"Expected 404 for non-existent task, got {response.status_code}")

    def test_status_update_employee_not_collaborator(self):
        # only collaborators can update status
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Status Update Test Task (not collaborator)",
            "description": "Testing status update by non-collaborator.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 201, msg=f"Create task failed: {response.status_code} {response.get_data(as_text=True)}")
        data = response.get_json()
        task_id = data.get("task_id")
        self.assertIsNotNone(task_id, msg="Response missing task_id")

        # Try to update the status as a non-collaborator
        self.login_as(self.manager_id, "manager")
        response = self.client.patch(f"/task/status/{task_id}", json={"status": "ongoing"})
        self.assertEqual(response.status_code, 403, msg=f"Expected 403 for non-collaborator, got {response.status_code}")


# ----------------------------------------------------------------------------------------------------------


# ------------------------ UPDATE TASKS METADATA TESTS --------------------------------------------------------


















































    # def test_metadata_update_by_owner(self):
    #     # only owner can update metadata
    #     self.login_as(self.owner_id, "staff")
    #     payload = {
    #         "title": "Metadata Update Test Task",
    #         "description": "Testing metadata update by owner.",
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
    #     # Update metadata
    #     update_payload = {
    #         "title": "Updated Metadata Task",
    #         "description": "Updated description.",
    #         "priority": 3,
    #         "deadline": (datetime.now(UTC) + timedelta(days=10)).replace(microsecond=0).isoformat(),
    #         # "attachments": ["file1.pdf", "file2.png"],
    #     }
    #     response = self.client.put(f"/task/{task_id}", json=update_payload)
    #     self.assertEqual(response.status_code, 200, msg=f"Metadata update failed: {response.status_code} {response.get_data(as_text=True)}")
    #     data = response.get_json()
    #     with self.app.app_context():
    #         task = Task.query.get(task_id)
    #         self.assertIsNotNone(task, msg="Task not found in database")
    #         self.assertEqual(task.title, update_payload["title"], msg="Title not updated")
    #         self.assertEqual(task.description, update_payload["description"], msg="Description not updated")
    #         self.assertEqual(task.priority, update_payload["priority"], msg="Priority not updated")
    #         self.assertEqual(task.deadline, update_payload["deadline"], msg="Deadline not updated")
    #         self.assertEqual(task.attachments, update_payload["attachments"], msg="Attachments not updated")

    def test_metadata_update_by_non_owner(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Metadata Update Test Task (non-owner)",
            "description": "Testing metadata update by non-owner.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 201, msg=f"Create task failed: {response.status_code} {response.get_data(as_text=True)}")
        data = response.get_json()
        task_id = data.get("task_id")
        self.assertIsNotNone(task_id, msg="Response missing task_id")
        # Try to update metadata as collaborator (non-owner)
        self.login_as(self.collab_id, "staff")
        update_payload = {
            "title": "Updated Metadata Task (non-owner)",
            "description": "Updated description by non-owner.",
            "priority": 3,
            "deadline": generate_deadline(10),
            "collaborators": [self.collab_id],
            "attachments": [],
        }
        response = self.client.put(f"/task/{task_id}", json=update_payload)
        self.assertEqual(response.status_code, 403, msg=f"Expected 403 for non-owner, got {response.status_code}")

        # Try to update metadata as manager (should fail too)
        self.login_as(self.manager_id, "manager")
        response = self.client.put(f"/task/{task_id}", json=update_payload)
        self.assertEqual(response.status_code, 403, msg=f"Expected 403 for non-owner manager, got {response.status_code}")

    def test_assign_tasks(self):
        pass


if __name__ == "__main__":
    unittest.main()