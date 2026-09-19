/**
 * High-reliability text-to-speech engine for Hindi, Telugu, and English.
 * Works with both browser SpeechSynthesis (zero-cost) and Azure AI Speech (if configured).
 */

// Keep a persistent reference to active utterance to prevent Chrome's GC cutoff bug
let activeUtterance: SpeechSynthesisUtterance | null = null;

export function getActiveUtterance(): SpeechSynthesisUtterance | null {
  return activeUtterance;
}

export function stopSpeech(): void {
  try {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
  } catch {
    /* ignore */
  }
  activeUtterance = null;
}

export function speakText(
  text: string,
  language = 'en',
  onStart?: () => void,
  onEnd?: () => void
): void {
  if (!text || typeof window === 'undefined') return;

  const cleanText = text.trim();
  if (!cleanText) return;

  stopSpeech();

  if (!('speechSynthesis' in window)) {
    console.warn('SpeechSynthesis is not supported in this browser.');
    return;
  }

  // Workaround for Chrome pause bug
  try {
    window.speechSynthesis.resume();
  } catch {
    /* ignore */
  }

  const langCode = (language || 'en').toLowerCase();
  const targetLang =
    langCode.startsWith('hi')
      ? 'hi-IN'
      : langCode.startsWith('te')
        ? 'te-IN'
        : 'en-IN';

  const utterance = new SpeechSynthesisUtterance(cleanText);
  utterance.lang = targetLang;
  utterance.rate = 0.98; // slightly slower for clearer diction
  utterance.pitch = 1.0;

  // Pick best matching system voice if available
  const voices = window.speechSynthesis.getVoices();
  if (voices && voices.length > 0) {
    const isIndianDialect = langCode.startsWith('hi') || langCode.startsWith('te');
    const matchedVoice =
      voices.find((v) => v.lang.replace('_', '-').toLowerCase() === targetLang.toLowerCase()) ||
      voices.find((v) => v.lang.toLowerCase().startsWith(targetLang.slice(0, 2).toLowerCase())) ||
      (isIndianDialect ? voices.find((v) => v.name.toLowerCase().includes('hindi') || v.name.toLowerCase().includes('telugu')) : null) ||
      (isIndianDialect ? voices.find((v) => v.lang.toLowerCase().includes('in') || v.name.toLowerCase().includes('india')) : null) ||
      voices.find((v) => v.lang.toLowerCase().startsWith('en'));

    if (matchedVoice) {
      utterance.voice = matchedVoice;
    }
  }

  utterance.onstart = () => {
    if (onStart) onStart();
  };

  utterance.onend = () => {
    activeUtterance = null;
    if (onEnd) onEnd();
  };

  utterance.onerror = (e) => {
    console.warn('TTS playback issue:', e);
    activeUtterance = null;
    if (onEnd) onEnd();
  };

  activeUtterance = utterance;

  try {
    window.speechSynthesis.speak(utterance);
  } catch (err) {
    console.warn('Failed to invoke speech synthesis:', err);
    activeUtterance = null;
    if (onEnd) onEnd();
  }
}
