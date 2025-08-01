#!/usr/bin/env python3
"""
Utility script to detect and fix stuck jobs in the Agentic Retrieval System.

This script identifies jobs that are stuck in RESEARCHING status but have all their
dossiers in AWAITING_VERIFICATION status, and updates them to AWAITING_VERIFICATION.
"""

import sqlite3
import sys
from datetime import datetime

def get_stuck_jobs():
    """Get all jobs that are stuck in RESEARCHING status but have complete dossiers"""
    conn = sqlite3.connect('ar_system.db')
    cursor = conn.cursor()
    
    query = """
    SELECT j.id, j.status, j.created_at, COUNT(d.id) as dossier_count, 
           COUNT(CASE WHEN d.status = 'AWAITING_VERIFICATION' THEN 1 END) as awaiting_verification_count
    FROM jobs j 
    LEFT JOIN evidence_dossiers d ON j.id = d.job_id 
    GROUP BY j.id 
    HAVING j.status = 'RESEARCHING' AND awaiting_verification_count = dossier_count AND dossier_count > 0
    ORDER BY j.created_at DESC
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    
    return results

def fix_stuck_jobs():
    """Fix all stuck jobs by updating their status to AWAITING_VERIFICATION"""
    conn = sqlite3.connect('ar_system.db')
    cursor = conn.cursor()
    
    # Get stuck jobs first
    stuck_jobs = get_stuck_jobs()
    
    if not stuck_jobs:
        print("No stuck jobs found.")
        return 0
    
    print(f"Found {len(stuck_jobs)} stuck jobs:")
    for job in stuck_jobs:
        print(f"  - {job[0]} (created: {job[2]})")
    
    # Update all stuck jobs
    update_query = """
    UPDATE jobs 
    SET status = 'AWAITING_VERIFICATION' 
    WHERE id IN (
        SELECT j.id 
        FROM jobs j 
        LEFT JOIN evidence_dossiers d ON j.id = d.job_id 
        GROUP BY j.id 
        HAVING j.status = 'RESEARCHING' AND 
               COUNT(CASE WHEN d.status = 'AWAITING_VERIFICATION' THEN 1 END) = COUNT(d.id) AND 
               COUNT(d.id) > 0
    )
    """
    
    cursor.execute(update_query)
    updated_count = cursor.rowcount
    conn.commit()
    conn.close()
    
    print(f"\nFixed {updated_count} stuck jobs.")
    return updated_count

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        # Just check for stuck jobs without fixing
        stuck_jobs = get_stuck_jobs()
        if stuck_jobs:
            print(f"Found {len(stuck_jobs)} stuck jobs:")
            for job in stuck_jobs:
                print(f"  - {job[0]} (created: {job[2]})")
        else:
            print("No stuck jobs found.")
    else:
        # Fix stuck jobs
        print(f"Checking for stuck jobs at {datetime.now()}")
        fixed_count = fix_stuck_jobs()
        if fixed_count > 0:
            print(f"Successfully fixed {fixed_count} stuck jobs.")
        else:
            print("No stuck jobs to fix.")

if __name__ == "__main__":
    main() 