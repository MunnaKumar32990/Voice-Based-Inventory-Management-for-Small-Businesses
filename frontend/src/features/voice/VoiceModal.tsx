import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { Check, X, AlertCircle, Pencil, Send } from 'lucide-react';
import { Modal } from '../../components/ui/Modal';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { VoiceVisualizer } from '../../components/ui/VoiceVisualizer';
import { useVoiceStore } from '../../stores/voiceStore';
import { Badge } from '../../components/ui/Badge';
import { api } from '../../lib/api';
import { UNITS } from '../../lib/constants';
import { speakText, stopSpeech } from '../../lib/tts';
import { useQueryClient } from '@tanstack/react-query';

export const VoiceModal: React.FC = () => {
  const { t, i18n } = useTranslation();
  const {
    voiceState,
    transcript,
    parsedCommand,
    interactionId,
    error,
    reset,
    setVoiceState,
    setError,
    setTranscript,
    setCommand,
  } = useVoiceStore();
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [qty, setQty] = useState('');
  const [unit, setUnit] = useState('');
  const [manualText, setManualText] = useState('');
  const [isSpeaking, setIsSpeaking] = useState(false);

  useEffect(() => {
    if (voiceState === 'needs_confirmation' && parsedCommand) {
      setEditing(false);
      setQty(parsedCommand.quantity != null ? String(parsedCommand.quantity) : '');
      setUnit(parsedCommand.unit || '');
    }
  }, [voiceState, parsedCommand]);

  const playVoiceOutput = (text: string, langOverride?: string) => {
    const lang = langOverride || parsedCommand?.detected_language || i18n.language || 'en';
    speakText(
      text,
      lang,
      () => setIsSpeaking(true),
      () => setIsSpeaking(false)
    );
  };

  // Automatically trigger voice output audio playback with animation when completed
  useEffect(() => {
    if (voiceState === 'completed' && parsedCommand?.original_text) {
      playVoiceOutput(parsedCommand.original_text, parsedCommand?.detected_language);
    }
    return () => {
      stopSpeech();
      setIsSpeaking(false);
    };
  }, [voiceState, parsedCommand]);

  const isOpen = [
    'uploading',
    'transcribing',
    'understanding',
    'needs_confirmation',
    'committing',
    'completed',
    'error',
  ].includes(voiceState);

  const handleConfirm = async () => {
    if (!interactionId) {
      setError('Missing command reference. Please try again.');
      return;
    }
    setVoiceState('committing');
    try {
      const overrides: Record<string, unknown> = { confirmed: true };
      if (editing) {
        const q = Number(qty);
        if (!q || q <= 0) {
          setVoiceState('needs_confirmation');
          setError('Quantity must be greater than 0.');
          return;
        }
        overrides.quantity = q;
        if (unit) overrides.unit = unit;
      }
      const res = await api.post(`/voice/commands/${interactionId}/commit`, overrides);
      const commitMsg = res.data?.message;

      await queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      await queryClient.invalidateQueries({ queryKey: ['products'] });
      await queryClient.invalidateQueries({ queryKey: ['transactions'] });
      await queryClient.invalidateQueries({ queryKey: ['alerts'] });
      await queryClient.invalidateQueries({ queryKey: ['balances'] });

      // Prepare natural speech feedback (e.g. "5 kg Rice added successfully")
      const finalMsg =
        commitMsg ||
        `${parsedCommand?.quantity ?? ''} ${parsedCommand?.unit ?? ''} ${parsedCommand?.product ?? ''} ${
          parsedCommand?.action === 'remove' ? 'removed' : 'added'
        } successfully.`;

      setCommand({
        action: parsedCommand?.action || 'add',
        product: res.data?.product_name || parsedCommand?.product || '',
        quantity: parsedCommand?.quantity,
        unit: parsedCommand?.unit,
        confidence: 1,
        original_text: finalMsg,
        detected_language: res.data?.detected_language || parsedCommand?.detected_language,
      });

      setVoiceState('completed');
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Could not save the change. Please try again.';
      setError(typeof msg === 'string' ? msg : 'Could not save the change.');
    }
  };

  const handleCancel = async () => {
    stopSpeech();
    setIsSpeaking(false);
    if (voiceState === 'needs_confirmation' && interactionId) {
      try {
        await api.post(`/voice/commands/${interactionId}/cancel`);
      } catch {
        /* best-effort cancel */
      }
    }
    reset();
  };

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = manualText.trim();
    if (!text) return;

    setTranscript(text);
    setVoiceState('transcribing');
    setManualText('');

    try {
      const lang = i18n.language || 'en';
      const res = await api.post('/voice/commands', {
        transcript: text,
        language: lang,
      });
      const data = res.data;
      const status = (data.status || '').toLowerCase();

      if (status === 'needs_confirmation' && data.command) {
        const c = data.command;
        setCommand(
          {
            action: c.intent === 'STOCK_IN' ? 'add' : 'remove',
            product: c.product_name || c.product_text || '',
            product_id: c.product_id,
            product_name: c.product_name,
            quantity: c.quantity,
            unit: c.unit,
            price: c.price_total ?? undefined,
            confidence: c.confidence ?? 0.8,
            original_text: data.confirmation_text || text,
            detected_language: data.detected_language,
          },
          data.interaction_id
        );
        setVoiceState('needs_confirmation');
      } else if (status === 'answered') {
        const answerText = data.message || String(data.answer || 'Done');
        setCommand(
          {
            action: 'query',
            product: data.product_name || '',
            quantity: data.quantity,
            unit: data.unit,
            confidence: 1,
            original_text: answerText,
            detected_language: data.detected_language,
          },
          data.interaction_id
        );
        setVoiceState('completed');
      } else {
        setError(data.message || 'Could not understand command.');
      }
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Could not process command.';
      setError(typeof msg === 'string' ? msg : 'Could not process command.');
    }
  };

  const isQuery = parsedCommand?.action === 'query';
  const actionLabel =
    isQuery
      ? 'Stock Query'
      : parsedCommand?.action === 'add'
        ? t('inventory.addStock', 'Add Stock')
        : parsedCommand?.action === 'remove'
          ? t('inventory.removeStock', 'Remove Stock')
          : t('voice.confirm', 'Confirm Action');

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleCancel}
      title={
        voiceState === 'needs_confirmation'
          ? actionLabel
          : voiceState === 'error'
            ? t('common.error', 'Notice')
            : voiceState === 'completed'
              ? isQuery
                ? 'Voice Output & Answer'
                : 'Stock Updated'
              : t('voice.processing', 'Processing Voice Command...')
      }
    >
      <div className="space-y-5">
        {/* Transcript Header Area */}
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200/80">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
            {t('voice.youSaid', 'Voice Input')}
          </p>
          <p className="text-lg font-medium text-slate-900 italic">
            &ldquo;{transcript || '...'}&rdquo;
          </p>
        </div>

        {/* Loading States */}
        {(voiceState === 'uploading' ||
          voiceState === 'transcribing' ||
          voiceState === 'understanding' ||
          voiceState === 'committing') && (
          <div className="flex flex-col items-center justify-center py-6">
            <div className="w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mb-4" />
            <p className="text-indigo-600 font-semibold text-base">
              {voiceState === 'committing'
                ? t('voice.saving', 'Updating inventory balance...')
                : t('voice.processing', 'Analyzing speech & inventory...')}
            </p>
          </div>
        )}

        {/* Confirmation State (For Stock In / Out mutations) */}
        {voiceState === 'needs_confirmation' && parsedCommand && (
          <div className="bg-white border-2 border-indigo-100 rounded-2xl p-5 shadow-sm">
            <h4 className="font-semibold text-gray-900 mb-4 text-center">
              {t('voice.verifyAction', 'Please verify this action:')}
            </h4>

            <div className="flex flex-col items-center mb-6">
              <Badge
                variant={
                  parsedCommand.action === 'add'
                    ? 'success'
                    : parsedCommand.action === 'remove'
                      ? 'info'
                      : 'secondary'
                }
              >
                {actionLabel}
              </Badge>

              <div className="mt-4 text-center w-full">
                {editing ? (
                  <div className="grid grid-cols-2 gap-3 w-full max-w-xs mx-auto">
                    <Input
                      label={t('inventory.quantity', 'Quantity')}
                      type="number"
                      min="0"
                      step="any"
                      value={qty}
                      onChange={(e) => setQty(e.target.value)}
                    />
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {t('inventory.unit', 'Unit')}
                      </label>
                      <select
                        value={unit}
                        onChange={(e) => setUnit(e.target.value)}
                        className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm min-h-[44px] px-3 border bg-white"
                      >
                        {UNITS.map((u) => (
                          <option key={u.value} value={u.value}>
                            {u.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                ) : (
                  <>
                    <span className="text-4xl font-extrabold text-gray-900 block">
                      {parsedCommand.quantity ?? '?'} {parsedCommand.unit ?? ''}
                    </span>
                    <span className="text-2xl font-semibold text-indigo-600 block mt-1">
                      {parsedCommand.product}
                    </span>
                  </>
                )}
              </div>
            </div>

            <div className="flex justify-center mb-4">
              <button
                type="button"
                onClick={() => setEditing((v) => !v)}
                className="text-sm font-medium text-indigo-600 hover:text-indigo-800 inline-flex items-center"
              >
                <Pencil className="h-4 w-4 mr-1" />
                {editing ? t('common.cancel', 'Cancel Edit') : t('voice.edit', 'Edit values')}
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 mt-2">
              <Button
                variant="secondary"
                onClick={handleCancel}
                className="w-full text-red-600 border-red-200 hover:bg-red-50"
              >
                <X className="h-5 w-5 mr-2" />
                {t('common.cancel', 'Cancel')}
              </Button>
              <Button
                variant="primary"
                onClick={handleConfirm}
                className="w-full bg-green-600 hover:bg-green-700 text-white"
              >
                <Check className="h-5 w-5 mr-2" />
                {t('common.confirm', 'Confirm & Speak')}
              </Button>
            </div>
          </div>
        )}

        {/* Voice Output & Animation State */}
        {voiceState === 'completed' && (
          <div className="bg-gradient-to-b from-indigo-50/80 to-white border-2 border-indigo-200 rounded-2xl p-6 text-center shadow-xs">
            <h3 className="text-xl font-bold text-gray-900 mb-1">
              {isQuery ? 'Voice Answer' : 'Inventory Updated'}
            </h3>

            {/* Sound Wave Frequency Visualizer & Glow Orb */}
            <VoiceVisualizer
              isSpeaking={isSpeaking}
              onReplay={() =>
                parsedCommand?.original_text && playVoiceOutput(parsedCommand.original_text)
              }
              onStop={() => {
                stopSpeech();
                setIsSpeaking(false);
              }}
            />

            {/* Voice Output Text Card */}
            <div className="bg-white p-4 rounded-xl border border-indigo-100 shadow-xs my-3 text-left">
              <p className="text-xs font-semibold uppercase tracking-wider text-indigo-500 mb-1">
                Voice Output
              </p>
              <p className="text-lg font-bold text-indigo-950 leading-relaxed">
                {parsedCommand?.original_text || 'Action completed successfully.'}
              </p>
            </div>

            <div className="flex items-center justify-center gap-3 mt-4">
              <Button
                variant="primary"
                onClick={handleCancel}
                className="py-2 px-8 text-base bg-indigo-600 hover:bg-indigo-700"
              >
                {t('common.done', 'Done')}
              </Button>
            </div>
          </div>
        )}

        {/* Error / Fallback State */}
        {voiceState === 'error' && (
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 text-center">
            <AlertCircle className="h-12 w-12 text-amber-500 mx-auto mb-3" />
            <p className="text-amber-900 font-medium text-base mb-4">
              {error || t('voice.notUnderstood', 'Could not understand the command.')}
            </p>

            {/* Quick Type fallback */}
            <form onSubmit={handleManualSubmit} className="mt-4 mb-4">
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder='Type here (e.g., "Add 5 bags rice" or "Rice stock?")'
                  value={manualText}
                  onChange={(e) => setManualText(e.target.value)}
                  className="flex-1 rounded-xl border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
                />
                <Button variant="primary" type="submit" className="px-3">
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </form>

            <div className="flex flex-col sm:flex-row gap-2 justify-center">
              <Button variant="secondary" onClick={handleCancel}>
                {t('voice.tryAgain', 'Close')}
              </Button>
              <Link to="/manual" onClick={handleCancel}>
                <Button variant="secondary" className="w-full">
                  {t('voice.manualEntry', 'Manual Form')}
                </Button>
              </Link>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
};
