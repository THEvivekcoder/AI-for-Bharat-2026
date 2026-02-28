#!/bin/bash
# Batch add multiple audio samples
# Usage: ./batch_add_samples.sh

echo "🎙️  Batch Audio Sample Processor"
echo "================================"
echo ""

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ FFmpeg not found. Please install it first:"
    echo "   macOS: brew install ffmpeg"
    echo "   Linux: sudo apt-get install ffmpeg"
    exit 1
fi

# Example recordings with metadata
# Modify this array with your actual recordings
declare -A SAMPLES=(
    # Format: "filename|language|text"
    # ["recording1.m4a"]="hi|नमस्ते मेरा नाम राज है"
    # ["recording2.m4a"]="en|Hello my name is John"
    # ["recording3.m4a"]="bn|আমার নাম রাজ"
)

# Check if samples array is empty
if [ ${#SAMPLES[@]} -eq 0 ]; then
    echo "⚠️  No samples configured in this script."
    echo ""
    echo "To use this script:"
    echo "1. Edit batch_add_samples.sh"
    echo "2. Add your recordings to the SAMPLES array"
    echo "3. Run: ./batch_add_samples.sh"
    echo ""
    echo "Example:"
    echo '  ["recording1.m4a"]="hi|नमस्ते मेरा नाम राज है"'
    echo '  ["recording2.m4a"]="en|Hello my name is John"'
    echo ""
    echo "Or use the interactive mode below:"
    echo ""
    
    # Interactive mode
    read -p "Would you like to add samples interactively? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
    
    echo ""
    echo "📁 Looking for audio files in current directory..."
    
    # Find audio files
    audio_files=(*.m4a *.mp3 *.wav *.aac 2>/dev/null)
    
    if [ ${#audio_files[@]} -eq 0 ] || [ ! -e "${audio_files[0]}" ]; then
        echo "❌ No audio files found in current directory"
        echo "   Supported formats: .m4a, .mp3, .wav, .aac"
        exit 1
    fi
    
    echo "Found ${#audio_files[@]} audio file(s):"
    for i in "${!audio_files[@]}"; do
        echo "  $((i+1)). ${audio_files[$i]}"
    done
    echo ""
    
    # Process each file interactively
    for file in "${audio_files[@]}"; do
        [ -e "$file" ] || continue
        
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "📄 File: $file"
        echo ""
        
        read -p "Process this file? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "⏭️  Skipped"
            echo ""
            continue
        fi
        
        # Get language
        echo ""
        echo "Select language:"
        echo "  1. Hindi (hi)"
        echo "  2. English (en)"
        echo "  3. Bengali (bn)"
        echo "  4. Telugu (te)"
        echo "  5. Marathi (mr)"
        echo "  6. Tamil (ta)"
        echo "  7. Gujarati (gu)"
        echo "  8. Kannada (kn)"
        echo "  9. Malayalam (ml)"
        read -p "Enter number (1-9): " lang_choice
        
        case $lang_choice in
            1) language="hi" ;;
            2) language="en" ;;
            3) language="bn" ;;
            4) language="te" ;;
            5) language="mr" ;;
            6) language="ta" ;;
            7) language="gu" ;;
            8) language="kn" ;;
            9) language="ml" ;;
            *) echo "❌ Invalid choice"; continue ;;
        esac
        
        # Get transcription
        echo ""
        read -p "Enter transcription text: " text
        
        if [ -z "$text" ]; then
            echo "❌ Text cannot be empty"
            continue
        fi
        
        # Add sample
        echo ""
        echo "🔄 Processing..."
        python add_sample.py "$file" "$language" "$text" --convert
        
        if [ $? -eq 0 ]; then
            echo "✅ Successfully added!"
        else
            echo "❌ Failed to add sample"
        fi
        echo ""
    done
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ Batch processing complete!"
    exit 0
fi

# Batch mode (using configured samples)
echo "Processing ${#SAMPLES[@]} sample(s)..."
echo ""

success_count=0
fail_count=0

for filename in "${!SAMPLES[@]}"; do
    IFS='|' read -r language text <<< "${SAMPLES[$filename]}"
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📄 Processing: $filename"
    echo "   Language: $language"
    echo "   Text: $text"
    echo ""
    
    if [ ! -f "$filename" ]; then
        echo "❌ File not found: $filename"
        ((fail_count++))
        echo ""
        continue
    fi
    
    # Add sample using helper script
    python add_sample.py "$filename" "$language" "$text" --convert
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully added!"
        ((success_count++))
    else
        echo "❌ Failed to add sample"
        ((fail_count++))
    fi
    echo ""
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Summary:"
echo "   ✅ Success: $success_count"
echo "   ❌ Failed: $fail_count"
echo "   📁 Total: ${#SAMPLES[@]}"
echo ""

if [ $success_count -gt 0 ]; then
    echo "🧪 Test your samples:"
    echo "   pytest .kiro/specs/bharatsahayak/tests/test_property_stt_accuracy.py -v"
fi
