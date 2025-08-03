#!/usr/bin/env python3
"""
Migration script to add tool_requests table to the database.
This script should be run after updating the models.py file.
"""

import sqlite3
import sys
import os

def migrate_tool_requests():
    """Add the tool_requests table to the database"""
    
    # Check if database file exists
    db_path = "./ar_system.db"
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found. Please run the application first to create it.")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if tool_requests table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='tool_requests'
        """)
        
        if cursor.fetchone():
            print("tool_requests table already exists. Migration not needed.")
            return True
        
        # Create the tool_requests table
        cursor.execute("""
            CREATE TABLE tool_requests (
                id VARCHAR PRIMARY KEY,
                job_id VARCHAR NOT NULL,
                dossier_id VARCHAR,
                step_id VARCHAR,
                request_type VARCHAR NOT NULL,
                tool_name VARCHAR NOT NULL,
                query TEXT,
                status VARCHAR NOT NULL,
                response TEXT,
                error_message TEXT,
                started_at DATETIME,
                completed_at DATETIME,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (job_id) REFERENCES jobs (id),
                FOREIGN KEY (dossier_id) REFERENCES evidence_dossiers (id),
                FOREIGN KEY (step_id) REFERENCES research_plan_steps (id)
            )
        """)
        
        # Commit the changes
        conn.commit()
        print("Successfully created tool_requests table.")
        
        # Verify the table was created
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='tool_requests'
        """)
        
        if cursor.fetchone():
            print("Migration completed successfully!")
            return True
        else:
            print("Error: Table was not created properly.")
            return False
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Starting tool_requests table migration...")
    success = migrate_tool_requests()
    if success:
        print("Migration completed successfully!")
        sys.exit(0)
    else:
        print("Migration failed!")
        sys.exit(1) 