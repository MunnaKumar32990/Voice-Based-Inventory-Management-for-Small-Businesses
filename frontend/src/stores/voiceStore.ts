import { create } from 'zustand';
import type { VoiceState, ParsedCommand } from '../types/voice';

interface VoiceStore {
  voiceState: VoiceState;
  transcript: string;
  parsedCommand: ParsedCommand | null;
  interactionId: string | null;
  error: string | null;
  setVoiceState: (state: VoiceState) => void;
  setTranscript: (transcript: string) => void;
  setCommand: (command: ParsedCommand, interactionId?: string) => void;
  setError: (error: string) => void;
  reset: () => void;
}

export const useVoiceStore = create<VoiceStore>((set) => ({
  voiceState: 'idle',
  transcript: '',
  parsedCommand: null,
  interactionId: null,
  error: null,
  setVoiceState: (state) => set({ voiceState: state, error: null }),
  setTranscript: (transcript) => set({ transcript }),
  setCommand: (parsedCommand, interactionId) => 
    set((state) => ({ 
      parsedCommand, 
      interactionId: interactionId || state.interactionId 
    })),
  setError: (error) => set({ error, voiceState: 'error' }),
  reset: () => set({
    voiceState: 'idle',
    transcript: '',
    parsedCommand: null,
    interactionId: null,
    error: null,
  }),
}));
