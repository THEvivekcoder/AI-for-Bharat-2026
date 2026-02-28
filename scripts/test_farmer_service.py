"""Test script for Farmer Advisory Service"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.user import User, UserProfile
from app.models.location import Location
from app.models.farmer import FarmProfile
from app.services.crop_advisor import CropAdvisor
from app.services.fertilizer_advisor import FertilizerAdvisor
from app.services.mandi_price_service import MandiPriceService
from app.schemas.farmer import SoilData
import uuid


def test_crop_advisor():
    """Test crop advisor service"""
    print("\n=== Testing Crop Advisor ===")
    
    db = SessionLocal()
    try:
        # Create test user
        user = User(
            phone_number="+919999999999",
            language="hi"
        )
        db.add(user)
        db.flush()
        
        # Create test location
        location = Location(
            state="Punjab",
            district="Ludhiana",
            pincode="141001",
            latitude=30.9010,
            longitude=75.8573
        )
        db.add(location)
        db.flush()
        
        # Create test farm profile
        farm_profile = FarmProfile(
            user_id=user.user_id,
            land_size_acres=5.0,
            soil_type="loam",
            irrigation_type="canal",
            location_id=location.id,
            current_crops=["wheat"],
            previous_crops=["rice"]
        )
        db.add(farm_profile)
        db.flush()
        
        # Test crop recommendations
        crop_advisor = CropAdvisor(db)
        
        print("\n1. Testing Kharif season recommendations:")
        kharif_recommendations = crop_advisor.recommend_crops(
            farm_profile=farm_profile,
            season="kharif",
            include_weather=True
        )
        
        print(f"   Found {len(kharif_recommendations)} recommendations")
        for rec in kharif_recommendations[:3]:
            print(f"   - {rec.crop_name}: Score {rec.suitability_score:.2f}")
            print(f"     Water: {rec.water_requirement}, Duration: {rec.duration_days} days")
            print(f"     Reasoning: {rec.reasoning[:100]}...")
        
        print("\n2. Testing Rabi season recommendations:")
        rabi_recommendations = crop_advisor.recommend_crops(
            farm_profile=farm_profile,
            season="rabi",
            include_weather=True
        )
        
        print(f"   Found {len(rabi_recommendations)} recommendations")
        for rec in rabi_recommendations[:3]:
            print(f"   - {rec.crop_name}: Score {rec.suitability_score:.2f}")
        
        print("\n3. Testing crop calendar:")
        calendar = crop_advisor.get_crop_calendar(
            crop_name="rice",
            state="Punjab",
            district="Ludhiana"
        )
        
        if calendar:
            print(f"   Crop: {calendar.crop_name}")
            print(f"   Season: {calendar.season}")
            print(f"   Sowing: {calendar.sowing_start} - {calendar.sowing_end}")
            print(f"   Harvest: {calendar.harvest_start} - {calendar.harvest_end}")
        
        print("\n✓ Crop Advisor tests passed")
        
    finally:
        db.rollback()
        db.close()


def test_fertilizer_advisor():
    """Test fertilizer advisor service"""
    print("\n=== Testing Fertilizer Advisor ===")
    
    db = SessionLocal()
    try:
        # Create test user
        user = User(
            phone_number="+919999999998",
            language="hi"
        )
        db.add(user)
        db.flush()
        
        # Create test location
        location = Location(
            state="Punjab",
            district="Ludhiana",
            pincode="141001"
        )
        db.add(location)
        db.flush()
        
        # Create test farm profile
        farm_profile = FarmProfile(
            user_id=user.user_id,
            land_size_acres=5.0,
            soil_type="loam",
            irrigation_type="canal",
            location_id=location.id
        )
        db.add(farm_profile)
        db.flush()
        
        # Test fertilizer recommendations
        fertilizer_advisor = FertilizerAdvisor(db)
        
        print("\n1. Testing rice fertilizer at sowing stage:")
        rec1 = fertilizer_advisor.recommend_fertilizer(
            farm_profile=farm_profile,
            crop_name="rice",
            growth_stage="sowing",
            soil_data=None
        )
        
        print(f"   Fertilizer: {rec1.fertilizer_type}")
        print(f"   Quantity: {rec1.quantity_per_acre}")
        print(f"   Timing: {rec1.timing}")
        print(f"   Method: {rec1.application_method}")
        
        print("\n2. Testing wheat fertilizer at vegetative stage with soil data:")
        soil_data = SoilData(
            soil_ph=6.5,
            nitrogen_level="low",
            phosphorus_level="medium",
            potassium_level="high"
        )
        
        rec2 = fertilizer_advisor.recommend_fertilizer(
            farm_profile=farm_profile,
            crop_name="wheat",
            growth_stage="vegetative",
            soil_data=soil_data
        )
        
        print(f"   Fertilizer: {rec2.fertilizer_type}")
        print(f"   Quantity: {rec2.quantity_per_acre}")
        print(f"   Additional notes: {rec2.additional_notes[:100]}...")
        
        print("\n3. Testing unknown crop:")
        rec3 = fertilizer_advisor.recommend_fertilizer(
            farm_profile=farm_profile,
            crop_name="unknown_crop",
            growth_stage="flowering",
            soil_data=None
        )
        
        print(f"   Fertilizer: {rec3.fertilizer_type}")
        print(f"   Quantity: {rec3.quantity_per_acre}")
        
        print("\n✓ Fertilizer Advisor tests passed")
        
    finally:
        db.rollback()
        db.close()


def test_mandi_price_service():
    """Test mandi price service"""
    print("\n=== Testing Mandi Price Service ===")
    
    db = SessionLocal()
    try:
        # Create test location
        location = Location(
            state="Delhi",
            district="New Delhi",
            pincode="110001",
            latitude=28.6139,
            longitude=77.2090
        )
        db.add(location)
        db.flush()
        
        # Test mandi price service
        mandi_service = MandiPriceService(db)
        
        print("\n1. Seeding sample prices:")
        count = mandi_service.seed_sample_prices()
        print(f"   Seeded {count} sample prices")
        
        print("\n2. Testing get current prices:")
        prices = mandi_service.get_current_price(
            crop_name="rice",
            location=location,
            radius_km=50
        )
        
        print(f"   Found {len(prices)} prices")
        for price in prices:
            print(f"   - {price.mandi_name}: ₹{price.price_per_quintal}/quintal")
            print(f"     Location: {price.district}, {price.state}")
            if price.distance_km:
                print(f"     Distance: {price.distance_km} km")
        
        print("\n3. Testing price trend:")
        trend = mandi_service.get_price_trend(
            crop_name="rice",
            location=location,
            days=30
        )
        
        if trend:
            print(f"   Crop: {trend.crop_name}")
            print(f"   Location: {trend.location}")
            print(f"   Average price: ₹{trend.average_price}/quintal")
            print(f"   Min price: ₹{trend.min_price}/quintal")
            print(f"   Max price: ₹{trend.max_price}/quintal")
            print(f"   Trend: {trend.trend}")
            print(f"   Data points: {len(trend.prices)}")
        
        print("\n✓ Mandi Price Service tests passed")
        
    finally:
        db.rollback()
        db.close()


def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Farmer Advisory Service")
    print("=" * 60)
    
    try:
        test_crop_advisor()
        test_fertilizer_advisor()
        test_mandi_price_service()
        
        print("\n" + "=" * 60)
        print("✓ All Farmer Advisory Service tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
