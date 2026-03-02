"""Script to load sample health facilities into DynamoDB."""

import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.health import HealthFacility
from src.core.health_facility_repository import HealthFacilityRepository


def load_health_facilities(json_file: str = "sample_health_facilities.json"):
    """
    Load health facilities from JSON file into DynamoDB.
    
    Args:
        json_file: Path to JSON file with health facility data
    """
    # Get the directory of this script
    script_dir = Path(__file__).parent
    json_path = script_dir / json_file
    
    # Read JSON file
    print(f"Reading health facilities from {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        facilities_data = json.load(f)
    
    print(f"Found {len(facilities_data)} health facilities to load")
    
    # Initialize repository
    table_name = os.environ.get('HEALTH_FACILITIES_TABLE', 'HealthFacilities')
    region = os.environ.get('AWS_REGION', 'us-east-1')
    
    print(f"Using table: {table_name} in region: {region}")
    repository = HealthFacilityRepository(table_name=table_name, region_name=region)
    
    # Load each facility
    loaded_count = 0
    error_count = 0
    
    for facility_data in facilities_data:
        try:
            facility = HealthFacility(**facility_data)
            repository.create(facility)
            print(f"✓ Loaded: {facility.name} ({facility.facility_id})")
            loaded_count += 1
        except Exception as e:
            print(f"✗ Error loading {facility_data.get('name', 'unknown')}: {e}")
            error_count += 1
    
    print(f"\n{'='*60}")
    print(f"Load complete!")
    print(f"Successfully loaded: {loaded_count}")
    print(f"Errors: {error_count}")
    print(f"{'='*60}")


if __name__ == "__main__":
    load_health_facilities()
