"""
Script to ingest documents into the vector database for RAG.
This includes government scheme documents, agricultural guidance, and health information.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.vector_store import vector_store, Document
from typing import List, Dict
from datetime import datetime
import uuid


# Sample documents for government schemes
SCHEME_DOCUMENTS = [
    {
        "content": """PM-KISAN (Pradhan Mantri Kisan Samman Nidhi) is a central sector scheme that provides income support to all landholding farmers' families. 
        Under the scheme, financial benefit of Rs. 6000 per year is provided to eligible farmer families in three equal installments of Rs. 2000 each every four months.
        The scheme is fully funded by the Government of India. It became operational from 1st December 2018.
        
        Eligibility: All landholding farmers' families having cultivable land are eligible. There is no upper limit on family income.
        
        Benefits: Direct benefit transfer of Rs. 6000 per year in three installments. Money is directly transferred to bank accounts.
        
        How to Apply: Visit PM-KISAN portal or nearest Common Service Center (CSC). Fill registration form with Aadhaar and bank details. 
        Upload land ownership documents. Submit application and receive confirmation SMS.""",
        "metadata": {
            "source": "PM-KISAN Official Portal",
            "category": "agriculture",
            "scheme_name": "PM-KISAN",
            "document_type": "scheme_description",
            "url": "https://pmkisan.gov.in/"
        }
    },
    {
        "content": """Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (PM-JAY) is the world's largest health insurance scheme.
        It provides health cover of Rs. 5 lakh per family per year for secondary and tertiary care hospitalization.
        
        Coverage: Over 10.74 crore poor and vulnerable families (approximately 50 crore beneficiaries). Covers pre and post hospitalization expenses.
        No cap on family size, age, or gender. Covers pre-existing conditions from day one.
        
        Benefits: Cashless treatment at any empaneled public or private hospital across India. Coverage for 1,393 procedures including surgeries, medical treatments, and day care procedures.
        
        Eligibility: Based on Socio-Economic Caste Census (SECC) 2011 data. Families identified as deprived or vulnerable are automatically eligible.
        
        How to Use: Check eligibility on PM-JAY website. Visit nearest Ayushman Mitra or CSC. Verify identity with Aadhaar. Receive Ayushman card. Use card at empaneled hospitals for cashless treatment.""",
        "metadata": {
            "source": "PM-JAY Official Portal",
            "category": "health",
            "scheme_name": "PM-JAY",
            "document_type": "scheme_description",
            "url": "https://pmjay.gov.in/"
        }
    },
    {
        "content": """MGNREGA (Mahatma Gandhi National Rural Employment Guarantee Act) provides at least 100 days of guaranteed wage employment in a financial year to every rural household.
        
        Key Features: Legal guarantee of employment. Work provided within 5 km of residence. If work not provided within 15 days, unemployment allowance must be paid.
        Minimum wage as per state rates. Creates durable assets in rural areas like roads, ponds, and irrigation facilities.
        
        Eligibility: Any rural household whose adult members volunteer to do unskilled manual work. Minimum age 18 years.
        
        How to Apply: Apply at Gram Panchayat office. Fill job card application form. Submit Aadhaar card, bank details, address proof, and photograph.
        Receive job card within 15 days. Apply for work when needed. Work must be provided within 15 days of application.""",
        "metadata": {
            "source": "MGNREGA Official Portal",
            "category": "employment",
            "scheme_name": "MGNREGA",
            "document_type": "scheme_description",
            "url": "https://nrega.nic.in/"
        }
    }
]

# Agricultural guidance documents
AGRICULTURE_DOCUMENTS = [
    {
        "content": """Rice Cultivation Guide for Kharif Season:
        
        Sowing Time: June to July (with onset of monsoon)
        
        Land Preparation: Plough the field 2-3 times. Level the field properly. Prepare nursery beds for transplanting.
        
        Seed Rate: 20-25 kg per hectare for transplanting. 60-80 kg per hectare for direct seeding.
        
        Transplanting: Transplant 20-25 day old seedlings. Maintain 20x15 cm spacing. Plant 2-3 seedlings per hill.
        
        Water Management: Keep 5-7 cm standing water for first 10 days. Maintain 2-3 cm water during vegetative stage. Drain water 10 days before harvest.
        
        Fertilizer Application: Apply NPK in ratio 120:60:40 kg per hectare. Split application: 50% N at transplanting, 25% N at tillering, 25% N at panicle initiation.
        
        Weed Control: First weeding 20-25 days after transplanting. Second weeding 40-45 days after transplanting.
        
        Pest Management: Monitor for stem borer, leaf folder, and brown plant hopper. Use integrated pest management practices.
        
        Harvesting: Harvest when 80% of grains turn golden yellow. Moisture content should be 20-25%.""",
        "metadata": {
            "source": "Indian Council of Agricultural Research",
            "category": "agriculture",
            "crop": "rice",
            "season": "kharif",
            "document_type": "cultivation_guide"
        }
    },
    {
        "content": """Wheat Cultivation Guide for Rabi Season:
        
        Sowing Time: November to December (after monsoon)
        
        Land Preparation: Deep ploughing in summer. 2-3 ploughings before sowing. Level the field for uniform irrigation.
        
        Seed Rate: 100 kg per hectare for timely sowing. 125 kg per hectare for late sowing.
        
        Sowing Method: Line sowing with 20-22.5 cm row spacing. Sowing depth 5-6 cm.
        
        Irrigation: First irrigation 20-25 days after sowing (Crown Root Initiation stage). Second irrigation at tillering (40-45 days). 
        Third irrigation at jointing (60-65 days). Fourth irrigation at flowering (80-85 days). Fifth irrigation at milk stage (100-105 days).
        
        Fertilizer Application: Apply NPK in ratio 120:60:40 kg per hectare. Full P and K at sowing. N in three splits: 50% at sowing, 25% at CRI, 25% at tillering.
        
        Weed Control: Pre-emergence herbicide within 3 days of sowing. Post-emergence herbicide 30-35 days after sowing if needed.
        
        Disease Management: Monitor for rust diseases, powdery mildew, and loose smut. Use resistant varieties and fungicides if needed.
        
        Harvesting: Harvest when grains are hard and moisture is 20-25%. Timely harvesting prevents shattering losses.""",
        "metadata": {
            "source": "Indian Council of Agricultural Research",
            "category": "agriculture",
            "crop": "wheat",
            "season": "rabi",
            "document_type": "cultivation_guide"
        }
    },
    {
        "content": """Organic Farming Practices and Benefits:
        
        What is Organic Farming: Farming without synthetic chemicals. Uses natural fertilizers, pest control, and soil management.
        
        Soil Health Management: Use farmyard manure, compost, and green manure. Practice crop rotation. Maintain soil cover with mulching.
        Add bio-fertilizers like Rhizobium, Azotobacter, and PSB.
        
        Pest and Disease Management: Use neem-based pesticides. Practice companion planting. Encourage natural predators. 
        Use pheromone traps. Maintain field hygiene.
        
        Weed Management: Manual weeding. Mulching to suppress weeds. Use of cover crops. Mechanical weeders.
        
        Composting: Collect farm waste, kitchen waste, and animal manure. Layer green and brown materials. Maintain moisture. 
        Turn pile every 15 days. Compost ready in 2-3 months.
        
        Benefits: Improves soil health and fertility. Reduces input costs over time. Better market price for organic produce. 
        Environmentally sustainable. Healthier food products.
        
        Certification: Contact certification agencies. Maintain records of inputs and practices. Undergo inspection. 
        Receive organic certification after 2-3 years of conversion period.""",
        "metadata": {
            "source": "National Centre of Organic Farming",
            "category": "agriculture",
            "topic": "organic_farming",
            "document_type": "guidance"
        }
    }
]

# Health information documents
HEALTH_DOCUMENTS = [
    {
        "content": """Common Health Problems in Rural India and Prevention:
        
        Diarrheal Diseases: Caused by contaminated water and food. Prevention: Drink boiled or filtered water. Wash hands before eating. 
        Maintain food hygiene. Use clean toilets. Treatment: ORS solution, zinc supplements, medical consultation if severe.
        
        Respiratory Infections: Common cold, flu, pneumonia. Prevention: Avoid crowded places during flu season. Cover mouth when coughing. 
        Maintain good ventilation. Get vaccinated. Treatment: Rest, fluids, medical consultation for persistent symptoms.
        
        Malaria and Dengue: Mosquito-borne diseases. Prevention: Use mosquito nets. Eliminate standing water. Use mosquito repellents. 
        Wear full-sleeve clothes. Treatment: Immediate medical consultation, blood test, prescribed medications.
        
        Anemia: Common in women and children. Prevention: Iron-rich diet (green leafy vegetables, jaggery, dates). 
        Take iron supplements if prescribed. Regular health checkups. Treatment: Iron and folic acid supplements, dietary changes.
        
        Tuberculosis (TB): Bacterial infection of lungs. Symptoms: Persistent cough for more than 2 weeks, fever, weight loss, night sweats.
        Prevention: BCG vaccination, avoid close contact with TB patients. Treatment: Free treatment available at government health centers. 
        Complete 6-9 months course of medicines. DOTS (Directly Observed Treatment Short-course) ensures cure.
        
        When to Seek Medical Help: High fever lasting more than 3 days. Difficulty breathing. Severe abdominal pain. 
        Persistent vomiting or diarrhea. Chest pain. Severe headache. Any emergency symptoms.""",
        "metadata": {
            "source": "Ministry of Health and Family Welfare",
            "category": "health",
            "topic": "common_diseases",
            "document_type": "health_guidance"
        }
    },
    {
        "content": """Maternal and Child Health Care:
        
        Antenatal Care (During Pregnancy): Register pregnancy at nearest health center within first 3 months. 
        Attend at least 4 antenatal checkups. Take iron and folic acid tablets daily. Get TT (Tetanus Toxoid) injections. 
        Eat nutritious food. Avoid heavy work. Recognize danger signs: bleeding, severe headache, blurred vision, reduced fetal movements.
        
        Institutional Delivery: Deliver at hospital or health center for safe delivery. Free delivery services under government schemes. 
        Skilled birth attendant reduces complications. Emergency services available 24x7.
        
        Postnatal Care: Rest for at least 6 weeks. Exclusive breastfeeding for 6 months. Attend postnatal checkups. 
        Take iron supplements. Practice family planning. Watch for danger signs: heavy bleeding, fever, foul-smelling discharge.
        
        Newborn Care: Keep baby warm. Start breastfeeding within 1 hour of birth. No water or other foods for first 6 months. 
        Keep umbilical cord clean and dry. Get baby vaccinated as per schedule.
        
        Immunization Schedule: BCG, OPV, Hepatitis B at birth. DPT, OPV, Hepatitis B at 6, 10, 14 weeks. 
        Measles at 9 months. DPT booster at 16-24 months. Complete immunization protects from deadly diseases.
        
        Child Nutrition: Exclusive breastfeeding for 6 months. Start complementary feeding at 6 months. 
        Give mashed foods, dal, rice, vegetables. Continue breastfeeding up to 2 years. Monitor growth regularly.""",
        "metadata": {
            "source": "Ministry of Health and Family Welfare",
            "category": "health",
            "topic": "maternal_child_health",
            "document_type": "health_guidance"
        }
    },
    {
        "content": """Government Health Services and Facilities:
        
        Primary Health Centers (PHC): Located in rural areas. Provides OPD services, maternal and child health care, immunization, 
        family planning, basic laboratory services, essential medicines. Open during working hours.
        
        Community Health Centers (CHC): Referral center for PHCs. Provides 24x7 emergency services, inpatient care (30 beds), 
        surgery (minor), obstetrics and gynecology, pediatrics, laboratory services, X-ray facility, blood storage.
        
        District Hospitals: Multi-specialty services. 24x7 emergency and trauma care. Inpatient care (200+ beds). 
        General surgery, orthopedics, medicine, pediatrics, gynecology. ICU and CCU facilities. Blood bank. Advanced diagnostics.
        
        Sub-Centers: Village level health facility. Provides basic health services, immunization, antenatal care, 
        health education, distribution of contraceptives. Staffed by ANM (Auxiliary Nurse Midwife).
        
        ASHA Workers: Community health workers. Help in accessing health services. Accompany pregnant women to health facilities. 
        Promote immunization and family planning. Provide health education.
        
        Ambulance Services: Dial 108 for free ambulance service. Available 24x7. Equipped with basic life support. 
        Trained paramedics. Free service for emergencies.
        
        Health Schemes: Ayushman Bharat for health insurance. Janani Suraksha Yojana for safe delivery. 
        Rashtriya Bal Swasthya Karyakram for child health screening. All services free or at minimal cost.""",
        "metadata": {
            "source": "Ministry of Health and Family Welfare",
            "category": "health",
            "topic": "health_services",
            "document_type": "service_information"
        }
    }
]


def ingest_documents_to_vector_store():
    """Ingest all documents into the vector database"""
    
    print("=" * 70)
    print(" " * 20 + "DOCUMENT INGESTION")
    print("=" * 70)
    print()
    
    all_documents = []
    
    # Combine all documents
    print("Preparing documents for ingestion...")
    print(f"  - Government scheme documents: {len(SCHEME_DOCUMENTS)}")
    print(f"  - Agricultural guidance documents: {len(AGRICULTURE_DOCUMENTS)}")
    print(f"  - Health information documents: {len(HEALTH_DOCUMENTS)}")
    
    all_documents.extend(SCHEME_DOCUMENTS)
    all_documents.extend(AGRICULTURE_DOCUMENTS)
    all_documents.extend(HEALTH_DOCUMENTS)
    
    print(f"\nTotal documents to ingest: {len(all_documents)}")
    print()
    
    # Ingest documents
    print("Ingesting documents into vector database...")
    print("(This may take a few moments...)")
    print()
    
    documents_to_add = []
    for i, doc in enumerate(all_documents, 1):
        try:
            # Create Document object
            document = Document(
                doc_id=str(uuid.uuid4()),
                content=doc["content"],
                metadata=doc["metadata"],
                source=doc["metadata"].get("source", "Unknown"),
                source_type="official",  # All our seed documents are from official sources
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            documents_to_add.append(document)
            
            category = doc["metadata"].get("category", "unknown")
            doc_type = doc["metadata"].get("document_type", "unknown")
            print(f"  ✓ [{i}/{len(all_documents)}] Prepared: {category}/{doc_type}")
            
        except Exception as e:
            print(f"  ✗ [{i}/{len(all_documents)}] Error: {e}")
    
    # Add all documents in batch
    print(f"\nAdding {len(documents_to_add)} documents to vector store...")
    vector_store.add_documents(documents_to_add)
    
    # Save the index
    print("Saving vector index...")
    vector_store.save_index()
    
    print()
    print("=" * 70)
    print(" " * 20 + "INGESTION COMPLETED!")
    print("=" * 70)
    print()
    print(f"Successfully ingested {len(all_documents)} documents into the vector database.")
    print()
    print("The RAG system is now ready to answer questions about:")
    print("  - Government schemes (PM-KISAN, PM-JAY, MGNREGA, etc.)")
    print("  - Agricultural practices (Rice, Wheat, Organic farming)")
    print("  - Health information (Common diseases, Maternal health, Health services)")
    print()
    print("=" * 70)


def test_vector_search():
    """Test the vector search with sample queries"""
    
    print("\n" + "=" * 70)
    print(" " * 25 + "TESTING SEARCH")
    print("=" * 70)
    print()
    
    test_queries = [
        "How do I apply for PM-KISAN scheme?",
        "What is the best time to plant rice?",
        "Where can I get free health services?"
    ]
    
    for query in test_queries:
        print(f"Query: {query}")
        try:
            results = vector_store.search(query, top_k=2)
            print(f"Found {len(results)} relevant documents:")
            for i, result in enumerate(results, 1):
                doc = result.document
                score = result.score
                metadata = doc.metadata
                print(f"  {i}. Category: {metadata.get('category')}, Score: {score:.3f}")
        except Exception as e:
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
        print()
    
    print("=" * 70)


def main():
    """Main function"""
    try:
        # Run ingestion
        ingest_documents_to_vector_store()
        
        # Test search
        response = input("\nWould you like to test the search functionality? (yes/no): ").strip().lower()
        if response in ['yes', 'y']:
            test_vector_search()
        
    except Exception as e:
        print(f"\n✗ Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
