"""
Script to seed crop-related data into the database.
This includes crop calendars and sample mandi prices.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.farmer import CropCalendar, MandiPrice
from datetime import datetime, date, timedelta
import uuid
import random


def seed_crop_calendars(db: Session):
    """Seed crop calendar data for major crops"""
    
    calendars_data = [
        # Kharif crops (Monsoon season: June-October)
        {
            "crop_name": "Rice",
            "state": "Punjab",
            "district": "Ludhiana",
            "season": "kharif",
            "sowing_start": "June 15",
            "sowing_end": "July 15",
            "harvest_start": "October 15",
            "harvest_end": "November 30",
            "care_schedule": [
                {"activity": "Land preparation", "timing": "May-June"},
                {"activity": "Transplanting", "timing": "June-July"},
                {"activity": "First weeding", "timing": "20-25 days after transplanting"},
                {"activity": "Second weeding", "timing": "40-45 days after transplanting"},
                {"activity": "Fertilizer application", "timing": "Split doses at 20, 40, 60 days"},
                {"activity": "Pest monitoring", "timing": "Throughout growing season"},
                {"activity": "Harvesting", "timing": "When 80% grains turn golden"}
            ]
        },
        {
            "crop_name": "Cotton",
            "state": "Gujarat",
            "district": "Ahmedabad",
            "season": "kharif",
            "sowing_start": "May 15",
            "sowing_end": "June 30",
            "harvest_start": "October 1",
            "harvest_end": "January 31",
            "care_schedule": [
                {"activity": "Land preparation", "timing": "April-May"},
                {"activity": "Sowing", "timing": "May-June"},
                {"activity": "Thinning", "timing": "15-20 days after sowing"},
                {"activity": "First irrigation", "timing": "20-25 days after sowing"},
                {"activity": "Fertilizer application", "timing": "At sowing and 45 days"},
                {"activity": "Pest control", "timing": "Regular monitoring, spray as needed"},
                {"activity": "First picking", "timing": "October onwards"}
            ]
        },
        {
            "crop_name": "Maize",
            "state": "Karnataka",
            "district": "Bangalore",
            "season": "kharif",
            "sowing_start": "June 1",
            "sowing_end": "July 15",
            "harvest_start": "September 15",
            "harvest_end": "November 15",
            "care_schedule": [
                {"activity": "Land preparation", "timing": "May"},
                {"activity": "Sowing", "timing": "June-July"},
                {"activity": "Thinning", "timing": "15 days after sowing"},
                {"activity": "Weeding", "timing": "20-25 and 40-45 days after sowing"},
                {"activity": "Fertilizer application", "timing": "Basal + top dressing at 30 days"},
                {"activity": "Irrigation", "timing": "Critical stages: knee-high, tasseling, grain filling"},
                {"activity": "Harvesting", "timing": "When grains are hard and moisture is 20-25%"}
            ]
        },
        {
            "crop_name": "Soybean",
            "state": "Madhya Pradesh",
            "district": "Indore",
            "season": "kharif",
            "sowing_start": "June 20",
            "sowing_end": "July 10",
            "harvest_start": "October 1",
            "harvest_end": "November 15",
            "care_schedule": [
                {"activity": "Land preparation", "timing": "May-June"},
                {"activity": "Seed treatment", "timing": "Before sowing"},
                {"activity": "Sowing", "timing": "June-July"},
                {"activity": "Weeding", "timing": "20-25 days after sowing"},
                {"activity": "Fertilizer application", "timing": "At sowing"},
                {"activity": "Pest and disease management", "timing": "Regular monitoring"},
                {"activity": "Harvesting", "timing": "When 95% pods turn brown"}
            ]
        },
        
        # Rabi crops (Winter season: October-March)
        {
            "crop_name": "Wheat",
            "state": "Uttar Pradesh",
            "district": "Meerut",
            "season": "rabi",
            "sowing_start": "November 1",
            "sowing_end": "December 15",
            "harvest_start": "March 15",
            "harvest_end": "April 30",
            "care_schedule": [
                {"activity": "Land preparation", "timing": "October"},
                {"activity": "Sowing", "timing": "November-December"},
                {"activity": "First irrigation", "timing": "20-25 days after sowing (CRI stage)"},
                {"activity": "Second irrigation", "timing": "40-45 days (tillering stage)"},
                {"activity": "Third irrigation", "timing": "60-65 days (jointing stage)"},
                {"activity": "Fourth irrigation", "timing": "80-85 days (flowering stage)"},
                {"activity": "Fifth irrigation", "timing": "100-105 days (milk stage)"},
                {"activity": "Fertilizer application", "timing": "Basal + top dressing at CRI and tillering"},
                {"activity": "Weed control", "timing": "30-35 days after sowing"},
                {"activity": "Harvesting", "timing": "When grains are hard"}
            ]
        },
        {
            "crop_name": "Mustard",
            "state": "Rajasthan",
            "district": "Jaipur",
            "season": "rabi",
            "sowing_start": "October 15",
            "sowing_end": "November 15",
            "harvest_start": "February 15",
            "harvest_end": "March 31",
            "care_schedule": [
                {"activity": "Land preparation", "timing": "September-October"},
                {"activity": "Sowing", "timing": "October-November"},
                {"activity": "Thinning", "timing": "15-20 days after sowing"},
                {"activity": "First irrigation", "timing": "30-35 days after sowing"},
                {"activity": "Second irrigation", "timing": "60-65 days (flowering stage)"},
                {"activity": "Third irrigation", "timing": "90-95 days (pod formation)"},
                {"activity": "Fertilizer application", "timing": "Basal + top dressing at 30 days"},
                {"activity": "Harvesting", "timing": "When 75% pods turn brown"}
            ]
        },
        {
            "crop_name": "Chickpea",
            "state": "Madhya Pradesh",
            "district": "Bhopal",
            "season": "rabi",
            "sowing_start": "October 15",
            "sowing_end": "November 15",
            "harvest_start": "March 1",
            "harvest_end": "April 15",
            "care_schedule": [
                {"activity": "Land preparation", "timing": "September-October"},
                {"activity": "Seed treatment", "timing": "Before sowing with Rhizobium"},
                {"activity": "Sowing", "timing": "October-November"},
                {"activity": "Weeding", "timing": "30-35 days after sowing"},
                {"activity": "Irrigation", "timing": "One at flowering, one at pod filling (if needed)"},
                {"activity": "Fertilizer application", "timing": "At sowing"},
                {"activity": "Pest control", "timing": "Monitor for pod borer"},
                {"activity": "Harvesting", "timing": "When pods turn brown and dry"}
            ]
        },
        {
            "crop_name": "Potato",
            "state": "West Bengal",
            "district": "Hooghly",
            "season": "rabi",
            "sowing_start": "November 1",
            "sowing_end": "December 15",
            "harvest_start": "February 15",
            "harvest_end": "March 31",
            "care_schedule": [
                {"activity": "Land preparation", "timing": "October"},
                {"activity": "Seed treatment", "timing": "Before planting"},
                {"activity": "Planting", "timing": "November-December"},
                {"activity": "Earthing up", "timing": "30 days after planting"},
                {"activity": "Irrigation", "timing": "Light frequent irrigation"},
                {"activity": "Fertilizer application", "timing": "Basal + top dressing at earthing up"},
                {"activity": "Late blight control", "timing": "Preventive sprays from 45 days"},
                {"activity": "Harvesting", "timing": "When tops dry up"}
            ]
        },
        
        # Zaid crops (Summer season: March-June)
        {
            "crop_name": "Watermelon",
            "state": "Uttar Pradesh",
            "district": "Lucknow",
            "season": "zaid",
            "sowing_start": "February 15",
            "sowing_end": "March 31",
            "harvest_start": "May 15",
            "harvest_end": "June 30",
            "care_schedule": [
                {"activity": "Land preparation", "timing": "January-February"},
                {"activity": "Sowing", "timing": "February-March"},
                {"activity": "Thinning", "timing": "15 days after germination"},
                {"activity": "Irrigation", "timing": "Frequent light irrigation"},
                {"activity": "Fertilizer application", "timing": "Basal + split doses"},
                {"activity": "Vine training", "timing": "As needed"},
                {"activity": "Harvesting", "timing": "When fruit gives hollow sound on tapping"}
            ]
        },
        {
            "crop_name": "Muskmelon",
            "state": "Rajasthan",
            "district": "Jodhpur",
            "season": "zaid",
            "sowing_start": "February 1",
            "sowing_end": "March 15",
            "harvest_start": "May 1",
            "harvest_end": "June 15",
            "care_schedule": [
                {"activity": "Land preparation", "timing": "January"},
                {"activity": "Sowing", "timing": "February-March"},
                {"activity": "Thinning", "timing": "10-15 days after germination"},
                {"activity": "Irrigation", "timing": "Regular light irrigation"},
                {"activity": "Fertilizer application", "timing": "Basal + foliar spray"},
                {"activity": "Harvesting", "timing": "When fruit develops characteristic aroma"}
            ]
        },
        
        # Year-round crops
        {
            "crop_name": "Sugarcane",
            "state": "Uttar Pradesh",
            "district": "Muzaffarnagar",
            "season": "kharif",
            "sowing_start": "February 15",
            "sowing_end": "March 31",
            "harvest_start": "December 1",
            "harvest_end": "March 31",
            "care_schedule": [
                {"activity": "Land preparation", "timing": "January-February"},
                {"activity": "Planting", "timing": "February-March"},
                {"activity": "Gap filling", "timing": "30 days after planting"},
                {"activity": "Irrigation", "timing": "Regular throughout growing season"},
                {"activity": "Fertilizer application", "timing": "Split doses at 30, 60, 90 days"},
                {"activity": "Earthing up", "timing": "90-120 days after planting"},
                {"activity": "Pest and disease management", "timing": "Regular monitoring"},
                {"activity": "Harvesting", "timing": "When cane matures (10-12 months)"}
            ]
        }
    ]
    
    print(f"Seeding {len(calendars_data)} crop calendars...")
    
    for calendar_data in calendars_data:
        calendar = CropCalendar(
            calendar_id=uuid.uuid4(),
            **calendar_data
        )
        db.add(calendar)
        print(f"  ✓ Added: {calendar.crop_name} ({calendar.season}, {calendar.state})")
    
    db.commit()
    print(f"\n✓ Successfully seeded {len(calendars_data)} crop calendars!")


def seed_mandi_prices(db: Session):
    """Seed sample mandi price data"""
    
    # Major crops
    crops = ["Rice", "Wheat", "Cotton", "Maize", "Soybean", "Mustard", "Chickpea", "Potato", "Sugarcane", "Onion", "Tomato"]
    
    # Mandis across different states
    mandis = [
        {"name": "Ludhiana Mandi", "state": "Punjab", "district": "Ludhiana", "lat": 30.9010, "lon": 75.8573},
        {"name": "Meerut Mandi", "state": "Uttar Pradesh", "district": "Meerut", "lat": 28.9845, "lon": 77.7064},
        {"name": "Ahmedabad APMC", "state": "Gujarat", "district": "Ahmedabad", "lat": 23.0225, "lon": 72.5714},
        {"name": "Indore Mandi", "state": "Madhya Pradesh", "district": "Indore", "lat": 22.7196, "lon": 75.8577},
        {"name": "Bangalore APMC", "state": "Karnataka", "district": "Bangalore", "lat": 12.9716, "lon": 77.5946},
        {"name": "Jaipur Mandi", "state": "Rajasthan", "district": "Jaipur", "lat": 26.9124, "lon": 75.7873},
        {"name": "Patna Mandi", "state": "Bihar", "district": "Patna", "lat": 25.5941, "lon": 85.1376},
        {"name": "Kolkata Mandi", "state": "West Bengal", "district": "Kolkata", "lat": 22.5726, "lon": 88.3639},
        {"name": "Pune APMC", "state": "Maharashtra", "district": "Pune", "lat": 18.5204, "lon": 73.8567},
        {"name": "Hyderabad Mandi", "state": "Telangana", "district": "Hyderabad", "lat": 17.3850, "lon": 78.4867},
    ]
    
    # Base prices per quintal (in INR) - realistic ranges
    base_prices = {
        "Rice": (1800, 2500),
        "Wheat": (1900, 2200),
        "Cotton": (5500, 6500),
        "Maize": (1400, 1800),
        "Soybean": (3500, 4200),
        "Mustard": (4500, 5500),
        "Chickpea": (4800, 5800),
        "Potato": (800, 1500),
        "Sugarcane": (280, 350),
        "Onion": (1000, 2500),
        "Tomato": (800, 2000)
    }
    
    prices_data = []
    
    # Generate prices for last 30 days
    today = date.today()
    
    for days_ago in range(30):
        price_date = today - timedelta(days=days_ago)
        
        # Generate prices for subset of crops at each mandi
        for mandi in mandis:
            # Each mandi has 5-7 crops
            num_crops = random.randint(5, 7)
            selected_crops = random.sample(crops, num_crops)
            
            for crop in selected_crops:
                min_price, max_price = base_prices[crop]
                # Add some variation
                price = random.uniform(min_price, max_price)
                # Round to nearest 10
                price = round(price / 10) * 10
                
                prices_data.append({
                    "crop_name": crop,
                    "mandi_name": mandi["name"],
                    "state": mandi["state"],
                    "district": mandi["district"],
                    "latitude": mandi["lat"],
                    "longitude": mandi["lon"],
                    "price_per_quintal": price,
                    "price_date": price_date,
                    "source": "Government Mandi API",
                    "last_updated": datetime.utcnow()
                })
    
    print(f"\nSeeding {len(prices_data)} mandi price records...")
    
    for price_data in prices_data:
        price = MandiPrice(
            price_id=uuid.uuid4(),
            **price_data
        )
        db.add(price)
    
    db.commit()
    print(f"✓ Successfully seeded {len(prices_data)} mandi price records!")
    print(f"  - Covering {len(crops)} crops across {len(mandis)} mandis")
    print(f"  - Price data for last 30 days")


def main():
    """Main function to run seeding"""
    print("=" * 60)
    print("Crop Data Seeding (Calendars and Mandi Prices)")
    print("=" * 60)
    print()
    
    db = SessionLocal()
    try:
        seed_crop_calendars(db)
        seed_mandi_prices(db)
    except Exception as e:
        print(f"\n✗ Error seeding crop data: {e}")
        db.rollback()
        raise
    finally:
        db.close()
    
    print("\n" + "=" * 60)
    print("Seeding completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
