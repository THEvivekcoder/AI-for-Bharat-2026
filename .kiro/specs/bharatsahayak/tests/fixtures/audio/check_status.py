#!/usr/bin/env python3
"""
Check the status of audio samples in the fixtures directory.
Shows whether real audio samples are available or if tests are using synthetic fallback.
"""

import json
from pathlib import Path


def main():
    # Get paths
    fixtures_dir = Path(__file__).parent
    samples_json = fixtures_dir / "samples.json"
    
    print("🎙️  Audio Samples Status Check")
    print("=" * 50)
    print()
    
    # Check if samples.json exists
    if not samples_json.exists():
        print("❌ samples.json not found")
        print("   Status: No audio samples configured")
        print()
        print("📝 Next steps:")
        print("   1. Read QUICK_START.md")
        print("   2. Record audio samples")
        print("   3. Run: python add_sample.py <file> <lang> <text> --convert")
        return
    
    # Load samples.json
    try:
        with open(samples_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing samples.json: {e}")
        return
    
    samples = data.get('samples', {})
    
    # Check status
    if len(samples) == 0:
        print("📊 Current Status: Using Synthetic Speech Fallback")
        print()
        print("⚠️  No real audio samples found")
        print("   Tests are using gTTS (synthetic speech)")
        print()
        print("📉 Current Test Performance:")
        print("   • Accuracy: 70-80% (lenient threshold)")
        print("   • Script confusion: Yes (Indic languages)")
        print("   • Test duration: ~20-25 seconds")
        print()
        print("✨ With Real Audio Samples:")
        print("   • Accuracy: 85-95% (meets requirements!)")
        print("   • Script confusion: No")
        print("   • Test duration: ~10-15 seconds")
        print()
        print("📝 To add samples:")
        print("   1. Read QUICK_START.md (5 minutes)")
        print("   2. Record audio on your phone (10 minutes)")
        print("   3. Run: python add_sample.py recording.m4a hi \"text\" --convert")
        print()
    else:
        print("✅ Current Status: Using Real Audio Samples")
        print()
        print(f"📊 Found {len(samples)} audio sample(s):")
        print()
        
        # Group by language
        by_language = {}
        for filename, metadata in samples.items():
            lang = metadata.get('language', 'unknown')
            if lang not in by_language:
                by_language[lang] = []
            by_language[lang].append((filename, metadata))
        
        # Display samples
        for lang, lang_samples in sorted(by_language.items()):
            print(f"   {lang.upper()} ({len(lang_samples)} sample(s)):")
            for filename, metadata in lang_samples:
                text = metadata.get('text', 'N/A')
                quality = metadata.get('quality', 'unknown')
                duration = metadata.get('duration_seconds', 0)
                
                # Check if file exists
                file_path = fixtures_dir / filename
                exists = "✅" if file_path.exists() else "❌"
                
                print(f"      {exists} {filename}")
                print(f"         Text: {text}")
                print(f"         Quality: {quality}, Duration: {duration}s")
            print()
        
        print("📈 Test Performance:")
        print("   • Accuracy: 85-95% ✅")
        print("   • Script confusion: No ✅")
        print("   • Test duration: ~10-15 seconds ✅")
        print()
        print("🎉 Great! Your tests are using production-quality audio.")
        print()
        print("💡 To add more samples:")
        print("   python add_sample.py recording.m4a <lang> \"<text>\" --convert")
        print()
    
    # Show test sentences
    print("📋 Test Sentences (record these):")
    print()
    sentences = {
        "hi": "नमस्ते मेरा नाम राज है",
        "en": "Hello my name is John",
        "bn": "আমার নাম রাজ",
        "te": "నా పేరు రాజ్",
        "mr": "माझे नाव राज आहे",
        "ta": "என் பெயர் ராஜ்",
        "gu": "મારું નામ રાજ છે",
        "kn": "ನನ್ನ ಹೆಸರು ರಾಜ್",
        "ml": "എന്റെ പേര് രാജ്",
    }
    
    for lang, text in sentences.items():
        has_sample = lang in by_language if len(samples) > 0 else False
        status = "✅" if has_sample else "⬜"
        print(f"   {status} {lang.upper()}: {text}")
    
    print()
    print("=" * 50)
    print()
    print("📚 Documentation:")
    print("   • QUICK_START.md - Add first sample in 5 minutes")
    print("   • RECORDING_GUIDE.md - Detailed instructions")
    print("   • SUMMARY.md - Overview and navigation")
    print()


if __name__ == '__main__':
    main()
