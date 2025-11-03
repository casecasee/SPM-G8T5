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

# Login information (Finance):
Email: david.yap@company.com
Dept: Finance
Role: director 
Password: Password@123

Email:emma.johnson@company.com
Dept: Finance
Role: manager
Password: Password@123

Email: natalie.foster@company.com
Dept: Finance
Role: staff 
Password: Password@123

Email: marcus.chen@company.com
Dept: Finance
Role: staff
Password: Password@123

# Login information (HR):
Email: jack.sim@company.com
Dept: HR
Role: director
Password: Password@123

Email: sally.loh@company.com
Dept: HR 
Role: director
Password: Password@123

Email: samuel.lee@company.com
Dept: HR 
Role: manager
Password: Password@123

Email: liam.patel@company.com
Dept: HR
Role: manager
Password: Password@123

Email: aria.kim@company.com
Dept: HR
Role: manager
Password: Password@123

Email: isabella.rossi@company.com
Dept: HR
Role: staff
Password: Password@123

Email: priya.nair@company.com
Dept: HR
Role: staff
Password: Password@123

Email: julian.herrera@company.com
Dept: HR
Role: staff
Password: Password@123

# Login information (IT):
Email: peter.yap@company.com
Dept: IT
Role: director 
Password: Password@123

Email: charlie.brown@company.com
Dept: IT
Role: manager 
Password: Password@123

Email: alice.jane@company.com
Dept: IT
Role: staff
Password: Password@123

Email:amelia.chen@company.com
Dept: IT
Role: staff 
Password: Password@123  

Email: oliver.smith@company.com
Dept: IT
Role: staff 
Password: Password@123

Email: bob.ranger@company.com
Dept: IT
Role: staff
Password: Password@123 

# Login information (Sales):
Email: derek.tan@company.com
Dept: Sales
Role: director 
Password: Password@123

Email :sophia.ibrahim@company.com
Dept: Sales
Role: manager 
Password: Password@123

Email: grace.miller@company.com
Dept: Sales
Role: staff 
Password: Password@123

# Login information (Consultancy):
Email: ernest.sim@company.com'
Dept: Consultancy
Role: director 
Password: Password@123

Email: freya.ahmed@company.com
Dept: Consultancy
Role: manager
Password: Password@123

Email: hannah.lim@company.com
Dept: Consultancy
Role: staff 
Password: Password@123

# Login information (Systems):
Email: eric.loh@company.com
Dept: Systems
Role: director
Password: Password@123

Email: ethan.rivera@company.com
Dept: Systems
Role: manager
Password: Password@123

Email: aiden.brooks@company.com
Dept: Systems
Role: manager
Password: Password@123

Email: zoe.martinez@company.com
Dept: Systems
Role: staff
Password: Password@123

Email: nathaniel.cruz@company.com
Dept: Systems
Role: staff
Password: Password@123

# Login information (Engineering):
Email: philip.lee@company.com
Dept: Engineering
Role: director
Password: Password@123

Email: mia.wilson@company.com
Dept: Engineering
Role: manager
Password: Password@123

Email: chloe.garcia@company.com
Dept: Engineering
Role: manager
Password: Password@123

Email: isaac.goldberg@company.com
Dept: Engineering
Role: manager
Password: Password@123

Email: gabriel.moreau@company.com
Dept: Engineering
Role: staff
Password: Password@123

Email: madison.clark@company.com
Dept: Engineering
Role: staff
Password: Password@123

Email: scarlett.lewis@company.com
Dept: Engineering
Role: staff
Password: Password@123