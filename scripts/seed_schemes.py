"""
Script to seed government schemes data into the database.
This includes central and state government schemes across various categories.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.scheme import Scheme, SchemeTranslation
from datetime import datetime
import uuid


def seed_schemes(db: Session):
    """Seed government schemes data"""
    
    schemes_data = [
        # Agriculture schemes
        {
            "name": "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
            "category": "agriculture",
            "description": "Direct income support of ₹6000 per year to all farmer families having cultivable land, paid in three equal installments of ₹2000 each.",
            "benefits": [
                "₹6000 per year direct benefit transfer",
                "Three equal installments of ₹2000",
                "No upper limit on family income",
                "Covers all landholding farmers"
            ],
            "eligibility_criteria": {
                "occupation": ["farmer", "agricultural_worker"],
                "custom_criteria": {
                    "land_ownership": "Must own cultivable land",
                    "family_definition": "Husband, wife and minor children"
                }
            },
            "required_documents": [
                "Aadhaar card",
                "Bank account details",
                "Land ownership documents"
            ],
            "application_process": [
                "Visit PM-KISAN portal or nearest CSC",
                "Fill registration form with Aadhaar and bank details",
                "Upload land ownership documents",
                "Submit application",
                "Receive confirmation SMS"
            ],
            "application_url": "https://pmkisan.gov.in/",
            "department": "Ministry of Agriculture and Farmers Welfare",
            "state": None,  # Central scheme
            "source_url": "https://pmkisan.gov.in/",
            "verification_status": "verified",
            "verification_source": "Official PM-KISAN portal",
            "translations": [
                {
                    "language": "hi",
                    "name": "प्रधानमंत्री किसान सम्मान निधि",
                    "description": "सभी भूमिधारक किसान परिवारों को प्रति वर्ष ₹6000 की प्रत्यक्ष आय सहायता, तीन समान किस्तों में ₹2000 प्रत्येक।",
                    "benefits": [
                        "प्रति वर्ष ₹6000 प्रत्यक्ष लाभ हस्तांतरण",
                        "₹2000 की तीन समान किस्तें",
                        "पारिवारिक आय पर कोई ऊपरी सीमा नहीं",
                        "सभी भूमिधारक किसानों को कवर करता है"
                    ]
                }
            ]
        },
        {
            "name": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
            "category": "agriculture",
            "description": "Crop insurance scheme providing financial support to farmers in case of crop failure due to natural calamities, pests, and diseases.",
            "benefits": [
                "Low premium rates (2% for Kharif, 1.5% for Rabi)",
                "Coverage for all stages from sowing to post-harvest",
                "Quick settlement of claims",
                "Coverage for prevented sowing and localized calamities"
            ],
            "eligibility_criteria": {
                "occupation": ["farmer"],
                "custom_criteria": {
                    "crop_cultivation": "Must be cultivating notified crops",
                    "enrollment": "Compulsory for loanee farmers, voluntary for others"
                }
            },
            "required_documents": [
                "Aadhaar card",
                "Bank account details",
                "Land records",
                "Sowing certificate (if applicable)"
            ],
            "application_process": [
                "Visit nearest bank, CSC, or insurance company office",
                "Fill crop insurance application form",
                "Pay premium amount",
                "Receive policy document",
                "In case of loss, report within 72 hours"
            ],
            "application_url": "https://pmfby.gov.in/",
            "department": "Ministry of Agriculture and Farmers Welfare",
            "state": None,
            "source_url": "https://pmfby.gov.in/",
            "verification_status": "verified",
            "verification_source": "Official PMFBY portal"
        },
        
        # Health schemes
        {
            "name": "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (PM-JAY)",
            "category": "health",
            "description": "World's largest health insurance scheme providing coverage of ₹5 lakh per family per year for secondary and tertiary care hospitalization.",
            "benefits": [
                "₹5 lakh health cover per family per year",
                "Cashless treatment at empaneled hospitals",
                "Coverage for pre and post hospitalization",
                "No cap on family size and age",
                "Covers pre-existing conditions"
            ],
            "eligibility_criteria": {
                "income_max": 100000,  # Based on SECC data
                "custom_criteria": {
                    "secc_inclusion": "Must be in SECC database or state-specific criteria",
                    "deprivation_criteria": "Based on socio-economic caste census"
                }
            },
            "required_documents": [
                "Aadhaar card",
                "Ration card",
                "Mobile number",
                "SECC verification"
            ],
            "application_process": [
                "Check eligibility on PM-JAY website",
                "Visit nearest Ayushman Mitra or CSC",
                "Verify identity with Aadhaar",
                "Receive Ayushman card",
                "Use card at empaneled hospitals"
            ],
            "application_url": "https://pmjay.gov.in/",
            "department": "Ministry of Health and Family Welfare",
            "state": None,
            "source_url": "https://pmjay.gov.in/",
            "verification_status": "verified",
            "verification_source": "Official PM-JAY portal",
            "translations": [
                {
                    "language": "hi",
                    "name": "आयुष्मान भारत - प्रधानमंत्री जन आरोग्य योजना",
                    "description": "विश्व की सबसे बड़ी स्वास्थ्य बीमा योजना जो द्वितीयक और तृतीयक देखभाल अस्पताल में भर्ती के लिए प्रति परिवार प्रति वर्ष ₹5 लाख का कवरेज प्रदान करती है।",
                    "benefits": [
                        "प्रति परिवार प्रति वर्ष ₹5 लाख स्वास्थ्य कवर",
                        "सूचीबद्ध अस्पतालों में कैशलेस उपचार",
                        "अस्पताल में भर्ती से पहले और बाद का कवरेज",
                        "परिवार के आकार और उम्र पर कोई सीमा नहीं",
                        "पहले से मौजूद बीमारियों को कवर करता है"
                    ]
                }
            ]
        },
        
        # Education schemes
        {
            "name": "National Scholarship Portal (NSP)",
            "category": "education",
            "description": "Unified platform for various scholarship schemes for students from pre-matric to post-graduation levels.",
            "benefits": [
                "Multiple scholarship schemes under one portal",
                "Direct benefit transfer to student accounts",
                "Scholarships for SC/ST/OBC/Minority students",
                "Merit-based and means-based scholarships"
            ],
            "eligibility_criteria": {
                "age_min": 6,
                "age_max": 35,
                "custom_criteria": {
                    "student_status": "Must be enrolled in recognized institution",
                    "income_criteria": "Varies by scheme",
                    "category": "Specific schemes for SC/ST/OBC/Minority/General"
                }
            },
            "required_documents": [
                "Aadhaar card",
                "Bank account details",
                "Income certificate",
                "Caste certificate (if applicable)",
                "Previous year marksheet",
                "Current enrollment certificate"
            ],
            "application_process": [
                "Register on NSP portal",
                "Fill application form",
                "Upload required documents",
                "Submit application before deadline",
                "Track application status online"
            ],
            "application_url": "https://scholarships.gov.in/",
            "department": "Ministry of Education",
            "state": None,
            "source_url": "https://scholarships.gov.in/",
            "verification_status": "verified",
            "verification_source": "Official NSP portal"
        },
        
        # Employment schemes
        {
            "name": "MGNREGA (Mahatma Gandhi National Rural Employment Guarantee Act)",
            "category": "employment",
            "description": "Provides at least 100 days of guaranteed wage employment in a financial year to every rural household whose adult members volunteer to do unskilled manual work.",
            "benefits": [
                "100 days guaranteed employment per household per year",
                "Minimum wage as per state rates",
                "Work within 5 km of residence",
                "Unemployment allowance if work not provided within 15 days",
                "Creates durable assets in rural areas"
            ],
            "eligibility_criteria": {
                "age_min": 18,
                "custom_criteria": {
                    "residence": "Must be rural household",
                    "work_type": "Willing to do unskilled manual work"
                }
            },
            "required_documents": [
                "Aadhaar card",
                "Bank account details",
                "Address proof",
                "Photograph"
            ],
            "application_process": [
                "Apply at Gram Panchayat office",
                "Fill job card application form",
                "Submit documents",
                "Receive job card within 15 days",
                "Apply for work when needed"
            ],
            "application_url": "https://nrega.nic.in/",
            "department": "Ministry of Rural Development",
            "state": None,
            "source_url": "https://nrega.nic.in/",
            "verification_status": "verified",
            "verification_source": "Official MGNREGA portal"
        },
        
        # Social welfare schemes
        {
            "name": "Pradhan Mantri Awas Yojana - Gramin (PMAY-G)",
            "category": "social_welfare",
            "description": "Provides financial assistance to construct pucca houses for homeless and those living in kutcha houses in rural areas.",
            "benefits": [
                "₹1.20 lakh assistance in plain areas",
                "₹1.30 lakh assistance in hilly/difficult areas",
                "120 sq ft minimum house with basic amenities",
                "Convergence with other schemes for toilet, electricity, LPG"
            ],
            "eligibility_criteria": {
                "custom_criteria": {
                    "housing_status": "Homeless or living in kutcha house",
                    "secc_inclusion": "Must be in SECC 2011 list",
                    "exclusion": "No pucca house in family name anywhere in India"
                }
            },
            "required_documents": [
                "Aadhaar card",
                "Bank account details",
                "SECC verification",
                "Land ownership documents (if available)",
                "Photograph"
            ],
            "application_process": [
                "Check eligibility in SECC list",
                "Apply through Gram Panchayat",
                "Verification by authorities",
                "Sanction and first installment release",
                "Complete construction and receive remaining installments"
            ],
            "application_url": "https://pmayg.nic.in/",
            "department": "Ministry of Rural Development",
            "state": None,
            "source_url": "https://pmayg.nic.in/",
            "verification_status": "verified",
            "verification_source": "Official PMAY-G portal"
        },
        
        # Women empowerment schemes
        {
            "name": "Pradhan Mantri Matru Vandana Yojana (PMMVY)",
            "category": "social_welfare",
            "description": "Maternity benefit program providing cash incentive to pregnant women and lactating mothers for first live birth.",
            "benefits": [
                "₹5000 cash incentive in three installments",
                "Promotes institutional delivery",
                "Encourages early registration of pregnancy",
                "Supports nutrition and health of mother and child"
            ],
            "eligibility_criteria": {
                "gender": "female",
                "age_min": 19,
                "custom_criteria": {
                    "pregnancy": "Pregnant women and lactating mothers",
                    "birth_order": "First live birth only",
                    "registration": "Must register pregnancy"
                }
            },
            "required_documents": [
                "Aadhaar card",
                "Bank account details",
                "MCP card (Mother and Child Protection)",
                "Identity proof",
                "Institutional delivery proof"
            ],
            "application_process": [
                "Register pregnancy at Anganwadi Center or health facility",
                "Fill PMMVY application form",
                "Submit required documents",
                "Receive first installment after registration",
                "Receive subsequent installments after delivery and immunization"
            ],
            "application_url": "https://pmmvy.nic.in/",
            "department": "Ministry of Women and Child Development",
            "state": None,
            "source_url": "https://pmmvy.nic.in/",
            "verification_status": "verified",
            "verification_source": "Official PMMVY portal"
        },
        
        # Skill development schemes
        {
            "name": "Pradhan Mantri Kaushal Vikas Yojana (PMKVY)",
            "category": "skill_development",
            "description": "Flagship scheme for skill training of youth with focus on industry-relevant skills and certification.",
            "benefits": [
                "Free skill training",
                "Industry-recognized certification",
                "Monetary reward on certification (average ₹8000)",
                "Placement assistance",
                "Recognition of Prior Learning (RPL)"
            ],
            "eligibility_criteria": {
                "age_min": 15,
                "age_max": 45,
                "custom_criteria": {
                    "education": "School dropout or unemployed youth",
                    "skills": "Willing to undergo skill training"
                }
            },
            "required_documents": [
                "Aadhaar card",
                "Bank account details",
                "Educational certificates",
                "Photograph",
                "Address proof"
            ],
            "application_process": [
                "Visit PMKVY portal or nearest training center",
                "Choose training course",
                "Register with Aadhaar",
                "Attend training sessions",
                "Appear for assessment",
                "Receive certificate and monetary reward"
            ],
            "application_url": "https://www.pmkvyofficial.org/",
            "department": "Ministry of Skill Development and Entrepreneurship",
            "state": None,
            "source_url": "https://www.pmkvyofficial.org/",
            "verification_status": "verified",
            "verification_source": "Official PMKVY portal"
        },
        
        # State-specific example (can be expanded)
        {
            "name": "Mukhyamantri Kisan Kalyan Yojana (Madhya Pradesh)",
            "category": "agriculture",
            "description": "State scheme providing additional financial assistance to farmers in Madhya Pradesh, supplementing PM-KISAN.",
            "benefits": [
                "₹4000 per year additional assistance",
                "Two installments of ₹2000 each",
                "Supplements PM-KISAN benefits",
                "Direct benefit transfer"
            ],
            "eligibility_criteria": {
                "occupation": ["farmer"],
                "location": ["Madhya Pradesh"],
                "custom_criteria": {
                    "pm_kisan": "Must be registered under PM-KISAN",
                    "land_ownership": "Must own cultivable land in MP"
                }
            },
            "required_documents": [
                "Aadhaar card",
                "PM-KISAN registration",
                "Land ownership documents",
                "Bank account details"
            ],
            "application_process": [
                "Automatic enrollment if registered under PM-KISAN",
                "Verify details at MP Kisan portal",
                "Receive benefits in bank account"
            ],
            "application_url": "https://mpkrishi.mp.gov.in/",
            "department": "Department of Agriculture, MP",
            "state": "Madhya Pradesh",
            "source_url": "https://mpkrishi.mp.gov.in/",
            "verification_status": "verified",
            "verification_source": "MP Agriculture Department"
        }
    ]
    
    print(f"Seeding {len(schemes_data)} government schemes...")
    
    for scheme_data in schemes_data:
        # Extract translations if present
        translations_data = scheme_data.pop("translations", [])
        
        # Create scheme
        scheme = Scheme(
            scheme_id=uuid.uuid4(),
            last_updated=datetime.utcnow(),
            verified_at=datetime.utcnow() if scheme_data.get("verification_status") == "verified" else None,
            **scheme_data
        )
        
        db.add(scheme)
        db.flush()  # Get the scheme_id
        
        # Add translations
        for trans_data in translations_data:
            translation = SchemeTranslation(
                scheme_id=scheme.scheme_id,
                **trans_data
            )
            db.add(translation)
        
        print(f"  ✓ Added: {scheme.name}")
    
    db.commit()
    print(f"\n✓ Successfully seeded {len(schemes_data)} schemes!")


def main():
    """Main function to run seeding"""
    print("=" * 60)
    print("Government Schemes Data Seeding")
    print("=" * 60)
    print()
    
    db = SessionLocal()
    try:
        seed_schemes(db)
    except Exception as e:
        print(f"\n✗ Error seeding schemes: {e}")
        db.rollback()
        raise
    finally:
        db.close()
    
    print("\n" + "=" * 60)
    print("Seeding completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
