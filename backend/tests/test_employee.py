import unittest
from employee.employee import app, db, Staff
from models.staff import Staff, Manager, Director, SeniorManager


class TestEmployee(unittest.TestCase):

    def setUp(self):
        """Set up a clean test client and in-memory database before each test."""
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        self.client = app.test_client()

        with app.app_context():
            db.create_all()

    def tearDown(self):
        """Clean up database after each test."""
        with app.app_context():
            db.session.remove()
            db.drop_all()

    # ----------------------------------------------------------------------
    def test_password_hashing(self):
        s = Staff(employee_name="Alice", email="a@b.com",
                  department="IT", role="staff", password="", team="T1")
        s.set_password("Secret123")
        self.assertNotEqual(s.password, "Secret123")
        self.assertTrue(s.check_password("Secret123"))
        self.assertFalse(s.check_password("WrongPwd"))

# idk if necessary
    def test_polymorphic_roles(self):
        self.assertEqual(Staff.__mapper_args__["polymorphic_identity"], "staff")
        self.assertEqual(Manager.__mapper_args__["polymorphic_identity"], "manager")
        self.assertEqual(Director.__mapper_args__["polymorphic_identity"], "director")
        self.assertEqual(SeniorManager.__mapper_args__["polymorphic_identity"], "senior manager")

    # def test_get_tasks_not_implemented(self):
    #     s = Staff()
    #     self.assertIsNone(s.get_tasks())
    #     self.assertIsNone(Manager().get_tasks())
    #     self.assertIsNone(Director().get_tasks())
    #     self.assertIsNone(SeniorManager().get_tasks())

    # API Tests (employee.py)
    # ----------------------------------------------------------------------

    def test_create_employee(self):
        """Register a new employee successfully."""
        response = self.client.post("/register", json={
            "email": "test12@gmail.com",
            "password": "PasswordNumber!1",
            "department": "Finance",
            "employee_name": "David Tan",
            "role": "senior manager",
            "team": "A"
        })
        print("Create Employee:", response.get_json())
        self.assertEqual(response.status_code, 201)

    def test_register_duplicate_email(self):
        """Register duplicate employee should return 409 conflict."""
        data = {
            "email": "duplicate@gmail.com",
            "password": "Password123!",
            "department": "IT",
            "employee_name": "John Lim",
            "role": "staff",
            "team": "Alpha"
        }
        self.client.post("/register", json=data)
        response = self.client.post("/register", json=data)
        print("Duplicate Email:", response.get_json())
        self.assertEqual(response.status_code, 409)

    def test_login_user_not_found(self):
        """Login with non-existent email should return 404."""
        response = self.client.post("/login", json={"email": "notfound@gmail.com", "password": "test"})
        print("Login User Not Found:", response.get_json())
        self.assertEqual(response.status_code, 404)

    def test_login_incorrect_password(self):
        """Login with wrong password should return 401."""
        self.client.post("/register", json={
            "email": "wrongpass@gmail.com",
            "password": "Right123!",
            "department": "Finance",
            "employee_name": "Wrong Pass",
            "role": "staff",
            "team": "A"
        })
        response = self.client.post("/login", json={
            "email": "wrongpass@gmail.com", "password": "WrongPwd"
        })
        print("Login Wrong Password:", response.get_json())
        self.assertEqual(response.status_code, 401)

    def test_login_success(self):
        """Login successfully after registration."""
        self.client.post("/register", json={
            "email": "goodlogin@gmail.com",
            "password": "Password123!",
            "department": "Finance",
            "employee_name": "Good Login",
            "role": "staff",
            "team": "B"
        })
        response = self.client.post("/login", json={
            "email": "goodlogin@gmail.com", "password": "Password123!"
        })
        print("Login Success:", response.get_json())
        self.assertEqual(response.status_code, 200)
        self.assertIn("employee_id", response.get_json())

    def test_get_employees_by_department(self):
        """Fetch employees by department."""
        self.client.post("/register", json={
            "email": "dep1@gmail.com",
            "password": "123",
            "department": "HR",
            "employee_name": "HR Person",
            "role": "staff",
            "team": "A"
        })
        response = self.client.get("/employees/HR")
        print("Employees by Department:", response.get_json())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.get_json()) > 0)

    def test_get_all_employees(self):
        """Fetch all employees."""
        response = self.client.get("/employees/all")
        print("All Employees:", response.get_json())
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.get_json(), list)

    def test_get_all_departments(self):
        """Fetch all unique departments."""
        self.client.post("/register", json={
            "email": "dept1@gmail.com",
            "password": "123",
            "department": "Technology",
            "employee_name": "Tech Guy",
            "role": "staff",
            "team": "Z"
        })
        response = self.client.get("/departments")
        print("Departments:", response.get_json())
        self.assertEqual(response.status_code, 200)
        self.assertIn("Technology", response.get_json())

    def test_get_employees_by_department_and_team(self):
        """Fetch employees filtered by department and team."""
        self.client.post("/register", json={
            "email": "team1@gmail.com",
            "password": "123",
            "department": "Operations",
            "employee_name": "Ops Guy",
            "role": "staff",
            "team": "Blue"
        })
        response = self.client.get("/employees/department/Operations/team/Blue")
        print("Employees by Dept & Team:", response.get_json())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(emp["department"] == "Operations" for emp in response.get_json()))

    # def test_get_employees_by_project_no_relation(self):
    #     """Fetch employees by project (empty result expected)."""
    #     response = self.client.get("/employee/1")
    #     print("Employees by Project:", response.get_json())
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.get_json(), [])

    # def test_reset_placeholder(self):
    #     """Test the reset endpoint placeholder."""
    #     response = self.client.post("/reset")
    #     print("Reset Response:", response.data)
    #     self.assertIn(response.status_code, (200, 500))


if __name__ == "__main__":
    unittest.main()
