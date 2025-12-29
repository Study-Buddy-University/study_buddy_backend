"""
Migration script to fix timestamp defaults in projects table.
Run this once to add default now() to created_at and updated_at columns.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.models.database import engine

def fix_timestamp_defaults():
    with engine.connect() as conn:
        try:
            # Add default to created_at
            conn.execute(text("""
                ALTER TABLE projects 
                ALTER COLUMN created_at SET DEFAULT now()
            """))
            print("✅ Added default now() to created_at column")
            
            # Add default to updated_at
            conn.execute(text("""
                ALTER TABLE projects 
                ALTER COLUMN updated_at SET DEFAULT now()
            """))
            print("✅ Added default now() to updated_at column")
            
            conn.commit()
            
            # Verify
            result = conn.execute(text("""
                SELECT column_name, column_default 
                FROM information_schema.columns 
                WHERE table_name='projects' AND column_name IN ('created_at', 'updated_at')
            """))
            print("\n📋 Current defaults:")
            for row in result:
                print(f"  {row[0]}: {row[1]}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            conn.rollback()

if __name__ == "__main__":
    fix_timestamp_defaults()
