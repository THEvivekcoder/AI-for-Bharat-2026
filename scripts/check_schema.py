"""Check database schema"""
from app.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)

print("Scheme table columns:")
cols = inspector.get_columns('schemes')
for c in cols:
    print(f"  - {c['name']}: {c['type']}")

print("\nMandi Prices table columns:")
cols = inspector.get_columns('mandi_prices')
for c in cols:
    print(f"  - {c['name']}: {c['type']}")

print("\nJob Postings table columns:")
cols = inspector.get_columns('job_postings')
for c in cols:
    print(f"  - {c['name']}: {c['type']}")
