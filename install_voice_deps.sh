#!/bin/bash

# Voice Interface Dependencies Installation Script
# This script installs dependencies in the correct order

echo "=========================================="
echo "Voice Interface Dependencies Installation"
echo "=========================================="
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: Virtual environment not activated"
    echo "Please run: source venv/bin/activate"
    exit 1
fi

echo "✓ Virtual environment detected: $VIRTUAL_ENV"
echo ""

# Step 1: Install basic dependencies (these should work)
echo "Step 1: Installing basic dependencies..."
pip install --upgrade pip setuptools wheel
echo ""

# Step 2: Install numpy (required by many packages)
echo "Step 2: Installing numpy..."
pip install numpy==1.26.3
echo ""

# Step 3: Install audio processing libraries
echo "Step 3: Installing audio processing libraries..."
pip install librosa==0.10.1
pip install soundfile==0.12.1
pip install pydub==0.25.1
echo ""

# Step 4: Install gTTS (Text-to-Speech)
echo "Step 4: Installing gTTS (Text-to-Speech)..."
pip install gTTS==2.5.0
echo ""

# Step 5: Install SpeechRecognition (alternative STT)
echo "Step 5: Installing SpeechRecognition..."
pip install SpeechRecognition==3.10.1
echo ""

# Step 6: Ask about Whisper installation
echo "=========================================="
echo "Optional: Whisper Installation"
echo "=========================================="
echo ""
echo "Whisper provides high-quality Speech-to-Text but requires:"
echo "  - PyTorch (~500MB)"
echo "  - Whisper models (~140MB for base model)"
echo "  - Total: ~640MB download"
echo ""
read -p "Do you want to install Whisper? (y/n): " install_whisper

if [ "$install_whisper" = "y" ] || [ "$install_whisper" = "Y" ]; then
    echo ""
    echo "Step 6a: Installing PyTorch (CPU version)..."
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
    
    echo ""
    echo "Step 6b: Installing Whisper..."
    pip install openai-whisper
    
    echo ""
    echo "✓ Whisper installed successfully!"
else
    echo ""
    echo "⚠️  Skipping Whisper installation"
    echo "   Note: STT functionality will be limited without Whisper"
fi

echo ""
echo "=========================================="
echo "Installation Summary"
echo "=========================================="
echo ""

# Check what's installed
python -c "
import sys

def check_import(module_name, display_name):
    try:
        __import__(module_name)
        print(f'✓ {display_name}')
        return True
    except ImportError:
        print(f'✗ {display_name}')
        return False

print('Installed packages:')
check_import('numpy', 'numpy')
check_import('librosa', 'librosa')
check_import('soundfile', 'soundfile')
check_import('pydub', 'pydub')
check_import('gtts', 'gTTS (Text-to-Speech)')
check_import('speech_recognition', 'SpeechRecognition')
check_import('torch', 'PyTorch')
check_import('whisper', 'Whisper (Speech-to-Text)')
"

echo ""
echo "=========================================="
echo "Next Steps"
echo "=========================================="
echo ""
echo "1. Test TTS functionality:"
echo "   python scripts/test_tts_only.py"
echo ""
echo "2. Validate module structure:"
echo "   python scripts/validate_voice_module.py"
echo ""
echo "3. Start the server:"
echo "   uvicorn app.main:app --reload"
echo ""
echo "4. Test the API:"
echo "   curl http://localhost:8000/api/languages"
echo ""
