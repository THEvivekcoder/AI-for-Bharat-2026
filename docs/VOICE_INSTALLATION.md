# Voice Interface Installation Guide

## Issue with OpenAI Whisper Installation

The `openai-whisper` package requires some build dependencies that may cause installation issues. Here are the solutions:

## Solution 1: Install setuptools first (Recommended)

```bash
# Activate your virtual environment
source venv/bin/activate

# Install/upgrade setuptools
pip install --upgrade setuptools wheel

# Install openai-whisper separately
pip install openai-whisper

# Install torch and torchaudio (required for Whisper)
pip install torch torchaudio

# Install remaining requirements
pip install -r requirements.txt
```

## Solution 2: Use Alternative STT (Lighter, No ML Models)

If you want to test the API structure without heavy ML dependencies:

```bash
# Just install the base requirements (already done)
pip install -r requirements.txt

# The system will use SpeechRecognition library instead
# This is lighter but less accurate than Whisper
```

## Solution 3: Manual Installation Steps

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Install build dependencies
pip install setuptools wheel

# 3. Install PyTorch (choose based on your system)
# For CPU only (lighter):
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# For GPU (CUDA):
pip install torch torchaudio

# 4. Install Whisper
pip install openai-whisper

# 5. Install other requirements
pip install -r requirements.txt
```

## Verification

After installation, verify the setup:

```bash
python scripts/validate_voice_module.py
```

## Testing Without Whisper

The voice interface module is designed to work with or without Whisper:

1. **With Whisper**: High accuracy, supports 10+ languages, automatic language detection
2. **Without Whisper**: Falls back to SpeechRecognition (Google Speech API), still functional but requires internet

## System Requirements

### Minimum (Without Whisper)
- Python 3.8+
- 2GB RAM
- Internet connection for Google Speech API

### Recommended (With Whisper)
- Python 3.8+
- 8GB RAM (4GB minimum)
- GPU with CUDA support (optional, for faster processing)
- 2GB disk space for models

## Troubleshooting

### Error: "No module named 'pkg_resources'"

```bash
pip install --upgrade setuptools
```

### Error: "Failed to build wheel for openai-whisper"

```bash
# Install build tools
pip install --upgrade pip setuptools wheel

# Try installing again
pip install openai-whisper
```

### Error: "torch not found"

```bash
# Install PyTorch first
pip install torch torchaudio
```

### macOS Specific: "Command 'clang' failed"

```bash
# Install Xcode command line tools
xcode-select --install
```

## Quick Start (Minimal Setup)

If you just want to test the API endpoints without ML models:

```bash
# Install only the base requirements
pip install fastapi uvicorn pydantic sqlalchemy redis python-jose passlib python-multipart python-dotenv gTTS

# Start the server
uvicorn app.main:app --reload

# Test the endpoints (TTS will work, STT will need Whisper)
curl http://localhost:8000/api/languages
```

## Production Deployment

For production, we recommend:

1. Use Docker to handle all dependencies
2. Pre-download Whisper models during build
3. Use GPU instances for better performance
4. Consider using managed ML services (AWS Transcribe, Google Speech-to-Text) for scalability

## Docker Installation (Coming Soon)

A Dockerfile will be provided that handles all dependencies automatically.
