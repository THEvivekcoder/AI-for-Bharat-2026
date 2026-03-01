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


def load_from_json(file_path: str) -> List[Dict[str, Any]]:
    """Load data from JSON file."""
    logger.info(f"Loading data from JSON: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, dict):
        return [data]
    return data


def get_sample_skill_programs() -> List[Dict[str, Any]]:
    """Generate sample skill development programs for testing."""
    current_time = datetime.now(timezone.utc).isoformat()

    
    programs = [
        {
            "program_id": "PMKVY-ELECT-2024",
            "name": "Electrician Training Program",
            "name_translations": {"hi": "इलेक्ट्रीशियन प्रशिक्षण कार्यक्रम"},
            "provider": "National Skill Development Corporation",
            "category": "technical",
            "description": "Comprehensive electrician training covering residential and commercial electrical work",
            "description_translations": {"hi": "आवासीय और वाणिज्यिक विद्युत कार्य को कवर करने वाला व्यापक इलेक्ट्रीशियन प्रशिक्षण"},
            "duration_weeks": 12,
            "cost": 0,
            "location": {"state": "Maharashtra", "district": "Pune", "pincode": "411001"},
            "mode": "in-person",
            "eligibility": {"age_min": 18, "age_max": 35, "education": ["10th pass", "12th pass"], "custom_criteria": {}},
            "certification": True,
            "placement_support": True,
            "registration_url": "https://pmkvyofficial.org",
            "contact": "1800-123-9626",
            "created_at": current_time
        },
        {
            "program_id": "PMKVY-PLUMB-2024",
            "name": "Plumbing Training Program",
            "name_translations": {"hi": "प्लंबिंग प्रशिक्षण कार्यक्रम"},
            "provider": "National Skill Development Corporation",
            "category": "technical",
            "description": "Professional plumbing training for residential and commercial installations",
            "description_translations": {"hi": "आवासीय और वाणिज्यिक प्रतिष्ठानों के लिए पेशेवर प्लंबिंग प्रशिक्षण"},
            "duration_weeks": 10,
            "cost": 0,
            "location": {"state": "Karnataka", "district": "Bangalore", "pincode": "560001"},
            "mode": "in-person",
            "eligibility": {"age_min": 18, "age_max": 35, "education": ["8th pass", "10th pass"], "custom_criteria": {}},
            "certification": True,
            "placement_support": True,
            "registration_url": "https://pmkvyofficial.org",
            "contact": "1800-123-9626",
            "created_at": current_time
        },
        {
            "program_id": "ITI-WELD-2024",
            "name": "Welding Technology Course",
            "name_translations": {"hi": "वेल्डिंग प्रौद्योगिकी पाठ्यक्रम"},
            "provider": "Industrial Training Institute",
            "category": "vocational",
            "description": "Advanced welding techniques for construction and manufacturing industries",
            "description_translations": {"hi": "निर्माण और विनिर्माण उद्योगों के लिए उन्नत वेल्डिंग तकनीक"},
            "duration_weeks": 24,
            "cost": 5000,
            "location": {"state": "Gujarat", "district": "Ahmedabad", "pincode": "380001"},
            "mode": "in-person",
            "eligibility": {"age_min": 18, "age_max": 40, "education": ["10th pass"], "custom_criteria": {}},
            "certification": True,
            "placement_support": True,
            "registration_url": "https://ncvtmis.gov.in",
            "contact": "079-2754-1234",
            "created_at": current_time
        },
        {
            "program_id": "NIELIT-WEB-2024",
            "name": "Web Development Bootcamp",
            "name_translations": {"hi": "वेब विकास बूटकैंप"},
            "provider": "NIELIT",
            "category": "digital",
            "description": "Full-stack web development training with HTML, CSS, JavaScript, and frameworks",
            "description_translations": {"hi": "HTML, CSS, JavaScript और फ्रेमवर्क के साथ फुल-स्टैक वेब विकास प्रशिक्षण"},
            "duration_weeks": 16,
            "cost": 15000,
            "location": {"state": "Delhi", "district": "New Delhi", "pincode": "110001"},
            "mode": "hybrid",
            "eligibility": {"age_min": 18, "age_max": 35, "education": ["12th pass", "undergraduate"], "custom_criteria": {}},
            "certification": True,
            "placement_support": True,
            "registration_url": "https://nielit.gov.in",
            "contact": "011-2430-5555",
            "created_at": current_time
        },
        {
            "program_id": "NIELIT-DATA-2024",
            "name": "Data Analytics and Visualization",
            "name_translations": {"hi": "डेटा एनालिटिक्स और विज़ुअलाइज़ेशन"},
            "provider": "NIELIT",
            "category": "digital",
            "description": "Learn data analysis, SQL, Python, and visualization tools like Tableau",
            "description_translations": {"hi": "डेटा विश्लेषण, SQL, Python और Tableau जैसे विज़ुअलाइज़ेशन टूल सीखें"},
            "duration_weeks": 20,
            "cost": 20000,
            "location": {"state": "Tamil Nadu", "district": "Chennai", "pincode": "600001"},
            "mode": "online",
            "eligibility": {"age_min": 20, "age_max": 40, "education": ["undergraduate", "postgraduate"], "custom_criteria": {}},
            "certification": True,
            "placement_support": False,
            "registration_url": "https://nielit.gov.in",
            "contact": "044-2852-1234",
            "created_at": current_time
        },
        {
            "program_id": "RSETI-TAILOR-2024",
            "name": "Tailoring and Fashion Design",
            "name_translations": {"hi": "दर्जी और फैशन डिजाइन"},
            "provider": "Rural Self Employment Training Institute",
            "category": "vocational",
            "description": "Professional tailoring and basic fashion design skills for self-employment",
            "description_translations": {"hi": "स्व-रोजगार के लिए पेशेवर दर्जी और बुनियादी फैशन डिजाइन कौशल"},
            "duration_weeks": 8,
            "cost": 0,
            "location": {"state": "Uttar Pradesh", "district": "Lucknow", "pincode": "226001"},
            "mode": "in-person",
            "eligibility": {"age_min": 18, "age_max": 45, "education": ["primary", "secondary"], "custom_criteria": {}},
            "certification": True,
            "placement_support": False,
            "registration_url": "https://rseti.in",
            "contact": "0522-2234-567",
            "created_at": current_time
        },
        {
            "program_id": "MUDRA-ENTREP-2024",
            "name": "Entrepreneurship Development Program",
            "name_translations": {"hi": "उद्यमिता विकास कार्यक्रम"},
            "provider": "MUDRA Institute",
            "category": "entrepreneurship",
            "description": "Business planning, financial management, and marketing for aspiring entrepreneurs",
            "description_translations": {"hi": "इच्छुक उद्यमियों के लिए व्यवसाय योजना, वित्तीय प्रबंधन और विपणन"},
            "duration_weeks": 6,
            "cost": 3000,
            "location": {"state": "Rajasthan", "district": "Jaipur", "pincode": "302001"},
            "mode": "hybrid",
            "eligibility": {"age_min": 21, "age_max": 50, "education": ["12th pass", "undergraduate"], "custom_criteria": {}},
            "certification": True,
            "placement_support": False,
            "registration_url": "https://mudra.org.in",
            "contact": "0141-2234-567",
            "created_at": current_time
        },
        {
            "program_id": "PMKVY-BEAUTY-2024",
            "name": "Beauty and Wellness Training",
            "name_translations": {"hi": "सौंदर्य और कल्याण प्रशिक्षण"},
            "provider": "Beauty & Wellness Sector Skill Council",
            "category": "vocational",
            "description": "Professional beauty therapy, hairstyling, and wellness services training",
            "description_translations": {"hi": "पेशेवर सौंदर्य चिकित्सा, हेयरस्टाइलिंग और कल्याण सेवाओं का प्रशिक्षण"},
            "duration_weeks": 12,
            "cost": 0,
            "location": {"state": "West Bengal", "district": "Kolkata", "pincode": "700001"},
            "mode": "in-person",
            "eligibility": {"age_min": 18, "age_max": 35, "education": ["8th pass", "10th pass"], "custom_criteria": {}},
            "certification": True,
            "placement_support": True,
            "registration_url": "https://pmkvyofficial.org",
            "contact": "1800-123-9626",
            "created_at": current_time
        },
        {
            "program_id": "NIELIT-CYBER-2024",
            "name": "Cybersecurity Fundamentals",
            "name_translations": {"hi": "साइबर सुरक्षा मूल बातें"},
            "provider": "NIELIT",
            "category": "digital",
            "description": "Network security, ethical hacking, and cybersecurity best practices",
            "description_translations": {"hi": "नेटवर्क सुरक्षा, एथिकल हैकिंग और साइबर सुरक्षा सर्वोत्तम प्रथाएं"},
            "duration_weeks": 18,
            "cost": 25000,
            "location": {"state": "Telangana", "district": "Hyderabad", "pincode": "500001"},
            "mode": "online",
            "eligibility": {"age_min": 20, "age_max": 40, "education": ["undergraduate", "postgraduate"], "custom_criteria": {}},
            "certification": True,
            "placement_support": True,
            "registration_url": "https://nielit.gov.in",
            "contact": "040-2345-6789",
            "created_at": current_time
        },
        {
            "program_id": "ITI-AUTO-2024",
            "name": "Automobile Mechanic Training",
            "name_translations": {"hi": "ऑटोमोबाइल मैकेनिक प्रशिक्षण"},
            "provider": "Industrial Training Institute",
            "category": "technical",
            "description": "Vehicle maintenance, repair, and diagnostics for cars and motorcycles",
            "description_translations": {"hi": "कारों और मोटरसाइकिलों के लिए वाहन रखरखाव, मरम्मत और निदान"},
            "duration_weeks": 24,
            "cost": 8000,
            "location": {"state": "Punjab", "district": "Ludhiana", "pincode": "141001"},
            "mode": "in-person",
            "eligibility": {"age_min": 18, "age_max": 35, "education": ["10th pass", "12th pass"], "custom_criteria": {}},
            "certification": True,
            "placement_support": True,
            "registration_url": "https://ncvtmis.gov.in",
            "contact": "0161-2345-678",
            "created_at": current_time
        }
    ]
    
    return programs


def get_sample_job_postings() -> List[Dict[str, Any]]:
    """Generate sample government job postings for testing."""
    current_time = datetime.now(timezone.utc).isoformat()
    today = date.today()
    
    jobs = [
        {
            "job_id": "UPSC-JE-CIVIL-2024",
            "title": "Junior Engineer (Civil)",
            "title_translations": {"hi": "कनिष्ठ अभियंता (सिविल)"},
            "department": "Ministry of Railways",
            "description": "Junior Engineer position for civil engineering work in railway construction and maintenance",
            "description_translations": {"hi": "रेलवे निर्माण और रखरखाव में सिविल इंजीनियरिंग कार्य के लिए कनिष्ठ अभियंता पद"},
            "qualifications": ["Diploma in Civil Engineering", "B.Tech in Civil Engineering"],
            "experience_years": 0,
            "location": {"state": "Maharashtra", "district": "Mumbai", "pincode": "400001"},
            "salary_range": "35000-45000 per month",
            "application_deadline": "2024-06-30",
            "application_url": "https://www.rrbcdg.gov.in",
            "posted_date": "2024-01-15",
            "vacancies": 50,
            "job_type": "permanent",
            "created_at": current_time
        },
        {
            "job_id": "SSC-STENO-2024",
            "title": "Stenographer Grade C",
            "title_translations": {"hi": "आशुलिपिक ग्रेड सी"},
            "department": "Staff Selection Commission",
            "description": "Stenographer position for various central government departments",
            "description_translations": {"hi": "विभिन्न केंद्र सरकार के विभागों के लिए आशुलिपिक पद"},
            "qualifications": ["12th pass", "Typing speed 80 wpm"],
            "experience_years": 0,
            "location": {"state": "Delhi", "district": "New Delhi", "pincode": "110001"},
            "salary_range": "25000-35000 per month",
            "application_deadline": "2024-05-31",
            "application_url": "https://ssc.nic.in",
            "posted_date": "2024-01-20",
            "vacancies": 100,
            "job_type": "permanent",
            "created_at": current_time
        },
        {
            "job_id": "IBPS-PO-2024",
            "title": "Probationary Officer",
            "title_translations": {"hi": "प्रोबेशनरी ऑफिसर"},
            "department": "Institute of Banking Personnel Selection",
            "description": "Banking officer position in public sector banks across India",
            "description_translations": {"hi": "भारत भर में सार्वजनिक क्षेत्र के बैंकों में बैंकिंग अधिकारी पद"},
            "qualifications": ["Bachelor's degree in any discipline"],
            "experience_years": 0,
            "location": {"state": "Karnataka", "district": "Bangalore", "pincode": "560001"},
            "salary_range": "40000-50000 per month",
            "application_deadline": "2024-07-15",
            "application_url": "https://www.ibps.in",
            "posted_date": "2024-02-01",
            "vacancies": 200,
            "job_type": "permanent",
            "created_at": current_time
        },
        {
            "job_id": "UPSC-ASST-2024",
            "title": "Assistant Section Officer",
            "title_translations": {"hi": "सहायक अनुभाग अधिकारी"},
            "department": "Union Public Service Commission",
            "description": "Administrative position in central government ministries",
            "description_translations": {"hi": "केंद्र सरकार के मंत्रालयों में प्रशासनिक पद"},
            "qualifications": ["Bachelor's degree"],
            "experience_years": 0,
            "location": {"state": "Delhi", "district": "New Delhi", "pincode": "110001"},
            "salary_range": "44900-142400 per month",
            "application_deadline": "2024-08-31",
            "application_url": "https://www.upsc.gov.in",
            "posted_date": "2024-02-15",
            "vacancies": 75,
            "job_type": "permanent",
            "created_at": current_time
        },
        {
            "job_id": "POLICE-CONST-2024",
            "title": "Police Constable",
            "title_translations": {"hi": "पुलिस कांस्टेबल"},
            "department": "State Police Department",
            "description": "Police constable position for law enforcement duties",
            "description_translations": {"hi": "कानून प्रवर्तन कर्तव्यों के लिए पुलिस कांस्टेबल पद"},
            "qualifications": ["12th pass", "Physical fitness requirements"],
            "experience_years": 0,
            "location": {"state": "Uttar Pradesh", "district": "Lucknow", "pincode": "226001"},
            "salary_range": "21700-69100 per month",
            "application_deadline": "2024-06-15",
            "application_url": "https://uppbpb.gov.in",
            "posted_date": "2024-01-25",
            "vacancies": 500,
            "job_type": "permanent",
            "created_at": current_time
        },
        {
            "job_id": "TEACHER-TGT-2024",
            "title": "Trained Graduate Teacher",
            "title_translations": {"hi": "प्रशिक्षित स्नातक शिक्षक"},
            "department": "Department of Education",
            "description": "Teaching position for secondary schools in government schools",
            "description_translations": {"hi": "सरकारी स्कूलों में माध्यमिक विद्यालयों के लिए शिक्षण पद"},
            "qualifications": ["B.Ed", "Bachelor's degree in relevant subject"],
            "experience_years": 0,
            "location": {"state": "Tamil Nadu", "district": "Chennai", "pincode": "600001"},
            "salary_range": "35000-45000 per month",
            "application_deadline": "2024-07-31",
            "application_url": "https://trb.tn.gov.in",
            "posted_date": "2024-02-10",
            "vacancies": 150,
            "job_type": "permanent",
            "created_at": current_time
        },
        {
            "job_id": "NURSE-STAFF-2024",
            "title": "Staff Nurse",
            "title_translations": {"hi": "स्टाफ नर्स"},
            "department": "Ministry of Health and Family Welfare",
            "description": "Nursing position in government hospitals and health centers",
            "description_translations": {"hi": "सरकारी अस्पतालों और स्वास्थ्य केंद्रों में नर्सिंग पद"},
            "qualifications": ["B.Sc Nursing", "GNM", "Registered Nurse"],
            "experience_years": 0,
            "location": {"state": "West Bengal", "district": "Kolkata", "pincode": "700001"},
            "salary_range": "30000-40000 per month",
            "application_deadline": "2024-05-15",
            "application_url": "https://wbhrb.in",
            "posted_date": "2024-01-30",
            "vacancies": 80,
            "job_type": "permanent",
            "created_at": current_time
        },
        {
            "job_id": "CLERK-LDC-2024",
            "title": "Lower Division Clerk",
            "title_translations": {"hi": "लोअर डिवीजन क्लर्क"},
            "department": "Staff Selection Commission",
            "description": "Clerical position in various central government offices",
            "description_translations": {"hi": "विभिन्न केंद्र सरकार के कार्यालयों में लिपिक पद"},
            "qualifications": ["12th pass", "Computer knowledge"],
            "experience_years": 0,
            "location": {"state": "Rajasthan", "district": "Jaipur", "pincode": "302001"},
            "salary_range": "19900-63200 per month",
            "application_deadline": "2024-06-30",
            "application_url": "https://ssc.nic.in",
            "posted_date": "2024-02-05",
            "vacancies": 300,
            "job_type": "permanent",
            "created_at": current_time
        },
        {
            "job_id": "TECH-ASST-2024",
            "title": "Technical Assistant",
            "title_translations": {"hi": "तकनीकी सहायक"},
            "department": "Council of Scientific and Industrial Research",
            "description": "Technical support position in CSIR laboratories",
            "description_translations": {"hi": "CSIR प्रयोगशालाओं में तकनीकी सहायता पद"},
            "qualifications": ["B.Tech", "M.Sc in relevant field"],
            "experience_years": 1,
            "location": {"state": "Delhi", "district": "New Delhi", "pincode": "110001"},
            "salary_range": "35000-50000 per month",
            "application_deadline": "2024-07-20",
            "application_url": "https://www.csir.res.in",
            "posted_date": "2024-02-12",
            "vacancies": 40,
            "job_type": "contract",
            "created_at": current_time
        },
        {
            "job_id": "AGRI-OFFICER-2024",
            "title": "Agriculture Field Officer",
            "title_translations": {"hi": "कृषि क्षेत्र अधिकारी"},
            "department": "Ministry of Agriculture and Farmers Welfare",
            "description": "Field officer position for agricultural extension services",
            "description_translations": {"hi": "कृषि विस्तार सेवाओं के लिए क्षेत्र अधिकारी पद"},
            "qualifications": ["B.Sc Agriculture", "Diploma in Agriculture"],
            "experience_years": 0,
            "location": {"state": "Punjab", "district": "Ludhiana", "pincode": "141001"},
            "salary_range": "30000-40000 per month",
            "application_deadline": "2024-08-15",
            "application_url": "https://agricoop.nic.in",
            "posted_date": "2024-02-20",
            "vacancies": 60,
            "job_type": "permanent",
            "created_at": current_time
        }
    ]
    
    return jobs


def validate_skill_program(program_dict: Dict[str, Any]) -> bool:
    """Validate skill program data before insertion."""
    try:
        location = Location(**program_dict['location'])
        eligibility = EligibilityCriteria(**program_dict['eligibility'])
        program_dict['location'] = location
        program_dict['eligibility'] = eligibility
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



def bulk_insert_programs(programs: List[Dict[str, Any]], table_name: str, region: str) -> tuple:
    """Bulk insert skill programs into DynamoDB."""
    import boto3
    
    dynamodb = boto3.resource('dynamodb', region_name=region)
    table = dynamodb.Table(table_name)
    
    success_count = 0
    failure_count = 0
    
    for program_dict in programs:
        try:
            if not validate_skill_program(program_dict):
                logger.warning(f"Skipping invalid program: {program_dict.get('program_id', 'UNKNOWN')}")
                failure_count += 1
                continue
            
            # Convert to dict for DynamoDB
            location = Location(**program_dict['location'])
            eligibility = EligibilityCriteria(**program_dict['eligibility'])
            program_dict['location'] = location.model_dump()
            program_dict['eligibility'] = eligibility.model_dump()
            
            program = SkillProgram(**program_dict)
            item = program.model_dump()
            
            # Convert datetime to string for DynamoDB
            if 'created_at' in item and isinstance(item['created_at'], datetime):
                item['created_at'] = item['created_at'].isoformat()
            
            table.put_item(Item=item)
            logger.info(f"Successfully inserted program: {program.program_id}")
            success_count += 1
            
        except Exception as e:
            logger.error(f"Failed to insert program {program_dict.get('program_id', 'UNKNOWN')}: {e}")
            failure_count += 1
    
    return success_count, failure_count


def bulk_insert_jobs(jobs: List[Dict[str, Any]], table_name: str, region: str) -> tuple:
    """Bulk insert job postings into DynamoDB."""
    import boto3
    
    dynamodb = boto3.resource('dynamodb', region_name=region)
    table = dynamodb.Table(table_name)
    
    success_count = 0
    failure_count = 0
    
    for job_dict in jobs:
        try:
            if not validate_job_posting(job_dict):
                logger.warning(f"Skipping invalid job: {job_dict.get('job_id', 'UNKNOWN')}")
                failure_count += 1
                continue
            
            # Convert to dict for DynamoDB
            location = Location(**job_dict['location'])
            job_dict['location'] = location.model_dump()
            
            # Convert date strings to date objects
            if isinstance(job_dict['application_deadline'], str):
                job_dict['application_deadline'] = date.fromisoformat(job_dict['application_deadline'])
            if isinstance(job_dict['posted_date'], str):
                job_dict['posted_date'] = date.fromisoformat(job_dict['posted_date'])
            
            job = JobPosting(**job_dict)
            item = job.model_dump()
            
            # Convert dates and datetime to strings for DynamoDB
            if 'application_deadline' in item and isinstance(item['application_deadline'], date):
                item['application_deadline'] = item['application_deadline'].isoformat()
            if 'posted_date' in item and isinstance(item['posted_date'], date):
                item['posted_date'] = item['posted_date'].isoformat()
            if 'created_at' in item and isinstance(item['created_at'], datetime):
                item['created_at'] = item['created_at'].isoformat()
            
            table.put_item(Item=item)
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
        '--source',
        choices=['json', 'sample'],
        default='sample',
        help='Data source: json file or sample data (default: sample)'
    )
    parser.add_argument(
        '--file',
        type=str,
        help='Path to JSON file (required for json source)'
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
    
    # Load data based on source
    programs = []
    jobs = []
    
    if args.source == 'sample':
        if args.type in ['programs', 'both']:
            logger.info("Loading sample skill programs...")
            programs = get_sample_skill_programs()
        if args.type in ['jobs', 'both']:
            logger.info("Loading sample job postings...")
            jobs = get_sample_job_postings()
    elif args.source == 'json':
        if not args.file:
            logger.error("--file argument required for json source")
            sys.exit(1)
        data = load_from_json(args.file)
        if args.type in ['programs', 'both']:
            programs = data if isinstance(data, list) else [data]
        if args.type in ['jobs', 'both']:
            jobs = data if isinstance(data, list) else [data]
    
    logger.info(f"Loaded {len(programs)} programs and {len(jobs)} jobs")
    
    # Validate data
    logger.info("Validating data...")
    valid_programs = [p for p in programs if validate_skill_program(p.copy())]
    valid_jobs = [j for j in jobs if validate_job_posting(j.copy())]
    
    logger.info(f"Validated {len(valid_programs)}/{len(programs)} programs")
    logger.info(f"Validated {len(valid_jobs)}/{len(jobs)} jobs")
    
    if args.dry_run:
        logger.info("Dry run mode - skipping DynamoDB insertion")
        logger.info(f"Would insert {len(valid_programs)} programs and {len(valid_jobs)} jobs")
        return
    
    # Insert data
    prog_success = prog_failure = 0
    job_success = job_failure = 0
    
    if valid_programs:
        logger.info(f"Inserting programs into DynamoDB table '{args.programs_table}'...")
        prog_success, prog_failure = bulk_insert_programs(valid_programs, args.programs_table, args.region)
    
    if valid_jobs:
        logger.info(f"Inserting jobs into DynamoDB table '{args.jobs_table}'...")
        job_success, job_failure = bulk_insert_jobs(valid_jobs, args.jobs_table, args.region)
    
    # Summary
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Programs loaded: {len(programs)}")
    logger.info(f"Programs validated: {len(valid_programs)}")
    logger.info(f"Programs inserted: {prog_success}")
    logger.info(f"Programs failed: {prog_failure}")
    logger.info("-" * 60)
    logger.info(f"Jobs loaded: {len(jobs)}")
    logger.info(f"Jobs validated: {len(valid_jobs)}")
    logger.info(f"Jobs inserted: {job_success}")
    logger.info(f"Jobs failed: {job_failure}")
    logger.info("=" * 60)
    
    if prog_failure > 0 or job_failure > 0:
        logger.warning(f"Some items failed to insert. Check logs for details.")
        sys.exit(1)
    else:
        logger.info("All items inserted successfully!")


if __name__ == '__main__':
    main()
