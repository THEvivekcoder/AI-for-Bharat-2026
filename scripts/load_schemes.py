#!/usr/bin/env python3
"""
Load sample government schemes into DynamoDB.

This script loads a curated set of real Indian government schemes
into the BharatSahayak-Schemes DynamoDB table for testing and demonstration.
"""

import boto3
import os
from datetime import datetime
from decimal import Decimal

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
table = dynamodb.Table(os.getenv('SCHEMES_TABLE', 'BharatSahayak-Schemes'))

# Sample government schemes
SCHEMES = [
    {
        'scheme_id': 'PM-KISAN-2024',
        'name': 'Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)',
        'name_translations': {
            'hi': 'प्रधानमंत्री किसान सम्मान निधि',
            'mr': 'प्रधानमंत्री किसान सन्मान निधी'
        },
        'category': 'agriculture',
        'description': 'Income support scheme providing Rs. 6000 per year to farmer families in three equal installments',
        'description_translations': {
            'hi': 'किसान परिवारों को तीन समान किस्तों में प्रति वर्ष 6000 रुपये प्रदान करने वाली आय सहायता योजना'
        },
        'benefits': [
            'Rs. 2000 per installment (3 times per year)',
            'Direct bank transfer',
            'No intermediaries',
            'Covers all landholding farmers'
        ],
        'eligibility_criteria': {
            'age_min': Decimal('18'),
            'occupation': ['farmer'],
            'custom_criteria': {
                'land_ownership': 'yes',
                'cultivable_land': 'any'
            }
        },
        'required_documents': [
            'Aadhaar card',
            'Bank account details',
            'Land ownership documents'
        ],
        'application_process': [
            'Visit PM-KISAN portal',
            'Register with Aadhaar',
            'Enter bank details',
            'Upload land records',
            'Submit application'
        ],
        'application_url': 'https://pmkisan.gov.in',
        'department': 'Ministry of Agriculture and Farmers Welfare',
        'state': None,  # Central scheme
        'last_updated': datetime.now().isoformat(),
        'source_url': 'https://pmkisan.gov.in'
    },
    {
        'scheme_id': 'PMAY-G-2024',
        'name': 'Pradhan Mantri Awas Yojana - Gramin (PMAY-G)',
        'name_translations': {
            'hi': 'प्रधानमंत्री आवास योजना - ग्रामीण'
        },
        'category': 'housing',
        'description': 'Housing scheme providing financial assistance to construct pucca houses in rural areas',
        'description_translations': {
            'hi': 'ग्रामीण क्षेत्रों में पक्के मकान बनाने के लिए वित्तीय सहायता प्रदान करने वाली आवास योजना'
        },
        'benefits': [
            'Rs. 1.20 lakh assistance in plains',
            'Rs. 1.30 lakh in hilly/difficult areas',
            'Toilet construction support',
            '90/95 days of unskilled labor under MGNREGA'
        ],
        'eligibility_criteria': {
            'age_min': Decimal('18'),
            'income_max': Decimal('0'),  # BPL families
            'custom_criteria': {
                'housing_status': 'kutcha or no house',
                'family_type': 'BPL'
            }
        },
        'required_documents': [
            'Aadhaar card',
            'BPL card',
            'Bank account',
            'Land documents'
        ],
        'application_process': [
            'Contact Gram Panchayat',
            'Get name in beneficiary list',
            'Submit documents',
            'Receive installments on construction progress'
        ],
        'application_url': 'https://pmayg.nic.in',
        'department': 'Ministry of Rural Development',
        'state': None,
        'last_updated': datetime.now().isoformat(),
        'source_url': 'https://pmayg.nic.in'
    },
    {
        'scheme_id': 'AYUSHMAN-BHARAT-2024',
        'name': 'Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (AB-PMJAY)',
        'name_translations': {
            'hi': 'आयुष्मान भारत - प्रधानमंत्री जन आरोग्य योजना'
        },
        'category': 'health',
        'description': 'Health insurance scheme providing Rs. 5 lakh coverage per family per year for secondary and tertiary care',
        'description_translations': {
            'hi': 'द्वितीयक और तृतीयक देखभाल के लिए प्रति परिवार प्रति वर्ष 5 लाख रुपये का कवरेज प्रदान करने वाली स्वास्थ्य बीमा योजना'
        },
        'benefits': [
            'Rs. 5 lakh health cover per family per year',
            'Cashless treatment at empanelled hospitals',
            'Covers pre and post hospitalization',
            'No cap on family size or age'
        ],
        'eligibility_criteria': {
            'custom_criteria': {
                'secc_2011': 'eligible',
                'family_type': 'economically vulnerable'
            }
        },
        'required_documents': [
            'Aadhaar card',
            'Ration card',
            'Mobile number'
        ],
        'application_process': [
            'Check eligibility on PMJAY website',
            'Visit nearest Common Service Centre',
            'Get Ayushman card',
            'Use at empanelled hospitals'
        ],
        'application_url': 'https://pmjay.gov.in',
        'department': 'Ministry of Health and Family Welfare',
        'state': None,
        'last_updated': datetime.now().isoformat(),
        'source_url': 'https://pmjay.gov.in'
    },
    {
        'scheme_id': 'MGNREGA-2024',
        'name': 'Mahatma Gandhi National Rural Employment Guarantee Act (MGNREGA)',
        'name_translations': {
            'hi': 'महात्मा गांधी राष्ट्रीय ग्रामीण रोजगार गारंटी अधिनियम'
        },
        'category': 'employment',
        'description': 'Employment guarantee scheme providing 100 days of wage employment per year to rural households',
        'description_translations': {
            'hi': 'ग्रामीण परिवारों को प्रति वर्ष 100 दिनों का मजदूरी रोजगार प्रदान करने वाली रोजगार गारंटी योजना'
        },
        'benefits': [
            '100 days guaranteed wage employment per household',
            'Work within 5 km of residence',
            'Unemployment allowance if work not provided',
            'Equal wages for men and women'
        ],
        'eligibility_criteria': {
            'age_min': Decimal('18'),
            'custom_criteria': {
                'residence': 'rural',
                'willing_to_do': 'unskilled manual work'
            }
        },
        'required_documents': [
            'Job card application',
            'Aadhaar card',
            'Bank account',
            'Photograph'
        ],
        'application_process': [
            'Apply for job card at Gram Panchayat',
            'Submit application with documents',
            'Receive job card within 15 days',
            'Apply for work when needed'
        ],
        'application_url': 'https://nrega.nic.in',
        'department': 'Ministry of Rural Development',
        'state': None,
        'last_updated': datetime.now().isoformat(),
        'source_url': 'https://nrega.nic.in'
    },
    {
        'scheme_id': 'PMFBY-2024',
        'name': 'Pradhan Mantri Fasal Bima Yojana (PMFBY)',
        'name_translations': {
            'hi': 'प्रधानमंत्री फसल बीमा योजना'
        },
        'category': 'agriculture',
        'description': 'Crop insurance scheme protecting farmers against crop loss due to natural calamities',
        'description_translations': {
            'hi': 'प्राकृतिक आपदाओं के कारण फसल नुकसान से किसानों की रक्षा करने वाली फसल बीमा योजना'
        },
        'benefits': [
            'Low premium: 2% for Kharif, 1.5% for Rabi',
            'Coverage for all stages of crop cycle',
            'Quick settlement of claims',
            'Use of technology for assessment'
        ],
        'eligibility_criteria': {
            'occupation': ['farmer'],
            'custom_criteria': {
                'crop_type': 'notified crops',
                'loan_status': 'loanee or non-loanee'
            }
        },
        'required_documents': [
            'Aadhaar card',
            'Bank account',
            'Land records',
            'Sowing certificate'
        ],
        'application_process': [
            'Visit bank or insurance company',
            'Fill application form',
            'Pay premium',
            'Receive policy document'
        ],
        'application_url': 'https://pmfby.gov.in',
        'department': 'Ministry of Agriculture and Farmers Welfare',
        'state': None,
        'last_updated': datetime.now().isoformat(),
        'source_url': 'https://pmfby.gov.in'
    },
    {
        'scheme_id': 'PMKVY-2024',
        'name': 'Pradhan Mantri Kaushal Vikas Yojana (PMKVY)',
        'name_translations': {
            'hi': 'प्रधानमंत्री कौशल विकास योजना'
        },
        'category': 'skill_development',
        'description': 'Skill development scheme providing free training and certification to youth',
        'description_translations': {
            'hi': 'युवाओं को मुफ्त प्रशिक्षण और प्रमाणन प्रदान करने वाली कौशल विकास योजना'
        },
        'benefits': [
            'Free skill training',
            'Government certification',
            'Monetary reward on completion',
            'Placement assistance'
        ],
        'eligibility_criteria': {
            'age_min': Decimal('15'),
            'age_max': Decimal('45'),
            'education': ['Class 10 dropout or above']
        },
        'required_documents': [
            'Aadhaar card',
            'Educational certificates',
            'Bank account',
            'Photograph'
        ],
        'application_process': [
            'Visit PMKVY portal',
            'Find training center',
            'Register for course',
            'Complete training',
            'Get certified'
        ],
        'application_url': 'https://www.pmkvyofficial.org',
        'department': 'Ministry of Skill Development and Entrepreneurship',
        'state': None,
        'last_updated': datetime.now().isoformat(),
        'source_url': 'https://www.pmkvyofficial.org'
    },
    {
        'scheme_id': 'SUKANYA-SAMRIDDHI-2024',
        'name': 'Sukanya Samriddhi Yojana',
        'name_translations': {
            'hi': 'सुकन्या समृद्धि योजना'
        },
        'category': 'social_welfare',
        'description': 'Savings scheme for girl child with attractive interest rates and tax benefits',
        'description_translations': {
            'hi': 'आकर्षक ब्याज दरों और कर लाभों के साथ बालिकाओं के लिए बचत योजना'
        },
        'benefits': [
            'High interest rate (currently 8.2%)',
            'Tax benefits under Section 80C',
            'Partial withdrawal for education',
            'Maturity at 21 years'
        ],
        'eligibility_criteria': {
            'age_max': Decimal('10'),
            'gender': 'female',
            'custom_criteria': {
                'citizenship': 'Indian',
                'accounts_per_family': 'max 2'
            }
        },
        'required_documents': [
            'Birth certificate of girl child',
            'Parent/guardian ID proof',
            'Address proof',
            'Photographs'
        ],
        'application_process': [
            'Visit post office or authorized bank',
            'Fill account opening form',
            'Submit documents',
            'Make initial deposit (min Rs. 250)',
            'Receive passbook'
        ],
        'application_url': 'https://www.indiapost.gov.in',
        'department': 'Ministry of Finance',
        'state': None,
        'last_updated': datetime.now().isoformat(),
        'source_url': 'https://www.indiapost.gov.in'
    },
    {
        'scheme_id': 'PMUY-2024',
        'name': 'Pradhan Mantri Ujjwala Yojana (PMUY)',
        'name_translations': {
            'hi': 'प्रधानमंत्री उज्ज्वला योजना'
        },
        'category': 'social_welfare',
        'description': 'LPG connection scheme for BPL families to promote clean cooking fuel',
        'description_translations': {
            'hi': 'स्वच्छ खाना पकाने के ईंधन को बढ़ावा देने के लिए बीपीएल परिवारों के लिए एलपीजी कनेक्शन योजना'
        },
        'benefits': [
            'Free LPG connection',
            'Financial assistance for first refill',
            'EMI facility for stove and regulator',
            'Promotes women empowerment'
        ],
        'eligibility_criteria': {
            'age_min': Decimal('18'),
            'gender': 'female',
            'custom_criteria': {
                'family_type': 'BPL or SECC listed',
                'existing_lpg': 'no'
            }
        },
        'required_documents': [
            'BPL card or SECC list proof',
            'Aadhaar card',
            'Bank account',
            'Address proof',
            'Photograph'
        ],
        'application_process': [
            'Visit nearest LPG distributor',
            'Fill PMUY application form',
            'Submit documents',
            'Get connection installed',
            'Receive subsidy in bank account'
        ],
        'application_url': 'https://www.pmuy.gov.in',
        'department': 'Ministry of Petroleum and Natural Gas',
        'state': None,
        'last_updated': datetime.now().isoformat(),
        'source_url': 'https://www.pmuy.gov.in'
    }
]


def load_schemes():
    """Load all schemes into DynamoDB."""
    print(f"Loading {len(SCHEMES)} schemes into DynamoDB table: {table.table_name}")
    print("-" * 80)
    
    success_count = 0
    error_count = 0
    
    for scheme in SCHEMES:
        try:
            table.put_item(Item=scheme)
            print(f"✓ Loaded: {scheme['name']}")
            success_count += 1
        except Exception as e:
            print(f"✗ Failed to load {scheme['name']}: {str(e)}")
            error_count += 1
    
    print("-" * 80)
    print(f"\nSummary:")
    print(f"  Successfully loaded: {success_count}")
    print(f"  Failed: {error_count}")
    print(f"  Total: {len(SCHEMES)}")
    
    if error_count == 0:
        print("\n✓ All schemes loaded successfully!")
    else:
        print(f"\n⚠ {error_count} schemes failed to load")
    
    return success_count, error_count


if __name__ == '__main__':
    print("BharatSahayak - Scheme Data Loader")
    print("=" * 80)
    print()
    
    # Check if table exists
    try:
        table.load()
        print(f"✓ Connected to DynamoDB table: {table.table_name}")
        print()
    except Exception as e:
        print(f"✗ Error: Could not connect to DynamoDB table")
        print(f"  {str(e)}")
        print()
        print("Make sure:")
        print("  1. AWS credentials are configured")
        print("  2. DynamoDB table exists (run 'make setup-aws')")
        print("  3. Table name in .env matches the actual table name")
        exit(1)
    
    # Load schemes
    success, errors = load_schemes()
    
    # Exit with appropriate code
    exit(0 if errors == 0 else 1)
