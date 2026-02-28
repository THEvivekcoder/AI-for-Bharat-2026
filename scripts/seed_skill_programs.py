"""
Script to seed skill development programs data into the database.
This includes various skill training programs under PMKVY and other schemes.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.skills import SkillProgram, JobPosting
from datetime import datetime, date, timedelta
from decimal import Decimal
import uuid


def seed_skill_programs(db: Session):
    """Seed skill development programs data"""
    
    programs_data = [
        # Technical skills
        {
            "name": "Computer Hardware and Networking",
            "provider": "PMKVY Training Center",
            "category": "technical",
            "description": "Comprehensive training in computer hardware assembly, troubleshooting, and networking fundamentals. Covers PC assembly, peripheral installation, network configuration, and basic server management.",
            "duration_weeks": 12,
            "cost": Decimal("0.00"),  # Free under PMKVY
            "state": "Uttar Pradesh",
            "district": "Lucknow",
            "mode": "in-person",
            "eligibility_criteria": {
                "age_min": 18,
                "age_max": 35,
                "education": ["10th", "12th", "ITI"]
            },
            "certification": True,
            "placement_support": True,
            "registration_url": "https://www.pmkvyofficial.org/",
            "contact": "+91-522-234-5678"
        },
        {
            "name": "Mobile Repair and Maintenance",
            "provider": "Skill India Training Partner",
            "category": "technical",
            "description": "Training in mobile phone repair, troubleshooting, and maintenance. Covers hardware repair, software installation, and customer service skills.",
            "duration_weeks": 8,
            "cost": Decimal("0.00"),
            "state": "Maharashtra",
            "district": "Mumbai",
            "mode": "in-person",
            "eligibility_criteria": {
                "age_min": 18,
                "age_max": 40,
                "education": ["8th", "10th", "12th"]
            },
            "certification": True,
            "placement_support": True,
            "registration_url": "https://www.pmkvyofficial.org/",
            "contact": "+91-22-2345-6789"
        },
        {
            "name": "Web Development Bootcamp",
            "provider": "National Skill Development Corporation",
            "category": "technical",
            "description": "Intensive web development training covering HTML, CSS, JavaScript, and modern frameworks. Includes hands-on projects and portfolio development.",
            "duration_weeks": 16,
            "cost": Decimal("5000.00"),
            "state": "Karnataka",
            "district": "Bangalore",
            "mode": "hybrid",
            "eligibility_criteria": {
                "age_min": 18,
                "age_max": 35,
                "education": ["12th", "graduate"]
            },
            "certification": True,
            "placement_support": True,
            "registration_url": "https://nsdcindia.org/",
            "contact": "+91-80-2345-6789"
        },
        
        # Vocational skills
        {
            "name": "Tailoring and Garment Making",
            "provider": "Women's Skill Development Center",
            "category": "vocational",
            "description": "Comprehensive tailoring course covering basic to advanced stitching, pattern making, and garment construction. Includes business skills for self-employment.",
            "duration_weeks": 12,
            "cost": Decimal("0.00"),
            "state": "Rajasthan",
            "district": "Jaipur",
            "mode": "in-person",
            "eligibility_criteria": {
                "age_min": 18,
                "age_max": 45,
                "education": ["5th", "8th", "10th"]
            },
            "certification": True,
            "placement_support": False,
            "registration_url": "https://www.pmkvyofficial.org/",
            "contact": "+91-141-234-5678"
        },
        {
            "name": "Plumbing and Sanitation",
            "provider": "Construction Skill Development Council",
            "category": "vocational",
            "description": "Training in plumbing installation, repair, and maintenance. Covers water supply systems, drainage, and sanitation fixtures.",
            "duration_weeks": 10,
            "cost": Decimal("0.00"),
            "state": "Gujarat",
            "district": "Ahmedabad",
            "mode": "in-person",
            "eligibility_criteria": {
                "age_min": 18,
                "age_max": 40,
                "education": ["8th", "10th"]
            },
            "certification": True,
            "placement_support": True,
            "registration_url": "https://www.pmkvyofficial.org/",
            "contact": "+91-79-2345-6789"
        },
        {
            "name": "Beautician and Cosmetology",
            "provider": "Beauty and Wellness Sector Skill Council",
            "category": "vocational",
            "description": "Professional beauty and wellness training covering hair care, skin care, makeup, and salon management.",
            "duration_weeks": 16,
            "cost": Decimal("3000.00"),
            "state": "Delhi",
            "district": "New Delhi",
            "mode": "in-person",
            "eligibility_criteria": {
                "age_min": 18,
                "age_max": 35,
                "education": ["10th", "12th"]
            },
            "certification": True,
            "placement_support": True,
            "registration_url": "https://www.pmkvyofficial.org/",
            "contact": "+91-11-2345-6789"
        },
        {
            "name": "Electrician Training",
            "provider": "Industrial Training Institute",
            "category": "vocational",
            "description": "Comprehensive electrical training covering domestic and industrial wiring, motor repair, and electrical safety.",
            "duration_weeks": 24,
            "cost": Decimal("2000.00"),
            "state": "Tamil Nadu",
            "district": "Chennai",
            "mode": "in-person",
            "eligibility_criteria": {
                "age_min": 18,
                "age_max": 35,
                "education": ["10th", "12th"]
            },
            "certification": True,
            "placement_support": True,
            "registration_url": "https://www.dget.nic.in/",
            "contact": "+91-44-2345-6789"
        },
        
        # Digital skills
        {
            "name": "Digital Literacy and Computer Basics",
            "provider": "Pradhan Mantri Gramin Digital Saksharta Abhiyan",
            "category": "digital",
            "description": "Basic digital literacy training covering computer fundamentals, internet usage, email, and digital payments.",
            "duration_weeks": 4,
            "cost": Decimal("0.00"),
            "state": "Bihar",
            "district": "Patna",
            "mode": "in-person",
            "eligibility_criteria": {
                "age_min": 14,
                "age_max": 60,
                "education": ["literate"]
            },
            "certification": True,
            "placement_support": False,
            "registration_url": "https://www.pmgdisha.in/",
            "contact": "+91-612-234-5678"
        },
        {
            "name": "Digital Marketing and Social Media",
            "provider": "Digital India Training Center",
            "category": "digital",
            "description": "Training in digital marketing strategies, social media management, content creation, and online advertising.",
            "duration_weeks": 12,
            "cost": Decimal("8000.00"),
            "state": "Maharashtra",
            "district": "Pune",
            "mode": "online",
            "eligibility_criteria": {
                "age_min": 18,
                "age_max": 40,
                "education": ["12th", "graduate"]
            },
            "certification": True,
            "placement_support": True,
            "registration_url": "https://digitalindia.gov.in/",
            "contact": "+91-20-2345-6789"
        },
        {
            "name": "Data Entry and Office Automation",
            "provider": "NIELIT Training Center",
            "category": "digital",
            "description": "Training in data entry, MS Office applications, and office automation tools. Covers typing, spreadsheets, and document processing.",
            "duration_weeks": 8,
            "cost": Decimal("1500.00"),
            "state": "West Bengal",
            "district": "Kolkata",
            "mode": "in-person",
            "eligibility_criteria": {
                "age_min": 18,
                "age_max": 35,
                "education": ["10th", "12th"]
            },
            "certification": True,
            "placement_support": True,
            "registration_url": "https://www.nielit.gov.in/",
            "contact": "+91-33-2345-6789"
        },
        
        # Entrepreneurship
        {
            "name": "Small Business Management",
            "provider": "Entrepreneurship Development Institute",
            "category": "entrepreneurship",
            "description": "Training for aspiring entrepreneurs covering business planning, financial management, marketing, and legal compliance.",
            "duration_weeks": 6,
            "cost": Decimal("5000.00"),
            "state": "Gujarat",
            "district": "Gandhinagar",
            "mode": "hybrid",
            "eligibility_criteria": {
                "age_min": 21,
                "age_max": 45,
                "education": ["12th", "graduate"]
            },
            "certification": True,
            "placement_support": False,
            "registration_url": "https://www.ediindia.org/",
            "contact": "+91-79-2345-6789"
        },
        {
            "name": "Rural Entrepreneurship Development",
            "provider": "NABARD Training Center",
            "category": "entrepreneurship",
            "description": "Specialized training for rural entrepreneurs in agriculture-based businesses, micro-enterprises, and self-help groups.",
            "duration_weeks": 8,
            "cost": Decimal("0.00"),
            "state": "Madhya Pradesh",
            "district": "Bhopal",
            "mode": "in-person",
            "eligibility_criteria": {
                "age_min": 18,
                "age_max": 50,
                "education": ["8th", "10th", "12th"]
            },
            "certification": True,
            "placement_support": False,
            "registration_url": "https://www.nabard.org/",
            "contact": "+91-755-234-5678"
        },
        
        # Agriculture-related skills
        {
            "name": "Organic Farming and Sustainable Agriculture",
            "provider": "Krishi Vigyan Kendra",
            "category": "vocational",
            "description": "Training in organic farming methods, composting, natural pest control, and sustainable agricultural practices.",
            "duration_weeks": 6,
            "cost": Decimal("0.00"),
            "state": "Punjab",
            "district": "Ludhiana",
            "mode": "in-person",
            "eligibility_criteria": {
                "age_min": 18,
                "age_max": 55,
                "occupation": ["farmer", "agricultural_worker"]
            },
            "certification": True,
            "placement_support": False,
            "registration_url": "https://kvk.icar.gov.in/",
            "contact": "+91-161-234-5678"
        },
        {
            "name": "Dairy Farming and Management",
            "provider": "National Dairy Development Board",
            "category": "vocational",
            "description": "Comprehensive training in dairy farming, cattle management, milk production, and dairy business management.",
            "duration_weeks": 12,
            "cost": Decimal("2000.00"),
            "state": "Haryana",
            "district": "Karnal",
            "mode": "in-person",
            "eligibility_criteria": {
                "age_min": 18,
                "age_max": 50,
                "occupation": ["farmer", "agricultural_worker"]
            },
            "certification": True,
            "placement_support": False,
            "registration_url": "https://www.nddb.coop/",
            "contact": "+91-184-234-5678"
        },
        
        # Healthcare skills
        {
            "name": "Community Health Worker Training",
            "provider": "National Health Mission",
            "category": "vocational",
            "description": "Training for community health workers (ASHA) covering basic healthcare, maternal and child health, and health education.",
            "duration_weeks": 8,
            "cost": Decimal("0.00"),
            "state": "Uttar Pradesh",
            "district": "Varanasi",
            "mode": "in-person",
            "eligibility_criteria": {
                "age_min": 21,
                "age_max": 45,
                "gender": "female",
                "education": ["8th", "10th"]
            },
            "certification": True,
            "placement_support": True,
            "registration_url": "https://nhm.gov.in/",
            "contact": "+91-542-234-5678"
        },
        {
            "name": "Nursing Assistant Training",
            "provider": "Healthcare Sector Skill Council",
            "category": "vocational",
            "description": "Training for nursing assistants covering patient care, basic nursing procedures, and hospital protocols.",
            "duration_weeks": 16,
            "cost": Decimal("10000.00"),
            "state": "Kerala",
            "district": "Kochi",
            "mode": "in-person",
            "eligibility_criteria": {
                "age_min": 18,
                "age_max": 35,
                "education": ["12th"]
            },
            "certification": True,
            "placement_support": True,
            "registration_url": "https://www.pmkvyofficial.org/",
            "contact": "+91-484-234-5678"
        }
    ]
    
    print(f"Seeding {len(programs_data)} skill development programs...")
    
    for program_data in programs_data:
        program = SkillProgram(
            program_id=uuid.uuid4(),
            **program_data
        )
        db.add(program)
        print(f"  ✓ Added: {program.name} ({program.category}, {program.district})")
    
    db.commit()
    print(f"\n✓ Successfully seeded {len(programs_data)} skill programs!")


def seed_job_postings(db: Session):
    """Seed sample government job postings"""
    
    # Calculate dates relative to today
    today = date.today()
    
    jobs_data = [
        {
            "title": "Junior Engineer (Civil)",
            "department": "Public Works Department",
            "description": "Recruitment for Junior Engineer positions in Civil Engineering for various infrastructure projects.",
            "qualifications": {
                "education": "Diploma or B.Tech in Civil Engineering",
                "experience_years": 0,
                "age_max": 30
            },
            "location": {
                "states": ["Uttar Pradesh", "Bihar", "Madhya Pradesh"],
                "districts": ["Multiple"]
            },
            "application_deadline": today + timedelta(days=30),
            "application_url": "https://www.sarkariresult.com/",
            "posted_date": today - timedelta(days=5)
        },
        {
            "title": "Primary School Teacher",
            "department": "Department of Education",
            "description": "Recruitment for Primary School Teachers for government schools across the state.",
            "qualifications": {
                "education": "B.Ed or D.El.Ed",
                "experience_years": 0,
                "age_max": 35
            },
            "location": {
                "states": ["Rajasthan"],
                "districts": ["Jaipur", "Jodhpur", "Udaipur", "Kota"]
            },
            "application_deadline": today + timedelta(days=45),
            "application_url": "https://education.rajasthan.gov.in/",
            "posted_date": today - timedelta(days=10)
        },
        {
            "title": "Staff Nurse",
            "department": "Health and Family Welfare",
            "description": "Recruitment for Staff Nurse positions in government hospitals and health centers.",
            "qualifications": {
                "education": "B.Sc Nursing or GNM",
                "experience_years": 0,
                "age_max": 32
            },
            "location": {
                "states": ["Maharashtra"],
                "districts": ["Mumbai", "Pune", "Nagpur"]
            },
            "application_deadline": today + timedelta(days=25),
            "application_url": "https://www.maharashtra.gov.in/",
            "posted_date": today - timedelta(days=3)
        },
        {
            "title": "Agriculture Extension Officer",
            "department": "Department of Agriculture",
            "description": "Recruitment for Agriculture Extension Officers to provide technical guidance to farmers.",
            "qualifications": {
                "education": "B.Sc Agriculture",
                "experience_years": 0,
                "age_max": 30
            },
            "location": {
                "states": ["Punjab", "Haryana"],
                "districts": ["Multiple"]
            },
            "application_deadline": today + timedelta(days=40),
            "application_url": "https://www.agricoop.nic.in/",
            "posted_date": today - timedelta(days=7)
        },
        {
            "title": "Computer Operator",
            "department": "Various Government Departments",
            "description": "Recruitment for Computer Operators for data entry and office automation work.",
            "qualifications": {
                "education": "12th with Computer Knowledge",
                "experience_years": 0,
                "age_max": 28,
                "skills": ["Typing", "MS Office", "Data Entry"]
            },
            "location": {
                "states": ["Karnataka", "Tamil Nadu"],
                "districts": ["Bangalore", "Chennai", "Mysore", "Coimbatore"]
            },
            "application_deadline": today + timedelta(days=20),
            "application_url": "https://www.sarkariresult.com/",
            "posted_date": today - timedelta(days=2)
        },
        {
            "title": "Anganwadi Worker",
            "department": "Women and Child Development",
            "description": "Recruitment for Anganwadi Workers for child care and nutrition programs.",
            "qualifications": {
                "education": "10th Pass",
                "experience_years": 0,
                "age_min": 21,
                "age_max": 45,
                "gender": "Female"
            },
            "location": {
                "states": ["Uttar Pradesh", "Bihar"],
                "districts": ["Multiple"]
            },
            "application_deadline": today + timedelta(days=35),
            "application_url": "https://www.wcd.nic.in/",
            "posted_date": today - timedelta(days=8)
        },
        {
            "title": "Forest Guard",
            "department": "Forest Department",
            "description": "Recruitment for Forest Guards for wildlife protection and forest conservation.",
            "qualifications": {
                "education": "12th Pass",
                "experience_years": 0,
                "age_max": 28,
                "physical_requirements": "Physical fitness test required"
            },
            "location": {
                "states": ["Madhya Pradesh", "Chhattisgarh"],
                "districts": ["Multiple"]
            },
            "application_deadline": today + timedelta(days=50),
            "application_url": "https://forest.mp.gov.in/",
            "posted_date": today - timedelta(days=12)
        },
        {
            "title": "Junior Accountant",
            "department": "Finance Department",
            "description": "Recruitment for Junior Accountants for accounting and financial record maintenance.",
            "qualifications": {
                "education": "B.Com or equivalent",
                "experience_years": 0,
                "age_max": 30,
                "skills": ["Accounting", "Tally", "MS Excel"]
            },
            "location": {
                "states": ["Gujarat"],
                "districts": ["Ahmedabad", "Surat", "Vadodara"]
            },
            "application_deadline": today + timedelta(days=28),
            "application_url": "https://www.gujaratinformatics.com/",
            "posted_date": today - timedelta(days=6)
        }
    ]
    
    print(f"\nSeeding {len(jobs_data)} government job postings...")
    
    for job_data in jobs_data:
        job = JobPosting(
            job_id=uuid.uuid4(),
            last_updated=datetime.utcnow(),
            **job_data
        )
        db.add(job)
        print(f"  ✓ Added: {job.title} ({job.department})")
    
    db.commit()
    print(f"\n✓ Successfully seeded {len(jobs_data)} job postings!")


def main():
    """Main function to run seeding"""
    print("=" * 60)
    print("Skill Programs and Job Postings Data Seeding")
    print("=" * 60)
    print()
    
    db = SessionLocal()
    try:
        seed_skill_programs(db)
        seed_job_postings(db)
    except Exception as e:
        print(f"\n✗ Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()
    
    print("\n" + "=" * 60)
    print("Seeding completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
