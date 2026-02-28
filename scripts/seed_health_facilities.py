"""
Script to seed health facilities data into the database.
This includes PHCs, CHCs, District Hospitals, and Specialty Centers across India.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.health import HealthFacility
from datetime import datetime
import uuid


def seed_health_facilities(db: Session):
    """Seed health facilities data"""
    
    facilities_data = [
        # Primary Health Centers (PHCs)
        {
            "name": "PHC Rampur",
            "facility_type": "PHC",
            "state": "Uttar Pradesh",
            "district": "Rampur",
            "address": "Village Rampur, Block Rampur, Uttar Pradesh - 244901",
            "latitude": 28.8094,
            "longitude": 79.0250,
            "contact": "+91-5925-234567",
            "services": [
                "OPD services",
                "Maternal and child health",
                "Immunization",
                "Family planning",
                "Basic laboratory services",
                "Essential medicines"
            ]
        },
        {
            "name": "PHC Khandwa",
            "facility_type": "PHC",
            "state": "Madhya Pradesh",
            "district": "Khandwa",
            "address": "Khandwa Road, Khandwa, Madhya Pradesh - 450001",
            "latitude": 21.8333,
            "longitude": 76.3500,
            "contact": "+91-733-222-3456",
            "services": [
                "OPD services",
                "Maternal health",
                "Child health",
                "Immunization",
                "Basic diagnostics",
                "Emergency care"
            ]
        },
        {
            "name": "PHC Warangal Rural",
            "facility_type": "PHC",
            "state": "Telangana",
            "district": "Warangal",
            "address": "Warangal Rural, Telangana - 506001",
            "latitude": 17.9784,
            "longitude": 79.5941,
            "contact": "+91-870-245-6789",
            "services": [
                "Primary healthcare",
                "Maternal services",
                "Immunization",
                "Family welfare",
                "Basic lab tests"
            ]
        },
        
        # Community Health Centers (CHCs)
        {
            "name": "CHC Saharanpur",
            "facility_type": "CHC",
            "state": "Uttar Pradesh",
            "district": "Saharanpur",
            "address": "Delhi Road, Saharanpur, Uttar Pradesh - 247001",
            "latitude": 29.9680,
            "longitude": 77.5460,
            "contact": "+91-132-276-5432",
            "services": [
                "24x7 emergency services",
                "Inpatient care (30 beds)",
                "Surgery (minor)",
                "Obstetrics and gynecology",
                "Pediatrics",
                "Laboratory services",
                "X-ray facility",
                "Blood storage"
            ]
        },
        {
            "name": "CHC Indore Rural",
            "facility_type": "CHC",
            "state": "Madhya Pradesh",
            "district": "Indore",
            "address": "Indore-Ujjain Road, Indore, Madhya Pradesh - 452001",
            "latitude": 22.7196,
            "longitude": 75.8577,
            "contact": "+91-731-234-5678",
            "services": [
                "Emergency services",
                "Inpatient care",
                "Surgical services",
                "Maternity services",
                "Pediatric care",
                "Diagnostic services",
                "Pharmacy"
            ]
        },
        {
            "name": "CHC Nizamabad",
            "facility_type": "CHC",
            "state": "Telangana",
            "district": "Nizamabad",
            "address": "Armoor Road, Nizamabad, Telangana - 503001",
            "latitude": 18.6725,
            "longitude": 78.0941,
            "contact": "+91-8461-234567",
            "services": [
                "24x7 emergency",
                "Inpatient services",
                "Surgery",
                "Maternity ward",
                "Laboratory",
                "X-ray",
                "Ambulance service"
            ]
        },
        
        # District Hospitals
        {
            "name": "District Hospital Meerut",
            "facility_type": "District Hospital",
            "state": "Uttar Pradesh",
            "district": "Meerut",
            "address": "Meerut Cantt, Meerut, Uttar Pradesh - 250001",
            "latitude": 28.9845,
            "longitude": 77.7064,
            "contact": "+91-121-266-7890",
            "services": [
                "24x7 emergency and trauma care",
                "Inpatient care (200+ beds)",
                "General surgery",
                "Orthopedics",
                "Obstetrics and gynecology",
                "Pediatrics",
                "Medicine",
                "ICU and CCU",
                "Blood bank",
                "Advanced diagnostics",
                "CT scan and ultrasound",
                "Ambulance services"
            ]
        },
        {
            "name": "District Hospital Bhopal",
            "facility_type": "District Hospital",
            "state": "Madhya Pradesh",
            "district": "Bhopal",
            "address": "Sultania Road, Bhopal, Madhya Pradesh - 462001",
            "latitude": 23.2599,
            "longitude": 77.4126,
            "contact": "+91-755-277-8901",
            "services": [
                "Emergency services",
                "Multi-specialty care",
                "Surgery",
                "Medicine",
                "Pediatrics",
                "Gynecology",
                "Orthopedics",
                "ICU",
                "Dialysis",
                "Blood bank",
                "Diagnostic center",
                "Pharmacy"
            ]
        },
        {
            "name": "District Hospital Hyderabad",
            "facility_type": "District Hospital",
            "state": "Telangana",
            "district": "Hyderabad",
            "address": "Nampally, Hyderabad, Telangana - 500001",
            "latitude": 17.3850,
            "longitude": 78.4867,
            "contact": "+91-40-2345-6789",
            "services": [
                "24x7 emergency",
                "Multi-specialty services",
                "Surgery",
                "Medicine",
                "Pediatrics",
                "Obstetrics",
                "Cardiology",
                "Neurology",
                "ICU and NICU",
                "Blood bank",
                "Advanced diagnostics",
                "Ambulance"
            ]
        },
        
        # Specialty Centers
        {
            "name": "TB Hospital Agra",
            "facility_type": "Specialty Center",
            "state": "Uttar Pradesh",
            "district": "Agra",
            "address": "MG Road, Agra, Uttar Pradesh - 282001",
            "latitude": 27.1767,
            "longitude": 78.0081,
            "contact": "+91-562-222-3456",
            "services": [
                "TB diagnosis and treatment",
                "DOTS center",
                "Drug-resistant TB care",
                "Contact tracing",
                "Counseling services",
                "Free medicines"
            ]
        },
        {
            "name": "Maternity Hospital Gwalior",
            "facility_type": "Specialty Center",
            "state": "Madhya Pradesh",
            "district": "Gwalior",
            "address": "Lashkar, Gwalior, Madhya Pradesh - 474001",
            "latitude": 26.2183,
            "longitude": 78.1828,
            "contact": "+91-751-234-5678",
            "services": [
                "Antenatal care",
                "Normal delivery",
                "C-section",
                "High-risk pregnancy care",
                "Neonatal care",
                "Family planning",
                "Postnatal care"
            ]
        },
        {
            "name": "Eye Hospital Warangal",
            "facility_type": "Specialty Center",
            "state": "Telangana",
            "district": "Warangal",
            "address": "Hanamkonda, Warangal, Telangana - 506001",
            "latitude": 17.9784,
            "longitude": 79.5941,
            "contact": "+91-870-256-7890",
            "services": [
                "Cataract surgery",
                "Glaucoma treatment",
                "Retinal services",
                "Pediatric ophthalmology",
                "Free eye camps",
                "Optical services"
            ]
        },
        
        # Additional facilities across different states
        {
            "name": "PHC Patna Rural",
            "facility_type": "PHC",
            "state": "Bihar",
            "district": "Patna",
            "address": "Danapur, Patna, Bihar - 801503",
            "latitude": 25.5941,
            "longitude": 85.1376,
            "contact": "+91-612-234-5678",
            "services": [
                "Primary healthcare",
                "Maternal and child health",
                "Immunization",
                "Family planning",
                "Basic diagnostics"
            ]
        },
        {
            "name": "CHC Jaipur Rural",
            "facility_type": "CHC",
            "state": "Rajasthan",
            "district": "Jaipur",
            "address": "Sanganer, Jaipur, Rajasthan - 302029",
            "latitude": 26.9124,
            "longitude": 75.7873,
            "contact": "+91-141-234-5678",
            "services": [
                "Emergency services",
                "Inpatient care",
                "Surgery",
                "Maternity services",
                "Laboratory",
                "X-ray"
            ]
        },
        {
            "name": "District Hospital Kolkata",
            "facility_type": "District Hospital",
            "state": "West Bengal",
            "district": "Kolkata",
            "address": "College Street, Kolkata, West Bengal - 700073",
            "latitude": 22.5726,
            "longitude": 88.3639,
            "contact": "+91-33-2234-5678",
            "services": [
                "24x7 emergency",
                "Multi-specialty care",
                "Surgery",
                "Medicine",
                "Pediatrics",
                "Gynecology",
                "ICU",
                "Blood bank",
                "Diagnostics"
            ]
        },
        {
            "name": "PHC Pune Rural",
            "facility_type": "PHC",
            "state": "Maharashtra",
            "district": "Pune",
            "address": "Haveli, Pune, Maharashtra - 412308",
            "latitude": 18.5204,
            "longitude": 73.8567,
            "contact": "+91-20-2345-6789",
            "services": [
                "Primary healthcare",
                "Maternal health",
                "Immunization",
                "Family welfare",
                "Basic lab services"
            ]
        },
        {
            "name": "CHC Bangalore Rural",
            "facility_type": "CHC",
            "state": "Karnataka",
            "district": "Bangalore Rural",
            "address": "Devanahalli, Bangalore, Karnataka - 562110",
            "latitude": 13.2443,
            "longitude": 77.7122,
            "contact": "+91-80-2345-6789",
            "services": [
                "Emergency services",
                "Inpatient care",
                "Surgery",
                "Maternity ward",
                "Laboratory",
                "Ambulance"
            ]
        }
    ]
    
    print(f"Seeding {len(facilities_data)} health facilities...")
    
    for facility_data in facilities_data:
        facility = HealthFacility(
            facility_id=uuid.uuid4(),
            **facility_data
        )
        db.add(facility)
        print(f"  ✓ Added: {facility.name} ({facility.facility_type}, {facility.district})")
    
    db.commit()
    print(f"\n✓ Successfully seeded {len(facilities_data)} health facilities!")


def main():
    """Main function to run seeding"""
    print("=" * 60)
    print("Health Facilities Data Seeding")
    print("=" * 60)
    print()
    
    db = SessionLocal()
    try:
        seed_health_facilities(db)
    except Exception as e:
        print(f"\n✗ Error seeding health facilities: {e}")
        db.rollback()
        raise
    finally:
        db.close()
    
    print("\n" + "=" * 60)
    print("Seeding completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
