import os
import json
import unittest
from datetime import datetime, timedelta, timezone
import zoneinfo

# Set TESTING environment variable BEFORE importing the app
os.environ['TESTING'] = 'True'

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
            new_person = Staff(employee_name="New Person", email="new_person@example.com", role="staff", department="Finance", team="A", password="Test123")
            director = Staff(employee_name="Director Four", email="director@example.com", role="director", department="Finance", team="A", password="Test123")

            db.session.add_all([owner, collab, manager, different_dept, new_person, director])
            db.session.commit()

            # seed tasks

            # Capture their IDs (primitive ints only)
            cls.owner_id = owner.employee_id
            cls.collab_id = collab.employee_id
            cls.manager_id = manager.employee_id
            cls.different_dept_id = different_dept.employee_id
            cls.new_collab_id = new_person.employee_id
            cls.director_id = director.employee_id

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

    # missing fields
    def test_create_task_missing_fields(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            # "title": "Sample Task",  # missing title
            "description": "This is a sample task for testing.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for missing fields, got {response.status_code}")

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

    # test title duplicate, previous task with same title is not completed
    def test_create_task_title_duplicate_not_completed(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Duplicate Title Task",
            "description": "This is the first task with this title.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 201, msg=f"Create first task failed: {response.status_code} {response.get_data(as_text=True)}")

        # Attempt to create another task with the same title
        payload["description"] = "This is the second task with the same title."
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for duplicate title of incomplete task, got {response.status_code}")

    # test title duplicate, previous task with same title is completed
    def test_create_task_title_duplicate_completed(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Completed Title Task",
            "description": "This is the first task with this title.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 201, msg=f"Create first task failed: {response.status_code} {response.get_data(as_text=True)}")
        data = response.get_json()
        task_id = data.get("task_id")
        self.assertIsNotNone(task_id, msg="Response missing task_id")

        # Mark the first task as completed directly in the database
        with self.app.app_context():
            task = Task.query.get(task_id)
            task.status = "done"
            task.completed_date = datetime.now(UTC)
            db.session.commit()

        # Attempt to create another task with the same title
        payload["description"] = "This is the second task with the same title."
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 201, msg=f"Create second task with duplicate title after completion failed: {response.status_code} {response.get_data(as_text=True)}")

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

    # test recurrence (not int or less than 1)
    def test_create_task_recurrence_invalid(self):
        self.login_as(self.owner_id, "staff")
        # test non-int
        payload = {
            "title": "Recurrence Invalid Test Task",
            "description": "Testing invalid recurrence assignment.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
            "recurrence": "weekly",  # invalid recurrence
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for non-integer recurrence, got {response.status_code}")

        # test less than 1
        payload["recurrence"] = 0  # invalid recurrence
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for recurrence less than 1, got {response.status_code}")

    # test recurrence ?
    # when a task is created with recurrence, nothing special happens until it's marked done
    # when it is marked done, a new task is created with same details and new deadline based on recurrence (recurrence + days from completed_date)
    def test_create_task_recurrence(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Recurrence Test Task",
            "description": "Testing recurrence assignment.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
            "recurrence": 7,  # weekly recurrence
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 201, msg=f"Create task with recurrence failed: {response.status_code} {response.get_data(as_text=True)}")
        data = response.get_json()
        task_id = data.get("task_id")
        self.assertIsNotNone(task_id, msg="Response missing task_id")
        with self.app.app_context():
            task = Task.query.get(task_id)
            self.assertIsNotNone(task, msg="Task not found in database")
            self.assertEqual(task.recurrence, 7, msg=f"Expected recurrence '7', got '{task.recurrence}'")

        # mark task as done and check if new task is created with correct deadline
        update_payload = {
            "status": "done"
        }
        response = self.client.patch(f"/task/status/{task_id}", json=update_payload)
        self.assertEqual(response.status_code, 200, msg=f"Mark task as done failed: {response.status_code} {response.get_data(as_text=True)}")
        with self.app.app_context():
            # check if new task is created
            new_task = Task.query.filter(Task.title == "Recurrence Test Task", Task.task_id != task_id).first()
            self.assertIsNotNone(new_task, msg="New recurring task not created")
            task = Task.query.get(task_id)
            expected_deadline = task.completed_date + timedelta(days=7)
            self.assertEqual(new_task.deadline.date(), expected_deadline.date(), msg=f"Expected new task deadline '{expected_deadline.date()}', got '{new_task.deadline.date()}'")

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

    # test subtask status (staff)
    # subtask status depends on status of subtask owner
    def test_create_subtask_status_assignment(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Task with Subtask",
            "description": "Testing subtask status assignment.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
            "subtasks": [{
                "title": "Subtask with status test",
                "description": "This subtask status depends on owner role.",
                "priority": 2,
                "deadline": generate_deadline(),
                "collaborators": [self.collab_id],
                "attachments": [],
            }]
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 201, msg=f"Create task with subtask failed: {response.status_code} {response.get_data(as_text=True)}")
        data = response.get_json()
        task_id = data.get("task_id")
        self.assertIsNotNone(task_id, msg="Response missing task_id")

        # Fetch the created subtask directly from the database to verify status
        with self.app.app_context():
            task = Task.query.get(task_id)
            self.assertIsNotNone(task, msg="Task not found in database")
            subtask = task.subtasks[0]
            self.assertEqual(subtask.status, "ongoing", msg=f"Expected subtask status 'ongoing' for staff owner, got '{subtask.status}'")

    # test subtask status (manager)
    def test_create_subtask_status_assignment_manager(self):
        self.login_as(self.manager_id, "manager")
        payload = {
            "title": "Task with Subtask (manager)",
            "description": "Testing subtask status assignment (manager).",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
            "subtasks": [{
                "title": "Subtask with status test",
                "description": "This subtask status depends on owner role.",
                "priority": 2,
                "deadline": generate_deadline(),
                "collaborators": [self.collab_id],
                "attachments": [],
            }]
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 201, msg=f"Create task with subtask failed: {response.status_code} {response.get_data(as_text=True)}")
        data = response.get_json()
        task_id = data.get("task_id")
        self.assertIsNotNone(task_id, msg="Response missing task_id")

        # Fetch the created subtask directly from the database to verify status
        with self.app.app_context():
            task = Task.query.get(task_id)
            self.assertIsNotNone(task, msg="Task not found in database")
            subtask = task.subtasks[0]
            self.assertEqual(subtask.status, "unassigned", msg=f"Expected subtask status 'unassigned' for manager owner, got '{subtask.status}'")

    # test subtask status (director)
    def test_create_subtask_status_assignment_director(self):
        self.login_as(self.director_id, "director")
        payload = {
            "title": "Task with Subtask (director)",
            "description": "Testing subtask status assignment (director).",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
            "subtasks": [{
                "title": "Subtask with status test",
                "description": "This subtask status depends on owner role.",
                "priority": 2,
                "deadline": generate_deadline(),
                "collaborators": [self.collab_id],
                "attachments": [],
            }]
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 201, msg=f"Create task with subtask failed: {response.status_code} {response.get_data(as_text=True)}")
        data = response.get_json()
        task_id = data.get("task_id")
        self.assertIsNotNone(task_id, msg="Response missing task_id")

        # Fetch the created subtask directly from the database to verify status
        with self.app.app_context():
            task = Task.query.get(task_id)
            self.assertIsNotNone(task, msg="Task not found in database")
            subtask = task.subtasks[0]
            self.assertEqual(subtask.status, "unassigned", msg=f"Expected subtask status 'unassigned' for director owner, got '{subtask.status}'")

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

    # test subtask recurrence ?
    # create a task with a subtask, mark parent task as done, subtask will be copied to new task
    # subtask has no recurrence field, so just check if it is copied over correctly
    def test_create_subtask_recurrence_inherit(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Task with Subtask for Recurrence",
            "description": "Testing subtask inheritance on recurrence.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
            "recurrence": 3,  # every 3 days
            "subtasks": [{
                "title": "Subtask to be copied",
                "description": "This subtask should be copied to new task on recurrence.",
                "priority": 2,
                "deadline": generate_deadline(),
                "collaborators": [self.collab_id],
                "attachments": [],
            }]
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 201, msg=f"Create task with subtask failed: {response.status_code} {response.get_data(as_text=True)}")
        data = response.get_json()
        task_id = data.get("task_id")
        with self.app.app_context():
            subtask_id = Task.query.filter(Task.title == "Subtask to be copied").first().task_id
            self.assertIsNotNone(task_id, msg="Response missing task_id")

        # mark task as done and check if new task is created with subtask copied over
        update_payload = {
            "status": "done"
        }
        update_subtask = self.client.patch(f"/task/status/{subtask_id}", json={"status": "done"})
        response = self.client.patch(f"/task/status/{task_id}", json=update_payload)
        self.assertEqual(response.status_code, 200, msg=f"Mark task as done failed: {response.status_code} {response.get_data(as_text=True)}")
        with self.app.app_context():
            # check if new task is created
            new_task = Task.query.filter(Task.title == "Task with Subtask for Recurrence", Task.task_id != task_id).first()
            self.assertIsNotNone(new_task, msg="New recurring task not created")
            self.assertEqual(len(new_task.subtasks.all()), 1, msg="Expected 1 subtask in new recurring task")
            subtask = new_task.subtasks[0]
            self.assertEqual(subtask.title, "Subtask to be copied", msg=f"Expected subtask title 'Subtask to be copied', got '{subtask.title}'")


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

    # main task can only be updated by task owner, subtasks can only be updated by their own owners (task owner cannot update subtasks unless they are also the subtask owner)

    # test update metadata task not found
    def test_metadata_update_task_not_found(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Updated Title",
            "description": "Updated Description",
            "priority": 3,
            "deadline": generate_deadline(10),
            "collaborators": [self.collab_id],
            "attachments": [],
        }
        response = self.client.put("/task/999999", json=payload)
        self.assertEqual(response.status_code, 404, msg=f"Expected 404 for non-existent task, got {response.status_code}")

    # test update metadata by non-owner
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

    # test update metadata invalid title
    def test_metadata_update_invalid_title(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Metadata Update Test Task (invalid title)",
            "description": "Testing metadata update with invalid title.",
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
        # Try to update metadata with invalid title
        update_payload = {
            "title": "",  # invalid title
            "description": "Updated description with invalid title.",
            "priority": 3,
            "deadline": generate_deadline(10),
            "collaborators": [self.collab_id],
            "attachments": [],
        }
        response = self.client.put(f"/task/{task_id}", json=update_payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for invalid title, got {response.status_code}")

    # test update metadata invalid description
    def test_metadata_update_invalid_description(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Metadata Update Test Task (invalid description)",
            "description": "Testing metadata update with invalid description.",
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
        # Try to update metadata with invalid description
        update_payload = {
            "title": "Updated Metadata Task (invalid description)",
            "description": "",  # invalid description
            "priority": 3,
            "deadline": generate_deadline(10),
            "collaborators": [self.collab_id],
            "attachments": [],
        }
        response = self.client.put(f"/task/{task_id}", json=update_payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for invalid description, got {response.status_code}")

    # test update metadata invalid deadline
    def test_metadata_update_invalid_deadline(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Metadata Update Test Task (invalid deadline)",
            "description": "Testing metadata update with invalid deadline.",
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
        # Try to update metadata with invalid deadline
        update_payload = {
            "title": "Updated Metadata Task (invalid deadline)",
            "description": "Updated description with invalid deadline.",
            "priority": 3,
            "deadline": "2023/10/10 10:00:00",  # invalid format
            "collaborators": [self.collab_id],
            "attachments": [],
        }
        response = self.client.put(f"/task/{task_id}", json=update_payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for invalid deadline, got {response.status_code}")

    # test update metadata invalid priority
    def test_metadata_update_invalid_priority(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Metadata Update Test Task (invalid priority)",
            "description": "Testing metadata update with invalid priority.",
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
        # Try to update metadata with invalid priority
        update_payload = {
            "title": "Updated Metadata Task (invalid priority)",
            "description": "Updated description with invalid priority.",
            "priority": 0,  # invalid priority
            "deadline": generate_deadline(10),
            "collaborators": [self.collab_id],
            "attachments": [],
        }
        response = self.client.put(f"/task/{task_id}", json=update_payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for invalid priority, got {response.status_code}")

    # edit project metadata (move from lonely to project. not doing project to lonely and project to project for now)
    # test update metadata project id (project does not exist)
    def test_metadata_update_invalid_project_id(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Metadata Update Test Task (invalid project id)",
            "description": "Testing metadata update with invalid project id.",
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
        # Try to update metadata with invalid project id
        update_payload = {
            "title": "Updated Metadata Task (invalid project id)",
            "description": "Updated description with invalid project id.",
            "priority": 3,
            "deadline": generate_deadline(10),
            "collaborators": [self.collab_id],
            "attachments": [],
            "project_id": 999999,  # non-existent project
        }
        response = self.client.put(f"/task/{task_id}", json=update_payload)
        self.assertEqual(response.status_code, 404, msg=f"Expected 404 for project id not found, got {response.status_code}")

    # test update metadata owner (assignment) - need to be same dept if lonely task, need to be project collaborator if project task, can only assign downwards, status needs to be updated from unassigned to ongoing if owner changed and task was unassigned, else status remains same
    def test_metadata_update_owner_assignment(self):
        self.login_as(self.manager_id, "manager")
        payload = {
            "title": "Metadata Update Test Task (owner assignment)",
            "description": "Testing metadata update with owner assignment.",
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
        # Try to update metadata with owner assignment
        update_payload = {
            "title": "Updated Metadata Task (owner assignment)",
            "description": "Updated description with owner assignment.",
            "priority": 3,
            "deadline": generate_deadline(10),
            "collaborators": [self.collab_id],
            "attachments": [],
            "owner": self.collab_id,  # assign owner to collab_id
        }
        response = self.client.put(f"/task/{task_id}", json=update_payload)
        self.assertEqual(response.status_code, 200, msg=f"Owner assignment update failed: {response.status_code} {response.get_data(as_text=True)}")
        data = response.get_json()
        with self.app.app_context():
            task = Task.query.get(task_id)
            self.assertIsNotNone(task, msg="Task not found in database")
            self.assertEqual(task.owner, self.collab_id, msg=f"Expected owner '{self.collab_id}', got '{task.owner}'")

    # test update metadata collaborators (must include owner, must be same dept if lonely task, must be project collaborators if project task)
    def test_metadata_update_collaborators(self):
        self.login_as(self.owner_id, "staff")
        print("self.new_collab_id:", self.new_collab_id)
        print("self.collab_id:", self.collab_id)
        print("self.owner_id:", self.owner_id)
        
        payload = {
            "title": "Metadata Update Test Task (collaborators update)",
            "description": "Testing metadata update with collaborators update.",
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
        # Try to update metadata with collaborators update
        # new_collab_id = self.seed_employee(department_id=self.department_id)
        update_payload = {
            "title": "Updated Metadata Task (collaborators update)",
            "description": "Updated description with collaborators update.",
            "priority": 3,
            "deadline": generate_deadline(10),
            "collaborators": [self.collab_id, self.new_collab_id],  # add new collaborator
            "attachments": [],
        }
        response = self.client.put(f"/task/{task_id}", json=update_payload)
        self.assertEqual(response.status_code, 200, msg=f"Collaborators update failed: {response.status_code} {response.get_data(as_text=True)}")
        data = response.get_json()
        with self.app.app_context():
            task = Task.query.get(task_id)
            self.assertIsNotNone(task, msg="Task not found in database")
            self.assertIn(self.new_collab_id, [collab.employee_id for collab in task.collaborators], msg=f"Expected collaborator '{self.new_collab_id}' not found in task collaborators")

    # test update metadata attachments ?

    # test update metadata comments ?

    # test update metadata recurrence ?

    # ------------------------- test update subtask metadata ---------------------------------------

    # test update subtask (create subtask) - given subtask without an id
    def test_update_subtask_create(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Task with Subtask to Update",
            "description": "Testing subtask creation during update.",
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
        # Now update the task to add a subtask
        # updated payload should still contain the main task details



        update_payload = {
            "title": "Task with Subtask to Update",
            "description": "Testing subtask creation during update.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
            "subtasks": [{
                "title": "New Subtask Created During Update",
                "description": "This subtask is created during task update.",
                "priority": 2,
                "deadline": generate_deadline(),
                "collaborators": [self.collab_id],
                "attachments": [],
            }]
        }
        response = self.client.put(f"/task/{task_id}", json=update_payload)
        self.assertEqual(response.status_code, 200, msg=f"Subtask creation during update failed: {response.status_code} {response.get_data(as_text=True)}")
        data = response.get_json()
        with self.app.app_context():
            task = Task.query.get(task_id)
            self.assertIsNotNone(task, msg="Task not found in database")
            self.assertEqual(len(task.subtasks.all()), 1, msg="Subtask not created during update")
            subtask = task.subtasks[0]
            self.assertEqual(subtask.title, update_payload["subtasks"][0]["title"], msg="Subtask title mismatch")

    # test update subtask (update existing subtask) - given subtask with an id
    def test_update_subtask_update_existing(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Task with Subtask to Update Existing",
            "description": "Testing subtask update during task update.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
            "subtasks": [{
                "title": "Existing Subtask",
                "description": "This subtask will be updated.",
                "priority": 2,
                "deadline": generate_deadline(),
                "collaborators": [self.collab_id],
                "attachments": [],
            }]
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 201, msg=f"Create task with subtask failed: {response.status_code} {response.get_data(as_text=True)}")
        data = response.get_json()
        task_id = data.get("task_id")
        self.assertIsNotNone(task_id, msg="Response missing task_id")
        with self.app.app_context():
            task = Task.query.get(task_id)
            self.assertIsNotNone(task, msg="Task not found in database")
            self.assertEqual(len(task.subtasks.all()), 1, msg="Subtask not created")
            subtask = task.subtasks[0]
            subtask_id = subtask.task_id
        # Now update the task to modify the existing subtask
        # updated payload should still contain the main task details
        
        update_payload = {
            "title": "Task with Subtask to Update",
            "description": "Testing subtask creation during update.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
            "subtasks": [{
                "task_id": subtask_id,
                "title": "Updated Existing Subtask",
                "description": "This subtask has been updated.",
                "priority": 3,
                "deadline": generate_deadline(5),
                "collaborators": [self.collab_id],
                "attachments": [],
            }]
        }
        response = self.client.put(f"/task/{task_id}", json=update_payload)
        self.assertEqual(response.status_code, 200, msg=f"Subtask update during task update failed: {response.status_code} {response.get_data(as_text=True)}")
        data = response.get_json()
        with self.app.app_context():
            task = Task.query.get(task_id)
            self.assertIsNotNone(task, msg="Task not found in database")
            self.assertEqual(len(task.subtasks.all()), 1, msg="Subtask not created during update")
            subtask = task.subtasks[0]
            self.assertEqual(subtask.title, update_payload["subtasks"][0]["title"], msg="Subtask title not updated")

    # test update subtask task id given but task not found
    def test_update_subtask_task_not_found(self):
        self.login_as(self.owner_id, "staff")
        update_payload = {
            "subtasks": [{
                "id": 1,
                "title": "Subtask for Non-existent Task",
                "description": "This subtask is for a non-existent task.",
                "priority": 2,
                "deadline": generate_deadline(),
                "collaborators": [self.collab_id],
                "attachments": [],
            }]
        }
        response = self.client.put("/task/999999", json=update_payload)
        self.assertEqual(response.status_code, 404, msg=f"Expected 404 for non-existent task, got {response.status_code}")

    # test update subtask by non-owner (subtasks can only be updated by main task owner or subtask owner)
    def test_update_subtask_by_non_owner(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Task with Subtask to Test Non-owner Update",
            "description": "Testing subtask update by non-owner.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
            "subtasks": [{
                "title": "Subtask to be Updated by Non-owner",
                "description": "This subtask will be attempted to be updated by non-owner.",
                "priority": 2,
                "deadline": generate_deadline(),
                "collaborators": [self.collab_id],
                "attachments": [],
            }]
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 201, msg=f"Create task with subtask failed: {response.status_code} {response.get_data(as_text=True)}")
        data = response.get_json()
        task_id = data.get("task_id")
        self.assertIsNotNone(task_id, msg="Response missing task_id")
        with self.app.app_context():
            task = Task.query.get(task_id)
            self.assertIsNotNone(task, msg="Task not found in database")
            self.assertEqual(len(task.subtasks.all()), 1, msg="Subtask not created")
            subtask = task.subtasks[0]
            subtask_id = subtask.task_id
        # Now try to update the subtask as a non-owner
        self.login_as(self.collab_id, "staff")  # collab is not owner of main task
        update_payload = {
            "subtasks": [{
                "id": subtask_id,
                "title": "Attempted Update by Non-owner",
                "description": "This update should fail.",
                "priority": 3,
                "deadline": generate_deadline(5),
                "collaborators": [self.collab_id],
                "attachments": [],
            }]
        }
        response = self.client.put(f"/task/{task_id}", json=update_payload)
        self.assertEqual(response.status_code, 403, msg=f"Expected 403 for non-owner subtask update, got {response.status_code}")

    # below tests are for subtask update (create)
    # test update subtask invalid title
    def test_update_subtask_invalid_title(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Task with Subtask to Test Invalid Title",
            "description": "Testing subtask creation with invalid title.",
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
        # Now try to create a subtask with invalid title
        # updated payload should still contain the main task details


        update_payload = {
            "title": "Task with Subtask to Test Invalid Title",
            "description": "Testing subtask creation with invalid title.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
            "subtasks": [{
                "title": "",  # invalid title
                "description": "This subtask has an invalid title.",
                "priority": 2,
                "deadline": generate_deadline(),
                "collaborators": [self.collab_id],
                "attachments": [],
            }]
        }
        response = self.client.put(f"/task/{task_id}", json=update_payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for invalid subtask title, got {response.status_code}")

    # test update subtask invalid description
    def test_update_subtask_invalid_description(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Task with Subtask to Test Invalid Description",
            "description": "Testing subtask creation with invalid description.",
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
        # Now try to create a subtask with invalid description
        # updated payload should still contain the main task details


        update_payload = {
            "title": "Task with Subtask to Test Invalid Description",
            "description": "Testing subtask creation with invalid description.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
            "subtasks": [{
                "title": "Subtask with Invalid Description",
                "description": "",  # invalid description
                "priority": 2,
                "deadline": generate_deadline(),
                "collaborators": [self.collab_id],
                "attachments": [],
            }]
        }
        response = self.client.put(f"/task/{task_id}", json=update_payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for invalid subtask description, got {response.status_code}")

    # test update subtask invalid deadline (must be within main task deadline)
    def test_update_subtask_invalid_deadline(self):
        self.login_as(self.owner_id, "staff")
        main_task_deadline = generate_deadline(5)
        payload = {
            "title": "Task with Subtask to Test Invalid Deadline",
            "description": "Testing subtask creation with invalid deadline.",
            "priority": 2,
            "deadline": main_task_deadline,
            "collaborators": [self.collab_id],
            "attachments": [],
        }
        response = self.client.post("/tasks", json=payload)
        self.assertEqual(response.status_code, 201, msg=f"Create task failed: {response.status_code} {response.get_data(as_text=True)}")
        data = response.get_json()
        task_id = data.get("task_id")
        self.assertIsNotNone(task_id, msg="Response missing task_id")
        # Now try to create a subtask with invalid deadline (beyond main task deadline)
        # updated payload should still contain the main task details


        update_payload = {
            "title": "Task with Subtask to Test Invalid Deadline",
            "description": "Testing subtask creation with invalid deadline.",
            "priority": 2,
            "deadline": main_task_deadline,
            "collaborators": [self.collab_id],
            "attachments": [],
            "subtasks": [{
                "title": "Subtask with Invalid Deadline",
                "description": "This subtask has a deadline beyond the main task deadline.",
                "priority": 2,
                "deadline": generate_deadline(10),  # invalid deadline
                "collaborators": [self.collab_id],
                "attachments": [],
            }]
        }
        response = self.client.put(f"/task/{task_id}", json=update_payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for invalid subtask deadline, got {response.status_code}")

    # test update subtask invalid priority
    def test_update_subtask_invalid_priority(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Task with Subtask to Test Invalid Priority",
            "description": "Testing subtask creation with invalid priority.",
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
        # Now try to create a subtask with invalid priority
        # updated payload should still contain the main task details


        update_payload = {
            "title": "Task with Subtask to Test Invalid Priority",
            "description": "Testing subtask creation with invalid priority.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
            "subtasks": [{
                "title": "Subtask with Invalid Priority",
                "description": "This subtask has an invalid priority.",
                "priority": 0,  # invalid priority
                "deadline": generate_deadline(),
                "collaborators": [self.collab_id],
                "attachments": [],
            }]
        }
        response = self.client.put(f"/task/{task_id}", json=update_payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for invalid subtask priority, got {response.status_code}")

    # test update subtask collaborators (must be subset of main task collaborators)
    def test_update_subtask_collaborators_invalid(self):
        self.login_as(self.owner_id, "staff")
        payload = {
            "title": "Task with Subtask to Test Invalid Collaborators",
            "description": "Testing subtask creation with invalid collaborators.",
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
        # Now try to create a subtask with invalid collaborators (not subset of main task collaborators)
        # updated payload should still contain the main task details


        update_payload = {
            "title": "Task with Subtask to Test Invalid Collaborators",
            "description": "Testing subtask creation with invalid collaborators.",
            "priority": 2,
            "deadline": generate_deadline(),
            "collaborators": [self.collab_id],
            "attachments": [],
            "subtasks": [{
                "title": "Subtask with Invalid Collaborators",
                "description": "This subtask has collaborators not in main task.",
                "priority": 2,
                "deadline": generate_deadline(),
                "collaborators": [self.new_collab_id],  # invalid collaborator
                "attachments": [],
            }]
        }
        response = self.client.put(f"/task/{task_id}", json=update_payload)
        self.assertEqual(response.status_code, 400, msg=f"Expected 400 for invalid subtask collaborators, got {response.status_code}")

    # test update subtask project id (should inherit from main task)
    

    # below tests are for subtask update (update existing)










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

    # def test_metadata_update_by_non_owner(self):
    #     self.login_as(self.owner_id, "staff")
    #     payload = {
    #         "title": "Metadata Update Test Task (non-owner)",
    #         "description": "Testing metadata update by non-owner.",
    #         "priority": 2,
    #         "deadline": generate_deadline(),
    #         "collaborators": [self.collab_id],
    #         "attachments": [],
    #     }
    #     response = self.client.post("/tasks", json=payload)
    #     self.assertEqual(response.status_code, 201, msg=f"Create task failed: {response.status_code} {response.get_data(as_text=True)}")
    #     data = response.get_json()
    #     task_id = data.get("task_id")
    #     self.assertIsNotNone(task_id, msg="Response missing task_id")
    #     # Try to update metadata as collaborator (non-owner)
    #     self.login_as(self.collab_id, "staff")
    #     update_payload = {
    #         "title": "Updated Metadata Task (non-owner)",
    #         "description": "Updated description by non-owner.",
    #         "priority": 3,
    #         "deadline": generate_deadline(10),
    #         "collaborators": [self.collab_id],
    #         "attachments": [],
    #     }
    #     response = self.client.put(f"/task/{task_id}", json=update_payload)
    #     self.assertEqual(response.status_code, 403, msg=f"Expected 403 for non-owner, got {response.status_code}")

    #     # Try to update metadata as manager (should fail too)
    #     self.login_as(self.manager_id, "manager")
    #     response = self.client.put(f"/task/{task_id}", json=update_payload)
    #     self.assertEqual(response.status_code, 403, msg=f"Expected 403 for non-owner manager, got {response.status_code}")

    # def test_assign_tasks(self):
    #     pass


if __name__ == "__main__":
    unittest.main()