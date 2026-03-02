#!/usr/bin/env python3
"""
Skill programs and job postings data loader script for BharatSahayak.

This script loads skill development programs and government job postings
into DynamoDB tables. It includes sample data for testing.
"""

import json
import logging
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.skill import SkillProgram, JobPosting
from src.models.eligibility import EligibilityCriteria
from src.models.location import Location

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_sample_skill_programs() -> List[Dict[str, Any]]:
    """
    Generate sample skill development programs for testing.
    
    Returns:
        List of 10+ sample skill program dictionaries
    """
    programs = [
        {
            "program_id": "PMKVY-ELEC-2024",
            "name": "Electrician Training Program",
            "provider": "National Skill Development Corporation",
            "category": "technical",
            "description": "Comprehensive electrician training covering residential and commercial wiring, safety protocols, and electrical maintenance",
            "duration_weeks": 12,
            "cost": 0,
            "location": {
                "state": "Maharashtra",
                "district": "Pune",
                "block": "Haveli",
                "village": None,
                "pincode": "411014",
                "latitude": 18.5204,
                "longitude": 73.8567
            },
            "mode": "in-person",
            "eligibility_criteria": {
                "age_min": 18,
                "age_max": 35,
                "education": ["8th pass", "10th pass", "12th pass"],
                "custom_criteria": {}
            },
            "certification": True,
            "placement_support": True,
            "registration_url": "https://pmkvyofficial.org/electrician",
            "contact": "1800-123-9626"
        },
        {
            "program_id": "PMKVY-PLUMB-2024",
            "name": "Plumbing Training Program",
            "provider": "National Skill Development Corporation",
            "category": "technical",
            "description": "Professional plumbing training including pipe fitting, drainage systems, and water supply installation",
            "duration_weeks": 10,
            "cost": 0,
            "location": {
                "state": "Maharashtra",
                "district": "Mumbai",
                "block": None,
                "village": None,
                "pincode": "400001",
                "latitude": 18.9388,
                "longitude": 72.8354
            },
            "mode": "in-person",
            "eligibility_criteria": {
                "age_min": 18,
                "age_max": 40,
                "education": ["8th pass", "10th pass"],
                "custom_criteria": {}
            },
            "certification": True,
            "placement_support": True,
            "registration_url": "https://pmkvyofficial.org/plumbing",
            "contact": "1800-123-9626"
        },
        {
            "program_id": "DDU-GKY-RETAIL-2024",
            "name": "Retail Sales Associate Training",
            "provider": "Deen Dayal Upadhyaya Grameen Kaushalya Yojana",
            "category": "vocational",
            "description": "Training for retail sales including customer service, inventory management, and point-of-sale operations",
            "duration_weeks": 8,
            "cost": 0,
            "location": {
                "state": "Karnataka",
                "district": "Bangalore",
                "block": None,
                "village": None,
                "pincode": "560001",
                "latitude": 12.9716,
                "longitude": 77.5946
            },
            "mode": "hybrid",
            "eligibility_criteria": {
                "age_min": 18,
                "age_max": 35,
                "education": ["10th pass", "12th pass"],
                "income_max": 100000,
                "custom_criteria": {}
            },
            "certification": True,
            "placement_support": True,
            "registration_url": "https://ddugky.gov.in/retail",
            "contact": "1800-300-9626"
        },
        {
            "program_id": "PMKVY-BEAUTY-2024",
            "name": "Beauty & Wellness Training",
            "provider": "Beauty & Wellness Sector Skill Council",
            "category": "vocational",
            "description": "Professional training in beauty therapy, hair styling, makeup, and salon management",
            "duration_weeks": 16,
            "cost": 5000,
            "location": {
                "state": "Delhi",
                "district": "New Delhi",
                "block": None,
                "village": None,
                "pincode": "110001",
                "latitude": 28.6139,
                "longitude": 77.2090
            },
            "mode": "in-person",
            "eligibility_criteria": {
                "age_min": 18,
                "age_max": 35,
                "gender": "female",
                "education": ["8th pass", "10th pass", "12th pass"],
                "custom_criteria": {}
            },
            "certification": True,
            "placement_support": True,
            "registration_url": "https://bwssc.in/training",
            "contact": "011-4567-8900"
        },
        {
            "program_id": "NIELIT-CCC-2024",
            "name": "Course on Computer Concepts (CCC)",
            "provider": "National Institute of Electronics & IT",
            "category": "digital",
            "description": "Basic computer literacy course covering MS Office, internet, email, and digital payments",
            "duration_weeks": 12,
            "cost": 500,
            "location": {
                "state": "Uttar Pradesh",
                "district": "Lucknow",
                "block": None,
                "village": None,
                "pincode": "226001",
                "latitude": 26.8467,
                "longitude": 80.9462
            },
            "mode": "online",
            "eligibility_criteria": {
                "age_min": 15,
                "age_max": 60,
                "education": ["8th pass", "10th pass", "12th pass"],
                "custom_criteria": {}
            },
            "certification": True,
            "placement_support": False,
            "registration_url": "https://student.nielit.gov.in",
            "contact": "0522-233-0084"
        },
        {
            "program_id": "PMKVY-TAILORING-2024",
            "name": "Tailoring & Garment Making",
            "provider": "Apparel Made-ups & Home Furnishing Sector Skill Council",
            "category": "vocational",
            "description": "Professional tailoring training including pattern making, stitching, and garment finishing",
            "duration_weeks": 14,
            "cost": 0,
            "location": {
                "state": "Tamil Nadu",
                "district": "Chennai",
                "block": None,
                "village": None,
                "pincode": "600001",
                "latitude": 13.0827,
                "longitude": 80.2707
            },
            "mode": "in-person",
            "eligibility_criteria": {
                "age_min": 18,
                "age_max": 45,
                "education": ["5th pass", "8th pass", "10th pass"],
                "custom_criteria": {}
            },
            "certification": True,
            "placement_support": True,
            "registration_url": "https://amhssc.in/tailoring",
            "contact": "044-2345-6789"
        },
        {
            "program_id": "PMKVY-MOBILE-2024",
            "name": "Mobile Phone Repair Technician",
            "provider": "Electronics Sector Skills Council",
            "category": "technical",
            "description": "Training in mobile phone hardware and software repair, troubleshooting, and maintenance",
            "duration_weeks": 10,
            "cost": 2000,
            "location": {
                "state": "Gujarat",
                "district": "Ahmedabad",
                "block": None,
                "village": None,
                "pincode": "380001",
                "latitude": 23.0225,
                "longitude": 72.5714
            },
            "mode": "in-person",
            "eligibility_criteria": {
                "age_min": 18,
                "age_max": 35,
                "education": ["10th pass", "12th pass"],
                "custom_criteria": {}
            },
            "certification": True,
            "placement_support": True,
            "registration_url": "https://essc-india.org/mobile-repair",
            "contact": "079-2658-4321"
        },
        {
            "program_id": "NIELIT-OLEVELS-2024",
            "name": "O Level Computer Course",
            "provider": "National Institute of Electronics & IT",
            "category": "digital",
            "description": "Advanced computer course covering programming, databases, web design, and networking",
            "duration_weeks": 52,
            "cost": 3000,
            "location": {
                "state": "West Bengal",
                "district": "Kolkata",
                "block": None,
                "village": None,
                "pincode": "700001",
                "latitude": 22.5726,
                "longitude": 88.3639
            },
            "mode": "hybrid",
            "eligibility_criteria": {
                "age_min": 18,
                "age_max": 40,
                "education": ["12th pass"],
                "custom_criteria": {}
            },
            "certification": True,
            "placement_support": False,
            "registration_url": "https://student.nielit.gov.in",
            "contact": "033-2357-8901"
        },
        {
            "program_id": "PMKVY-HOSPITALITY-2024",
            "name": "Food & Beverage Service Training",
            "provider": "Tourism & Hospitality Skill Council",
            "category": "vocational",
            "description": "Training for hotel and restaurant service including table service, customer interaction, and food safety",
            "duration_weeks": 12,
            "cost": 0,
            "location": {
                "state": "Rajasthan",
                "district": "Jaipur",
                "block": None,
                "village": None,
                "pincode": "302001",
                "latitude": 26.9124,
                "longitude": 75.7873
            },
            "mode": "in-person",
            "eligibility_criteria": {
                "age_min": 18,
                "age_max": 30,
                "education": ["10th pass", "12th pass"],
                "custom_criteria": {}
            },
            "certification": True,
            "placement_support": True,
            "registration_url": "https://thsc.co.in/hospitality",
            "contact": "0141-2345-6789"
        },
        {
            "program_id": "RSETI-ENTREPRENEUR-2024",
            "name": "Rural Entrepreneurship Development",
            "provider": "Rural Self Employment Training Institute",
            "category": "entrepreneurship",
            "description": "Training for starting and managing small businesses including business planning, marketing, and finance",
            "duration_weeks": 6,
            "cost": 0,
            "location": {
                "state": "Bihar",
                "district": "Patna",
                "block": None,
                "village": None,
                "pincode": "800001",
                "latitude": 25.5941,
                "longitude": 85.1376
            },
            "mode": "in-person",
            "eligibility_criteria": {
                "age_min": 18,
                "age_max": 45,
                "education": ["8th pass", "10th pass", "12th pass"],
                "custom_criteria": {}
            },
            "certification": True,
            "placement_support": False,
            "registration_url": "https://rseti.in/entrepreneurship",
            "contact": "0612-2234-5678"
        }
    ]
    
    return programs



def get_sample_job_postings() -> List[Dict[str, Any]]:
    """
    Generate sample government job postings for testing.
    
    Returns:
        List of 10+ sample job posting dictionaries
    """
    jobs = [
        {
            "job_id": "MAHA-PWD-2024-001",
            "title": "Junior Engineer (Civil)",
            "department": "Maharashtra Public Works Department",
            "description": "Junior Engineer position for civil engineering projects including road construction, building maintenance, and infrastructure development",
            "qualifications": {
                "education": ["Diploma in Civil Engineering", "B.E./B.Tech in Civil Engineering"],
                "experience": ["Freshers welcome", "0-2 years experience"],
                "skills": ["AutoCAD", "Site supervision", "Quality control"]
            },
            "location": {
                "state": "Maharashtra",
                "district": "Pune",
                "block": None,
                "village": None,
                "pincode": "411001",
                "latitude": 18.5204,
                "longitude": 73.8567
            },
            "application_deadline": "2024-06-30",
            "application_url": "https://mahapwd.gov.in/recruitment",
            "posted_date": "2024-01-15",
            "salary_range": "Rs. 35,000 - 50,000 per month",
            "vacancies": 25
        },
        {
            "job_id": "UPSC-SSC-2024-002",
            "title": "Staff Selection Commission - Multi Tasking Staff",
            "department": "Staff Selection Commission",
            "description": "Multi Tasking Staff positions in various government departments for general administrative support",
            "qualifications": {
                "education": ["10th pass"],
                "experience": ["No experience required"],
                "skills": ["Basic computer knowledge", "Communication skills"]
            },
            "location": {
                "state": "All India",
                "district": "Various",
                "block": None,
                "village": None,
                "pincode": "000000",
                "latitude": None,
                "longitude": None
            },
            "application_deadline": "2024-05-31",
            "application_url": "https://ssc.nic.in",
            "posted_date": "2024-01-20",
            "salary_range": "Rs. 18,000 - 22,000 per month",
            "vacancies": 500
        },
        {
            "job_id": "RAILWAY-RRB-2024-003",
            "title": "Railway Recruitment Board - Assistant Loco Pilot",
            "department": "Indian Railways",
            "description": "Assistant Loco Pilot for operating and maintaining locomotives on Indian Railways network",
            "qualifications": {
                "education": ["ITI in relevant trade", "Diploma in Mechanical/Electrical Engineering"],
                "experience": ["Freshers welcome"],
                "skills": ["Mechanical aptitude", "Safety awareness", "Physical fitness"]
            },
            "location": {
                "state": "All India",
                "district": "Various",
                "block": None,
                "village": None,
                "pincode": "000000",
                "latitude": None,
                "longitude": None
            },
            "application_deadline": "2024-07-15",
            "application_url": "https://rrbcdg.gov.in",
            "posted_date": "2024-02-01",
            "salary_range": "Rs. 19,900 - 63,200 per month",
            "vacancies": 1000
        },
        {
            "job_id": "KARNATAKA-POLICE-2024-004",
            "title": "Police Constable",
            "department": "Karnataka State Police",
            "description": "Police Constable positions for law enforcement, crime prevention, and public safety duties",
            "qualifications": {
                "education": ["12th pass"],
                "experience": ["No experience required"],
                "skills": ["Physical fitness", "Communication", "Local language proficiency"]
            },
            "location": {
                "state": "Karnataka",
                "district": "Bangalore",
                "block": None,
                "village": None,
                "pincode": "560001",
                "latitude": 12.9716,
                "longitude": 77.5946
            },
            "application_deadline": "2024-06-15",
            "application_url": "https://ksp.gov.in/recruitment",
            "posted_date": "2024-01-25",
            "salary_range": "Rs. 25,000 - 35,000 per month",
            "vacancies": 150
        },
        {
            "job_id": "DELHI-TEACHER-2024-005",
            "title": "Primary School Teacher",
            "department": "Delhi Directorate of Education",
            "description": "Primary school teacher for government schools teaching classes 1-5",
            "qualifications": {
                "education": ["B.Ed or equivalent", "CTET qualified"],
                "experience": ["Freshers welcome", "Teaching experience preferred"],
                "skills": ["Child psychology", "Classroom management", "Subject knowledge"]
            },
            "location": {
                "state": "Delhi",
                "district": "New Delhi",
                "block": None,
                "village": None,
                "pincode": "110001",
                "latitude": 28.6139,
                "longitude": 77.2090
            },
            "application_deadline": "2024-05-20",
            "application_url": "https://edudel.nic.in/recruitment",
            "posted_date": "2024-02-05",
            "salary_range": "Rs. 44,900 - 1,42,400 per month",
            "vacancies": 200
        },
        {
            "job_id": "UPSC-CAPF-2024-006",
            "title": "Central Armed Police Forces - Sub Inspector",
            "department": "Union Public Service Commission",
            "description": "Sub Inspector positions in CRPF, BSF, CISF, ITBP, and SSB for security and law enforcement",
            "qualifications": {
                "education": ["Bachelor's degree"],
                "experience": ["No experience required"],
                "skills": ["Physical fitness", "Leadership", "Decision making"]
            },
            "location": {
                "state": "All India",
                "district": "Various",
                "block": None,
                "village": None,
                "pincode": "000000",
                "latitude": None,
                "longitude": None
            },
            "application_deadline": "2024-08-31",
            "application_url": "https://upsc.gov.in",
            "posted_date": "2024-02-10",
            "salary_range": "Rs. 35,400 - 1,12,400 per month",
            "vacancies": 300
        },
        {
            "job_id": "TAMILNADU-CLERK-2024-007",
            "title": "Office Assistant/Clerk",
            "department": "Tamil Nadu Public Service Commission",
            "description": "Office Assistant positions in various government departments for clerical and administrative work",
            "qualifications": {
                "education": ["12th pass", "Bachelor's degree preferred"],
                "experience": ["Freshers welcome"],
                "skills": ["Computer knowledge", "Tamil typing", "MS Office"]
            },
            "location": {
                "state": "Tamil Nadu",
                "district": "Chennai",
                "block": None,
                "village": None,
                "pincode": "600001",
                "latitude": 13.0827,
                "longitude": 80.2707
            },
            "application_deadline": "2024-06-10",
            "application_url": "https://tnpsc.gov.in",
            "posted_date": "2024-01-30",
            "salary_range": "Rs. 19,500 - 62,000 per month",
            "vacancies": 100
        },
        {
            "job_id": "BANK-IBPS-2024-008",
            "title": "IBPS - Probationary Officer",
            "department": "Institute of Banking Personnel Selection",
            "description": "Probationary Officer positions in public sector banks for banking operations and customer service",
            "qualifications": {
                "education": ["Bachelor's degree in any discipline"],
                "experience": ["Freshers welcome"],
                "skills": ["Banking knowledge", "Computer proficiency", "Communication"]
            },
            "location": {
                "state": "All India",
                "district": "Various",
                "block": None,
                "village": None,
                "pincode": "000000",
                "latitude": None,
                "longitude": None
            },
            "application_deadline": "2024-07-31",
            "application_url": "https://ibps.in",
            "posted_date": "2024-02-15",
            "salary_range": "Rs. 23,700 - 42,020 per month",
            "vacancies": 400
        },
        {
            "job_id": "GUJARAT-HEALTH-2024-009",
            "title": "Staff Nurse",
            "department": "Gujarat Health Department",
            "description": "Staff Nurse positions in government hospitals and health centers for patient care",
            "qualifications": {
                "education": ["B.Sc Nursing", "GNM"],
                "experience": ["Freshers welcome", "1-2 years preferred"],
                "skills": ["Patient care", "Medical procedures", "Emergency response"]
            },
            "location": {
                "state": "Gujarat",
                "district": "Ahmedabad",
                "block": None,
                "village": None,
                "pincode": "380001",
                "latitude": 23.0225,
                "longitude": 72.5714
            },
            "application_deadline": "2024-05-25",
            "application_url": "https://gujhealth.gov.in/recruitment",
            "posted_date": "2024-02-01",
            "salary_range": "Rs. 25,000 - 40,000 per month",
            "vacancies": 75
        },
        {
            "job_id": "UP-AGRICULTURE-2024-010",
            "title": "Agriculture Extension Officer",
            "department": "Uttar Pradesh Agriculture Department",
            "description": "Agriculture Extension Officer for providing technical guidance to farmers and implementing agricultural schemes",
            "qualifications": {
                "education": ["B.Sc Agriculture", "Diploma in Agriculture"],
                "experience": ["Freshers welcome"],
                "skills": ["Farming knowledge", "Communication", "Field work"]
            },
            "location": {
                "state": "Uttar Pradesh",
                "district": "Lucknow",
                "block": None,
                "village": None,
                "pincode": "226001",
                "latitude": 26.8467,
                "longitude": 80.9462
            },
            "application_deadline": "2024-06-20",
            "application_url": "https://upagriculture.gov.in/recruitment",
            "posted_date": "2024-02-08",
            "salary_range": "Rs. 30,000 - 45,000 per month",
            "vacancies": 50
        }
    ]
    
    return jobs



# Simple repository classes for DynamoDB operations
import boto3
from botocore.exceptions import ClientError


class SkillProgramRepository:
    """Repository for skill program DynamoDB operations."""
    
    def __init__(self, table_name: str = "SkillPrograms", region_name: str = "us-east-1"):
        """Initialize repository with DynamoDB table."""
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.table = self.dynamodb.Table(table_name)
        logger.info(f"Connected to DynamoDB table: {table_name}")
    
    def create(self, program: SkillProgram) -> None:
        """Insert skill program into DynamoDB."""
        item = program.model_dump()
        # Convert nested models to dicts
        item['location'] = dict(item['location'])
        item['eligibility_criteria'] = dict(item['eligibility_criteria'])
        
        self.table.put_item(Item=item)


class JobPostingRepository:
    """Repository for job posting DynamoDB operations."""
    
    def __init__(self, table_name: str = "JobPostings", region_name: str = "us-east-1"):
        """Initialize repository with DynamoDB table."""
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.table = self.dynamodb.Table(table_name)
        logger.info(f"Connected to DynamoDB table: {table_name}")
    
    def create(self, job: JobPosting) -> None:
        """Insert job posting into DynamoDB."""
        item = job.model_dump()
        # Convert nested models to dicts
        item['location'] = dict(item['location'])
        # Convert date objects to strings
        item['application_deadline'] = item['application_deadline'].isoformat()
        item['posted_date'] = item['posted_date'].isoformat()
        
        self.table.put_item(Item=item)



def validate_skill_program(program_dict: Dict[str, Any]) -> bool:
    """Validate skill program data before insertion."""
    try:
        location = Location(**program_dict['location'])
        eligibility = EligibilityCriteria(**program_dict['eligibility_criteria'])
        program_dict['location'] = location
        program_dict['eligibility_criteria'] = eligibility
        program = SkillProgram(**program_dict)
        logger.debug(f"Validated program: {program.program_id}")
        return True
    except Exception as e:
        logger.error(f"Validation failed for program {program_dict.get('program_id', 'UNKNOWN')}: {e}")
        return False


def validate_job_posting(job_dict: Dict[str, Any]) -> bool:
    """Validate job posting data before insertion."""
    try:
        location = Location(**job_dict['location'])
        job_dict['location'] = location
        # Convert date strings to date objects
        if isinstance(job_dict['application_deadline'], str):
            job_dict['application_deadline'] = date.fromisoformat(job_dict['application_deadline'])
        if isinstance(job_dict['posted_date'], str):
            job_dict['posted_date'] = date.fromisoformat(job_dict['posted_date'])
        job = JobPosting(**job_dict)
        logger.debug(f"Validated job: {job.job_id}")
        return True
    except Exception as e:
        logger.error(f"Validation failed for job {job_dict.get('job_id', 'UNKNOWN')}: {e}")
        return False


def bulk_insert_programs(programs: List[Dict[str, Any]], repository: SkillProgramRepository) -> tuple:
    """Bulk insert skill programs into DynamoDB."""
    success_count = 0
    failure_count = 0
    
    for program_dict in programs:
        try:
            if not validate_skill_program(program_dict):
                logger.warning(f"Skipping invalid program: {program_dict.get('program_id', 'UNKNOWN')}")
                failure_count += 1
                continue
            
            program = SkillProgram(**program_dict)
            repository.create(program)
            logger.info(f"Successfully inserted program: {program.program_id}")
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to insert program {program_dict.get('program_id', 'UNKNOWN')}: {e}")
            failure_count += 1
    
    return success_count, failure_count


def bulk_insert_jobs(jobs: List[Dict[str, Any]], repository: JobPostingRepository) -> tuple:
    """Bulk insert job postings into DynamoDB."""
    success_count = 0
    failure_count = 0
    
    for job_dict in jobs:
        try:
            if not validate_job_posting(job_dict):
                logger.warning(f"Skipping invalid job: {job_dict.get('job_id', 'UNKNOWN')}")
                failure_count += 1
                continue
            
            job = JobPosting(**job_dict)
            repository.create(job)
            logger.info(f"Successfully inserted job: {job.job_id}")
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to insert job {job_dict.get('job_id', 'UNKNOWN')}: {e}")
            failure_count += 1
    
    return success_count, failure_count



def main():
    """Main function to load skill programs and job postings."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Load skill programs and job postings into DynamoDB')
    parser.add_argument(
        '--type',
        choices=['programs', 'jobs', 'both'],
        default='both',
        help='Data type to load: programs, jobs, or both (default: both)'
    )
    parser.add_argument(
        '--programs-table',
        type=str,
        default='SkillPrograms',
        help='DynamoDB table name for programs (default: SkillPrograms)'
    )
    parser.add_argument(
        '--jobs-table',
        type=str,
        default='JobPostings',
        help='DynamoDB table name for jobs (default: JobPostings)'
    )
    parser.add_argument(
        '--region',
        type=str,
        default='us-east-1',
        help='AWS region (default: us-east-1)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate data without inserting into DynamoDB'
    )
    
    args = parser.parse_args()
    
    # Load data
    programs = []
    jobs = []
    
    if args.type in ['programs', 'both']:
        logger.info("Loading sample skill programs...")
        programs = get_sample_skill_programs()
        logger.info(f"Loaded {len(programs)} skill programs")
    
    if args.type in ['jobs', 'both']:
        logger.info("Loading sample job postings...")
        jobs = get_sample_job_postings()
        logger.info(f"Loaded {len(jobs)} job postings")
    
    # Validate data
    valid_programs = []
    valid_jobs = []
    
    if programs:
        logger.info("Validating skill programs...")
        for program_dict in programs:
            if validate_skill_program(program_dict):
                valid_programs.append(program_dict)
        logger.info(f"Validated {len(valid_programs)}/{len(programs)} programs")
    
    if jobs:
        logger.info("Validating job postings...")
        for job_dict in jobs:
            if validate_job_posting(job_dict):
                valid_jobs.append(job_dict)
        logger.info(f"Validated {len(valid_jobs)}/{len(jobs)} jobs")
    
    if args.dry_run:
        logger.info("Dry run mode - skipping DynamoDB insertion")
        logger.info(f"Would insert {len(valid_programs)} programs and {len(valid_jobs)} jobs")
        return
    
    # Insert data
    program_success = 0
    program_failure = 0
    job_success = 0
    job_failure = 0
    
    if valid_programs:
        logger.info(f"Connecting to DynamoDB table '{args.programs_table}'...")
        program_repo = SkillProgramRepository(table_name=args.programs_table, region_name=args.region)
        logger.info("Inserting skill programs...")
        program_success, program_failure = bulk_insert_programs(valid_programs, program_repo)
    
    if valid_jobs:
        logger.info(f"Connecting to DynamoDB table '{args.jobs_table}'...")
        job_repo = JobPostingRepository(table_name=args.jobs_table, region_name=args.region)
        logger.info("Inserting job postings...")
        job_success, job_failure = bulk_insert_jobs(valid_jobs, job_repo)
    
    # Summary
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    if programs:
        logger.info(f"Skill Programs - Loaded: {len(programs)}, Valid: {len(valid_programs)}, Inserted: {program_success}, Failed: {program_failure}")
    if jobs:
        logger.info(f"Job Postings - Loaded: {len(jobs)}, Valid: {len(valid_jobs)}, Inserted: {job_success}, Failed: {job_failure}")
    logger.info("=" * 60)
    
    if program_failure > 0 or job_failure > 0:
        logger.warning(f"Some insertions failed. Check logs for details.")
        sys.exit(1)
    else:
        logger.info("All data inserted successfully!")


if __name__ == '__main__':
    main()
