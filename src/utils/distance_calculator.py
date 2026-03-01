"""Utility for calculating distances between locations."""

import math
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class DistanceCalculator:
    """Calculate distances between geographic coordinates."""
    
    # Earth radius in kilometers
    EARTH_RADIUS_KM = 6371.0
    
    # Approximate coordinates for Indian districts (simplified mapping)
    # In production, this would be a comprehensive database
    DISTRICT_COORDINATES = {
        'Maharashtra': {
            'Pune': (18.5204, 73.8567),
            'Mumbai': (19.0760, 72.8777),
            'Nagpur': (21.1458, 79.0882),
            'Nashik': (19.9975, 73.7898),
            'Aurangabad': (19.8762, 75.3433),
            'Solapur': (17.6599, 75.9064),
            'Kolhapur': (16.7050, 74.2433),
        },
        'Karnataka': {
            'Bangalore': (12.9716, 77.5946),
            'Mysore': (12.2958, 76.6394),
            'Hubli': (15.3647, 75.1240),
            'Mangalore': (12.9141, 74.8560),
            'Belgaum': (15.8497, 74.4977),
        },
        'Gujarat': {
            'Ahmedabad': (23.0225, 72.5714),
            'Surat': (21.1702, 72.8311),
            'Vadodara': (22.3072, 73.1812),
            'Rajkot': (22.3039, 70.8022),
        },
        'Tamil Nadu': {
            'Chennai': (13.0827, 80.2707),
            'Coimbatore': (11.0168, 76.9558),
            'Madurai': (9.9252, 78.1198),
            'Tiruchirappalli': (10.7905, 78.7047),
        },
        'Rajasthan': {
            'Jaipur': (26.9124, 75.7873),
            'Jodhpur': (26.2389, 73.0243),
            'Udaipur': (24.5854, 73.7125),
            'Kota': (25.2138, 75.8648),
        },
        'Uttar Pradesh': {
            'Lucknow': (26.8467, 80.9462),
            'Kanpur': (26.4499, 80.3319),
            'Agra': (27.1767, 78.0081),
            'Varanasi': (25.3176, 82.9739),
        },
        'Madhya Pradesh': {
            'Bhopal': (23.2599, 77.4126),
            'Indore': (22.7196, 75.8577),
            'Jabalpur': (23.1815, 79.9864),
            'Gwalior': (26.2183, 78.1828),
        },
        'West Bengal': {
            'Kolkata': (22.5726, 88.3639),
            'Howrah': (22.5958, 88.2636),
            'Durgapur': (23.5204, 87.3119),
        },
        'Punjab': {
            'Ludhiana': (30.9010, 75.8573),
            'Amritsar': (31.6340, 74.8723),
            'Jalandhar': (31.3260, 75.5762),
        },
        'Haryana': {
            'Gurgaon': (28.4595, 77.0266),
            'Faridabad': (28.4089, 77.3178),
            'Panipat': (29.3909, 76.9635),
        },
    }
    
    @classmethod
    def haversine_distance(
        cls,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calculate distance between two points using Haversine formula.
        
        Args:
            lat1: Latitude of first point
            lon1: Longitude of first point
            lat2: Latitude of second point
            lon2: Longitude of second point
            
        Returns:
            Distance in kilometers
        """
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
        
        c = 2 * math.asin(math.sqrt(a))
        
        # Distance in kilometers
        distance = cls.EARTH_RADIUS_KM * c
        
        return distance
    
    @classmethod
    def get_coordinates(cls, state: str, district: str) -> Optional[Tuple[float, float]]:
        """
        Get coordinates for a district.
        
        Args:
            state: State name
            district: District name
            
        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        state_data = cls.DISTRICT_COORDINATES.get(state, {})
        return state_data.get(district)
    
    @classmethod
    def calculate_distance(
        cls,
        state1: str,
        district1: str,
        state2: str,
        district2: str
    ) -> Optional[float]:
        """
        Calculate distance between two districts.
        
        Args:
            state1: First state
            district1: First district
            state2: Second state
            district2: Second district
            
        Returns:
            Distance in kilometers or None if coordinates not found
        """
        # Get coordinates
        coords1 = cls.get_coordinates(state1, district1)
        coords2 = cls.get_coordinates(state2, district2)
        
        if not coords1 or not coords2:
            logger.warning(
                f"Coordinates not found for {district1}, {state1} or {district2}, {state2}"
            )
            return None
        
        # Calculate distance
        lat1, lon1 = coords1
        lat2, lon2 = coords2
        
        distance = cls.haversine_distance(lat1, lon1, lat2, lon2)
        
        return distance
    
    @classmethod
    def is_within_radius(
        cls,
        state1: str,
        district1: str,
        state2: str,
        district2: str,
        radius_km: float
    ) -> bool:
        """
        Check if two districts are within a specified radius.
        
        Args:
            state1: First state
            district1: First district
            state2: Second state
            district2: Second district
            radius_km: Radius in kilometers
            
        Returns:
            True if within radius, False otherwise
        """
        # Same district is always within radius
        if state1 == state2 and district1 == district2:
            return True
        
        # Calculate distance
        distance = cls.calculate_distance(state1, district1, state2, district2)
        
        if distance is None:
            # If coordinates not found, assume within radius for same state
            return state1 == state2
        
        return distance <= radius_km
