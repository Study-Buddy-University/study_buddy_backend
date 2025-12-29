#!/usr/bin/env python3
"""Run SQL migration to fix timestamp defaults"""
import sys
import os
from sqlalchemy import create_engine, text

def run_migration():
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:studybuddy_secure_2024@postgres:5432/studybuddy")
    engine = create_engine(database_url)
    
    with engine.connect() as conn:
        # Run migration
        conn.execute(text("ALTER TABLE projects ALTER COLUMN created_at SET DEFAULT now();"))
        conn.execute(text("ALTER TABLE projects ALTER COLUMN updated_at SET DEFAULT now();"))
        conn.commit()
        print("✅ Migration complete - timestamp defaults added")
        
        # Verify
        result = conn.execute(text("SELECT column_name, column_default FROM information_schema.columns WHERE table_name='projects' AND column_name IN ('created_at', 'updated_at')"))
        for row in result:
            print(f"  {row[0]}: {row[1]}")

if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
