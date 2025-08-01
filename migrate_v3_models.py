#!/usr/bin/env python3
"""
Migration script to add v3.0 Deductive Proxy Framework fields to existing database.
This script adds the new fields required for Checkpoint 5.
"""

import sqlite3
import json
from datetime import datetime

def migrate_database():
    """Migrate the database to add v3.0 fields"""
    
    print("Starting v3.0 database migration...")
    
    # Connect to the database
    conn = sqlite3.connect('ar_system.db')
    cursor = conn.cursor()
    
    try:
        # Check if the new fields already exist
        cursor.execute("PRAGMA table_info(research_plan_steps)")
        research_plan_steps_columns = [column[1] for column in cursor.fetchall()]
        
        cursor.execute("PRAGMA table_info(evidence_items)")
        evidence_items_columns = [column[1] for column in cursor.fetchall()]
        
        # Add new fields to research_plan_steps if they don't exist
        if 'data_gap_identified' not in research_plan_steps_columns:
            print("Adding data_gap_identified column to research_plan_steps...")
            cursor.execute("ALTER TABLE research_plan_steps ADD COLUMN data_gap_identified TEXT")
        
        if 'proxy_hypothesis' not in research_plan_steps_columns:
            print("Adding proxy_hypothesis column to research_plan_steps...")
            cursor.execute("ALTER TABLE research_plan_steps ADD COLUMN proxy_hypothesis TEXT")
        
        # Add new field to evidence_items if it doesn't exist
        if 'tags' not in evidence_items_columns:
            print("Adding tags column to evidence_items...")
            cursor.execute("ALTER TABLE evidence_items ADD COLUMN tags TEXT")
        
        # Commit the changes
        conn.commit()
        print("Migration completed successfully!")
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(research_plan_steps)")
        updated_research_plan_steps_columns = [column[1] for column in cursor.fetchall()]
        print(f"research_plan_steps columns: {updated_research_plan_steps_columns}")
        
        cursor.execute("PRAGMA table_info(evidence_items)")
        updated_evidence_items_columns = [column[1] for column in cursor.fetchall()]
        print(f"evidence_items columns: {updated_evidence_items_columns}")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database() 