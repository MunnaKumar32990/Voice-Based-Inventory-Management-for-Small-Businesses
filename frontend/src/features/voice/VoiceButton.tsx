import { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Mic, Sparkles } from 'lucide-react';
import { useVoiceStore } from '../../stores/voiceStore';
import { startRecording } from '../../lib/audio';
import { api } from '../../lib/api';
import type { BackendVoicePreview } from '../../types/voice';

// Minimal Web Speech API typings
interface SpeechRecognitionResultLike {
  transcript: string;
}
interface SpeechRecognitionEventLike {
  results: ArrayLike<ArrayLike<SpeechRecognitionResultLike>>;
}
interface SpeechRecognitionLike {
  lang: string;
  interimResults: boolean;
  maxAlternatives: number;
  onresult: ((ev: SpeechRecognitionEventLike) => void) | null;
  onerror: ((ev: { error?: string }) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
}
declare global {
  interface Window {
    SpeechRecognition?: new () => SpeechRecognitionLike;
    webkitSpeechRecognition?: new () => SpeechRecognitionLike;
  }
}

function intentToAction(intent?: string): 'add' | 'remove' | 'query' | 'unknown' {
  if (intent === 'STOCK_IN') return 'add';
  if (intent === 'STOCK_OUT') return 'remove';
  if (intent === 'STOCK_QUERY' || intent === 'LOW_STOCK_QUERY') return 'query';
  return 'unknown';
}

const LANG_MAP: Record<string, string> = {
  en: 'en-IN',
  hi: 'hi-IN',
  te: 'te-IN',
};

export const VoiceButton: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { voiceState, setVoiceState, setTranscript, setCommand, setError } = useVoiceStore();
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const recorderRef = useRef<{ stop: () => Promise<Blob> } | null>(null);
  const timersRef = useRef<number[]>([]);

  const azureMode = (import.meta.env.VITE_SPEECH_PROVIDER as string | undefined || 'webspeech').toLowerCase() === 'azure';

  const isRecording = voiceState === 'listening' || voiceState === 'recording';
  const isProcessing =
    voiceState === 'transcribing' ||
    voiceState === 'understanding' ||
    voiceState === 'uploading' ||
    voiceState === 'checking_db';

  useEffect(() => {
    const timers = timersRef.current;
    return () => {
      timers.forEach((id) => window.clearTimeout(id));
      try {
        recognitionRef.current?.abort();
      } catch {
        /* noop */
      }
      try {
        void recorderRef.current?.stop();
      } catch {
        /* noop */
      }
    };
  }, []);

  const later = (fn: () => void, ms: number) => {
    const id = window.setTimeout(fn, ms);
    timersRef.current.push(id);
  };

  const sendTranscript = async (transcript: string) => {
    const text = transcript.trim();
    if (!text) {
      setError('Did not hear anything. Please try again.');
      return;
    }
    setTranscript(text);
    setVoiceState('transcribing');

    // Smooth step-by-step pipeline progression
    later(() => {
      if (useVoiceStore.getState().voiceState === 'transcribing') {
        useVoiceStore.getState().setVoiceState('understanding');
      }
    }, 250);
    later(() => {
      if (useVoiceStore.getState().voiceState === 'understanding') {
        useVoiceStore.getState().setVoiceState('checking_db');
      }
    }, 650);

    try {
      const lang = i18n.language || 'en';
      const res = await api.post<BackendVoicePreview>('/voice/commands', {
        transcript: text,
        language: lang,
      });
      const data = res.data;
      handleBackendResponse(data, text);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string; error?: { message?: string } } } })?.response?.data?.detail ||
        (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message ||
        'Voice processing failed. Check your connection or type the command manually.';
      setError(typeof msg === 'string' ? msg : 'Voice processing failed.');
    }
  };

  const handleBackendResponse = (data: BackendVoicePreview, fallbackTranscript: string) => {
    const status = (data.status || '').toLowerCase();
    if (status === 'needs_confirmation' && data.command) {
      const c = data.command;
      setTranscript(data.transcript || fallbackTranscript);
      setCommand(
        {
          action: intentToAction(c.intent),
          product: c.product_name || c.product_text || '',
          product_id: c.product_id,
          product_name: c.product_name,
          quantity: c.quantity,
          unit: c.unit,
          price: c.price_total ?? undefined,
          confidence: c.confidence ?? 0.8,
          original_text: data.transcript || fallbackTranscript,
          detected_language: data.detected_language,
        },
        data.interaction_id
      );
      setVoiceState('needs_confirmation');
    } else if (status === 'answered') {
      const answerText =
        data.message ||
        data.display_text ||
        (typeof data.answer === 'string'
          ? data.answer
          : `Answer: ${JSON.stringify(data.answer)}`);
      setTranscript(data.transcript || fallbackTranscript);
      setCommand(
        {
          action: 'query',
          product: data.product_name || '',
          quantity: data.quantity,
          unit: data.unit,
          confidence: 1,
          original_text: answerText,
          detected_language: data.detected_language,
          query_type: data.query_type,
          title: data.title,
          display_text: data.display_text,
          structured_data: data.structured_data,
        },
        data.interaction_id
      );
      setVoiceState('completed');
    } else if (status === 'clarification_needed' || status === 'error') {
      const candidates = (data.candidates || []).map((c) => c.name).join(', ');
      setError(
        data.message
          ? candidates
            ? `${data.message} ${candidates}`
            : data.message
          : 'I did not understand that. Try "How much rice is available?"'
      );
    } else {
      setError(data.message || 'Unexpected response from server.');
    }
  };

  const startListening = () => {
    if (azureMode) {
      void startListeningAzure();
      return;
    }
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const lang = LANG_MAP[i18n.language] || 'en-IN';

    if (!SR) {
      const typed = window.prompt('Type your voice command (e.g. "How much rice do I have?"):');
      if (typed === null) return;
      setVoiceState('uploading');
      void sendTranscript(typed);
      return;
    }

    try {
      const rec = new SR();
      recognitionRef.current = rec;
      rec.lang = lang;
      rec.interimResults = false;
      rec.maxAlternatives = 1;
      setVoiceState('listening');

      rec.onresult = (ev) => {
        try {
          const transcript = ev.results[0][0].transcript;
          setVoiceState('uploading');
          void sendTranscript(transcript);
        } catch {
          setError('Could not read the speech result. Please try again.');
        }
      };
      rec.onerror = (ev) => {
        if (ev.error === 'not-allowed' || ev.error === 'service-not-allowed') {
          setError('Microphone blocked. Allow microphone access or type the command instead.');
        } else if (ev.error === 'no-speech') {
          setError('Did not hear anything. Please try again.');
        } else {
          setError('Speech recognition failed. Please try again or type the command.');
        }
      };
      rec.onend = () => {
        const s = useVoiceStore.getState().voiceState;
        if (s === 'listening' || s === 'recording') {
          useVoiceStore.getState().setVoiceState('idle');
        }
      };
      rec.start();
      setVoiceState('recording');
    } catch {
      setError('Could not start microphone. Please check permissions.');
    }
  };

  const startListeningAzure = async () => {
    try {
      setVoiceState('listening');
      const handle = await startRecording();
      recorderRef.current = handle;
      setVoiceState('recording');
      later(() => {
        if (useVoiceStore.getState().voiceState === 'recording') {
          void finishAzureRecording();
        }
      }, 13000);
    } catch {
      setError('Could not start microphone. Allow access or type the command instead.');
    }
  };

  const finishAzureRecording = async () => {
    const handle = recorderRef.current;
    recorderRef.current = null;
    if (!handle) {
      setVoiceState('idle');
      return;
    }
    setVoiceState('uploading');
    try {
      const blob = await handle.stop();
      const form = new FormData();
      form.append('file', blob, 'voice.webm');
      const lang = i18n.language || 'en';
      form.append('language_hint', lang);
      const res = await api.post<{ transcript: string }>('/voice/transcribe', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      await sendTranscript(res.data.transcript || '');
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Azure transcription failed. Check SPEECH_PROVIDER=azure + keys in backend/.env.';
      setError(typeof msg === 'string' ? msg : 'Transcription failed.');
    }
  };

  const handleClick = () => {
    if (voiceState === 'idle' || voiceState === 'error' || voiceState === 'completed') {
      startListening();
    } else if (isRecording) {
      if (azureMode) {
        void finishAzureRecording();
        return;
      }
      try {
        recognitionRef.current?.stop();
      } catch {
        /* noop */
      }
    }
  };

  return (
    <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50 flex flex-col items-center">
      {/* Floating State Tooltip */}
      <div className="mb-2.5 whitespace-nowrap bg-slate-900/90 backdrop-blur-md text-white text-xs font-bold py-1.5 px-3.5 rounded-full shadow-lg border border-slate-700/60 pointer-events-none flex items-center gap-1.5 animate-in fade-in">
        {isRecording ? (
          <>
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
            <span>Listening to you...</span>
          </>
        ) : isProcessing ? (
          <>
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            <span>Understanding request...</span>
          </>
        ) : (
          <>
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>{t('voice.tapToSpeak', 'Tap to Talk')}</span>
          </>
        )}
      </div>

      {/* Hero Animated Microphone Action Button */}
      <button
        onClick={handleClick}
        aria-label={t('voice.tapToSpeak', 'Tap to Talk')}
        aria-pressed={isRecording}
        className={`relative flex items-center justify-center w-20 h-20 rounded-full shadow-2xl transition-all duration-300 focus:outline-none focus:ring-4 focus:ring-indigo-300 cursor-pointer ${
          isRecording
            ? 'bg-rose-600 scale-105 shadow-rose-500/50'
            : isProcessing
              ? 'bg-amber-500 shadow-amber-500/40'
              : 'bg-gradient-to-tr from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 hover:scale-105 shadow-indigo-500/40'
        }`}
      >
        {isProcessing ? (
          <div className="flex space-x-1.5">
            <div className="w-2.5 h-2.5 bg-white rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <div className="w-2.5 h-2.5 bg-white rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <div className="w-2.5 h-2.5 bg-white rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        ) : (
          <Mic className="h-9 w-9 text-white" />
        )}

        {/* Multi-Ring Ripple Animation When Listening */}
        {isRecording && (
          <>
            <span className="absolute inline-flex h-full w-full rounded-full bg-rose-500 opacity-60 animate-ping pointer-events-none" />
            <span
              className="absolute inline-flex h-28 w-28 rounded-full bg-rose-400 opacity-40 animate-ping pointer-events-none"
              style={{ animationDelay: '300ms' }}
            />
          </>
        )}
      </button>
    </div>
  );
};
