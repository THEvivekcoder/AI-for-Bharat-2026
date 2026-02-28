"""
Master script to seed all data into the database.
Runs all individual seeding scripts in the correct order.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
import importlib


def run_seeding_script(script_name: str, db: Session):
    """Import and run a seeding script"""
    try:
        print(f"\n{'=' * 60}")
        print(f"Running: {script_name}")
        print(f"{'=' * 60}\n")
        
        # Import the module
        module = importlib.import_module(f"scripts.{script_name}")
        
        # Get the main seeding functions
        if script_name == "seed_schemes":
            module.seed_schemes(db)
        elif script_name == "seed_health_facilities":
            module.seed_health_facilities(db)
        elif script_name == "seed_skill_programs":
            module.seed_skill_programs(db)
            module.seed_job_postings(db)
        elif script_name == "seed_crop_data":
            module.seed_crop_calendars(db)
            module.seed_mandi_prices(db)
        
        print(f"\n✓ {script_name} completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Error in {script_name}: {e}")
        raise


def main():
    """Main function to run all seeding scripts"""
    print("\n" + "=" * 70)
    print(" " * 15 + "BHARATSAHAYAK DATA SEEDING")
    print("=" * 70)
    print("\nThis script will seed the following data:")
    print("  1. Government Schemes (Central and State)")
    print("  2. Health Facilities (PHCs, CHCs, Hospitals)")
    print("  3. Skill Development Programs")
    print("  4. Government Job Postings")
    print("  5. Crop Calendars")
    print("  6. Mandi Prices")
    print("\n" + "=" * 70)
    
    # Confirm before proceeding
    response = input("\nProceed with seeding? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Seeding cancelled.")
        return
    
    db = SessionLocal()
    
    try:
        # Run seeding scripts in order
        scripts = [
            "seed_schemes",
            "seed_health_facilities",
            "seed_skill_programs",
            "seed_crop_data"
        ]
        
        for script in scripts:
            run_seeding_script(script, db)
        
        print("\n" + "=" * 70)
        print(" " * 20 + "SEEDING COMPLETED!")
        print("=" * 70)
        print("\nAll data has been successfully seeded into the database.")
        print("\nSummary:")
        print("  ✓ Government schemes")
        print("  ✓ Health facilities")
        print("  ✓ Skill development programs")
        print("  ✓ Government job postings")
        print("  ✓ Crop calendars")
        print("  ✓ Mandi prices")
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n{'=' * 70}")
        print(" " * 25 + "SEEDING FAILED!")
        print("=" * 70)
        print(f"\nError: {e}")
        print("\nThe database has been rolled back to its previous state.")
        db.rollback()
        sys.exit(1)
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
