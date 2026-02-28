"""Reset database and run migrations"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import engine
from sqlalchemy import text

# Drop alembic version table
with engine.connect() as conn:
    conn.execute(text('DROP TABLE IF EXISTS alembic_version CASCADE'))
    conn.commit()
    print("✓ Alembic version table dropped")

print("\nNow run: alembic upgrade head")
