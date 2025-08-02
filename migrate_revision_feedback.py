#!/usr/bin/env python3
"""
Migration script to add RevisionFeedback table for Checkpoint 6
"""

import sqlite3
import sys

def migrate():
    """Add RevisionFeedback table to the database"""
    
    try:
        # Connect to the database
        conn = sqlite3.connect('ar_system.db')
        cursor = conn.cursor()
        
        # Check if the table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='revision_feedback'
        """)
        
        if cursor.fetchone():
            print("RevisionFeedback table already exists. Skipping migration.")
            return
        
        # Create the revision_feedback table
        cursor.execute("""
            CREATE TABLE revision_feedback (
                id VARCHAR PRIMARY KEY,
                dossier_id VARCHAR NOT NULL,
                feedback TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                processed_at DATETIME,
                FOREIGN KEY (dossier_id) REFERENCES evidence_dossiers (id)
            )
        """)
        
        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX idx_revision_feedback_dossier_id 
            ON revision_feedback (dossier_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_revision_feedback_processed_at 
            ON revision_feedback (processed_at)
        """)
        
        # Commit the changes
        conn.commit()
        print("✅ Successfully created revision_feedback table")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    migrate() 