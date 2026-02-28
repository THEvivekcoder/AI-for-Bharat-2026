"""
API Key Management
Centralized management of API keys for external services
"""
import os
from typing import Optional
from pydantic import BaseModel


class APIKeys(BaseModel):
    """API keys configuration"""
    # Government scheme APIs
    data_gov_in_key: Optional[str] = None
    
    # Mandi price APIs
    agmarknet_key: Optional[str] = None
    
    # Weather APIs
    openweather_key: Optional[str] = None
    imd_key: Optional[str] = None  # India Meteorological Department
    
    # SMS/OTP service
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    
    # Translation APIs (if using cloud services)
    bhashini_key: Optional[str] = None
    google_translate_key: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "APIKeys":
        """Load API keys from environment variables"""
        return cls(
            data_gov_in_key=os.getenv("DATA_GOV_IN_API_KEY"),
            agmarknet_key=os.getenv("AGMARKNET_API_KEY"),
            openweather_key=os.getenv("OPENWEATHER_API_KEY"),
            imd_key=os.getenv("IMD_API_KEY"),
            twilio_account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
            twilio_auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
            twilio_phone_number=os.getenv("TWILIO_PHONE_NUMBER"),
            bhashini_key=os.getenv("BHASHINI_API_KEY"),
            google_translate_key=os.getenv("GOOGLE_TRANSLATE_API_KEY")
        )


# Global API keys instance
api_keys = APIKeys.from_env()
