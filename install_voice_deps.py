#!/usr/bin/env python3
"""
Voice Interface Dependencies Installer

This script installs the required dependencies for the voice interface module
in the correct order to avoid dependency conflicts.
"""

import subprocess
import sys


def run_pip_install(packages, description):
    """Install packages using pip"""
    print(f"\n{'='*60}")
    print(f"Installing: {description}")
    print(f"{'='*60}")
    
    if isinstance(packages, str):
        packages = [packages]
    
    for package in packages:
        print(f"\n📦 Installing {package}...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package
            ])
            print(f"✓ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install {package}: {e}")
            return False
    
    return True


def check_installation():
    """Check which packages are installed"""
    print(f"\n{'='*60}")
    print("Checking Installation")
    print(f"{'='*60}\n")
    
    packages = {
        'numpy': 'numpy',
        'librosa': 'librosa',
        'soundfile': 'soundfile',
        'pydub': 'pydub',
        'gtts': 'gTTS (Text-to-Speech)',
        'speech_recognition': 'SpeechRecognition',
        'torch': 'PyTorch',
        'whisper': 'Whisper (Speech-to-Text)'
    }
    
    installed = []
    missing = []
    
    for module, display_name in packages.items():
        try:
            __import__(module)
            print(f"✓ {display_name}")
            installed.append(display_name)
        except ImportError:
            print(f"✗ {display_name}")
            missing.append(display_name)
    
    return installed, missing


def main():
    print("="*60)
    print("Voice Interface Dependencies Installer")
    print("="*60)
    print("\nThis will install the required packages for voice interface.")
    print("Installation will be done in steps to avoid conflicts.\n")
    
    # Step 1: Upgrade pip and setuptools
    print("\nStep 1: Upgrading pip, setuptools, and wheel...")
    run_pip_install(["--upgrade", "pip", "setuptools", "wheel"], "Build tools")
    
    # Step 2: Install numpy
    if not run_pip_install("numpy==1.26.3", "NumPy"):
        print("\n⚠️  Failed to install numpy. Continuing anyway...")
    
    # Step 3: Install audio processing libraries
    audio_libs = [
        "librosa==0.10.1",
        "soundfile==0.12.1",
        "pydub==0.25.1"
    ]
    run_pip_install(audio_libs, "Audio processing libraries")
    
    # Step 4: Install gTTS
    run_pip_install("gTTS==2.5.0", "gTTS (Text-to-Speech)")
    
    # Step 5: Install SpeechRecognition
    run_pip_install("SpeechRecognition==3.10.1", "SpeechRecognition")
    
    # Step 6: Ask about Whisper
    print("\n" + "="*60)
    print("Optional: Whisper Installation")
    print("="*60)
    print("\nWhisper provides high-quality Speech-to-Text but requires:")
    print("  • PyTorch (~500MB)")
    print("  • Whisper models (~140MB for base model)")
    print("  • Total: ~640MB download")
    print("\nWithout Whisper:")
    print("  • Text-to-Speech will work perfectly")
    print("  • Speech-to-Text will show an error message")
    
    response = input("\nDo you want to install Whisper? (y/n): ").strip().lower()
    
    if response in ['y', 'yes']:
        print("\nInstalling PyTorch (CPU version)...")
        subprocess.call([
            sys.executable, "-m", "pip", "install",
            "torch", "torchaudio",
            "--index-url", "https://download.pytorch.org/whl/cpu"
        ])
        
        print("\nInstalling Whisper...")
        run_pip_install("openai-whisper", "Whisper")
    else:
        print("\n⚠️  Skipping Whisper installation")
        print("   You can install it later with:")
        print("   pip install torch torchaudio openai-whisper")
    
    # Final check
    installed, missing = check_installation()
    
    # Summary
    print("\n" + "="*60)
    print("Installation Complete!")
    print("="*60)
    print(f"\n✓ Installed: {len(installed)} packages")
    if missing:
        print(f"⚠️  Missing: {len(missing)} packages")
        print(f"   {', '.join(missing)}")
    
    # Next steps
    print("\n" + "="*60)
    print("Next Steps")
    print("="*60)
    print("\n1. Test TTS functionality:")
    print("   python scripts/test_tts_only.py")
    print("\n2. Validate module structure:")
    print("   python scripts/validate_voice_module.py")
    print("\n3. Start the server:")
    print("   uvicorn app.main:app --reload")
    print("\n4. Test the API:")
    print("   curl http://localhost:8000/api/languages")
    print()


if __name__ == "__main__":
    main()
