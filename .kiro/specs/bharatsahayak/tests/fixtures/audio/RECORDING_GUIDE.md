# 🎙️ Audio Recording Guide for STT Testing

This guide will help you create high-quality audio samples for testing the BharatSahayak voice interface.

## 📋 What You Need

### Hardware
- **Smartphone** (iPhone/Android) - easiest option
- **OR** Laptop/computer with built-in microphone
- **OR** External USB microphone (best quality)

### Software
- **Recording:** Voice Memos (iOS), Voice Recorder (Android), Audacity (desktop)
- **Conversion:** FFmpeg (install instructions below)

---

## 🎯 Test Sentences to Record

Record these sentences in the languages you speak:

### Hindi (hi)
```
नमस्ते मेरा नाम राज है
```

### English (en)
```
Hello my name is John
```

### Bengali (bn)
```
আমার নাম রাজ
```

### Telugu (te)
```
నా పేరు రాజ్
```

### Marathi (mr)
```
माझे नाव राज आहे
```

### Tamil (ta)
```
என் பெயர் ராஜ்
```

### Gujarati (gu)
```
મારું નામ રાજ છે
```

### Kannada (kn)
```
ನನ್ನ ಹೆಸರು ರಾಜ್
```

### Malayalam (ml)
```
എന്റെ പേര് രാജ്
```

---

## 📱 Step-by-Step Recording Instructions

### Option 1: Using Your Smartphone (Recommended)

#### iPhone:
1. Open **Voice Memos** app
2. Tap the red record button
3. Speak clearly: "नमस्ते मेरा नाम राज है"
4. Tap stop
5. Tap the recording → Share → Save to Files
6. Transfer to your computer via AirDrop or iCloud

#### Android:
1. Open **Voice Recorder** or **Sound Recorder** app
2. Tap record
3. Speak clearly: "नमस्ते मेरा नाम राज है"
4. Tap stop
5. Share the file to your computer via Google Drive or USB

### Option 2: Using Your Computer

#### macOS:
```bash
# Record using QuickTime Player
# File → New Audio Recording → Click record button
```

#### Linux:
```bash
# Install and use arecord
sudo apt-get install alsa-utils
arecord -f cd -d 5 recording.wav
```

#### Windows:
```
# Use Voice Recorder app (built-in)
# Or download Audacity (free)
```

---

## 🎤 Recording Tips for Best Quality

### Environment
- ✅ Record in a **quiet room** (no TV, traffic, or background noise)
- ✅ Close windows and doors
- ✅ Turn off fans, AC, or noisy appliances
- ❌ Avoid echo-y rooms (bathrooms, empty rooms)

### Microphone Position
- ✅ Hold phone/mic **6-8 inches** from your mouth
- ✅ Speak **directly** toward the microphone
- ❌ Don't cover the microphone with your hand
- ❌ Don't speak too close (causes distortion)

### Speaking Style
- ✅ Speak at **normal conversational pace**
- ✅ Speak **clearly** but naturally
- ✅ Use your **normal voice** (not too loud or soft)
- ❌ Don't shout or whisper
- ❌ Don't speak too fast or too slow

### Recording Quality
- ✅ Record **2-5 seconds** per sentence
- ✅ Leave **0.5 seconds silence** at start and end
- ✅ Record **multiple takes** if needed
- ✅ Listen back to verify quality

---

## 🔧 Installing FFmpeg

FFmpeg is needed to convert audio files to the correct format.

### macOS:
```bash
# Using Homebrew
brew install ffmpeg
```

### Linux (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

### Windows:
1. Download from: https://ffmpeg.org/download.html
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to PATH environment variable

### Verify Installation:
```bash
ffmpeg -version
```

---

## 🎵 Converting Audio Files

After recording, convert your audio to the correct format:

### From iPhone (M4A):
```bash
ffmpeg -i recording.m4a -ar 16000 -ac 1 hi_001_namaste.wav
```

### From Android (MP3/AAC):
```bash
ffmpeg -i recording.mp3 -ar 16000 -ac 1 hi_001_namaste.wav
```

### From Any Format:
```bash
ffmpeg -i input_file.* -ar 16000 -ac 1 -sample_fmt s16 output.wav
```

### Batch Convert Multiple Files:
```bash
# macOS/Linux
for file in *.m4a; do
    ffmpeg -i "$file" -ar 16000 -ac 1 "${file%.m4a}.wav"
done

# Windows PowerShell
Get-ChildItem *.m4a | ForEach-Object {
    ffmpeg -i $_.Name -ar 16000 -ac 1 "$($_.BaseName).wav"
}
```

---

## 📁 File Naming Convention

Name your files using this pattern:
```
{language}_{number}_{description}.wav
```

Examples:
- `hi_001_namaste.wav` - Hindi greeting
- `en_001_hello.wav` - English greeting
- `bn_001_name.wav` - Bengali name introduction
- `hi_002_farmer.wav` - Hindi farmer sentence

---

## 📝 Creating the Metadata File

Create `samples.json` in this directory:

```json
{
  "_comment": "Audio sample metadata for STT testing",
  "_instructions": "Add metadata for each audio file you record",
  "samples": {
    "hi_001_namaste.wav": {
      "language": "hi",
      "text": "नमस्ते मेरा नाम राज है",
      "speaker": "native",
      "quality": "high",
      "duration_seconds": 3.2,
      "sample_rate": 16000,
      "source": "recorded",
      "notes": "Clear pronunciation, minimal background noise"
    },
    "en_001_hello.wav": {
      "language": "en",
      "text": "Hello my name is John",
      "speaker": "native",
      "quality": "high",
      "duration_seconds": 2.8,
      "sample_rate": 16000,
      "source": "recorded",
      "notes": "American accent"
    }
  }
}
```

### Metadata Fields:
- **language**: Language code (hi, en, bn, etc.)
- **text**: Exact transcription of what was spoken
- **speaker**: "native" or "non-native"
- **quality**: "high", "medium", or "low"
- **duration_seconds**: Length of audio (optional)
- **sample_rate**: Should be 16000
- **source**: "recorded", "mozilla_common_voice", "openslr", etc.
- **notes**: Any additional information

---

## ✅ Quick Start Checklist

1. **Choose 1-2 languages** you speak fluently
2. **Find a quiet room**
3. **Open recording app** on your phone
4. **Record the test sentence** (speak clearly, 2-5 seconds)
5. **Listen back** to verify quality
6. **Transfer file** to your computer
7. **Install FFmpeg** (if not already installed)
8. **Convert to WAV format** using FFmpeg command
9. **Rename file** using naming convention
10. **Copy to this directory** (`.kiro/specs/bharatsahayak/tests/fixtures/audio/`)
11. **Create/update `samples.json`** with metadata
12. **Run tests** to verify improvement

---

## 🧪 Testing Your Samples

After adding samples, run the tests:

```bash
# Check if samples are detected
pytest .kiro/specs/bharatsahayak/tests/test_property_stt_accuracy.py::test_real_audio_sample_detection -v -s

# Run full STT test suite
pytest .kiro/specs/bharatsahayak/tests/test_property_stt_accuracy.py -v

# Run with verbose output
pytest .kiro/specs/bharatsahayak/tests/test_property_stt_accuracy.py -v -s
```

---

## 📊 Expected Results

### Before (Synthetic Speech):
- ⚠️ Accuracy: 70-80%
- ⚠️ Script confusion with Indic languages
- ⚠️ Test duration: ~20-25 seconds

### After (Real Audio):
- ✅ Accuracy: 85-95%
- ✅ No script confusion
- ✅ Test duration: ~10-15 seconds
- ✅ Production-quality testing

---

## 🎯 Priority Languages

Start with these languages (most commonly used):

1. **Hindi** (hi) - Primary language
2. **English** (en) - Secondary language
3. **Bengali** (bn) - Large user base
4. **Tamil** (ta) - Large user base
5. **Telugu** (te) - Large user base

Add others as needed based on your target audience.

---

## 🆘 Troubleshooting

### "FFmpeg not found"
- Make sure FFmpeg is installed
- Verify it's in your PATH: `ffmpeg -version`
- Restart your terminal after installation

### "Audio quality is poor"
- Record in a quieter environment
- Move closer to the microphone (6-8 inches)
- Use a better microphone if available
- Check that nothing is blocking the mic

### "Conversion failed"
- Check input file is not corrupted
- Try playing the file first to verify it works
- Use the generic conversion command: `ffmpeg -i input.* -ar 16000 -ac 1 output.wav`

### "Tests still failing"
- Verify `samples.json` is valid JSON
- Check file names match exactly in `samples.json`
- Verify text in metadata matches what was spoken
- Check audio files are in the correct directory

---

## 💡 Pro Tips

1. **Record multiple takes** - Choose the best one
2. **Get native speakers** - Better accuracy for regional languages
3. **Vary speakers** - Different voices improve test coverage
4. **Start small** - 1-2 samples per language is enough to start
5. **Test immediately** - Verify samples work before recording more
6. **Document issues** - Note any problems in the metadata

---

## 🌐 Alternative: Download Existing Datasets

If you can't record your own samples, download from:

### Mozilla Common Voice (Recommended)
- URL: https://commonvoice.mozilla.org/
- Languages: Hindi, Bengali, Tamil, and more
- License: CC0 (Public Domain)
- Quality: Community-validated

### OpenSLR
- URL: http://www.openslr.org/
- Datasets: Indian language speech corpora
- Quality: Research-grade

See `IMPROVED_STT_TESTING.md` for detailed instructions on using these datasets.

---

## 📞 Need Help?

If you encounter issues:
1. Check the troubleshooting section above
2. Review `IMPROVED_STT_TESTING.md` for more details
3. Check `README.md` for overview
4. Run the detection test to see current status

---

## 🎉 Success!

Once you've added samples:
- ✅ Tests will automatically use real audio
- ✅ Accuracy will improve to 85%+
- ✅ Tests will run faster
- ✅ Results will be more reliable

**Thank you for improving the test quality!** 🙏
