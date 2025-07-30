#!/usr/bin/env python3
"""
Migration script to add LLMRequest table to existing database
"""

import sqlite3
import os

def migrate_llm_requests():
    """Add LLMRequest table to existing database"""
    
    db_path = "ar_system.db"
    
    if not os.path.exists(db_path):
        print("Database file not found. Creating new database with all tables...")
        from models import create_tables
        create_tables()
        print("✅ Database created with all tables including LLMRequest")
        return
    
    print("🔄 Migrating existing database to add LLMRequest table...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if LLMRequest table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='llm_requests'")
        if cursor.fetchone():
            print("✅ LLMRequest table already exists")
            return
        
        # Create LLMRequest table
        cursor.execute("""
            CREATE TABLE llm_requests (
                id VARCHAR PRIMARY KEY,
                job_id VARCHAR NOT NULL,
                dossier_id VARCHAR,
                request_type VARCHAR NOT NULL,
                status VARCHAR NOT NULL,
                prompt TEXT NOT NULL,
                response TEXT,
                error_message TEXT,
                started_at DATETIME,
                completed_at DATETIME,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (job_id) REFERENCES jobs (id),
                FOREIGN KEY (dossier_id) REFERENCES evidence_dossiers (id)
            )
        """)
        
        conn.commit()
        print("✅ LLMRequest table created successfully")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_llm_requests() 