// Chat interface module
import { API } from './api.js';
import { playAudioResponse } from './voice.js';

let sessionId = null;
let currentLanguage = 'hi';
let messageHistory = [];

export function initChat(app) {
  console.log('Initializing chat interface...');
  
  const textInput = document.getElementById('textInput');
  const sendBtn = document.getElementById('sendBtn');
  const chatMessages = document.getElementById('chatMessages');
  
  if (!textInput || !sendBtn || !chatMessages) {
    console.error('Chat elements not found');
    return;
  }

  // Create session
  createChatSession(app);

  // Send button click handler
  sendBtn.addEventListener('click', () => {
    sendMessage(app);
  });

  // Enter key handler
  textInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(app);
    }
  });

  // Input validation
  textInput.addEventListener('input', () => {
    sendBtn.disabled = !textInput.value.trim();
  });

  // Initial state
  sendBtn.disabled = true;

  // Display welcome message
  displayWelcomeMessage();

  console.log('Chat interface initialized');
}

async function createChatSession(app) {
  try {
    currentLanguage = app.currentLanguage || 'hi';
    const response = await API.createSession(currentLanguage);
    sessionId = response.session_id;
    console.log('Chat session created:', sessionId);
  } catch (error) {
    console.error('Failed to create chat session:', error);
    // Continue without session (stateless mode)
  }
}

function displayWelcomeMessage() {
  const welcomeMessages = {
    hi: 'नमस्ते! मैं भारत सहायक हूं। मैं आपकी कैसे मदद कर सकता हूं?',
    en: 'Hello! I am BharatSahayak. How can I help you?',
    bn: 'নমস্কার! আমি ভারত সহায়ক। আমি আপনাকে কীভাবে সাহায্য করতে পারি?',
    te: 'నమస్కారం! నేను భారత సహాయక్. నేను మీకు ఎలా సహాయం చేయగలను?',
    mr: 'नमस्कार! मी भारत सहायक आहे. मी तुम्हाला कशी मदत करू शकतो?',
    ta: 'வணக்கம்! நான் பாரத சஹாயக். நான் உங்களுக்கு எப்படி உதவ முடியும்?',
    gu: 'નમસ્તે! હું ભારત સહાયક છું. હું તમને કેવી રીતે મદદ કરી શકું?',
    kn: 'ನಮಸ್ಕಾರ! ನಾನು ಭಾರತ ಸಹಾಯಕ. ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?'
  };

  const message = welcomeMessages[currentLanguage] || welcomeMessages.hi;
  
  addMessage({
    text: message,
    sender: 'assistant',
    timestamp: new Date()
  });
}

async function sendMessage(app) {
  const textInput = document.getElementById('textInput');
  const messageText = textInput.value.trim();
  
  if (!messageText) {
    return;
  }

  // Clear input
  textInput.value = '';
  const sendBtn = document.getElementById('sendBtn');
  sendBtn.disabled = true;

  // Add user message to chat
  addMessage({
    text: messageText,
    sender: 'user',
    timestamp: new Date()
  });

  // Show loading state
  const loadingId = addLoadingMessage();

  try {
    // Send to backend
    currentLanguage = app.currentLanguage || 'hi';
    const response = await API.sendMessage(messageText, sessionId, currentLanguage);
    
    // Remove loading message
    removeLoadingMessage(loadingId);

    // Add assistant response
    addMessage({
      text: response.answer || response.response,
      sender: 'assistant',
      timestamp: new Date(),
      sources: response.sources
    });

    // Store in history
    messageHistory.push({
      user: messageText,
      assistant: response.answer || response.response,
      timestamp: new Date()
    });

    // Optionally play audio response
    if (app.autoPlayAudio) {
      try {
        await playAudioResponse(response.answer || response.response, currentLanguage);
      } catch (error) {
        console.error('Failed to play audio response:', error);
      }
    }

    // Record interaction event
    try {
      await API.recordEvent('query_submitted', {
        query: messageText,
        language: currentLanguage,
        session_id: sessionId
      });
    } catch (error) {
      console.error('Failed to record event:', error);
    }

  } catch (error) {
    console.error('Failed to send message:', error);
    
    // Remove loading message
    removeLoadingMessage(loadingId);
    
    // Show error message
    addMessage({
      text: 'Sorry, I encountered an error. Please try again.',
      sender: 'assistant',
      timestamp: new Date(),
      isError: true
    });
  }
}

function addMessage(message) {
  const chatMessages = document.getElementById('chatMessages');
  
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${message.sender}`;
  
  // Avatar
  const avatar = document.createElement('div');
  avatar.className = 'message-avatar';
  avatar.textContent = message.sender === 'user' ? 'U' : 'B';
  
  // Content
  const content = document.createElement('div');
  content.className = 'message-content';
  
  const text = document.createElement('div');
  text.textContent = message.text;
  content.appendChild(text);
  
  // Sources (if available)
  if (message.sources && message.sources.length > 0) {
    const sources = document.createElement('div');
    sources.className = 'message-sources';
    sources.innerHTML = '<small>Sources: ' + 
      message.sources.map(s => s.title || s.source).join(', ') + 
      '</small>';
    content.appendChild(sources);
  }
  
  // Timestamp
  const time = document.createElement('div');
  time.className = 'message-time';
  time.textContent = formatTime(message.timestamp);
  content.appendChild(time);
  
  messageDiv.appendChild(avatar);
  messageDiv.appendChild(content);
  
  chatMessages.appendChild(messageDiv);
  
  // Scroll to bottom
  chatMessages.scrollTop = chatMessages.scrollHeight;
  
  return messageDiv;
}

function addLoadingMessage() {
  const chatMessages = document.getElementById('chatMessages');
  
  const loadingDiv = document.createElement('div');
  loadingDiv.className = 'message assistant loading-message';
  loadingDiv.id = `loading-${Date.now()}`;
  
  const avatar = document.createElement('div');
  avatar.className = 'message-avatar';
  avatar.textContent = 'B';
  
  const content = document.createElement('div');
  content.className = 'message-content';
  content.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
  
  loadingDiv.appendChild(avatar);
  loadingDiv.appendChild(content);
  
  chatMessages.appendChild(loadingDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  
  return loadingDiv.id;
}

function removeLoadingMessage(loadingId) {
  const loadingMsg = document.getElementById(loadingId);
  if (loadingMsg) {
    loadingMsg.remove();
  }
}

function formatTime(date) {
  const hours = date.getHours().toString().padStart(2, '0');
  const minutes = date.getMinutes().toString().padStart(2, '0');
  return `${hours}:${minutes}`;
}

export function clearChat() {
  const chatMessages = document.getElementById('chatMessages');
  chatMessages.innerHTML = '';
  messageHistory = [];
  displayWelcomeMessage();
}

export function getMessageHistory() {
  return messageHistory;
}

export function setLanguage(language) {
  currentLanguage = language;
}

export default {
  initChat,
  clearChat,
  getMessageHistory,
  setLanguage
};
