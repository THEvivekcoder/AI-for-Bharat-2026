# Voice Interface Services

This directory contains AWS-based voice interface services for BharatSahayak, enabling voice-first interaction for rural users.

## Services

### 1. TranscribeService (`transcribe_service.py`)

Converts speech to text using Amazon Transcribe.

**Features:**
- Supports 10 Indian languages (Hindi, English, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi)
- Automatic language detection
- Handles audio in multiple formats (WAV, MP3, MP4, FLAC)
- Returns transcription with confidence scores

**Usage:**
```python
from src.services.transcribe_service import TranscribeService

service = TranscribeService(s3_bucket='my-bucket')

# With specific language
result = service.transcribe_audio(
    audio_data=audio_bytes,
    language_code='hi-IN',
    audio_format='wav'
)

# With auto-detection
result = service.transcribe_audio(
    audio_data=audio_bytes,
    language_code=None,  # Auto-detect
    audio_format='mp3'
)

print(result['text'])
print(result['confidence'])
print(result['detected_language'])
```

**Supported Languages:**
- `hi-IN`: Hindi
- `en-IN`: English (India)
- `ta-IN`: Tamil
- `te-IN`: Telugu
- `bn-IN`: Bengali
- `mr-IN`: Marathi
- `gu-IN`: Gujarati
- `kn-IN`: Kannada
- `ml-IN`: Malayalam
- `pa-IN`: Punjabi

### 2. PollyService (`polly_service.py`)

Converts text to natural-sounding speech using Amazon Polly.

**Features:**
- Neural TTS voices for Hindi and English
- Fallback voices for other Indian languages
- Multiple output formats (MP3, OGG, PCM)
- Automatic S3 storage with presigned URLs
- Duration estimation

**Usage:**
```python
from src.services.polly_service import PollyService

service = PollyService(s3_bucket='my-bucket')

result = service.synthesize_speech(
    text='नमस्ते, आप कैसे हैं?',
    language_code='hi-IN',
    output_format='mp3'
)

print(result['audio_url'])  # Presigned S3 URL
print(result['voice_id'])   # 'Aditi' for Hindi
print(result['duration_seconds'])
```

**Voice Profiles:**
- Hindi (`hi-IN`): Aditi (Neural)
- English (`en-IN`): Kajal (Neural)
- Other languages: Fallback to Hindi or English voices

### 3. ComprehendService (`comprehend_service.py`)

Detects language from text using Amazon Comprehend.

**Features:**
- Automatic language detection
- Batch processing (up to 25 texts)
- Confidence scores for all detected languages
- Handles long text (auto-truncates to 5000 chars)

**Usage:**
```python
from src.services.comprehend_service import ComprehendService

service = ComprehendService()

# Single text
result = service.detect_language('नमस्ते')
print(result['language_code'])  # 'hi-IN'
print(result['confidence'])     # 0.98

# Batch processing
results = service.detect_language_batch([
    'नमस्ते',
    'Hello',
    'வணக்கம்'
])
for result in results:
    print(result['language_code'], result['confidence'])
```

## API Endpoints

### POST /voice/transcribe

Transcribe audio to text.

**Request:**
```json
{
  "audio_data": "base64-encoded-audio",
  "language_code": "hi-IN",  // Optional, auto-detect if omitted
  "audio_format": "wav"       // Optional, default: wav
}
```

**Response:**
```json
{
  "text": "नमस्ते, आप कैसे हैं?",
  "confidence": 0.95,
  "detected_language": "hi-IN",
  "timestamp": "2026-03-02T10:30:00Z"
}
```

### POST /voice/synthesize

Convert text to speech.

**Request:**
```json
{
  "text": "नमस्ते, आप कैसे हैं?",
  "language_code": "hi-IN",    // Optional, default: hi-IN
  "output_format": "mp3"       // Optional, default: mp3
}
```

**Response:**
```json
{
  "audio_url": "https://s3.amazonaws.com/...",
  "audio_format": "mp3",
  "language": "hi-IN",
  "voice_id": "Aditi",
  "timestamp": "2026-03-02T10:30:00Z",
  "audio_duration_seconds": 3.5
}
```

### POST /voice/detect-language

Detect language from text.

**Request (Single):**
```json
{
  "text": "नमस्ते"
}
```

**Request (Batch):**
```json
{
  "texts": ["नमस्ते", "Hello", "வணக்கம்"]
}
```

**Response (Single):**
```json
{
  "language_code": "hi-IN",
  "confidence": 0.98,
  "all_languages": [
    {"language_code": "hi-IN", "confidence": 0.98},
    {"language_code": "en-IN", "confidence": 0.02}
  ]
}
```

**Response (Batch):**
```json
{
  "results": [
    {"language_code": "hi-IN", "confidence": 0.98, "all_languages": [...]},
    {"language_code": "en-IN", "confidence": 0.95, "all_languages": [...]},
    {"language_code": "ta-IN", "confidence": 0.92, "all_languages": [...]}
  ]
}
```

## Configuration

### Environment Variables

- `S3_BUCKET_NAME`: S3 bucket for storing audio files (required for transcribe and polly)
- `AWS_REGION`: AWS region (default: ap-south-1)

### IAM Permissions

The Lambda functions require the following IAM permissions:

**Transcribe:**
```json
{
  "Effect": "Allow",
  "Action": [
    "transcribe:StartTranscriptionJob",
    "transcribe:GetTranscriptionJob",
    "transcribe:DeleteTranscriptionJob",
    "s3:PutObject",
    "s3:GetObject",
    "s3:DeleteObject"
  ],
  "Resource": "*"
}
```

**Polly:**
```json
{
  "Effect": "Allow",
  "Action": [
    "polly:SynthesizeSpeech",
    "s3:PutObject",
    "s3:GetObject"
  ],
  "Resource": "*"
}
```

**Comprehend:**
```json
{
  "Effect": "Allow",
  "Action": [
    "comprehend:DetectDominantLanguage",
    "comprehend:BatchDetectDominantLanguage"
  ],
  "Resource": "*"
}
```

## Testing

Run unit tests:
```bash
pytest tests/unit/test_transcribe_service.py -v
pytest tests/unit/test_polly_service.py -v
pytest tests/unit/test_comprehend_service.py -v
```

## Limitations

### Amazon Transcribe
- Maximum audio file size: 2 GB
- Maximum audio duration: 4 hours
- Supported formats: WAV, MP3, MP4, FLAC, OGG, AMR, WebM

### Amazon Polly
- Maximum text length: 3000 characters per request
- Neural voices available for Hindi and English only
- Other languages use standard voices or fallback

### Amazon Comprehend
- Maximum text length: 5000 bytes per document
- Batch API: Maximum 25 documents per request
- Language detection confidence varies by text length

## Cost Optimization

1. **Transcribe**: Use automatic language detection only when necessary (costs more than specifying language)
2. **Polly**: Cache frequently used audio responses in S3
3. **Comprehend**: Use batch API for multiple texts to reduce API calls
4. **S3**: Set lifecycle policies to delete old audio files (configured in template.yaml)

## Future Enhancements

- [ ] Add support for more regional languages as AWS adds them
- [ ] Implement audio preprocessing for noise reduction
- [ ] Add streaming transcription for real-time voice interaction
- [ ] Cache common phrases in multiple languages
- [ ] Implement voice biometrics for user authentication
