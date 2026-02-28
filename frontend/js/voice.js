// Voice interface module for recording and playback
import { API } from './api.js';

let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let currentLanguage = 'hi';

export function initVoice(app) {
  console.log('Initializing voice interface...');
  
  const voiceBtn = document.getElementById('voiceBtn');
  
  if (!voiceBtn) {
    console.error('Voice button not found');
    return;
  }

  // Check for browser support
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    console.warn('Voice recording not supported in this browser');
    voiceBtn.disabled = true;
    voiceBtn.title = 'Voice recording not supported';
    return;
  }

  // Voice button click handler
  voiceBtn.addEventListener('click', async () => {
    if (isRecording) {
      stopRecording();
    } else {
      await startRecording(app);
    }
  });

  console.log('Voice interface initialized');
}

async function startRecording(app) {
  try {
    console.log('Requesting microphone access...');
    
    const stream = await navigator.mediaDevices.getUserMedia({ 
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      } 
    });

    // Create media recorder
    const options = { mimeType: 'audio/webm' };
    
    // Fallback for browsers that don't support webm
    if (!MediaRecorder.isTypeSupported(options.mimeType)) {
      options.mimeType = 'audio/mp4';
      if (!MediaRecorder.isTypeSupported(options.mimeType)) {
        options.mimeType = '';
      }
    }

    mediaRecorder = new MediaRecorder(stream, options);
    audioChunks = [];

    mediaRecorder.addEventListener('dataavailable', (event) => {
      if (event.data.size > 0) {
        audioChunks.push(event.data);
      }
    });

    mediaRecorder.addEventListener('stop', async () => {
      console.log('Recording stopped, processing audio...');
      
      // Stop all tracks
      stream.getTracks().forEach(track => track.stop());
      
      // Create audio blob
      const audioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType });
      
      // Process the recording
      await processRecording(audioBlob, app);
    });

    // Start recording
    mediaRecorder.start();
    isRecording = true;
    updateVoiceButton(true);
    
    console.log('Recording started');
    
  } catch (error) {
    console.error('Failed to start recording:', error);
    alert('Failed to access microphone. Please check permissions.');
  }
}

function stopRecording() {
  if (mediaRecorder && isRecording) {
    console.log('Stopping recording...');
    mediaRecorder.stop();
    isRecording = false;
    updateVoiceButton(false);
  }
}

function updateVoiceButton(recording) {
  const voiceBtn = document.getElementById('voiceBtn');
  
  if (recording) {
    voiceBtn.classList.add('recording');
    voiceBtn.setAttribute('aria-label', 'Stop Recording');
  } else {
    voiceBtn.classList.remove('recording');
    voiceBtn.setAttribute('aria-label', 'Voice Input');
  }
}

async function processRecording(audioBlob, app) {
  try {
    app.showLoading('Transcribing audio...');
    
    // Get current language
    currentLanguage = app.currentLanguage || 'hi';
    
    // Send to backend for transcription
    const result = await API.voiceToText(audioBlob, currentLanguage);
    
    console.log('Transcription result:', result);
    
    if (result.text) {
      // Add transcribed text to chat input
      const textInput = document.getElementById('textInput');
      textInput.value = result.text;
      
      // Optionally auto-send
      if (result.confidence > 0.8) {
        // High confidence, auto-send
        const sendBtn = document.getElementById('sendBtn');
        sendBtn.click();
      }
    } else {
      throw new Error('No transcription received');
    }
    
  } catch (error) {
    console.error('Failed to process recording:', error);
    app.showError('Failed to transcribe audio. Please try again.');
  } finally {
    app.hideLoading();
  }
}

export async function playAudioResponse(text, language = 'hi') {
  try {
    console.log('Generating audio for text:', text);
    
    // Get audio from backend
    const audioBlob = await API.textToVoice(text, language);
    
    // Create audio element and play
    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);
    
    audio.addEventListener('ended', () => {
      URL.revokeObjectURL(audioUrl);
    });
    
    audio.addEventListener('error', (error) => {
      console.error('Audio playback error:', error);
    });
    
    await audio.play();
    
    return audio;
    
  } catch (error) {
    console.error('Failed to play audio response:', error);
    throw error;
  }
}

export function stopAudioPlayback() {
  // Stop all audio elements
  document.querySelectorAll('audio').forEach(audio => {
    audio.pause();
    audio.currentTime = 0;
  });
}

// Language selector integration
export function setVoiceLanguage(language) {
  currentLanguage = language;
  console.log('Voice language set to:', language);
}

// Audio visualization (optional enhancement)
export function createAudioVisualizer(stream) {
  const audioContext = new (window.AudioContext || window.webkitAudioContext)();
  const analyser = audioContext.createAnalyser();
  const source = audioContext.createMediaStreamSource(stream);
  
  source.connect(analyser);
  analyser.fftSize = 256;
  
  const bufferLength = analyser.frequencyBinCount;
  const dataArray = new Uint8Array(bufferLength);
  
  return {
    analyser,
    dataArray,
    bufferLength,
    audioContext
  };
}

export default {
  initVoice,
  playAudioResponse,
  stopAudioPlayback,
  setVoiceLanguage,
  createAudioVisualizer
};
