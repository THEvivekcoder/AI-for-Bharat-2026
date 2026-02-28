# Language Processing Module Implementation

## Overview

The Language Processing Module provides multilingual support for BharatSahayak, enabling translation, language detection, romanization, and transliteration for Indian languages.

## Implementation Status

✅ **Task 12.1**: Set up translation and NLP models
- Integrated googletrans for translation
- Integrated langdetect for language detection
- Implemented fallback detection using Unicode ranges
- Created LanguageProcessor service class

✅ **Task 12.2**: Implement Language Processor
- `translate()` - Translate between supported languages
- `romanize()` - Convert Devanagari to Roman script
- `transliterate()` - Convert between Indic scripts (basic implementation)
- `detect_language()` - Detect language from text
- `get_supported_languages()` - List supported languages

✅ **Task 12.3**: Create Language Processing endpoints
- POST /api/translate - Translate text
- POST /api/detect-language - Detect language
- POST /api/transliterate - Convert between scripts
- POST /api/romanize - Convert to Roman script
- GET /api/languages - List supported languages

## Supported Languages

The module supports 12 Indian languages:

| Code | Language   | Script      |
|------|-----------|-------------|
| hi   | Hindi     | Devanagari  |
| en   | English   | Latin       |
| bn   | Bengali   | Bengali     |
| te   | Telugu    | Telugu      |
| mr   | Marathi   | Devanagari  |
| ta   | Tamil     | Tamil       |
| gu   | Gujarati  | Gujarati    |
| kn   | Kannada   | Kannada     |
| ml   | Malayalam | Malayalam   |
| pa   | Punjabi   | Gurmukhi    |
| or   | Odia      | Odia        |
| as   | Assamese  | Bengali     |

## Architecture

### Components

1. **LanguageProcessor Service** (`app/services/language_processor.py`)
   - Core service handling all language processing operations
   - Uses googletrans for translation
   - Uses langdetect for language detection
   - Implements custom romanization for Devanagari

2. **Language API** (`app/api/language.py`)
   - REST API endpoints for language operations
   - Request/response validation using Pydantic
   - Error handling and logging

3. **Schemas** (`app/schemas/language.py`)
   - Pydantic models for API requests and responses
   - Input validation and documentation

### Dependencies

```
googletrans==4.0.0rc1  # Translation service
langdetect==1.0.9      # Language detection
```

## API Endpoints

### 1. Translate Text

**Endpoint**: `POST /api/translate`

**Request**:
```json
{
  "text": "Hello",
  "source_lang": "en",
  "target_lang": "hi"
}
```

**Response**:
```json
{
  "translated_text": "नमस्ते",
  "source_lang": "en",
  "target_lang": "hi",
  "original_text": "Hello"
}
```

### 2. Detect Language

**Endpoint**: `POST /api/detect-language`

**Request**:
```json
{
  "text": "नमस्ते, आप कैसे हैं?"
}
```

**Response**:
```json
{
  "detected_language": "hi",
  "language_name": "Hindi",
  "confidence": null
}
```

### 3. Romanize Text

**Endpoint**: `POST /api/romanize`

**Request**:
```json
{
  "text": "नमस्ते",
  "source_script": "devanagari"
}
```

**Response**:
```json
{
  "romanized_text": "namasatae",
  "source_script": "devanagari",
  "original_text": "नमस्ते"
}
```

### 4. Transliterate Text

**Endpoint**: `POST /api/transliterate`

**Request**:
```json
{
  "text": "नमस्ते",
  "source_script": "devanagari",
  "target_script": "roman"
}
```

**Response**:
```json
{
  "transliterated_text": "namasatae",
  "source_script": "devanagari",
  "target_script": "roman",
  "original_text": "नमस्ते"
}
```

### 5. Get Supported Languages

**Endpoint**: `GET /api/languages`

**Response**:
```json
{
  "languages": {
    "hi": "Hindi",
    "en": "English",
    "bn": "Bengali",
    ...
  },
  "count": 12
}
```

## Testing

### Unit Tests

Run the service-level tests:
```bash
python scripts/test_language_service.py
```

### API Tests

Start the server:
```bash
python -m uvicorn app.main:app --reload
```

Run the endpoint tests:
```bash
python scripts/test_language_endpoints.py
```

### Test Coverage

- ✅ Language detection for English and Hindi
- ✅ Translation between English and Hindi
- ✅ Romanization of Devanagari script
- ✅ Transliteration (basic implementation)
- ✅ Supported languages listing
- ✅ Error handling for invalid inputs

## Usage Examples

### Python Service Usage

```python
from app.services.language_processor import get_language_processor

processor = get_language_processor()

# Detect language
lang = processor.detect_language("नमस्ते")
print(lang)  # 'hi'

# Translate
translated = processor.translate("Hello", "en", "hi")
print(translated)  # 'नमस्ते'

# Romanize
romanized = processor.romanize("नमस्ते", "devanagari")
print(romanized)  # 'namasatae'
```

### API Usage (curl)

```bash
# Detect language
curl -X POST http://localhost:8000/api/detect-language \
  -H "Content-Type: application/json" \
  -d '{"text": "नमस्ते"}'

# Translate
curl -X POST http://localhost:8000/api/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello", "source_lang": "en", "target_lang": "hi"}'

# Get supported languages
curl http://localhost:8000/api/languages
```

## Implementation Notes

### Translation

- Uses Google Translate API via googletrans library
- Supports all 12 configured Indian languages
- Falls back to original text if translation fails
- Caching available via `translate_cached()` method

### Language Detection

- Primary: Uses langdetect library for accurate detection
- Fallback: Unicode range-based heuristics for Indic scripts
- Defaults to English if detection fails or language unsupported

### Romanization

- Currently supports Devanagari to Roman script
- Uses character-by-character mapping
- Simplified implementation suitable for basic use cases
- For production, consider using specialized libraries

### Transliteration

- Basic implementation through romanization
- Currently limited to Devanagari source script
- For production, integrate libraries like:
  - indic-transliteration
  - Aksharamukha
  - IndicNLP

## Future Enhancements

1. **Advanced Transliteration**
   - Integrate IndicTrans2 for better quality
   - Support all Indic script pairs
   - Context-aware transliteration

2. **Bhashini Integration**
   - Use government Bhashini API for official support
   - Better quality for Indian languages
   - Offline model support

3. **Caching**
   - Redis-based translation cache
   - Reduce API calls for common phrases
   - Improve response times

4. **Batch Operations**
   - Translate multiple texts in one request
   - Bulk language detection
   - Improved efficiency

5. **Quality Improvements**
   - Confidence scores for detection
   - Alternative translations
   - Context-aware translation

## Error Handling

The module handles various error scenarios:

- **Unsupported Language**: Returns 400 with list of supported languages
- **Empty Text**: Returns 422 validation error
- **Translation Failure**: Falls back to original text with warning
- **Detection Failure**: Defaults to English with warning
- **Service Unavailable**: Returns 500 with appropriate message

## Performance Considerations

- Language detection: ~10-50ms
- Translation: ~200-500ms (depends on Google Translate API)
- Romanization: ~1-5ms (local operation)
- Caching recommended for frequently translated phrases

## Requirements Validation

✅ **Requirement 1.3**: Language detection and multilingual support
- Supports 12 Indian languages
- Automatic language detection
- Translation between language pairs
- Script conversion capabilities

## Related Documentation

- [Voice Interface Implementation](voice_interface_implementation.md)
- [RAG Implementation](rag_implementation.md)
- [API Documentation](../README.md)
