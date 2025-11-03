# SPM-G8T5
SPMMMMMMM PRODUCTIVITYYYYYY MANAGEMENT THINGGGGG

To run frontend: (refer to frontend readme)
    0. (first time only) npm install
    1. cd frontend
    2. npm run dev
    3. localhost link (localhost:5173)

To run microservices: 
    0. cd backend
    1. install requirements: pip install -r requirements.txt
    2a. run employee MS: python -m employee.employee
    2b. run task MS: python -m tasks.task
    2c. run projects MS: python -m projects.app
    2d. run notification MS: python -m notifications.app


Database:

To update local db everytime someone pushes a change

Find YOUR_MYSQL_PATH, might be 
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" 
OR 
"C:\wamp64\bin\mysql\mysql8.2.0\bin\mysql.exe"

Then run these commands (replace YOUR_MYSQL_PATH with your actual path):
# Navigate to backend directory
cd backend

# Drop and recreate database (run with cmd pompt not powershell)
YOUR_MYSQL_PATH -u root -p -e "DROP DATABASE IF EXISTS SPM;"
YOUR_MYSQL_PATH -u root -p -e "CREATE DATABASE SPM;"
# Create all tables
YOUR_MYSQL_PATH -u root -p SPM < database/schema.sql
# Add sample data
YOUR_MYSQL_PATH -u root -p SPM < database/seeds/development.sql

Login information:
