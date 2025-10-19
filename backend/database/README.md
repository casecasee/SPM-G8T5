#To update local db everytime someone pushes a change

#Find YOUR_MYSQL_PATH, might be "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"

Then run these commands (replace YOUR_MYSQL_PATH with your actual path):
# Navigate to backend directory
cd backend

# Drop and recreate database
YOUR_MYSQL_PATH -u root -p -e "DROP DATABASE IF EXISTS SPM;"
YOUR_MYSQL_PATH -u root -p -e "CREATE DATABASE SPM;"

# Create all tables
YOUR_MYSQL_PATH -u root -p SPM < database/schema.sql

# Add sample data
YOUR_MYSQL_PATH -u root -p SPM < database/seeds/development.sql



# Install Python Dependencies
pip install -r requirements.txt
