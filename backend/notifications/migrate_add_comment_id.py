"""
Database migration script to add related_comment_id column to notifications table
Run with: python backend/notifications/migrate_add_comment_id.py
"""

import mysql.connector
from mysql.connector import Error

def migrate_database():
    """Add related_comment_id column to notifications table"""
    try:
        # Connect to MySQL
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',  # Add password if you have one
            database='SPM'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Check if column already exists
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = 'SPM' 
                AND TABLE_NAME = 'notifications' 
                AND COLUMN_NAME = 'related_comment_id'
            """)
            
            if cursor.fetchone():
                print("✅ Column 'related_comment_id' already exists")
            else:
                # Add the column
                cursor.execute("""
                    ALTER TABLE notifications 
                    ADD COLUMN related_comment_id INT NULL,
                    ADD CONSTRAINT fk_notifications_comment_id 
                    FOREIGN KEY (related_comment_id) 
                    REFERENCES comments(id) 
                    ON DELETE CASCADE
                """)
                connection.commit()
                print("✅ Added 'related_comment_id' column to notifications table")
            
            cursor.close()
            connection.close()
            print("✅ Migration completed successfully")
            
    except Error as e:
        print(f"❌ Database migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔄 Running database migration...")
    migrate_database()
