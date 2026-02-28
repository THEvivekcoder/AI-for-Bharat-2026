# 📚 Audio Fixtures Documentation Index

Complete guide to adding real audio samples for STT testing.

---

## 🎯 Start Here

**New to this?** Choose your path:

| If you want to... | Start with... | Time |
|-------------------|---------------|------|
| Add first sample quickly | **QUICK_START.md** | 5 min |
| Understand the big picture | **SUMMARY.md** | 10 min |
| See visual workflow | **WORKFLOW.md** | 5 min |
| Get detailed instructions | **RECORDING_GUIDE.md** | 15 min |
| Check current status | `python check_status.py` | 1 min |

---

## 📁 All Files

### 📖 Documentation (Read These)

| File | Purpose | When to Read |
|------|---------|-------------|
| **README.md** | Quick overview and reference | Need basic info |
| **QUICK_START.md** | Fast track (5 minutes) | Want to start immediately |
| **RECORDING_GUIDE.md** | Complete recording guide | Need detailed instructions |
| **SUMMARY.md** | Overview and navigation | Want to understand everything |
| **WORKFLOW.md** | Visual workflow diagrams | Prefer visual guides |
| **IMPROVED_STT_TESTING.md** | Technical testing details | Want deep technical info |
| **INDEX.md** (this file) | Complete file index | Need to find something |

### 🛠️ Tools (Use These)

| File | Purpose | Usage |
|------|---------|-------|
| **add_sample.py** | Add single audio sample | `python add_sample.py file.m4a hi "text" --convert` |
| **batch_add_samples.sh** | Process multiple samples | `./batch_add_samples.sh` |
| **check_status.py** | Check current status | `python check_status.py` |
| **samples.json** | Audio metadata | Auto-updated by scripts |

---

## 🗺️ Documentation Map

```
┌─────────────────────────────────────────────────────────┐
│                    START HERE                           │
│                                                         │
│  New User? → QUICK_START.md (5 min)                    │
│  Want Overview? → SUMMARY.md (10 min)                  │
│  Visual Learner? → WORKFLOW.md (5 min)                 │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  DETAILED GUIDES                        │
│                                                         │
│  Recording Help → RECORDING_GUIDE.md                   │
│  Technical Details → IMPROVED_STT_TESTING.md           │
│  Quick Reference → README.md                           │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    USE TOOLS                            │
│                                                         │
│  Check Status → python check_status.py                 │
│  Add Sample → python add_sample.py                     │
│  Batch Process → ./batch_add_samples.sh                │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   RUN TESTS                             │
│                                                         │
│  pytest test_property_stt_accuracy.py -v               │
└─────────────────────────────────────────────────────────┘
```

---

## 📖 Documentation Details

### README.md
- **Length:** Short (1 page)
- **Purpose:** Quick reference card
- **Contains:**
  - Overview of purpose
  - Quick commands
  - Test sentences
  - Basic requirements
- **Best for:** Quick lookup

### QUICK_START.md
- **Length:** Short (2 pages)
- **Purpose:** Fastest path to success
- **Contains:**
  - 5-minute workflow
  - Essential commands
  - Priority languages
  - Success checklist
- **Best for:** Getting started fast

### RECORDING_GUIDE.md
- **Length:** Long (comprehensive)
- **Purpose:** Complete recording instructions
- **Contains:**
  - Step-by-step recording
  - FFmpeg installation
  - Audio conversion
  - Troubleshooting
  - Pro tips
- **Best for:** Detailed guidance

### SUMMARY.md
- **Length:** Medium (overview)
- **Purpose:** Navigation and overview
- **Contains:**
  - File descriptions
  - Quick start steps
  - Tool descriptions
  - Expected results
  - Documentation index
- **Best for:** Understanding the system

### WORKFLOW.md
- **Length:** Medium (visual)
- **Purpose:** Visual workflow guide
- **Contains:**
  - Workflow diagrams
  - Decision trees
  - Priority matrix
  - Time estimates
  - Before/after comparison
- **Best for:** Visual learners

### IMPROVED_STT_TESTING.md
- **Length:** Long (technical)
- **Purpose:** Technical testing strategy
- **Contains:**
  - Hybrid audio strategy
  - Test implementation
  - Performance comparison
  - Dataset sources
  - Technical specifications
- **Best for:** Technical deep dive

### INDEX.md (this file)
- **Length:** Medium (reference)
- **Purpose:** Complete file index
- **Contains:**
  - All file descriptions
  - Documentation map
  - Quick reference
  - Recommended paths
- **Best for:** Finding what you need

---

## 🛠️ Tool Details

### add_sample.py
**Purpose:** Add a single audio sample with automatic conversion and validation

**Features:**
- ✅ Automatic format conversion (M4A/MP3 → WAV)
- ✅ Audio quality validation
- ✅ Automatic filename generation
- ✅ samples.json update
- ✅ Helpful error messages

**Usage:**
```bash
# Basic usage
python add_sample.py recording.m4a hi "नमस्ते मेरा नाम राज है" --convert

# With options
python add_sample.py recording.wav en "Hello" \
  --speaker native \
  --quality high \
  --notes "Clear audio"

# Custom filename
python add_sample.py recording.m4a hi "नमस्ते" \
  --output hi_custom.wav \
  --convert
```

**Help:**
```bash
python add_sample.py --help
```

### batch_add_samples.sh
**Purpose:** Process multiple audio samples at once

**Features:**
- ✅ Interactive mode (guides you through each file)
- ✅ Batch mode (configure in script)
- ✅ Automatic format conversion
- ✅ Progress tracking
- ✅ Summary report

**Usage:**
```bash
# Interactive mode (recommended)
./batch_add_samples.sh

# Or configure samples in script and run
# Edit the SAMPLES array in the script first
./batch_add_samples.sh
```

### check_status.py
**Purpose:** Check current status of audio samples

**Features:**
- ✅ Shows number of samples
- ✅ Lists samples by language
- ✅ Shows test performance metrics
- ✅ Displays test sentences
- ✅ Provides next steps

**Usage:**
```bash
python check_status.py
```

**Output:**
- Current status (real audio or synthetic)
- Sample count and details
- Performance metrics
- Test sentences checklist
- Next steps

### samples.json
**Purpose:** Metadata for all audio samples

**Format:**
```json
{
  "_comment": "Audio sample metadata",
  "_instructions": "Add metadata for each file",
  "samples": {
    "hi_001_namaste.wav": {
      "language": "hi",
      "text": "नमस्ते मेरा नाम राज है",
      "speaker": "native",
      "quality": "high",
      "duration_seconds": 3.2,
      "sample_rate": 16000,
      "source": "recorded",
      "notes": "Clear pronunciation"
    }
  }
}
```

**Auto-updated by:** add_sample.py, batch_add_samples.sh

---

## 🎯 Recommended Paths

### Path 1: Absolute Beginner (20 minutes)
1. Read **QUICK_START.md** (5 min)
2. Run `python check_status.py` (1 min)
3. Record 1 audio sample on phone (5 min)
4. Transfer to computer (2 min)
5. Run `python add_sample.py recording.m4a hi "text" --convert` (2 min)
6. Run tests (1 min)
7. Celebrate! 🎉

### Path 2: Want Details First (40 minutes)
1. Read **SUMMARY.md** (10 min)
2. Read **RECORDING_GUIDE.md** (15 min)
3. Run `python check_status.py` (1 min)
4. Record 2-3 samples (10 min)
5. Use `add_sample.py` for each (5 min)
6. Run tests (1 min)

### Path 3: Visual Learner (30 minutes)
1. Read **WORKFLOW.md** (10 min)
2. Read **QUICK_START.md** (5 min)
3. Follow workflow diagram (10 min)
4. Run tests (1 min)

### Path 4: Technical Deep Dive (60 minutes)
1. Read **IMPROVED_STT_TESTING.md** (20 min)
2. Read **RECORDING_GUIDE.md** (15 min)
3. Understand test implementation (10 min)
4. Record samples (10 min)
5. Run and analyze tests (5 min)

### Path 5: Batch Processing (45 minutes)
1. Read **RECORDING_GUIDE.md** (15 min)
2. Record 5-10 samples (20 min)
3. Run `./batch_add_samples.sh` (5 min)
4. Run tests (1 min)

---

## 🧪 Testing Commands

```bash
# Check if samples are detected
pytest .kiro/specs/bharatsahayak/tests/test_property_stt_accuracy.py::test_real_audio_sample_detection -v -s

# View audio source strategy
pytest .kiro/specs/bharatsahayak/tests/test_property_stt_accuracy.py::test_audio_source_strategy -v -s

# Run full STT test suite
pytest .kiro/specs/bharatsahayak/tests/test_property_stt_accuracy.py -v

# Run with verbose output
pytest .kiro/specs/bharatsahayak/tests/test_property_stt_accuracy.py -v -s

# Run specific language test
pytest .kiro/specs/bharatsahayak/tests/test_property_stt_accuracy.py::test_stt_accuracy_hindi_example -v
```

---

## 📊 Quick Reference

### Test Sentences

| Language | Code | Sentence |
|----------|------|----------|
| Hindi | `hi` | नमस्ते मेरा नाम राज है |
| English | `en` | Hello my name is John |
| Bengali | `bn` | আমার নাম রাজ |
| Telugu | `te` | నా పేరు రాజ్ |
| Marathi | `mr` | माझे नाव राज आहे |
| Tamil | `ta` | என் பெயர் ராஜ் |
| Gujarati | `gu` | મારું નામ રાજ છે |
| Kannada | `kn` | ನನ್ನ ಹೆಸರು ರಾಜ್ |
| Malayalam | `ml` | എന്റെ പേര് രാജ് |

### Audio Requirements

- **Format:** WAV (16kHz, mono, 16-bit)
- **Duration:** 2-5 seconds
- **Quality:** Clear speech, minimal noise
- **Environment:** Quiet room

### Common Commands

```bash
# Install FFmpeg
brew install ffmpeg  # macOS
sudo apt-get install ffmpeg  # Linux

# Convert audio
ffmpeg -i input.m4a -ar 16000 -ac 1 output.wav

# Check status
python check_status.py

# Add sample
python add_sample.py file.m4a hi "text" --convert

# Batch process
./batch_add_samples.sh

# Run tests
pytest test_property_stt_accuracy.py -v
```

---

## 🎯 Success Metrics

### Before Adding Samples
- ⚠️ Accuracy: 70-80%
- ⚠️ Script confusion: Yes
- ⚠️ Test duration: ~25s
- ❌ Requirements: Not met

### After Adding Samples
- ✅ Accuracy: 85-95%
- ✅ Script confusion: No
- ✅ Test duration: ~15s
- ✅ Requirements: Met!

---

## 💡 Pro Tips

1. **Start small** - Add 1-2 samples first
2. **Use the tools** - Scripts handle technical details
3. **Test immediately** - Verify each sample works
4. **Quiet environment** - Makes huge difference
5. **Native speakers** - Best results
6. **Multiple takes** - Keep the best one
7. **Check status** - Run `check_status.py` often

---

## 🆘 Troubleshooting

| Problem | Solution | See |
|---------|----------|-----|
| FFmpeg not found | Install FFmpeg | RECORDING_GUIDE.md |
| Audio quality poor | Record in quiet room | RECORDING_GUIDE.md |
| Conversion failed | Check input file | RECORDING_GUIDE.md |
| Tests still failing | Verify samples.json | IMPROVED_STT_TESTING.md |
| Can't record | Download datasets | IMPROVED_STT_TESTING.md |

---

## 📞 Need Help?

1. **Check status**: `python check_status.py`
2. **Read docs**: Start with QUICK_START.md
3. **Run tests**: See what's working
4. **Check samples.json**: Verify metadata
5. **Review logs**: Look for error messages

---

## ✅ Completion Checklist

- [ ] Read documentation (choose your path)
- [ ] Installed FFmpeg
- [ ] Recorded audio sample(s)
- [ ] Ran `check_status.py`
- [ ] Used `add_sample.py` or batch script
- [ ] Verified samples.json updated
- [ ] Ran tests
- [ ] Saw improved accuracy (85%+)
- [ ] Celebrated success! 🎉

---

## 🎉 You're Ready!

Everything you need is here. Choose your path and start improving those test results!

**Recommended first step:** Read **QUICK_START.md** (5 minutes)

---

**Last Updated:** February 26, 2026  
**Files:** 9 documentation files + 4 tools  
**Status:** Complete and ready to use  
**Goal:** Achieve 85%+ STT accuracy with real audio samples
