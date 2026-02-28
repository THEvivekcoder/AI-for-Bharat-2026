"""
Weather API Integration
Integrates with OpenWeatherMap and India Meteorological Department APIs
"""
import httpx
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from app.integrations.api_keys import api_keys

logger = logging.getLogger(__name__)


class WeatherAPI:
    """Client for weather APIs"""
    
    def __init__(self):
        self.openweather_base_url = "https://api.openweathermap.org/data/2.5"
        self.openweather_key = api_keys.openweather_key
        self.imd_key = api_keys.imd_key
        self.timeout = 30.0
        
    async def get_current_weather(
        self,
        latitude: float,
        longitude: float
    ) -> Optional[Dict[str, Any]]:
        """
        Get current weather for a location
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            
        Returns:
            Weather data dictionary or None
        """
        if not self.openweather_key:
            logger.warning("OpenWeather API key not configured")
            return None
        
        try:
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": self.openweather_key,
                "units": "metric"  # Celsius
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.openweather_base_url}/weather",
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Extract relevant information
                weather_info = {
                    "temperature": data["main"]["temp"],
                    "feels_like": data["main"]["feels_like"],
                    "humidity": data["main"]["humidity"],
                    "pressure": data["main"]["pressure"],
                    "description": data["weather"][0]["description"],
                    "wind_speed": data["wind"]["speed"],
                    "clouds": data["clouds"]["all"],
                    "timestamp": datetime.fromtimestamp(data["dt"])
                }
                
                if "rain" in data:
                    weather_info["rainfall_1h"] = data["rain"].get("1h", 0)
                    weather_info["rainfall_3h"] = data["rain"].get("3h", 0)
                
                logger.info(f"Fetched current weather for ({latitude}, {longitude})")
                return weather_info
                
        except httpx.HTTPError as e:
            logger.error(f"Error fetching current weather: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching weather: {e}")
            return None
    
    async def get_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Get weather forecast for a location
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            days: Number of days to forecast (max 5 for free tier)
            
        Returns:
            Forecast data dictionary or None
        """
        if not self.openweather_key:
            logger.warning("OpenWeather API key not configured")
            return None
        
        try:
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": self.openweather_key,
                "units": "metric",
                "cnt": days * 8  # 8 forecasts per day (3-hour intervals)
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.openweather_base_url}/forecast",
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Process forecast data
                forecasts = []
                for item in data["list"]:
                    forecast = {
                        "datetime": datetime.fromtimestamp(item["dt"]),
                        "temperature": item["main"]["temp"],
                        "humidity": item["main"]["humidity"],
                        "description": item["weather"][0]["description"],
                        "wind_speed": item["wind"]["speed"],
                        "clouds": item["clouds"]["all"]
                    }
                    
                    if "rain" in item:
                        forecast["rainfall_3h"] = item["rain"].get("3h", 0)
                    
                    forecasts.append(forecast)
                
                logger.info(f"Fetched {len(forecasts)} forecast entries for ({latitude}, {longitude})")
                return {
                    "location": {
                        "latitude": latitude,
                        "longitude": longitude,
                        "city": data["city"]["name"]
                    },
                    "forecasts": forecasts
                }
                
        except httpx.HTTPError as e:
            logger.error(f"Error fetching weather forecast: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching forecast: {e}")
            return None
    
    async def get_agricultural_weather(
        self,
        latitude: float,
        longitude: float
    ) -> Optional[Dict[str, Any]]:
        """
        Get weather information relevant for agriculture
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            
        Returns:
            Agricultural weather data or None
        """
        current = await self.get_current_weather(latitude, longitude)
        forecast = await self.get_forecast(latitude, longitude, days=7)
        
        if not current or not forecast:
            return None
        
        # Calculate agricultural metrics
        forecasts = forecast["forecasts"]
        
        # Rainfall prediction
        total_rainfall = sum(f.get("rainfall_3h", 0) for f in forecasts)
        rainy_days = len([f for f in forecasts if f.get("rainfall_3h", 0) > 0])
        
        # Temperature analysis
        avg_temp = sum(f["temperature"] for f in forecasts) / len(forecasts)
        max_temp = max(f["temperature"] for f in forecasts)
        min_temp = min(f["temperature"] for f in forecasts)
        
        # Humidity analysis
        avg_humidity = sum(f["humidity"] for f in forecasts) / len(forecasts)
        
        return {
            "current": current,
            "forecast_summary": {
                "days": 7,
                "total_rainfall_mm": round(total_rainfall, 2),
                "rainy_days": rainy_days,
                "avg_temperature": round(avg_temp, 1),
                "max_temperature": round(max_temp, 1),
                "min_temperature": round(min_temp, 1),
                "avg_humidity": round(avg_humidity, 1)
            },
            "agricultural_advice": self._generate_agricultural_advice(
                total_rainfall, avg_temp, avg_humidity
            )
        }
    
    def _generate_agricultural_advice(
        self,
        rainfall: float,
        temperature: float,
        humidity: float
    ) -> str:
        """Generate basic agricultural advice based on weather"""
        advice = []
        
        if rainfall > 50:
            advice.append("Heavy rainfall expected. Ensure proper drainage.")
        elif rainfall < 10:
            advice.append("Low rainfall expected. Plan for irrigation.")
        
        if temperature > 35:
            advice.append("High temperatures expected. Provide shade for sensitive crops.")
        elif temperature < 15:
            advice.append("Cool temperatures expected. Protect frost-sensitive crops.")
        
        if humidity > 80:
            advice.append("High humidity may increase disease risk. Monitor crops closely.")
        elif humidity < 40:
            advice.append("Low humidity. Increase irrigation frequency.")
        
        return " ".join(advice) if advice else "Weather conditions are favorable for farming."


# Singleton instance
weather_api = WeatherAPI()
