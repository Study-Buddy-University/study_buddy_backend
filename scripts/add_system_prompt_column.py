"""
Migration script to add system_prompt column to projects table.
Run this once to update existing database schema.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.models.database import engine

def add_system_prompt_column():
    with engine.connect() as conn:
        try:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='projects' AND column_name='system_prompt'
            """))
            
            if result.fetchone() is None:
                # Add the column
                conn.execute(text("""
                    ALTER TABLE projects 
                    ADD COLUMN system_prompt TEXT NULL
                """))
                conn.commit()
                print("✅ Added system_prompt column to projects table")
            else:
                print("ℹ️  system_prompt column already exists")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            conn.rollback()

if __name__ == "__main__":
    add_system_prompt_column()
