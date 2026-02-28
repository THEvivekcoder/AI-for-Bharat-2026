# 🔄 Audio Sample Workflow

Visual guide to adding audio samples for STT testing.

---

## 📊 Current State

```
┌─────────────────────────────────────────┐
│  STT Tests (Property 1)                 │
│  ─────────────────────────────────────  │
│                                         │
│  Status: Using Synthetic Speech         │
│  Accuracy: 70-80% ⚠️                    │
│  Script Confusion: Yes ⚠️               │
│  Duration: ~25s ⚠️                      │
│                                         │
│  ❌ Does not meet 85% requirement       │
└─────────────────────────────────────────┘
```

---

## 🎯 Goal State

```
┌─────────────────────────────────────────┐
│  STT Tests (Property 1)                 │
│  ─────────────────────────────────────  │
│                                         │
│  Status: Using Real Audio Samples       │
│  Accuracy: 85-95% ✅                    │
│  Script Confusion: No ✅                │
│  Duration: ~15s ✅                      │
│                                         │
│  ✅ Meets requirements!                 │
└─────────────────────────────────────────┘
```

---

## 🚀 Workflow Options

### Option A: Quick Start (Recommended)

```
┌──────────────┐
│ 1. Record    │  📱 Use your smartphone
│    Audio     │  🎤 Speak test sentence
└──────┬───────┘  ⏱️  2-5 seconds
       │
       ▼
┌──────────────┐
│ 2. Transfer  │  📲 AirDrop / USB / Cloud
│    to PC     │  💾 Save to Downloads
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 3. Run       │  🛠️  python add_sample.py \
│    Script    │      recording.m4a hi "text" \
└──────┬───────┘      --convert
       │
       ▼
┌──────────────┐
│ 4. Test      │  🧪 pytest test_property_stt_accuracy.py -v
│    & Verify  │  ✅ See improved accuracy!
└──────────────┘

Total Time: ~20 minutes
```

### Option B: Batch Processing

```
┌──────────────┐
│ 1. Record    │  📱 Record multiple sentences
│    Multiple  │  🎤 All languages you speak
└──────┬───────┘  ⏱️  10-30 minutes
       │
       ▼
┌──────────────┐
│ 2. Transfer  │  📲 Transfer all files
│    All Files │  💾 Save to one folder
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 3. Run Batch │  🔄 ./batch_add_samples.sh
│    Script    │  📝 Interactive prompts
└──────┬───────┘  ⚡ Processes all files
       │
       ▼
┌──────────────┐
│ 4. Test      │  🧪 pytest test_property_stt_accuracy.py -v
│    & Verify  │  ✅ See improved accuracy!
└──────────────┘

Total Time: ~45 minutes
```

### Option C: Download Datasets

```
┌──────────────┐
│ 1. Download  │  🌐 Mozilla Common Voice
│    Dataset   │  📦 Filter by language
└──────┬───────┘  💾 Download validated clips
       │
       ▼
┌──────────────┐
│ 2. Extract   │  📂 Unzip dataset
│    & Filter  │  🔍 Find matching sentences
└──────┬───────┘  ✂️  Extract relevant clips
       │
       ▼
┌──────────────┐
│ 3. Add to    │  🛠️  python add_sample.py \
│    Fixtures  │      clip.mp3 hi "text" \
└──────┬───────┘      --convert
       │
       ▼
┌──────────────┐
│ 4. Test      │  🧪 pytest test_property_stt_accuracy.py -v
│    & Verify  │  ✅ See improved accuracy!
└──────────────┘

Total Time: ~60 minutes
```

---

## 🔧 Technical Workflow

### What Happens Behind the Scenes

```
┌─────────────────────────────────────────────────────────┐
│                    add_sample.py                        │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│ 1. Input Validation                                     │
│    • Check file exists                                  │
│    • Verify file format                                 │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 2. Audio Conversion (if needed)                         │
│    • FFmpeg: input → WAV                                │
│    • Sample rate: 16kHz                                 │
│    • Channels: Mono                                     │
│    • Bit depth: 16-bit                                  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 3. Quality Validation                                   │
│    • Check sample rate (16kHz)                          │
│    • Check channels (mono)                              │
│    • Check bit depth (16-bit)                           │
│    • Calculate duration                                 │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 4. File Management                                      │
│    • Generate filename (lang_###_desc.wav)              │
│    • Copy to fixtures directory                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 5. Metadata Update                                      │
│    • Load samples.json                                  │
│    • Add new entry with metadata                        │
│    • Save with pretty formatting                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 6. Success Report                                       │
│    • Show file details                                  │
│    • Display test command                               │
└─────────────────────────────────────────────────────────┘
```

---

## 🧪 Test Workflow

### How Tests Use Audio Samples

```
┌─────────────────────────────────────────────────────────┐
│              test_property_stt_accuracy.py              │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│ 1. Check for Real Audio                                 │
│    • Load samples.json                                  │
│    • Look for matching language + text                  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ├─── Found? ───┐
                     │               │
                     ▼               ▼
         ┌───────────────┐   ┌──────────────┐
         │ Use Real      │   │ Generate     │
         │ Audio Sample  │   │ Synthetic    │
         │               │   │ (gTTS)       │
         │ Threshold:    │   │              │
         │ 85% ✅        │   │ Threshold:   │
         └───────┬───────┘   │ 70-80% ⚠️    │
                 │           └──────┬───────┘
                 │                  │
                 └────────┬─────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │ 2. Transcribe with Whisper     │
         │    • Load audio                │
         │    • Run STT model             │
         │    • Get transcription         │
         └────────────┬───────────────────┘
                      │
                      ▼
         ┌────────────────────────────────┐
         │ 3. Calculate Accuracy          │
         │    • Compare with reference    │
         │    • Word-level matching       │
         │    • Calculate percentage      │
         └────────────┬───────────────────┘
                      │
                      ▼
         ┌────────────────────────────────┐
         │ 4. Assert Threshold            │
         │    • Real audio: >= 85%        │
         │    • Synthetic: >= 70-80%      │
         └────────────┬───────────────────┘
                      │
                      ▼
         ┌────────────────────────────────┐
         │ 5. Report Results              │
         │    ✅ Pass or ❌ Fail          │
         └────────────────────────────────┘
```

---

## 📊 Decision Tree

```
                    Start
                      │
                      ▼
        ┌─────────────────────────┐
        │ Do you speak any of     │
        │ the test languages?     │
        └─────────┬───────────────┘
                  │
         ┌────────┴────────┐
         │                 │
        Yes               No
         │                 │
         ▼                 ▼
┌─────────────────┐  ┌──────────────────┐
│ Record Your Own │  │ Download Dataset │
│ (Option A/B)    │  │ (Option C)       │
└────────┬────────┘  └────────┬─────────┘
         │                     │
         └──────────┬──────────┘
                    │
                    ▼
        ┌─────────────────────────┐
        │ How many samples?       │
        └─────────┬───────────────┘
                  │
         ┌────────┴────────┐
         │                 │
       1-2            Multiple
         │                 │
         ▼                 ▼
┌─────────────────┐  ┌──────────────────┐
│ Use Quick Start │  │ Use Batch Script │
│ add_sample.py   │  │ batch_add.sh     │
└────────┬────────┘  └────────┬─────────┘
         │                     │
         └──────────┬──────────┘
                    │
                    ▼
        ┌─────────────────────────┐
        │ Run Tests               │
        │ pytest -v               │
        └─────────┬───────────────┘
                  │
                  ▼
        ┌─────────────────────────┐
        │ ✅ 85%+ Accuracy!       │
        └─────────────────────────┘
```

---

## 🎯 Priority Matrix

### What to Record First

```
┌─────────────────────────────────────────────────────────┐
│                    Priority Matrix                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  High Priority (Record First)                           │
│  ────────────────────────────                           │
│  ✅ Hindi (hi) - Primary language                       │
│  ✅ English (en) - Secondary language                   │
│                                                         │
│  Medium Priority (Record Next)                          │
│  ──────────────────────────────                         │
│  ⬜ Bengali (bn) - Large user base                      │
│  ⬜ Tamil (ta) - Large user base                        │
│  ⬜ Telugu (te) - Large user base                       │
│                                                         │
│  Lower Priority (Optional)                              │
│  ─────────────────────────                              │
│  ⬜ Marathi (mr)                                        │
│  ⬜ Gujarati (gu)                                       │
│  ⬜ Kannada (kn)                                        │
│  ⬜ Malayalam (ml)                                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## ⏱️ Time Estimates

| Task | Time | Cumulative |
|------|------|------------|
| Read QUICK_START.md | 5 min | 5 min |
| Record 1 sample | 5 min | 10 min |
| Transfer to PC | 2 min | 12 min |
| Run add_sample.py | 2 min | 14 min |
| Run tests | 1 min | 15 min |
| **Total for 1 sample** | **15 min** | - |
| | | |
| Record 5 samples | 25 min | 25 min |
| Transfer to PC | 5 min | 30 min |
| Run batch script | 5 min | 35 min |
| Run tests | 1 min | 36 min |
| **Total for 5 samples** | **36 min** | - |

---

## 🎉 Success Metrics

### Before vs After

```
┌──────────────────────────────────────────────────────────┐
│                    BEFORE                                │
├──────────────────────────────────────────────────────────┤
│  Audio Source:     Synthetic (gTTS)                      │
│  Accuracy:         70-80% ⚠️                             │
│  Script Issues:    Yes (Indic confusion) ⚠️              │
│  Test Duration:    ~25 seconds ⚠️                        │
│  Reliability:      Medium ⚠️                             │
│  Requirements:     Not met ❌                            │
└──────────────────────────────────────────────────────────┘

                         ⬇️  Add Real Audio

┌──────────────────────────────────────────────────────────┐
│                    AFTER                                 │
├──────────────────────────────────────────────────────────┤
│  Audio Source:     Real Human Speech                     │
│  Accuracy:         85-95% ✅                             │
│  Script Issues:    None ✅                               │
│  Test Duration:    ~15 seconds ✅                        │
│  Reliability:      High ✅                               │
│  Requirements:     Met! ✅                               │
└──────────────────────────────────────────────────────────┘
```

---

## 📚 Quick Reference

| Need | See |
|------|-----|
| Get started fast | QUICK_START.md |
| Recording help | RECORDING_GUIDE.md |
| Technical details | IMPROVED_STT_TESTING.md |
| Overview | SUMMARY.md |
| Check status | `python check_status.py` |
| Add sample | `python add_sample.py` |
| Batch process | `./batch_add_samples.sh` |

---

## 🚀 Ready to Start?

1. **Check current status**: `python check_status.py`
2. **Read quick start**: Open `QUICK_START.md`
3. **Record audio**: Use your phone
4. **Add sample**: `python add_sample.py recording.m4a hi "text" --convert`
5. **Test**: `pytest test_property_stt_accuracy.py -v`
6. **Celebrate**: 85%+ accuracy achieved! 🎉

---

**Let's improve those test results!** 💪
