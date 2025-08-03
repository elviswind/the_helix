#!/usr/bin/env python3
"""
Migration script to add synthesis_reports table for Checkpoint 7
"""

import sqlite3
import uuid
from datetime import datetime

def migrate_synthesis_report():
    """Add synthesis_reports table to the database"""
    
    conn = sqlite3.connect('ar_system.db')
    cursor = conn.cursor()
    
    try:
        # Check if table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='synthesis_reports'
        """)
        
        if cursor.fetchone() is None:
            # Create synthesis_reports table
            cursor.execute("""
                CREATE TABLE synthesis_reports (
                    id VARCHAR PRIMARY KEY,
                    job_id VARCHAR NOT NULL,
                    content TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES jobs (id)
                )
            """)
            
            print("✅ Created synthesis_reports table")
        else:
            print("ℹ️  synthesis_reports table already exists")
            
        conn.commit()
        
    except Exception as e:
        print(f"❌ Error creating synthesis_reports table: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_synthesis_report() 