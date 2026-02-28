"""Error message translation service"""
from typing import Dict, Optional


class ErrorTranslator:
    """Translates error messages to supported languages"""
    
    # Error message translations
    TRANSLATIONS: Dict[str, Dict[str, str]] = {
        # Voice Processing Errors
        "VOICE_PROCESSING_ERROR": {
            "en": "Unable to process audio. Please try speaking clearly in a supported language.",
            "hi": "ऑडियो प्रोसेस नहीं हो सका। कृपया समर्थित भाषा में स्पष्ट रूप से बोलें।",
            "bn": "অডিও প্রক্রিয়া করা যায়নি। অনুগ্রহ করে সমর্থিত ভাষায় স্পষ্টভাবে বলুন।",
            "te": "ఆడియో ప్రాసెస్ చేయడం సాధ్యం కాలేదు. దయచేసి మద్దతు ఉన్న భాషలో స్పష్టంగా మాట్లాడండి.",
            "mr": "ऑडिओ प्रक्रिया करू शकलो नाही. कृपया समर्थित भाषेत स्पष्टपणे बोला.",
        },
        
        # Data Not Found Errors
        "DATA_NOT_FOUND": {
            "en": "The requested information is not available.",
            "hi": "अनुरोधित जानकारी उपलब्ध नहीं है।",
            "bn": "অনুরোধকৃত তথ্য উপলব্ধ নয়।",
            "te": "అభ్యర్థించిన సమాచారం అందుబాటులో లేదు.",
            "mr": "विनंती केलेली माहिती उपलब्ध नाही.",
        },
        
        "SCHEME_NOT_FOUND": {
            "en": "No schemes found matching your criteria.",
            "hi": "आपके मानदंडों से मेल खाने वाली कोई योजना नहीं मिली।",
            "bn": "আপনার মানদণ্ডের সাথে মিলে এমন কোনো প্রকল্প পাওয়া যায়নি।",
            "te": "మీ ప్రమాణాలకు సరిపోయే పథకాలు కనుగొనబడలేదు.",
            "mr": "तुमच्या निकषांशी जुळणारी कोणतीही योजना आढळली नाही.",
        },
        
        "MARKET_PRICE_UNAVAILABLE": {
            "en": "Market prices are not available for this crop and location.",
            "hi": "इस फसल और स्थान के लिए बाजार मूल्य उपलब्ध नहीं हैं।",
            "bn": "এই ফসল এবং অবস্থানের জন্য বাজার মূল্য উপলব্ধ নয়।",
            "te": "ఈ పంట మరియు స్థానం కోసం మార్కెట్ ధరలు అందుబాటులో లేవు.",
            "mr": "या पिकासाठी आणि स्थानासाठी बाजार किंमती उपलब्ध नाहीत.",
        },
        
        # Profile Data Errors
        "INSUFFICIENT_PROFILE_DATA": {
            "en": "Cannot complete this request. Please provide required information.",
            "hi": "यह अनुरोध पूरा नहीं किया जा सकता। कृपया आवश्यक जानकारी प्रदान करें।",
            "bn": "এই অনুরোধ সম্পূর্ণ করা যাচ্ছে না। অনুগ্রহ করে প্রয়োজনীয় তথ্য প্রদান করুন।",
            "te": "ఈ అభ్యర్థనను పూర్తి చేయలేము. దయచేసి అవసరమైన సమాచారాన్ని అందించండి.",
            "mr": "ही विनंती पूर्ण करू शकत नाही. कृपया आवश्यक माहिती प्रदान करा.",
        },
        
        # Authentication Errors
        "AUTHENTICATION_FAILED": {
            "en": "Authentication failed. Please try again.",
            "hi": "प्रमाणीकरण विफल रहा। कृपया पुनः प्रयास करें।",
            "bn": "প্রমাণীকরণ ব্যর্থ হয়েছে। অনুগ্রহ করে আবার চেষ্টা করুন।",
            "te": "ప్రామాణీకరణ విఫలమైంది. దయచేసి మళ్లీ ప్రయత్నించండి.",
            "mr": "प्रमाणीकरण अयशस्वी झाले. कृपया पुन्हा प्रयत्न करा.",
        },
        
        "INVALID_OTP": {
            "en": "Invalid OTP. Please check and try again.",
            "hi": "अमान्य OTP। कृपया जांचें और पुनः प्रयास करें।",
            "bn": "অবৈধ OTP। অনুগ্রহ করে পরীক্ষা করুন এবং আবার চেষ্টা করুন।",
            "te": "చెల్లని OTP. దయచేసి తనిఖీ చేసి మళ్లీ ప్రయత్నించండి.",
            "mr": "अवैध OTP. कृपया तपासा आणि पुन्हा प्रयत्न करा.",
        },
        
        # Rate Limiting Errors
        "RATE_LIMIT_EXCEEDED": {
            "en": "Too many requests. Please try again later.",
            "hi": "बहुत अधिक अनुरोध। कृपया बाद में पुनः प्रयास करें।",
            "bn": "অনেক বেশি অনুরোধ। অনুগ্রহ করে পরে আবার চেষ্টা করুন।",
            "te": "చాలా ఎక్కువ అభ్యర్థనలు. దయచేసి తర్వాత మళ్లీ ప్రయత్నించండి.",
            "mr": "खूप जास्त विनंत्या. कृपया नंतर पुन्हा प्रयत्न करा.",
        },
        
        # Offline Errors
        "OFFLINE_FEATURE_UNAVAILABLE": {
            "en": "This feature requires internet connection. Please connect and try again.",
            "hi": "इस सुविधा के लिए इंटरनेट कनेक्शन की आवश्यकता है। कृपया कनेक्ट करें और पुनः प्रयास करें।",
            "bn": "এই বৈশিষ্ট্যের জন্য ইন্টারনেট সংযোগ প্রয়োজন। অনুগ্রহ করে সংযুক্ত করুন এবং আবার চেষ্টা করুন।",
            "te": "ఈ ఫీచర్‌కు ఇంటర్నెట్ కనెక్షన్ అవసరం. దయచేసి కనెక్ట్ చేసి మళ్లీ ప్రయత్నించండి.",
            "mr": "या वैशिष्ट्यासाठी इंटरनेट कनेक्शन आवश्यक आहे. कृपया कनेक्ट करा आणि पुन्हा प्रयत्न करा.",
        },
        
        # External Service Errors
        "EXTERNAL_SERVICE_ERROR": {
            "en": "External service is temporarily unavailable. Please try again later.",
            "hi": "बाहरी सेवा अस्थायी रूप से अनुपलब्ध है। कृपया बाद में पुनः प्रयास करें।",
            "bn": "বাহ্যিক পরিষেবা সাময়িকভাবে অনুপলব্ধ। অনুগ্রহ করে পরে আবার চেষ্টা করুন।",
            "te": "బాహ్య సేవ తాత్కాలికంగా అందుబాటులో లేదు. దయచేసి తర్వాత మళ్లీ ప్రయత్నించండి.",
            "mr": "बाह्य सेवा तात्पुरती अनुपलब्ध आहे. कृपया नंतर पुन्हा प्रयत्न करा.",
        },
        
        # Validation Errors
        "VALIDATION_ERROR": {
            "en": "Invalid request data. Please check your input.",
            "hi": "अमान्य अनुरोध डेटा। कृपया अपना इनपुट जांचें।",
            "bn": "অবৈধ অনুরোধ ডেটা। অনুগ্রহ করে আপনার ইনপুট পরীক্ষা করুন।",
            "te": "చెల్లని అభ్యర్థన డేటా. దయచేసి మీ ఇన్‌పుట్‌ను తనిఖీ చేయండి.",
            "mr": "अवैध विनंती डेटा. कृपया तुमचे इनपुट तपासा.",
        },
        
        # Database Errors
        "DATABASE_ERROR": {
            "en": "Database error occurred. Please try again.",
            "hi": "डेटाबेस त्रुटि हुई। कृपया पुनः प्रयास करें।",
            "bn": "ডাটাবেস ত্রুটি ঘটেছে। অনুগ্রহ করে আবার চেষ্টা করুন।",
            "te": "డేటాబేస్ లోపం సంభవించింది. దయచేసి మళ్లీ ప్రయత్నించండి.",
            "mr": "डेटाबेस त्रुटी आली. कृपया पुन्हा प्रयत्न करा.",
        },
        
        # Generic Errors
        "INTERNAL_SERVER_ERROR": {
            "en": "An unexpected error occurred. Please try again later.",
            "hi": "एक अप्रत्याशित त्रुटि हुई। कृपया बाद में पुनः प्रयास करें।",
            "bn": "একটি অপ্রত্যাশিত ত্রুটি ঘটেছে। অনুগ্রহ করে পরে আবার চেষ্টা করুন।",
            "te": "ఊహించని లోపం సంభవించింది. దయచేసి తర్వాత మళ్లీ ప్రయత్నించండి.",
            "mr": "एक अनपेक्षित त्रुटी आली. कृपया नंतर पुन्हा प्रयत्न करा.",
        },
    }
    
    # Supported languages
    SUPPORTED_LANGUAGES = ["en", "hi", "bn", "te", "mr"]
    
    @classmethod
    def translate(cls, error_code: str, language: str = "en") -> str:
        """
        Translate error message to specified language
        
        Args:
            error_code: Error code identifier
            language: Target language code (default: en)
            
        Returns:
            Translated error message
        """
        # Default to English if language not supported
        if language not in cls.SUPPORTED_LANGUAGES:
            language = "en"
        
        # Get translations for error code
        translations = cls.TRANSLATIONS.get(error_code, {})
        
        # Return translated message or fallback to English
        return translations.get(language, translations.get("en", "An error occurred"))
    
    @classmethod
    def get_all_translations(cls, error_code: str) -> Dict[str, str]:
        """
        Get all translations for an error code
        
        Args:
            error_code: Error code identifier
            
        Returns:
            Dictionary of language code to translated message
        """
        return cls.TRANSLATIONS.get(error_code, {})
    
    @classmethod
    def add_translation(cls, error_code: str, language: str, message: str) -> None:
        """
        Add a new translation for an error code
        
        Args:
            error_code: Error code identifier
            language: Language code
            message: Translated message
        """
        if error_code not in cls.TRANSLATIONS:
            cls.TRANSLATIONS[error_code] = {}
        
        cls.TRANSLATIONS[error_code][language] = message
