#!/usr/bin/env python3
"""
Scheme data loader script for BharatSahayak.

This script loads government scheme data from JSON or CSV files and bulk inserts
them into the DynamoDB Schemes table. It includes sample schemes for testing.
"""

import json
import csv
import logging
import sys
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.scheme import Scheme
from src.models.eligibility import EligibilityCriteria
from src.core.scheme_repository import SchemeRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_from_json(file_path: str) -> List[Dict[str, Any]]:
    """
    Load scheme data from JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        List of scheme dictionaries
    """
    logger.info(f"Loading schemes from JSON: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both single scheme and array of schemes
    if isinstance(data, dict):
        return [data]
    return data


def load_from_csv(file_path: str) -> List[Dict[str, Any]]:
    """
    Load scheme data from CSV file.
    
    CSV format expected:
    scheme_id,name,category,description,department,state,source_url,benefits,
    required_documents,application_process,application_url,age_min,age_max,
    income_max,gender,occupation,education,location,caste
    
    Args:
        file_path: Path to CSV file
        
    Returns:
        List of scheme dictionaries
    """
    logger.info(f"Loading schemes from CSV: {file_path}")
    
    schemes = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Parse list fields (pipe-separated)
            benefits = row.get('benefits', '').split('|') if row.get('benefits') else []
            required_docs = row.get('required_documents', '').split('|') if row.get('required_documents') else []
            app_process = row.get('application_process', '').split('|') if row.get('application_process') else []
            occupation = row.get('occupation', '').split('|') if row.get('occupation') else None
            education = row.get('education', '').split('|') if row.get('education') else None
            location = row.get('location', '').split('|') if row.get('location') else None
            caste = row.get('caste', '').split('|') if row.get('caste') else None
            
            # Build eligibility criteria
            eligibility = {
                'age_min': int(row['age_min']) if row.get('age_min') else None,
                'age_max': int(row['age_max']) if row.get('age_max') else None,
                'income_max': int(row['income_max']) if row.get('income_max') else None,
                'gender': row.get('gender') or None,
                'occupation': occupation,
                'education': education,
                'location': location,
                'caste': caste,
                'custom_criteria': {}
            }
            
            # Build scheme dictionary
            scheme = {
                'scheme_id': row['scheme_id'],
                'name': row['name'],
                'name_translations': {},
                'category': row['category'],
                'description': row['description'],
                'description_translations': {},
                'benefits': benefits,
                'eligibility_criteria': eligibility,
                'required_documents': required_docs,
                'application_process': app_process,
                'application_url': row.get('application_url') or None,
                'department': row['department'],
                'state': row.get('state') or None,
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'source_url': row['source_url']
            }
            
            schemes.append(scheme)
    
    return schemes


def get_sample_schemes() -> List[Dict[str, Any]]:
    """
    Generate sample schemes for testing across all categories.
    
    Returns:
        List of 20+ sample scheme dictionaries
    """
    current_time = datetime.now(timezone.utc).isoformat()
    
    schemes = [
        # AGRICULTURE SCHEMES (5 schemes)
        {
            "scheme_id": "PM-KISAN-2024",
            "name": "Pradhan Mantri Kisan Samman Nidhi",
            "name_translations": {"hi": "प्रधानमंत्री किसान सम्मान निधि"},
            "category": "agriculture",
            "description": "Income support scheme providing Rs. 6000 per year to farmers in three installments",
            "description_translations": {"hi": "किसानों को तीन किस्तों में प्रति वर्ष 6000 रुपये प्रदान करने वाली आय सहायता योजना"},
            "benefits": ["Rs. 2000 per installment", "Direct bank transfer", "No intermediaries"],
            "eligibility_criteria": {
                "age_min": 18,
                "occupation": ["farmer"],
                "custom_criteria": {"land_ownership": "yes"}
            },
            "required_documents": ["Aadhaar card", "Bank account details", "Land ownership documents"],
            "application_process": ["Visit PM-KISAN portal", "Fill registration form", "Upload land records", "Submit application"],
            "application_url": "https://pmkisan.gov.in",
            "department": "Ministry of Agriculture and Farmers Welfare",
            "state": None,
            "last_updated": current_time,
            "source_url": "https://pmkisan.gov.in"
        },
        {
            "scheme_id": "PMFBY-2024",
            "name": "Pradhan Mantri Fasal Bima Yojana",
            "name_translations": {"hi": "प्रधानमंत्री फसल बीमा योजना"},
            "category": "agriculture",
            "description": "Crop insurance scheme protecting farmers against crop loss due to natural calamities",
            "benefits": ["Comprehensive risk coverage", "Low premium rates", "Quick claim settlement"],
            "eligibility_criteria": {
                "age_min": 18,
                "occupation": ["farmer", "agricultural_worker"],
                "custom_criteria": {"crop_cultivation": "yes"}
            },
            "required_documents": ["Aadhaar card", "Land records", "Bank account", "Sowing certificate"],
            "application_process": ["Visit nearest bank or CSC", "Fill application form", "Pay premium", "Get policy document"],
            "application_url": "https://pmfby.gov.in",
            "department": "Ministry of Agriculture and Farmers Welfare",
            "state": None,
            "last_updated": current_time,
            "source_url": "https://pmfby.gov.in"
        },
        {
            "scheme_id": "KCC-2024",
            "name": "Kisan Credit Card",
            "name_translations": {"hi": "किसान क्रेडिट कार्ड"},
            "category": "agriculture",
            "description": "Credit facility for farmers to meet agricultural expenses at subsidized interest rates",
            "benefits": ["Credit up to Rs. 3 lakh", "4% interest rate", "Flexible repayment"],
            "eligibility_criteria": {
                "age_min": 18,
                "age_max": 75,
                "occupation": ["farmer"],
                "custom_criteria": {"land_ownership": "yes"}
            },
            "required_documents": ["Aadhaar card", "Land documents", "Bank account", "Passport photo"],
            "application_process": ["Visit bank branch", "Submit application with documents", "Bank verification", "Card issuance"],
            "application_url": "https://www.nabard.org/kcc",
            "department": "Ministry of Agriculture and Farmers Welfare",
            "state": None,
            "last_updated": current_time,
            "source_url": "https://www.nabard.org"
        },
        {
            "scheme_id": "SOIL-HEALTH-2024",
            "name": "Soil Health Card Scheme",
            "name_translations": {"hi": "मृदा स्वास्थ्य कार्ड योजना"},
            "category": "agriculture",
            "description": "Free soil testing and health card to help farmers improve soil fertility and crop yield",
            "benefits": ["Free soil testing", "Nutrient recommendations", "Improved crop yield"],
            "eligibility_criteria": {
                "age_min": 18,
                "occupation": ["farmer"],
                "custom_criteria": {"land_ownership": "yes"}
            },
            "required_documents": ["Aadhaar card", "Land records"],
            "application_process": ["Contact local agriculture office", "Provide soil sample", "Receive health card"],
            "application_url": "https://soilhealth.dac.gov.in",
            "department": "Ministry of Agriculture and Farmers Welfare",
            "state": None,
            "last_updated": current_time,
            "source_url": "https://soilhealth.dac.gov.in"
        },
        {
            "scheme_id": "PMKSY-2024",
            "name": "Pradhan Mantri Krishi Sinchayee Yojana",
            "name_translations": {"hi": "प्रधानमंत्री कृषि सिंचाई योजना"},
            "category": "agriculture",
            "description": "Irrigation scheme to expand cultivable area and improve water use efficiency",
            "benefits": ["Subsidy on drip irrigation", "Sprinkler system support", "Water conservation"],
            "eligibility_criteria": {
                "age_min": 18,
                "occupation": ["farmer"],
                "custom_criteria": {"land_ownership": "yes"}
            },
            "required_documents": ["Aadhaar card", "Land documents", "Bank account"],
            "application_process": ["Apply through agriculture department", "Site inspection", "Subsidy approval"],
            "application_url": "https://pmksy.gov.in",
            "department": "Ministry of Agriculture and Farmers Welfare",
            "state": None,
            "last_updated": current_time,
            "source_url": "https://pmksy.gov.in"
        },
        
        # HEALTH SCHEMES (5 schemes)
        {
            "scheme_id": "AYUSHMAN-2024",
            "name": "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana",
            "name_translations": {"hi": "आयुष्मान भारत - प्रधानमंत्री जन आरोग्य योजना"},
            "category": "health",
            "description": "Health insurance scheme providing Rs. 5 lakh coverage per family per year",
            "benefits": ["Rs. 5 lakh annual coverage", "Cashless treatment", "1400+ procedures covered"],
            "eligibility_criteria": {
                "income_max": 100000,
                "custom_criteria": {"secc_listed": "yes"}
            },
            "required_documents": ["Aadhaar card", "Ration card", "SECC verification"],
            "application_process": ["Check eligibility online", "Visit nearest hospital", "Get Ayushman card"],
            "application_url": "https://pmjay.gov.in",
            "department": "Ministry of Health and Family Welfare",
            "state": None,
            "last_updated": current_time,
            "source_url": "https://pmjay.gov.in"
        },
        {
            "scheme_id": "JANANI-2024",
            "name": "Janani Suraksha Yojana",
            "name_translations": {"hi": "जननी सुरक्षा योजना"},
            "category": "health",
            "description": "Safe motherhood intervention providing cash assistance for institutional delivery",
            "benefits": ["Rs. 1400 for rural delivery", "Rs. 1000 for urban delivery", "Free delivery care"],
            "eligibility_criteria": {
                "age_min": 18,
                "age_max": 45,
                "gender": "female",
                "income_max": 200000,
                "custom_criteria": {"pregnancy": "yes"}
            },
            "required_documents": ["Aadhaar card", "BPL card", "Pregnancy registration"],
            "application_process": ["Register at health center", "Attend ANC checkups", "Deliver at facility"],
            "application_url": "https://nhm.gov.in/jsy",
            "department": "Ministry of Health and Family Welfare",
            "state": None,
            "last_updated": current_time,
            "source_url": "https://nhm.gov.in"
        },
        {
            "scheme_id": "RBSK-2024",
            "name": "Rashtriya Bal Swasthya Karyakram",
            "name_translations": {"hi": "राष्ट्रीय बाल स्वास्थ्य कार्यक्रम"},
            "category": "health",
            "description": "Child health screening and early intervention for birth defects and diseases",
            "benefits": ["Free health screening", "Early disease detection", "Free treatment"],
            "eligibility_criteria": {
                "age_min": 0,
                "age_max": 18,
                "custom_criteria": {}
            },
            "required_documents": ["Birth certificate", "Aadhaar card (if available)"],
            "application_process": ["Visit school or anganwadi", "Health screening by mobile team", "Referral if needed"],
            "application_url": "https://nhm.gov.in/rbsk",
            "department": "Ministry of Health and Family Welfare",
            "state": None,
            "last_updated": current_time,
            "source_url": "https://nhm.gov.in"
        },
        {
            "scheme_id": "PMJAY-SEHAT-2024",
            "name": "PM-JAY SEHAT (J&K)",
            "name_translations": {"hi": "पीएम-जेएवाई सेहत"},
            "category": "health",
            "description": "Extended health coverage for all residents of Jammu & Kashmir",
            "benefits": ["Rs. 5 lakh coverage", "Cashless treatment", "All residents covered"],
            "eligibility_criteria": {
                "location": ["Jammu and Kashmir"],
                "custom_criteria": {}
            },
            "required_documents": ["Aadhaar card", "Domicile certificate"],
            "application_process": ["Visit SEHAT center", "Get e-card", "Use at empanelled hospitals"],
            "application_url": "https://pmjaysehat.in",
            "department": "Ministry of Health and Family Welfare",
            "state": "Jammu and Kashmir",
            "last_updated": current_time,
            "source_url": "https://pmjaysehat.in"
        },
        {
            "scheme_id": "MISSION-INDRADHANUSH-2024",
            "name": "Mission Indradhanush",
            "name_translations": {"hi": "मिशन इंद्रधनुष"},
            "category": "health",
            "description": "Immunization program to vaccinate all children and pregnant women",
            "benefits": ["Free vaccination", "Protection against 12 diseases", "Mobile vaccination camps"],
            "eligibility_criteria": {
                "age_min": 0,
                "age_max": 5,
                "custom_criteria": {}
            },
            "required_documents": ["Birth certificate", "Mother's ID"],
            "application_process": ["Visit nearest health center", "Register for vaccination", "Follow schedule"],
            "application_url": "https://nhm.gov.in/mission-indradhanush",
            "department": "Ministry of Health and Family Welfare",
            "state": None,
            "last_updated": current_time,
            "source_url": "https://nhm.gov.in"
        },
        
        # EDUCATION SCHEMES (5 schemes)
        {
            "scheme_id": "NSP-2024",
            "name": "National Scholarship Portal",
            "name_translations": {"hi": "राष्ट्रीय छात्रवृत्ति पोर्टल"},
            "category": "education",
            "description": "Centralized portal for various scholarships for students from different backgrounds",
            "benefits": ["Multiple scholarship schemes", "Direct bank transfer", "Online application"],
            "eligibility_criteria": {
                "age_min": 10,
                "age_max": 35,
                "education": ["primary", "secondary", "higher_secondary", "undergraduate", "postgraduate"],
                "income_max": 800000,
                "custom_criteria": {}
            },
            "required_documents": ["Aadhaar card", "Income certificate", "Caste certificate", "Bank account", "Mark sheets"],
            "application_process": ["Register on NSP portal", "Fill application", "Upload documents", "Submit"],
            "application_url": "https://scholarships.gov.in",
            "department": "Ministry of Education",
            "state": None,
            "last_updated": current_time,
            "source_url": "https://scholarships.gov.in"
        },
        {
            "scheme_id": "MDM-2024",
            "name": "Mid-Day Meal Scheme",
            "name_translations": {"hi": "मध्याह्न भोजन योजना"},
            "category": "education",
            "description": "Free lunch program for school children to improve nutrition and attendance",
            "benefits": ["Free nutritious meal", "Improved attendance", "Better learning outcomes"],
            "eligibility_criteria": {
                "age_min": 6,
                "age_max": 14,
                "education": ["primary", "secondary"],
                "custom_criteria": {"school_enrollment": "yes"}
            },
            "required_documents": ["School enrollment certificate"],
            "application_process": ["Enroll in government school", "Automatic eligibility"],
            "application_url": "https://mdm.nic.in",
            "department": "Ministry of Education",
            "state": None,
            "last_updated": current_time,
            "source_url": "https://mdm.nic.in"
        },
        {
            "scheme_id": "PMSS-2024",
            "name": "Prime Minister's Scholarship Scheme",
            "name_translations": {"hi": "प्रधानमंत्री छात्रवृत्ति योजना"},
            "category": "education",
            "description": "Scholarship for wards of armed forces and paramilitary personnel",
            "benefits": ["Rs. 2500/month for boys", "Rs. 3000/month for girls", "Merit-based selection"],
            "eligibility_criteria": {
                "age_min": 18,
                "age_max": 25,
                "education": ["undergraduate"],
                "custom_criteria": {"parent_service": "armed_forces"}
            },
            "required_documents": ["Service certificate", "Mark sheets", "Bank account", "Aadhaar"],
            "application_process": ["Apply on KSB portal", "Upload documents", "Merit list selection"],
            "application_url": "https://ksb.gov.in",
            "department": "Ministry of Defence",
            "state": None,
            "last_updated": current_time,
            "source_url": "https://ksb.gov.in"
        },
        {
            "scheme_id": "BEGUM-HAZRAT-2024",
            "name": "Begum Hazrat Mahal National Scholarship",
            "name_translations": {"hi": "बेगम हज़रत महल राष्ट्रीय छात्रवृत्ति"},
            "category": "education",
            "description": "Scholarship for minority community girl students",
            "benefits": ["Rs. 5000-12000 per year", "For class 9 to postgraduate", "Merit-cum-means based"],
            "eligibility_criteria": {
                "age_min": 14,
                "age_max": 30,
                "gender": "female",
                "education": ["secondary", "higher_secondary", "undergraduate", "postgraduate"],
                "income_max": 200000,
                "custom_criteria": {"minority_community": "yes"}
            },
            "required_documents": ["Income certificate", "Minority certificate", "Mark sheets", "Bank account"],
            "application_process": ["Apply on Maulana Azad portal", "Upload documents", "Selection"],
            "application_url": "https://maef.nic.in",
            "department": "Ministry of Minority Affairs",
            "state": None,
            "last_updated": current_time,
            "source_url": "https://maef.nic.in"
        },
        {
            "scheme_id": "SWAMI-VIVEKANANDA-2024",
            "name": "Swami Vivekananda Single Girl Child Scholarship",
            "name_translations": {"hi": "स्वामी विवेकानंद एकल बालिका छात्रवृत्ति"},
            "category": "education",
            "description": "Scholarship for single girl child pursuing postgraduate studies",
            "benefits": ["Rs. 500/month", "For 2 years", "UGC scholarship"],
            "eligibility_criteria": {
                "age_min": 21,
                "age_max": 30,
                "gender": "female",
                "education": ["postgraduate"],
                "custom_criteria": {"single_girl_child": "yes"}
            },
            "required_documents": ["Single girl child certificate", "Admission proof", "Bank account"],
            "application_process": ["Apply through university", "Submit documents", "UGC approval"],
            "application_url": "https://www.ugc.ac.in",
            "department": "University Grants Commission",
            "state": None,
            "last_updated": current_time,
            "source_url": "https://www.ugc.ac.in"
        },
        
        # EMPLOYMENT SCHEMES (5 schemes)
        {
            "scheme_id": "MGNREGA-2024",
            "name": "Mahatma Gandhi National Rural Employment Guarantee Act",
            "name_translations": {"hi": "महात्मा गांधी राष्ट्रीय ग्रामीण रोजगार गारंटी अधिनियम"},
            "category": "employment",
            "description": "100 days guaranteed wage employment to rural households",
            "benefits": ["100 days work guarantee", "Minimum wages", "Asset creation"],
            "eligibility_criteria": {
                "age_min": 18,
                "location": ["Rural areas"],
                "custom_criteria": {"willing_to_work": "yes"}
            },
            "required_documents": ["Aadhaar card", "Bank account", "Job card application"],
            "application_process": ["Apply at gram panchayat", "Get job card", "Request work"],
            "application_url": "https://nrega.nic.in",
            "department": "Ministry of Rural Development",
            "state": None,
            "last_updated": current_time,
            "source_url": "https://nrega.nic.in"
        },
        {
            "scheme_id": "PMEGP-2024",
            "name": "Prime Minister's Employment Generation Programme",
            "name_translations": {"hi": "प्रधानमंत्री रोजगार सृजन कार्यक्रम"},
            "category": "employment",
            "description": "Credit-linked subsidy for setting up micro-enterprises",
            "benefits": ["15-35% subsidy", "Loan up to Rs. 50 lakh", "Self-employment"],
            "eligibility_criteria": {
                "age_min": 18,
                "education": ["primary", "secondary", "higher_secondary", "undergraduate"],
                "custom_criteria": {}
            },
            "required_documents": ["Project report", "Aadhaar", "Educational certificates", "Bank account"],
            "application_process": ["Apply online on PMEGP portal", "Submit project", "Bank loan approval"],
            "application_url": "https://www.kviconline.gov.in/pmegp",
            "department": "Ministry of MSME",
            "state": None,
            "last_updated": current_time,
            "source_url": "https://www.kviconline.gov.in"
        },
        {
            "scheme_id": "DDU-GKY-2024",
            "name": "Deen Dayal Upadhyaya Grameen Kaushalya Yojana",
            "name_translations": {"hi": "दीन दयाल उपाध्याय ग्रामीण कौशल्य योजना"},
            "category": "employment",
            "description": "Skill training and placement for rural youth",
            "benefits": ["Free skill training", "Placement assistance", "Post-placement support"],
            "eligibility_criteria": {
                "age_min": 15,
                "age_max": 35,
                "location": ["Rural areas"],
                "income_max": 100000,
                "custom_criteria": {}
            },
            "required_documents": ["Aadhaar card", "Income certificate", "Educational certificates"],
            "application_process": ["Register at training center", "Complete training", "Get placement"],
            "application_url": "https://ddugky.gov.in",
            "department": "Ministry of Rural Development",
            "state": None,
            "last_updated": current_time,
            "source_url": "https://ddugky.gov.in"
        },
        {
            "scheme_id": "PMKVY-2024",
            "name": "Pradhan Mantri Kaushal Vikas Yojana",
            "name_translations": {"hi": "प्रधानमंत्री कौशल विकास योजना"},
            "category": "employment",
            "description": "Skill development training for youth with certification",
            "benefits": ["Free training", "Industry-recognized certification", "Monetary reward"],
            "eligibility_criteria": {
                "age_min": 15,
                "age_max": 45,
                "education": ["primary", "secondary", "higher_secondary"],
                "custom_criteria": {}
            },
            "required_documents": ["Aadhaar card", "Bank account", "Educational certificates"],
            "application_process": ["Register on PMKVY portal", "Choose training center", "Complete training"],
            "application_url": "https://www.pmkvyofficial.org",
            "department": "Ministry of Skill Development and Entrepreneurship",
            "state": None,
            "last_updated": current_time,
            "source_url": "https://www.pmkvyofficial.org"
        },
        {
            "scheme_id": "STAND-UP-INDIA-2024",
            "name": "Stand-Up India Scheme",
            "name_translations": {"hi": "स्टैंड-अप इंडिया योजना"},
            "category": "employment",
            "description": "Bank loans for SC/ST and women entrepreneurs",
            "benefits": ["Loan Rs. 10 lakh to 1 crore", "Low interest rate", "Handholding support"],
            "eligibility_criteria": {
                "age_min": 18,
                "gender": "female",
                "custom_criteria": {"first_time_entrepreneur": "yes"}
            },
            "required_documents": ["Aadhaar", "Business plan", "Caste certificate (if applicable)", "Bank account"],
            "application_process": ["Apply through bank", "Submit business plan", "Loan approval"],
            "application_url": "https://www.standupmitra.in",
            "department": "Ministry of Finance",
            "state": None,
            "last_updated": current_time,
            "source_url": "https://www.standupmitra.in"
        },
        
        # SOCIAL WELFARE SCHEMES (5 schemes)
        {
            "scheme_id": "NSAP-2024",
            "name": "National Social Assistance Programme",
            "name_translations": {"hi": "राष्ट्रीय सामाजिक सहायता कार्यक्रम"},
            "category": "social_welfare",
            "description": "Pension for elderly, widows, and persons with disabilities",
            "benefits": ["Rs. 200-500/month pension", "Direct bank transfer", "Lifelong support"],
            "eligibility_criteria": {
                "age_min": 60,
                "income_max": 0,
                "custom_criteria": {"bpl_family": "yes"}
            },
            "required_documents": ["Age proof", "BPL card", "Bank account", "Aadhaar"],
            "application_process": ["Apply at panchayat/municipality", "Verification", "Pension approval"],
            "application_url": "https://nsap.nic.in",
            "department": "Ministry of Rural Development",
            "state": None,
            "last_updated": current_time,
            "source_url": "https://nsap.nic.in"
        },
        {
            "scheme_id": "UJJWALA-2024",
            "name": "Pradhan Mantri Ujjwala Yojana",
            "name_translations": {"hi": "प्रधानमंत्री उज्ज्वला योजना"},
            "category": "social_welfare",
            "description": "Free LPG connection to BPL households",
            "benefits": ["Free LPG connection", "Subsidy on cylinder", "Clean cooking fuel"],
            "eligibility_criteria": {
                "age_min": 18,
                "gender": "female",
                "income_max": 100000,
                "custom_criteria": {"bpl_family": "yes"}
            },
            "required_documents": ["BPL card", "Aadhaar", "Bank account", "Address proof"],
            "application_process": ["Apply at LPG distributor", "Submit documents", "Connection installation"],
            "application_url": "https://www.pmujjwalayojana.com",
            "department": "Ministry of Petroleum and Natural Gas",
            "state": None,
            "last_updated": current_time,
            "source_url": "https://www.pmujjwalayojana.com"
        },
        {
            "scheme_id": "PMAY-2024",
            "name": "Pradhan Mantri Awas Yojana",
            "name_translations": {"hi": "प्रधानमंत्री आवास योजना"},
            "category": "social_welfare",
            "description": "Affordable housing for all with subsidy on home loans",
            "benefits": ["Subsidy up to Rs. 2.67 lakh", "Low interest rate", "Pucca house"],
            "eligibility_criteria": {
                "age_min": 18,
                "income_max": 1800000,
                "custom_criteria": {"no_pucca_house": "yes"}
            },
            "required_documents": ["Aadhaar", "Income certificate", "Property documents", "Bank account"],
            "application_process": ["Apply online on PMAY portal", "Bank loan approval", "Subsidy credit"],
            "application_url": "https://pmaymis.gov.in",
            "department": "Ministry of Housing and Urban Affairs",
            "state": None,
            "last_updated": current_time,
            "source_url": "https://pmaymis.gov.in"
        },
        {
            "scheme_id": "SUKANYA-2024",
            "name": "Sukanya Samriddhi Yojana",
            "name_translations": {"hi": "सुकन्या समृद्धि योजना"},
            "category": "social_welfare",
            "description": "Savings scheme for girl child with high interest rate",
            "benefits": ["7.6% interest rate", "Tax benefits", "Maturity at 21 years"],
            "eligibility_criteria": {
                "age_min": 0,
                "age_max": 10,
                "gender": "female",
                "custom_criteria": {}
            },
            "required_documents": ["Birth certificate", "Parent's ID", "Address proof"],
            "application_process": ["Open account at post office/bank", "Deposit minimum Rs. 250", "Annual deposits"],
            "application_url": "https://www.nsiindia.gov.in",
            "department": "Ministry of Finance",
            "state": None,
            "last_updated": current_time,
            "source_url": "https://www.nsiindia.gov.in"
        },
        {
            "scheme_id": "BBBP-2024",
            "name": "Beti Bachao Beti Padhao",
            "name_translations": {"hi": "बेटी बचाओ बेटी पढ़ाओ"},
            "category": "social_welfare",
            "description": "Campaign to prevent gender-biased sex selection and promote girl child education",
            "benefits": ["Awareness campaigns", "Educational support", "Community mobilization"],
            "eligibility_criteria": {
                "age_min": 0,
                "age_max": 18,
                "gender": "female",
                "custom_criteria": {}
            },
            "required_documents": ["Birth certificate", "School enrollment"],
            "application_process": ["Automatic coverage", "Access through schools and anganwadis"],
            "application_url": "https://wcd.nic.in/bbbp",
            "department": "Ministry of Women and Child Development",
            "state": None,
            "last_updated": current_time,
            "source_url": "https://wcd.nic.in"
        }
    ]
    
    return schemes


def validate_scheme(scheme_dict: Dict[str, Any]) -> bool:
    """
    Validate scheme data before insertion.
    
    Args:
        scheme_dict: Scheme dictionary to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Validate eligibility criteria
        eligibility = EligibilityCriteria(**scheme_dict['eligibility_criteria'])
        
        # Validate complete scheme
        scheme = Scheme(**scheme_dict)
        
        logger.debug(f"Validated scheme: {scheme.scheme_id}")
        return True
        
    except Exception as e:
        logger.error(f"Validation failed for scheme {scheme_dict.get('scheme_id', 'UNKNOWN')}: {e}")
        return False


def bulk_insert_schemes(schemes: List[Dict[str, Any]], repository: SchemeRepository) -> tuple:
    """
    Bulk insert schemes into DynamoDB.
    
    Args:
        schemes: List of scheme dictionaries
        repository: SchemeRepository instance
        
    Returns:
        Tuple of (success_count, failure_count)
    """
    success_count = 0
    failure_count = 0
    
    for scheme_dict in schemes:
        try:
            # Validate scheme
            if not validate_scheme(scheme_dict):
                logger.warning(f"Skipping invalid scheme: {scheme_dict.get('scheme_id', 'UNKNOWN')}")
                failure_count += 1
                continue
            
            # Create Scheme object
            eligibility = EligibilityCriteria(**scheme_dict['eligibility_criteria'])
            scheme_dict['eligibility_criteria'] = eligibility
            scheme = Scheme(**scheme_dict)
            
            # Insert into DynamoDB
            repository.create(scheme)
            logger.info(f"Successfully inserted scheme: {scheme.scheme_id}")
            success_count += 1
            
        except Exception as e:
            logger.error(f"Failed to insert scheme {scheme_dict.get('scheme_id', 'UNKNOWN')}: {e}")
            failure_count += 1
    
    return success_count, failure_count


def main():
    """Main function to load schemes."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Load government schemes into DynamoDB')
    parser.add_argument(
        '--source',
        choices=['json', 'csv', 'sample'],
        default='sample',
        help='Data source: json file, csv file, or sample data (default: sample)'
    )
    parser.add_argument(
        '--file',
        type=str,
        help='Path to JSON or CSV file (required for json/csv source)'
    )
    parser.add_argument(
        '--table',
        type=str,
        default='Schemes',
        help='DynamoDB table name (default: Schemes)'
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
    
    # Load schemes based on source
    schemes = []
    
    if args.source == 'sample':
        logger.info("Loading sample schemes...")
        schemes = get_sample_schemes()
    elif args.source == 'json':
        if not args.file:
            logger.error("--file argument required for json source")
            sys.exit(1)
        schemes = load_from_json(args.file)
    elif args.source == 'csv':
        if not args.file:
            logger.error("--file argument required for csv source")
            sys.exit(1)
        schemes = load_from_csv(args.file)
    
    logger.info(f"Loaded {len(schemes)} schemes")
    
    # Validate all schemes
    logger.info("Validating schemes...")
    valid_schemes = []
    for scheme_dict in schemes:
        if validate_scheme(scheme_dict):
            valid_schemes.append(scheme_dict)
    
    logger.info(f"Validated {len(valid_schemes)}/{len(schemes)} schemes")
    
    if args.dry_run:
        logger.info("Dry run mode - skipping DynamoDB insertion")
        logger.info(f"Would insert {len(valid_schemes)} schemes")
        return
    
    # Initialize repository
    logger.info(f"Connecting to DynamoDB table '{args.table}' in region '{args.region}'...")
    repository = SchemeRepository(table_name=args.table, region_name=args.region)
    
    # Bulk insert schemes
    logger.info("Inserting schemes into DynamoDB...")
    success_count, failure_count = bulk_insert_schemes(valid_schemes, repository)
    
    # Summary
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total schemes loaded: {len(schemes)}")
    logger.info(f"Valid schemes: {len(valid_schemes)}")
    logger.info(f"Successfully inserted: {success_count}")
    logger.info(f"Failed insertions: {failure_count}")
    logger.info("=" * 60)
    
    if failure_count > 0:
        logger.warning(f"{failure_count} schemes failed to insert. Check logs for details.")
        sys.exit(1)
    else:
        logger.info("All schemes inserted successfully!")


if __name__ == '__main__':
    main()
