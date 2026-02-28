"""
Unit tests for Language Processing Module

Tests translation between language pairs, language detection accuracy,
and transliteration edge cases.

Feature: bharatsahayak
Requirements: 1.3
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from app.services.language_processor import (
    LanguageProcessor,
    get_language_processor
)


class TestTranslationBetweenLanguagePairs:
    """Test translation functionality between different language pairs"""
    
    def test_translate_english_to_hindi(self):
        """Test translation from English to Hindi"""
        processor = LanguageProcessor()
        
        # Mock the translator
        with patch.object(processor, '_translator') as mock_translator:
            mock_result = Mock()
            mock_result.text = "नमस्ते"
            mock_translator.translate.return_value = mock_result
            
            result = processor.translate("Hello", "en", "hi")
            
            assert isinstance(result, str)
            assert len(result) > 0
            mock_translator.translate.assert_called_once()
    
    def test_translate_hindi_to_english(self):
        """Test translation from Hindi to English"""
        processor = LanguageProcessor()
        
        with patch.object(processor, '_translator') as mock_translator:
            mock_result = Mock()
            mock_result.text = "Hello"
            mock_translator.translate.return_value = mock_result
            
            result = processor.translate("नमस्ते", "hi", "en")
            
            assert isinstance(result, str)
            assert len(result) > 0
    
    def test_translate_between_indic_languages(self):
        """Test translation between two Indic languages"""
        processor = LanguageProcessor()
        
        with patch.object(processor, '_translator') as mock_translator:
            mock_result = Mock()
            mock_result.text = "নমস্কার"
            mock_translator.translate.return_value = mock_result
            
            result = processor.translate("नमस्ते", "hi", "bn")
            
            assert isinstance(result, str)
            assert len(result) > 0
    
    def test_translate_same_language_returns_original(self):
        """Test that translating to same language returns original text"""
        processor = LanguageProcessor()
        
        text = "Hello world"
        result = processor.translate(text, "en", "en")
        
        assert result == text
    
    def test_translate_unsupported_source_language_raises_error(self):
        """Test that unsupported source language raises ValueError"""
        processor = LanguageProcessor()
        
        with pytest.raises(ValueError, match="Source language .* not supported"):
            processor.translate("Hello", "xx", "en")
    
    def test_translate_unsupported_target_language_raises_error(self):
        """Test that unsupported target language raises ValueError"""
        processor = LanguageProcessor()
        
        with pytest.raises(ValueError, match="Target language .* not supported"):
            processor.translate("Hello", "en", "xx")
    
    def test_translate_without_translator_returns_original(self):
        """Test that translation without translator returns original text"""
        processor = LanguageProcessor()
        processor._translator = None
        
        text = "Hello world"
        result = processor.translate(text, "en", "hi")
        
        # Should return original text when translator not available
        assert result == text
    
    def test_translate_handles_translation_error(self):
        """Test that translation errors are handled gracefully"""
        processor = LanguageProcessor()
        
        with patch.object(processor, '_translator') as mock_translator:
            mock_translator.translate.side_effect = Exception("Translation API error")
            
            text = "Hello"
            result = processor.translate(text, "en", "hi")
            
            # Should return original text on error
            assert result == text
    
    def test_translate_empty_text(self):
        """Test translation of empty text"""
        processor = LanguageProcessor()
        
        with patch.object(processor, '_translator') as mock_translator:
            mock_result = Mock()
            mock_result.text = ""
            mock_translator.translate.return_value = mock_result
            
            result = processor.translate("", "en", "hi")
            
            assert result == ""
    
    def test_translate_long_text(self):
        """Test translation of long text"""
        processor = LanguageProcessor()
        
        long_text = "This is a very long text. " * 100
        
        with patch.object(processor, '_translator') as mock_translator:
            mock_result = Mock()
            mock_result.text = "Translated text"
            mock_translator.translate.return_value = mock_result
            
            result = processor.translate(long_text, "en", "hi")
            
            assert isinstance(result, str)
            assert len(result) > 0
    
    def test_translate_special_characters(self):
        """Test translation with special characters"""
        processor = LanguageProcessor()
        
        text = "Hello! How are you? @#$%"
        
        with patch.object(processor, '_translator') as mock_translator:
            mock_result = Mock()
            mock_result.text = "नमस्ते! आप कैसे हैं? @#$%"
            mock_translator.translate.return_value = mock_result
            
            result = processor.translate(text, "en", "hi")
            
            assert isinstance(result, str)
            assert len(result) > 0
    
    def test_translate_numbers_and_text(self):
        """Test translation with mixed numbers and text"""
        processor = LanguageProcessor()
        
        text = "I have 5 apples and 10 oranges"
        
        with patch.object(processor, '_translator') as mock_translator:
            mock_result = Mock()
            mock_result.text = "मेरे पास 5 सेब और 10 संतरे हैं"
            mock_translator.translate.return_value = mock_result
            
            result = processor.translate(text, "en", "hi")
            
            assert isinstance(result, str)
            assert len(result) > 0
    
    def test_translate_cached_uses_cache(self):
        """Test that translate_cached uses caching"""
        processor = LanguageProcessor()
        
        with patch.object(processor, '_translator') as mock_translator:
            mock_result = Mock()
            mock_result.text = "नमस्ते"
            mock_translator.translate.return_value = mock_result
            
            # First call
            result1 = processor.translate_cached("Hello", "en", "hi")
            # Second call with same parameters
            result2 = processor.translate_cached("Hello", "en", "hi")
            
            assert result1 == result2
            # Should only call translator once due to caching
            assert mock_translator.translate.call_count == 1


class TestLanguageDetectionAccuracy:
    """Test language detection functionality"""
    
    def test_detect_english_text(self):
        """Test detection of English text"""
        processor = LanguageProcessor()
        
        with patch.object(processor, '_detector') as mock_detector:
            mock_detector.return_value = "en"
            
            result = processor.detect_language("Hello, how are you?")
            
            assert result == "en"
    
    def test_detect_hindi_text(self):
        """Test detection of Hindi text"""
        processor = LanguageProcessor()
        
        with patch.object(processor, '_detector') as mock_detector:
            mock_detector.return_value = "hi"
            
            result = processor.detect_language("नमस्ते, आप कैसे हैं?")
            
            assert result == "hi"
    
    def test_detect_bengali_text(self):
        """Test detection of Bengali text"""
        processor = LanguageProcessor()
        
        with patch.object(processor, '_detector') as mock_detector:
            mock_detector.return_value = "bn"
            
            result = processor.detect_language("নমস্কার")
            
            assert result == "bn"
    
    def test_detect_tamil_text(self):
        """Test detection of Tamil text"""
        processor = LanguageProcessor()
        
        with patch.object(processor, '_detector') as mock_detector:
            mock_detector.return_value = "ta"
            
            result = processor.detect_language("வணக்கம்")
            
            assert result == "ta"
    
    def test_detect_empty_text_raises_error(self):
        """Test that empty text raises ValueError"""
        processor = LanguageProcessor()
        
        with pytest.raises(ValueError, match="Cannot detect language of empty text"):
            processor.detect_language("")
    
    def test_detect_whitespace_only_raises_error(self):
        """Test that whitespace-only text raises ValueError"""
        processor = LanguageProcessor()
        
        with pytest.raises(ValueError, match="Cannot detect language of empty text"):
            processor.detect_language("   ")
    
    def test_detect_unsupported_language_defaults_to_english(self):
        """Test that unsupported detected language defaults to English"""
        processor = LanguageProcessor()
        
        with patch.object(processor, '_detector') as mock_detector:
            mock_detector.return_value = "xx"  # Unsupported language
            
            result = processor.detect_language("Some text")
            
            assert result == "en"
    
    def test_detect_language_without_detector_uses_fallback(self):
        """Test language detection without detector uses fallback"""
        processor = LanguageProcessor()
        processor._detector = None
        
        # Test with Hindi text (Devanagari script)
        result = processor.detect_language("नमस्ते")
        assert result == "hi"
        
        # Test with English text
        result = processor.detect_language("Hello")
        assert result == "en"
    
    def test_detect_language_fallback_devanagari(self):
        """Test fallback detection for Devanagari script"""
        processor = LanguageProcessor()
        
        result = processor._detect_language_fallback("नमस्ते दुनिया")
        
        assert result == "hi"
    
    def test_detect_language_fallback_bengali(self):
        """Test fallback detection for Bengali script"""
        processor = LanguageProcessor()
        
        result = processor._detect_language_fallback("নমস্কার")
        
        assert result == "bn"
    
    def test_detect_language_fallback_telugu(self):
        """Test fallback detection for Telugu script"""
        processor = LanguageProcessor()
        
        result = processor._detect_language_fallback("నమస్కారం")
        
        assert result == "te"
    
    def test_detect_language_fallback_tamil(self):
        """Test fallback detection for Tamil script"""
        processor = LanguageProcessor()
        
        result = processor._detect_language_fallback("வணக்கம்")
        
        assert result == "ta"
    
    def test_detect_language_fallback_gujarati(self):
        """Test fallback detection for Gujarati script"""
        processor = LanguageProcessor()
        
        result = processor._detect_language_fallback("નમસ્તે")
        
        assert result == "gu"
    
    def test_detect_language_fallback_kannada(self):
        """Test fallback detection for Kannada script"""
        processor = LanguageProcessor()
        
        result = processor._detect_language_fallback("ನಮಸ್ಕಾರ")
        
        assert result == "kn"
    
    def test_detect_language_fallback_malayalam(self):
        """Test fallback detection for Malayalam script"""
        processor = LanguageProcessor()
        
        result = processor._detect_language_fallback("നമസ്കാരം")
        
        assert result == "ml"
    
    def test_detect_language_fallback_gurmukhi(self):
        """Test fallback detection for Gurmukhi script (Punjabi)"""
        processor = LanguageProcessor()
        
        result = processor._detect_language_fallback("ਸਤ ਸ੍ਰੀ ਅਕਾਲ")
        
        assert result == "pa"
    
    def test_detect_language_fallback_english(self):
        """Test fallback detection defaults to English for Latin script"""
        processor = LanguageProcessor()
        
        result = processor._detect_language_fallback("Hello world")
        
        assert result == "en"
    
    def test_detect_language_handles_detection_error(self):
        """Test that detection errors are handled gracefully"""
        processor = LanguageProcessor()
        
        with patch.object(processor, '_detector') as mock_detector:
            mock_detector.side_effect = Exception("Detection error")
            
            result = processor.detect_language("Some text")
            
            # Should default to English on error
            assert result == "en"
    
    def test_detect_mixed_script_text(self):
        """Test detection of text with mixed scripts"""
        processor = LanguageProcessor()
        
        with patch.object(processor, '_detector') as mock_detector:
            mock_detector.return_value = "hi"
            
            # Mixed Hindi and English
            result = processor.detect_language("Hello नमस्ते")
            
            assert result in processor.SUPPORTED_LANGUAGES


class TestTransliterationEdgeCases:
    """Test transliteration functionality with edge cases"""
    
    def test_romanize_simple_devanagari(self):
        """Test romanization of simple Devanagari text"""
        processor = LanguageProcessor()
        
        result = processor.romanize("नमस्ते", "devanagari")
        
        assert isinstance(result, str)
        assert len(result) > 0
        # Should contain romanized characters
        assert any(c.isalpha() for c in result)
    
    def test_romanize_devanagari_with_vowels(self):
        """Test romanization of Devanagari with various vowels"""
        processor = LanguageProcessor()
        
        # Text with different vowels
        text = "अआइईउऊ"
        result = processor.romanize(text, "devanagari")
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_romanize_devanagari_with_consonants(self):
        """Test romanization of Devanagari with consonants"""
        processor = LanguageProcessor()
        
        # Text with consonants
        text = "कखगघ"
        result = processor.romanize(text, "devanagari")
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_romanize_devanagari_with_matras(self):
        """Test romanization of Devanagari with matras (vowel signs)"""
        processor = LanguageProcessor()
        
        # Text with matras
        text = "काकिकीकुकू"
        result = processor.romanize(text, "devanagari")
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_romanize_devanagari_with_halant(self):
        """Test romanization of Devanagari with halant (virama)"""
        processor = LanguageProcessor()
        
        # Text with halant
        text = "क्त"
        result = processor.romanize(text, "devanagari")
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_romanize_empty_text(self):
        """Test romanization of empty text"""
        processor = LanguageProcessor()
        
        result = processor.romanize("", "devanagari")
        
        assert result == ""
    
    def test_romanize_text_with_spaces(self):
        """Test romanization preserves spaces"""
        processor = LanguageProcessor()
        
        text = "नमस्ते दुनिया"
        result = processor.romanize(text, "devanagari")
        
        assert " " in result
    
    def test_romanize_text_with_punctuation(self):
        """Test romanization preserves punctuation"""
        processor = LanguageProcessor()
        
        text = "नमस्ते!"
        result = processor.romanize(text, "devanagari")
        
        assert "!" in result
    
    def test_romanize_text_with_numbers(self):
        """Test romanization preserves numbers"""
        processor = LanguageProcessor()
        
        text = "नमस्ते 123"
        result = processor.romanize(text, "devanagari")
        
        assert "123" in result
    
    def test_romanize_mixed_devanagari_english(self):
        """Test romanization of mixed Devanagari and English"""
        processor = LanguageProcessor()
        
        text = "Hello नमस्ते"
        result = processor.romanize(text, "devanagari")
        
        assert "Hello" in result
        assert isinstance(result, str)
    
    def test_romanize_unsupported_script_raises_error(self):
        """Test that unsupported script raises ValueError"""
        processor = LanguageProcessor()
        
        with pytest.raises(ValueError, match="Source script .* not supported"):
            processor.romanize("नमस्ते", "arabic")
    
    def test_romanize_unknown_characters_preserved(self):
        """Test that unknown characters are preserved in romanization"""
        processor = LanguageProcessor()
        
        # Mix of Devanagari and special characters
        text = "नमस्ते@#$"
        result = processor.romanize(text, "devanagari")
        
        assert "@#$" in result
    
    def test_transliterate_same_script_returns_original(self):
        """Test that transliterating to same script returns original"""
        processor = LanguageProcessor()
        
        text = "नमस्ते"
        result = processor.transliterate(text, "devanagari", "devanagari")
        
        assert result == text
    
    def test_transliterate_devanagari_to_other_script(self):
        """Test transliteration from Devanagari to another script"""
        processor = LanguageProcessor()
        
        text = "नमस्ते"
        # Currently returns romanized version as fallback
        result = processor.transliterate(text, "devanagari", "bengali")
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_transliterate_unsupported_source_script_raises_error(self):
        """Test that unsupported source script raises ValueError"""
        processor = LanguageProcessor()
        
        with pytest.raises(ValueError, match="Transliteration from .* not supported"):
            processor.transliterate("Hello", "arabic", "devanagari")
    
    def test_transliterate_empty_text(self):
        """Test transliteration of empty text"""
        processor = LanguageProcessor()
        
        result = processor.transliterate("", "devanagari", "bengali")
        
        assert result == ""
    
    def test_romanize_long_text(self):
        """Test romanization of long text"""
        processor = LanguageProcessor()
        
        # Long Devanagari text
        text = "नमस्ते " * 100
        result = processor.romanize(text, "devanagari")
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_romanize_all_devanagari_vowels(self):
        """Test romanization of all Devanagari vowels"""
        processor = LanguageProcessor()
        
        vowels = "अआइईउऊऋएऐओऔ"
        result = processor.romanize(vowels, "devanagari")
        
        assert isinstance(result, str)
        assert len(result) > 0
        # All vowels should be romanized
        assert result != vowels
    
    def test_romanize_all_devanagari_consonants(self):
        """Test romanization of all Devanagari consonants"""
        processor = LanguageProcessor()
        
        consonants = "कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह"
        result = processor.romanize(consonants, "devanagari")
        
        assert isinstance(result, str)
        assert len(result) > 0
        # All consonants should be romanized
        assert result != consonants


class TestLanguageProcessorUtilities:
    """Test utility functions of Language Processor"""
    
    def test_get_supported_languages(self):
        """Test getting list of supported languages"""
        processor = LanguageProcessor()
        
        languages = processor.get_supported_languages()
        
        assert isinstance(languages, dict)
        assert len(languages) > 0
        assert "hi" in languages
        assert "en" in languages
        assert languages["hi"] == "Hindi"
        assert languages["en"] == "English"
    
    def test_supported_languages_includes_all_major_indic_languages(self):
        """Test that supported languages include major Indic languages"""
        processor = LanguageProcessor()
        
        languages = processor.get_supported_languages()
        
        # Check for major Indic languages
        expected_languages = ["hi", "bn", "te", "mr", "ta", "gu", "kn", "ml", "pa"]
        for lang in expected_languages:
            assert lang in languages
    
    def test_supported_languages_returns_copy(self):
        """Test that get_supported_languages returns a copy"""
        processor = LanguageProcessor()
        
        languages1 = processor.get_supported_languages()
        languages2 = processor.get_supported_languages()
        
        # Modify one copy
        languages1["test"] = "Test Language"
        
        # Other copy should not be affected
        assert "test" not in languages2
    
    def test_language_processor_singleton(self):
        """Test that get_language_processor returns singleton instance"""
        processor1 = get_language_processor()
        processor2 = get_language_processor()
        
        assert processor1 is processor2
    
    def test_language_processor_initialization(self):
        """Test Language Processor initialization"""
        processor = LanguageProcessor()
        
        assert processor is not None
        assert hasattr(processor, '_translator')
        assert hasattr(processor, '_detector')
    
    def test_language_processor_has_devanagari_mapping(self):
        """Test that Language Processor has Devanagari to Roman mapping"""
        processor = LanguageProcessor()
        
        assert hasattr(processor, 'DEVANAGARI_TO_ROMAN')
        assert isinstance(processor.DEVANAGARI_TO_ROMAN, dict)
        assert len(processor.DEVANAGARI_TO_ROMAN) > 0
        
        # Check some basic mappings
        assert 'अ' in processor.DEVANAGARI_TO_ROMAN
        assert 'क' in processor.DEVANAGARI_TO_ROMAN
    
    def test_language_processor_supported_languages_constant(self):
        """Test that SUPPORTED_LANGUAGES constant is properly defined"""
        assert hasattr(LanguageProcessor, 'SUPPORTED_LANGUAGES')
        assert isinstance(LanguageProcessor.SUPPORTED_LANGUAGES, dict)
        assert len(LanguageProcessor.SUPPORTED_LANGUAGES) >= 12


class TestLanguageProcessorErrorHandling:
    """Test error handling in Language Processor"""
    
    def test_translate_with_none_text(self):
        """Test translation with None text"""
        processor = LanguageProcessor()
        
        with patch.object(processor, '_translator') as mock_translator:
            mock_result = Mock()
            mock_result.text = ""
            mock_translator.translate.return_value = mock_result
            
            # Should handle None gracefully
            try:
                result = processor.translate(None, "en", "hi")
                assert result is not None
            except (TypeError, AttributeError):
                # Acceptable to raise error for None input
                pass
    
    def test_detect_language_with_none_text(self):
        """Test language detection with None text"""
        processor = LanguageProcessor()
        
        with pytest.raises((ValueError, TypeError, AttributeError)):
            processor.detect_language(None)
    
    def test_romanize_with_none_text(self):
        """Test romanization with None text"""
        processor = LanguageProcessor()
        
        try:
            result = processor.romanize(None, "devanagari")
            # If it doesn't raise error, should return empty or None
            assert result is None or result == ""
        except (TypeError, AttributeError):
            # Acceptable to raise error for None input
            pass
    
    def test_transliterate_with_none_text(self):
        """Test transliteration with None text"""
        processor = LanguageProcessor()
        
        try:
            result = processor.transliterate(None, "devanagari", "bengali")
            # If it doesn't raise error, should return empty or None
            assert result is None or result == ""
        except (TypeError, AttributeError, ValueError):
            # Acceptable to raise error for None input
            pass
