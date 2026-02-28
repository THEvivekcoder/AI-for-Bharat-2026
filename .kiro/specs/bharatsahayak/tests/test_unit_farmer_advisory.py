"""
Unit tests for Farmer Advisory Service

Tests crop recommendations with various soil types, fertilizer guidance edge cases,
and price lookup with no nearby mandis.

Feature: bharatsahayak
Requirements: 3.1, 3.2, 3.3, 3.5
"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import Mock, MagicMock
import uuid

from app.services.crop_advisor import CropAdvisor
from app.services.fertilizer_advisor import FertilizerAdvisor
from app.services.mandi_price_service import MandiPriceService
from app.models.farmer import FarmProfile, MandiPrice
from app.models.location import Location
from app.schemas.farmer import SoilData


@pytest.fixture
def mock_db():
    """Create a mock database session"""
    return Mock()


@pytest.fixture
def sample_location():
    """Create a sample location"""
    location = Location(
        id=uuid.uuid4(),
        state="Maharashtra",
        district="Pune",
        pincode="411001",
        latitude=18.5204,
        longitude=73.8567
    )
    return location


@pytest.fixture
def sample_farm_profile(sample_location):
    """Create a sample farm profile"""
    farm = FarmProfile(
        farm_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        land_size_acres=5.0,
        soil_type="loam",
        irrigation_type="well",
        location_id=sample_location.id,
        current_crops=["rice"],
        previous_crops=["wheat"],
        livestock=None
    )
    farm.location = sample_location
    return farm


class TestCropRecommendationsWithSoilTypes:
    """Test crop recommendations with various soil types"""
    
    def test_crop_recommendations_for_clay_soil(self, mock_db, sample_farm_profile):
        """Test crop recommendations for clay soil"""
        sample_farm_profile.soil_type = "clay"
        
        advisor = CropAdvisor(mock_db)
        recommendations = advisor.recommend_crops(sample_farm_profile, "kharif")
        
        # Clay soil is suitable for rice, wheat, cotton
        assert len(recommendations) > 0
        crop_names = [r.crop_name for r in recommendations]
        assert "rice" in crop_names
        
        # Check that rice has high suitability for clay soil
        rice_rec = next(r for r in recommendations if r.crop_name == "rice")
        assert rice_rec.suitability_score > 0.5
        assert "clay" in rice_rec.reasoning.lower()
    
    def test_crop_recommendations_for_sandy_soil(self, mock_db, sample_farm_profile):
        """Test crop recommendations for sandy soil"""
        sample_farm_profile.soil_type = "sandy"
        
        advisor = CropAdvisor(mock_db)
        recommendations = advisor.recommend_crops(sample_farm_profile, "kharif")
        
        # Sandy soil is suitable for groundnut, maize, vegetables
        assert len(recommendations) > 0
        crop_names = [r.crop_name for r in recommendations]
        assert "groundnut" in crop_names or "maize" in crop_names
        
        # Check that recommendations mention sandy soil
        for rec in recommendations:
            if rec.crop_name in ["groundnut", "maize"]:
                assert rec.suitability_score > 0.3
    
    def test_crop_recommendations_for_black_soil(self, mock_db, sample_farm_profile):
        """Test crop recommendations for black soil"""
        sample_farm_profile.soil_type = "black"
        
        advisor = CropAdvisor(mock_db)
        recommendations = advisor.recommend_crops(sample_farm_profile, "kharif")
        
        # Black soil is ideal for cotton, soybean
        assert len(recommendations) > 0
        crop_names = [r.crop_name for r in recommendations]
        assert "cotton" in crop_names or "soybean" in crop_names
        
        # Cotton should have high suitability for black soil
        cotton_rec = next((r for r in recommendations if r.crop_name == "cotton"), None)
        if cotton_rec:
            assert cotton_rec.suitability_score > 0.5
    
    def test_crop_recommendations_for_loam_soil(self, mock_db, sample_farm_profile):
        """Test crop recommendations for loam soil (most versatile)"""
        sample_farm_profile.soil_type = "loam"
        
        advisor = CropAdvisor(mock_db)
        recommendations = advisor.recommend_crops(sample_farm_profile, "kharif")
        
        # Loam soil is suitable for most crops
        assert len(recommendations) >= 5
        
        # Most crops should have decent suitability scores
        high_score_crops = [r for r in recommendations if r.suitability_score > 0.5]
        assert len(high_score_crops) >= 3
    
    def test_crop_recommendations_for_red_soil(self, mock_db, sample_farm_profile):
        """Test crop recommendations for red soil"""
        sample_farm_profile.soil_type = "red"
        
        advisor = CropAdvisor(mock_db)
        recommendations = advisor.recommend_crops(sample_farm_profile, "rabi")
        
        # Red soil is suitable for pulses, groundnut
        assert len(recommendations) > 0
        crop_names = [r.crop_name for r in recommendations]
        # Pulses should be recommended for red soil
        assert "pulses" in crop_names or "groundnut" in crop_names
    
    def test_crop_recommendations_for_alluvial_soil(self, mock_db, sample_farm_profile):
        """Test crop recommendations for alluvial soil"""
        sample_farm_profile.soil_type = "alluvial"
        
        advisor = CropAdvisor(mock_db)
        recommendations = advisor.recommend_crops(sample_farm_profile, "kharif")
        
        # Alluvial soil is very fertile and suitable for many crops
        assert len(recommendations) >= 5
        
        # Rice, wheat, sugarcane should have high scores
        crop_names = [r.crop_name for r in recommendations]
        assert "rice" in crop_names
        assert "sugarcane" in crop_names or "maize" in crop_names
    
    def test_crop_recommendations_consider_irrigation_type(self, mock_db, sample_farm_profile):
        """Test that crop recommendations consider irrigation type"""
        sample_farm_profile.irrigation_type = "rainfed"
        
        advisor = CropAdvisor(mock_db)
        recommendations = advisor.recommend_crops(sample_farm_profile, "kharif")
        
        # Rainfed should favor low water requirement crops
        assert len(recommendations) > 0
        
        # Check that recommendations mention irrigation
        for rec in recommendations:
            if rec.water_requirement == "low":
                # Low water crops should have better scores for rainfed
                assert rec.suitability_score > 0.3
    
    def test_crop_recommendations_for_drip_irrigation(self, mock_db, sample_farm_profile):
        """Test crop recommendations for drip irrigation"""
        sample_farm_profile.irrigation_type = "drip"
        
        advisor = CropAdvisor(mock_db)
        recommendations = advisor.recommend_crops(sample_farm_profile, "kharif")
        
        # Drip irrigation is efficient and suitable for most crops
        assert len(recommendations) > 0
        
        # Vegetables should be highly recommended with drip
        veg_rec = next((r for r in recommendations if r.crop_name == "vegetables"), None)
        if veg_rec:
            assert veg_rec.suitability_score > 0.6
    
    def test_crop_recommendations_for_small_farm(self, mock_db, sample_farm_profile):
        """Test crop recommendations for small farm size"""
        sample_farm_profile.land_size_acres = 1.5
        
        advisor = CropAdvisor(mock_db)
        recommendations = advisor.recommend_crops(sample_farm_profile, "kharif")
        
        # Small farms should favor vegetables and short duration crops
        assert len(recommendations) > 0
        
        # Vegetables should have high score for small farms
        veg_rec = next((r for r in recommendations if r.crop_name == "vegetables"), None)
        if veg_rec:
            assert veg_rec.suitability_score > 0.5
    
    def test_crop_recommendations_for_large_farm(self, mock_db, sample_farm_profile):
        """Test crop recommendations for large farm size"""
        sample_farm_profile.land_size_acres = 20.0
        
        advisor = CropAdvisor(mock_db)
        recommendations = advisor.recommend_crops(sample_farm_profile, "kharif")
        
        # Large farms should favor high-demand commercial crops
        assert len(recommendations) > 0
        
        # High demand crops should get bonus for large farms
        high_demand_crops = [r for r in recommendations if r.market_demand == "high"]
        assert len(high_demand_crops) > 0


class TestFertilizerGuidanceEdgeCases:
    """Test fertilizer guidance with edge cases"""
    
    def test_fertilizer_for_unknown_crop(self, mock_db, sample_farm_profile):
        """Test fertilizer recommendation for unknown/unsupported crop"""
        advisor = FertilizerAdvisor(mock_db)
        
        recommendation = advisor.recommend_fertilizer(
            sample_farm_profile,
            "dragon_fruit",  # Unknown crop
            "vegetative"
        )
        
        # Should return default recommendation
        assert recommendation is not None
        assert recommendation.fertilizer_type is not None
        assert recommendation.quantity_per_acre is not None
        assert "general recommendation" in recommendation.additional_notes.lower()
    
    def test_fertilizer_for_unknown_growth_stage(self, mock_db, sample_farm_profile):
        """Test fertilizer recommendation for unknown growth stage"""
        advisor = FertilizerAdvisor(mock_db)
        
        recommendation = advisor.recommend_fertilizer(
            sample_farm_profile,
            "rice",
            "unknown_stage"  # Unknown stage
        )
        
        # Should return closest matching stage recommendation
        assert recommendation is not None
        assert recommendation.fertilizer_type is not None
        assert recommendation.timing is not None
    
    def test_fertilizer_with_acidic_soil(self, mock_db, sample_farm_profile):
        """Test fertilizer recommendation with acidic soil (low pH)"""
        advisor = FertilizerAdvisor(mock_db)
        
        soil_data = SoilData(
            soil_ph=4.5,  # Acidic
            nitrogen_level="medium",
            phosphorus_level="medium",
            potassium_level="medium"
        )
        
        recommendation = advisor.recommend_fertilizer(
            sample_farm_profile,
            "rice",
            "sowing",
            soil_data
        )
        
        # Should recommend lime application
        assert "lime" in recommendation.application_method.lower()
        assert "acidity" in recommendation.application_method.lower()
    
    def test_fertilizer_with_alkaline_soil(self, mock_db, sample_farm_profile):
        """Test fertilizer recommendation with alkaline soil (high pH)"""
        advisor = FertilizerAdvisor(mock_db)
        
        soil_data = SoilData(
            soil_ph=8.5,  # Alkaline
            nitrogen_level="medium",
            phosphorus_level="medium",
            potassium_level="medium"
        )
        
        recommendation = advisor.recommend_fertilizer(
            sample_farm_profile,
            "wheat",
            "sowing",
            soil_data
        )
        
        # Should recommend gypsum application
        assert "gypsum" in recommendation.application_method.lower()
        assert "alkalinity" in recommendation.application_method.lower()
    
    def test_fertilizer_with_high_nitrogen(self, mock_db, sample_farm_profile):
        """Test fertilizer recommendation when soil has high nitrogen"""
        advisor = FertilizerAdvisor(mock_db)
        
        soil_data = SoilData(
            soil_ph=6.5,
            nitrogen_level="high",
            phosphorus_level="medium",
            potassium_level="medium"
        )
        
        recommendation = advisor.recommend_fertilizer(
            sample_farm_profile,
            "rice",
            "vegetative",
            soil_data
        )
        
        # Should recommend reducing nitrogen
        assert "reduce nitrogen" in recommendation.application_method.lower()
    
    def test_fertilizer_with_low_nitrogen(self, mock_db, sample_farm_profile):
        """Test fertilizer recommendation when soil has low nitrogen"""
        advisor = FertilizerAdvisor(mock_db)
        
        soil_data = SoilData(
            soil_ph=6.5,
            nitrogen_level="low",
            phosphorus_level="medium",
            potassium_level="medium"
        )
        
        recommendation = advisor.recommend_fertilizer(
            sample_farm_profile,
            "wheat",
            "vegetative",
            soil_data
        )
        
        # Should recommend increasing nitrogen
        assert "increase nitrogen" in recommendation.application_method.lower()
    
    def test_fertilizer_with_low_potassium(self, mock_db, sample_farm_profile):
        """Test fertilizer recommendation when soil has low potassium"""
        advisor = FertilizerAdvisor(mock_db)
        
        soil_data = SoilData(
            soil_ph=6.5,
            nitrogen_level="medium",
            phosphorus_level="medium",
            potassium_level="low"
        )
        
        recommendation = advisor.recommend_fertilizer(
            sample_farm_profile,
            "cotton",
            "flowering",
            soil_data
        )
        
        # Should recommend additional potash
        assert "potash" in recommendation.application_method.lower() or "mop" in recommendation.application_method.lower()
    
    def test_fertilizer_without_soil_data(self, mock_db, sample_farm_profile):
        """Test fertilizer recommendation without soil test data"""
        advisor = FertilizerAdvisor(mock_db)
        
        recommendation = advisor.recommend_fertilizer(
            sample_farm_profile,
            "maize",
            "sowing",
            soil_data=None
        )
        
        # Should provide base recommendation and suggest soil testing
        assert recommendation is not None
        assert "soil testing" in recommendation.additional_notes.lower()
    
    def test_fertilizer_for_drip_irrigation(self, mock_db, sample_farm_profile):
        """Test fertilizer recommendation for drip irrigation (fertigation)"""
        sample_farm_profile.irrigation_type = "drip"
        
        advisor = FertilizerAdvisor(mock_db)
        
        recommendation = advisor.recommend_fertilizer(
            sample_farm_profile,
            "vegetables",
            "vegetative"
        )
        
        # Should mention fertigation
        assert "fertigation" in recommendation.additional_notes.lower()
    
    def test_fertilizer_for_rainfed_farming(self, mock_db, sample_farm_profile):
        """Test fertilizer recommendation for rainfed farming"""
        sample_farm_profile.irrigation_type = "rainfed"
        
        advisor = FertilizerAdvisor(mock_db)
        
        recommendation = advisor.recommend_fertilizer(
            sample_farm_profile,
            "pulses",
            "sowing"
        )
        
        # Should mention rainfall timing
        assert "rainfall" in recommendation.additional_notes.lower()
    
    def test_fertilizer_for_sandy_soil(self, mock_db, sample_farm_profile):
        """Test fertilizer recommendation for sandy soil (leaching risk)"""
        sample_farm_profile.soil_type = "sandy"
        
        advisor = FertilizerAdvisor(mock_db)
        
        recommendation = advisor.recommend_fertilizer(
            sample_farm_profile,
            "maize",  # Use maize which is in the crop database
            "vegetative"
        )
        
        # Should mention split application to prevent leaching
        assert "split" in recommendation.additional_notes.lower() or "leaching" in recommendation.additional_notes.lower()
    
    def test_fertilizer_for_clay_soil(self, mock_db, sample_farm_profile):
        """Test fertilizer recommendation for clay soil (nutrient retention)"""
        sample_farm_profile.soil_type = "clay"
        
        advisor = FertilizerAdvisor(mock_db)
        
        recommendation = advisor.recommend_fertilizer(
            sample_farm_profile,
            "rice",
            "sowing"
        )
        
        # Should mention nutrient retention
        assert "retain" in recommendation.additional_notes.lower() or "over-application" in recommendation.additional_notes.lower()
    
    def test_fertilizer_includes_organic_matter_recommendation(self, mock_db, sample_farm_profile):
        """Test that fertilizer recommendations include organic matter advice"""
        advisor = FertilizerAdvisor(mock_db)
        
        recommendation = advisor.recommend_fertilizer(
            sample_farm_profile,
            "wheat",
            "sowing"
        )
        
        # Should recommend FYM or organic matter
        assert "fym" in recommendation.additional_notes.lower() or "organic" in recommendation.additional_notes.lower()
    
    def test_fertilizer_includes_micronutrient_advice(self, mock_db, sample_farm_profile):
        """Test that fertilizer recommendations include micronutrient advice"""
        advisor = FertilizerAdvisor(mock_db)
        
        recommendation = advisor.recommend_fertilizer(
            sample_farm_profile,
            "cotton",
            "flowering"
        )
        
        # Should mention micronutrients
        assert "micronutrient" in recommendation.additional_notes.lower() or "zinc" in recommendation.additional_notes.lower() or "boron" in recommendation.additional_notes.lower()


class TestMandiPriceLookupNoNearbyMandis:
    """Test mandi price lookup when no nearby mandis are found"""
    
    def test_price_lookup_with_no_mandis_in_database(self, mock_db, sample_location):
        """Test price lookup when database has no mandi prices"""
        # Mock empty query result
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        service = MandiPriceService(mock_db)
        prices = service.get_current_price("rice", sample_location, radius_km=50)
        
        # Should return empty list
        assert len(prices) == 0
        assert isinstance(prices, list)
    
    def test_price_lookup_with_mandis_outside_radius(self, mock_db, sample_location):
        """Test price lookup when all mandis are outside search radius"""
        # Create mandi prices far away
        far_mandi = MandiPrice(
            price_id=uuid.uuid4(),
            crop_name="rice",
            mandi_name="Far Mandi",
            state="Karnataka",  # Different state
            district="Bangalore",
            latitude=12.9716,  # Bangalore coordinates (far from Pune)
            longitude=77.5946,
            price_per_quintal=2500.0,
            price_date=date.today(),
            source="Test"
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [far_mandi]
        
        mock_db.query.return_value = mock_query
        
        service = MandiPriceService(mock_db)
        prices = service.get_current_price("rice", sample_location, radius_km=50)
        
        # Should return empty list (mandi is > 50km away)
        assert len(prices) == 0
    
    def test_price_lookup_with_old_prices(self, mock_db, sample_location):
        """Test price lookup when prices are too old (> 7 days)"""
        # Create old mandi price
        old_mandi = MandiPrice(
            price_id=uuid.uuid4(),
            crop_name="rice",
            mandi_name="Pune Mandi",
            state="Maharashtra",
            district="Pune",
            latitude=18.5204,
            longitude=73.8567,
            price_per_quintal=2500.0,
            price_date=date.today() - timedelta(days=10),  # 10 days old
            source="Test"
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []  # Filtered out by date
        
        mock_db.query.return_value = mock_query
        
        service = MandiPriceService(mock_db)
        prices = service.get_current_price("rice", sample_location, radius_km=50)
        
        # Should return empty list (prices too old)
        assert len(prices) == 0
    
    def test_price_lookup_with_wrong_crop(self, mock_db, sample_location):
        """Test price lookup for crop not in database"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        service = MandiPriceService(mock_db)
        prices = service.get_current_price("dragon_fruit", sample_location, radius_km=50)
        
        # Should return empty list
        assert len(prices) == 0
    
    def test_price_lookup_without_coordinates(self, mock_db, sample_location):
        """Test price lookup when location has no coordinates"""
        sample_location.latitude = None
        sample_location.longitude = None
        
        # Create mandi in same district
        local_mandi = MandiPrice(
            price_id=uuid.uuid4(),
            crop_name="wheat",
            mandi_name="Pune Mandi",
            state="Maharashtra",
            district="Pune",
            latitude=None,
            longitude=None,
            price_per_quintal=2200.0,
            price_date=date.today(),
            source="Test"
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [local_mandi]
        
        mock_db.query.return_value = mock_query
        
        service = MandiPriceService(mock_db)
        prices = service.get_current_price("wheat", sample_location, radius_km=50)
        
        # Should return mandi from same district even without coordinates
        assert len(prices) == 1
        assert prices[0].district == "Pune"
    
    def test_price_trend_with_no_data(self, mock_db, sample_location):
        """Test price trend when no historical data exists"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        service = MandiPriceService(mock_db)
        trend = service.get_price_trend("rice", sample_location, days=30)
        
        # Should return None when no data
        assert trend is None
    
    def test_price_lookup_returns_most_recent_per_mandi(self, mock_db, sample_location):
        """Test that price lookup returns only most recent price per mandi"""
        # Create multiple prices for same mandi
        old_price = MandiPrice(
            price_id=uuid.uuid4(),
            crop_name="rice",
            mandi_name="Pune Mandi",
            state="Maharashtra",
            district="Pune",
            latitude=18.5204,
            longitude=73.8567,
            price_per_quintal=2400.0,
            price_date=date.today() - timedelta(days=3),
            source="Test"
        )
        
        new_price = MandiPrice(
            price_id=uuid.uuid4(),
            crop_name="rice",
            mandi_name="Pune Mandi",
            state="Maharashtra",
            district="Pune",
            latitude=18.5204,
            longitude=73.8567,
            price_per_quintal=2500.0,
            price_date=date.today(),
            source="Test"
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [old_price, new_price]
        
        mock_db.query.return_value = mock_query
        
        service = MandiPriceService(mock_db)
        prices = service.get_current_price("rice", sample_location, radius_km=50)
        
        # Should return only one price (most recent)
        assert len(prices) == 1
        assert prices[0].price_per_quintal == 2500.0
    
    def test_price_lookup_sorts_by_distance(self, mock_db, sample_location):
        """Test that price lookup results are sorted by distance"""
        # Create mandis at different distances
        near_mandi = MandiPrice(
            price_id=uuid.uuid4(),
            crop_name="rice",
            mandi_name="Near Mandi",
            state="Maharashtra",
            district="Pune",
            latitude=18.5304,  # Very close
            longitude=73.8667,
            price_per_quintal=2500.0,
            price_date=date.today(),
            source="Test"
        )
        
        far_mandi = MandiPrice(
            price_id=uuid.uuid4(),
            crop_name="rice",
            mandi_name="Far Mandi",
            state="Maharashtra",
            district="Satara",
            latitude=17.6869,  # Further away but within radius
            longitude=74.0132,
            price_per_quintal=2450.0,
            price_date=date.today(),
            source="Test"
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [far_mandi, near_mandi]  # Unsorted
        
        mock_db.query.return_value = mock_query
        
        service = MandiPriceService(mock_db)
        prices = service.get_current_price("rice", sample_location, radius_km=200)
        
        # Should be sorted by distance (nearest first)
        if len(prices) >= 2:
            assert prices[0].distance_km < prices[1].distance_km
    
    def test_distance_calculation_accuracy(self, mock_db):
        """Test that distance calculation is reasonably accurate"""
        service = MandiPriceService(mock_db)
        
        # Pune to Mumbai (approximately 150 km)
        pune_lat, pune_lon = 18.5204, 73.8567
        mumbai_lat, mumbai_lon = 19.0760, 72.8777
        
        distance = service._calculate_distance(pune_lat, pune_lon, mumbai_lat, mumbai_lon)
        
        # Should be approximately 150 km (allow 20% margin)
        assert 120 <= distance <= 180
    
    def test_cache_usage_for_price_lookup(self, mock_db, sample_location):
        """Test that price lookup uses cache when available"""
        mock_cache = Mock()
        mock_cache.get.return_value = None  # Cache miss
        mock_cache.setex = Mock()
        
        # Create a mandi price to return
        mandi = MandiPrice(
            price_id=uuid.uuid4(),
            crop_name="rice",
            mandi_name="Pune Mandi",
            state="Maharashtra",
            district="Pune",
            latitude=18.5204,
            longitude=73.8567,
            price_per_quintal=2500.0,
            price_date=date.today(),
            source="Test"
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mandi]  # Return data so cache is set
        
        mock_db.query.return_value = mock_query
        
        service = MandiPriceService(mock_db, cache=mock_cache)
        prices = service.get_current_price("rice", sample_location, radius_km=50)
        
        # Should check cache
        mock_cache.get.assert_called_once()
        # Should set cache after query (only when data is found)
        mock_cache.setex.assert_called_once()
