#!/usr/bin/env python3
"""
Helper script to add audio samples to the test fixtures.

Usage:
    python add_sample.py audio_file.wav hi "नमस्ते मेरा नाम राज है"
    python add_sample.py audio_file.m4a en "Hello my name is John" --convert
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
import wave


def get_audio_duration(audio_path: Path) -> float:
    """Get duration of WAV file in seconds."""
    try:
        with wave.open(str(audio_path), 'rb') as wav_file:
            frames = wav_file.getnframes()
            rate = wav_file.getframerate()
            duration = frames / float(rate)
            return round(duration, 1)
    except Exception as e:
        print(f"⚠️  Could not determine duration: {e}")
        return 0.0


def convert_to_wav(input_path: Path, output_path: Path) -> bool:
    """Convert audio file to WAV format using FFmpeg."""
    try:
        cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-ar', '16000',  # 16kHz sample rate
            '-ac', '1',      # Mono
            '-sample_fmt', 's16',  # 16-bit
            '-y',            # Overwrite output
            str(output_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg conversion failed: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ FFmpeg not found. Please install FFmpeg:")
        print("   macOS: brew install ffmpeg")
        print("   Linux: sudo apt-get install ffmpeg")
        print("   Windows: https://ffmpeg.org/download.html")
        return False


def validate_audio_file(audio_path: Path) -> bool:
    """Validate that audio file meets requirements."""
    if not audio_path.exists():
        print(f"❌ File not found: {audio_path}")
        return False
    
    # Check if it's a WAV file
    if audio_path.suffix.lower() != '.wav':
        print(f"⚠️  File is not WAV format: {audio_path.suffix}")
        return False
    
    # Check WAV properties
    try:
        with wave.open(str(audio_path), 'rb') as wav_file:
            channels = wav_file.getnchannels()
            sample_rate = wav_file.getframerate()
            sample_width = wav_file.getsampwidth()
            
            print(f"📊 Audio properties:")
            print(f"   Channels: {channels} ({'Mono' if channels == 1 else 'Stereo'})")
            print(f"   Sample rate: {sample_rate} Hz")
            print(f"   Bit depth: {sample_width * 8}-bit")
            
            if channels != 1:
                print("⚠️  Warning: Audio should be mono (1 channel)")
            
            if sample_rate != 16000:
                print(f"⚠️  Warning: Sample rate should be 16000 Hz (got {sample_rate})")
            
            if sample_width != 2:
                print(f"⚠️  Warning: Bit depth should be 16-bit (got {sample_width * 8}-bit)")
            
            return True
    except Exception as e:
        print(f"❌ Invalid WAV file: {e}")
        return False


def load_samples_json(json_path: Path) -> dict:
    """Load existing samples.json or create new structure."""
    if json_path.exists():
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"⚠️  Warning: Could not parse existing samples.json: {e}")
            print("   Creating new samples.json")
    
    # Create new structure
    return {
        "_comment": "Audio sample metadata for STT testing",
        "_instructions": "Add metadata for each audio file you record",
        "samples": {}
    }


def save_samples_json(json_path: Path, data: dict):
    """Save samples.json with pretty formatting."""
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def generate_filename(language: str, text: str, existing_samples: dict) -> str:
    """Generate a unique filename for the audio sample."""
    # Count existing samples for this language
    count = sum(1 for meta in existing_samples.values() 
                if meta.get('language') == language)
    
    # Generate filename
    number = str(count + 1).zfill(3)
    
    # Create short description from text
    words = text.split()
    if len(words) > 0:
        description = words[0][:10].lower()
        # Remove non-alphanumeric characters
        description = ''.join(c for c in description if c.isalnum())
    else:
        description = "sample"
    
    return f"{language}_{number}_{description}.wav"


def main():
    parser = argparse.ArgumentParser(
        description='Add audio sample to test fixtures',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add a WAV file
  python add_sample.py recording.wav hi "नमस्ते मेरा नाम राज है"
  
  # Convert and add an M4A file
  python add_sample.py recording.m4a en "Hello my name is John" --convert
  
  # Specify custom output filename
  python add_sample.py recording.wav hi "नमस्ते" --output hi_custom.wav
  
  # Add with additional metadata
  python add_sample.py recording.wav hi "नमस्ते" --speaker native --quality high
        """
    )
    
    parser.add_argument('input_file', type=str, help='Input audio file')
    parser.add_argument('language', type=str, help='Language code (hi, en, bn, etc.)')
    parser.add_argument('text', type=str, help='Transcription text')
    parser.add_argument('--convert', action='store_true', 
                       help='Convert to WAV format using FFmpeg')
    parser.add_argument('--output', type=str, 
                       help='Output filename (default: auto-generated)')
    parser.add_argument('--speaker', type=str, default='native',
                       choices=['native', 'non-native'],
                       help='Speaker type (default: native)')
    parser.add_argument('--quality', type=str, default='high',
                       choices=['high', 'medium', 'low'],
                       help='Audio quality (default: high)')
    parser.add_argument('--source', type=str, default='recorded',
                       help='Source of audio (default: recorded)')
    parser.add_argument('--notes', type=str, default='',
                       help='Additional notes')
    
    args = parser.parse_args()
    
    # Get paths
    script_dir = Path(__file__).parent
    input_path = Path(args.input_file)
    json_path = script_dir / 'samples.json'
    
    print("🎙️  Adding audio sample to test fixtures\n")
    
    # Check input file exists
    if not input_path.exists():
        print(f"❌ Input file not found: {input_path}")
        return 1
    
    # Load existing samples
    samples_data = load_samples_json(json_path)
    existing_samples = samples_data.get('samples', {})
    
    # Generate output filename if not provided
    if args.output:
        output_filename = args.output
    else:
        output_filename = generate_filename(args.language, args.text, existing_samples)
    
    output_path = script_dir / output_filename
    
    # Convert if needed
    if args.convert or input_path.suffix.lower() != '.wav':
        print(f"🔄 Converting {input_path.name} to WAV format...")
        if not convert_to_wav(input_path, output_path):
            return 1
        print(f"✅ Converted to {output_filename}\n")
    else:
        # Copy WAV file
        print(f"📁 Copying {input_path.name}...")
        shutil.copy2(input_path, output_path)
        print(f"✅ Copied to {output_filename}\n")
    
    # Validate audio file
    print("🔍 Validating audio file...")
    if not validate_audio_file(output_path):
        print("\n⚠️  Audio file has issues but will be added anyway.")
        print("   Consider re-recording or converting with correct parameters.")
    else:
        print("✅ Audio file is valid\n")
    
    # Get audio duration
    duration = get_audio_duration(output_path)
    
    # Create metadata
    metadata = {
        "language": args.language,
        "text": args.text,
        "speaker": args.speaker,
        "quality": args.quality,
        "duration_seconds": duration,
        "sample_rate": 16000,
        "source": args.source
    }
    
    if args.notes:
        metadata["notes"] = args.notes
    
    # Add to samples
    samples_data['samples'][output_filename] = metadata
    
    # Save samples.json
    save_samples_json(json_path, samples_data)
    
    print("📝 Updated samples.json")
    print(f"\n✅ Successfully added audio sample!")
    print(f"\n📊 Summary:")
    print(f"   File: {output_filename}")
    print(f"   Language: {args.language}")
    print(f"   Text: {args.text}")
    print(f"   Duration: {duration}s")
    print(f"   Quality: {args.quality}")
    print(f"\n🧪 Test the sample:")
    print(f"   pytest .kiro/specs/bharatsahayak/tests/test_property_stt_accuracy.py -v")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
