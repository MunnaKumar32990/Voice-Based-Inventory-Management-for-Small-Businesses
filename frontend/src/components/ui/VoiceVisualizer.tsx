import React from 'react';
import { Volume2, VolumeX } from 'lucide-react';

interface VoiceVisualizerProps {
  isSpeaking: boolean;
  onReplay?: () => void;
  onStop?: () => void;
}

export const VoiceVisualizer: React.FC<VoiceVisualizerProps> = ({
  isSpeaking,
  onReplay,
  onStop,
}) => {
  return (
    <div className="flex flex-col items-center justify-center my-4 py-3">
      {/* Central Glowing Voice Orb */}
      <div className="relative flex items-center justify-center mb-4">
        {/* Pulsing halo rings when speaking */}
        {isSpeaking && (
          <>
            <span className="absolute w-24 h-24 rounded-full bg-indigo-400/30 animate-ping pointer-events-none" />
            <span className="absolute w-20 h-20 rounded-full bg-indigo-500/40 animate-pulse pointer-events-none" />
          </>
        )}

        {/* Main Orb */}
        <div
          className={`w-16 h-16 rounded-full flex items-center justify-center transition-all duration-300 ${
            isSpeaking
              ? 'bg-gradient-to-tr from-indigo-600 to-violet-500 text-white shadow-lg animate-voice-glow scale-105'
              : 'bg-indigo-100 text-indigo-600'
          }`}
        >
          {isSpeaking ? (
            <Volume2 className="h-8 w-8 animate-bounce" />
          ) : (
            <Volume2 className="h-8 w-8" />
          )}
        </div>
      </div>

      {/* Rhythmic Sound Wave Frequency Bars */}
      <div className="flex items-center justify-center gap-1.5 h-10 px-4 py-1 bg-slate-100/80 rounded-full border border-slate-200/60 shadow-inner">
        <span
          className={`w-1.5 rounded-full transition-all duration-300 ${
            isSpeaking ? 'bg-indigo-600 animate-soundwave-1' : 'h-2 bg-slate-400'
          }`}
        />
        <span
          className={`w-1.5 rounded-full transition-all duration-300 ${
            isSpeaking ? 'bg-violet-600 animate-soundwave-2' : 'h-2.5 bg-slate-400'
          }`}
        />
        <span
          className={`w-1.5 rounded-full transition-all duration-300 ${
            isSpeaking ? 'bg-indigo-500 animate-soundwave-3' : 'h-3 bg-slate-400'
          }`}
        />
        <span
          className={`w-1.5 rounded-full transition-all duration-300 ${
            isSpeaking ? 'bg-indigo-600 animate-soundwave-4' : 'h-4 bg-slate-400'
          }`}
        />
        <span
          className={`w-1.5 rounded-full transition-all duration-300 ${
            isSpeaking ? 'bg-violet-500 animate-soundwave-5' : 'h-3 bg-slate-400'
          }`}
        />
        <span
          className={`w-1.5 rounded-full transition-all duration-300 ${
            isSpeaking ? 'bg-indigo-600 animate-soundwave-6' : 'h-2.5 bg-slate-400'
          }`}
        />
        <span
          className={`w-1.5 rounded-full transition-all duration-300 ${
            isSpeaking ? 'bg-indigo-400 animate-soundwave-7' : 'h-2 bg-slate-400'
          }`}
        />
      </div>

      {/* State Text & Control Buttons */}
      <div className="flex items-center gap-2 mt-3">
        {isSpeaking ? (
          <div className="flex items-center gap-2">
            <span className="flex h-2.5 w-2.5 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500" />
            </span>
            <span className="text-xs font-semibold uppercase tracking-wider text-indigo-600">
              Speaking response...
            </span>
            {onStop && (
              <button
                type="button"
                onClick={onStop}
                className="ml-2 text-xs text-slate-500 hover:text-red-600 flex items-center gap-1 p-1 hover:bg-slate-100 rounded"
                title="Stop Speaking"
              >
                <VolumeX className="h-3.5 w-3.5" />
                Stop
              </button>
            )}
          </div>
        ) : (
          onReplay && (
            <button
              type="button"
              onClick={onReplay}
              className="inline-flex items-center text-xs font-medium text-indigo-700 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 rounded-full px-3 py-1 transition-colors"
            >
              <Volume2 className="h-3.5 w-3.5 mr-1" />
              Play Voice Again
            </button>
          )
        )}
      </div>
    </div>
  );
};
