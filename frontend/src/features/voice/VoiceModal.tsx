import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import {
  Check,
  X,
  AlertCircle,
  Pencil,
  Send,
  Package,
  Activity,
  Clock,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  ArrowDownLeft,
  ArrowUpRight,
  Database,
  Brain,
  Sparkles,
  Mic,
} from 'lucide-react';
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
    'checking_db',
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

  const handleCancel = () => {
    stopSpeech();
    setIsSpeaking(false);
    if (voiceState === 'needs_confirmation' && interactionId) {
      try {
        void api.post(`/voice/commands/${interactionId}/cancel`);
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

    // Smooth conversational progression
    setTimeout(() => {
      if (useVoiceStore.getState().voiceState === 'transcribing') {
        useVoiceStore.getState().setVoiceState('understanding');
      }
    }, 250);
    setTimeout(() => {
      if (useVoiceStore.getState().voiceState === 'understanding') {
        useVoiceStore.getState().setVoiceState('checking_db');
      }
    }, 600);

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
        const answerText = data.message || data.display_text || String(data.answer || 'Done');
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
  const queryType = parsedCommand?.query_type;
  const structuredData = parsedCommand?.structured_data || {};

  const actionLabel =
    isQuery
      ? parsedCommand?.title || 'Inventory Query'
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
                ? parsedCommand?.title || 'Voice Answer'
                : 'Stock Updated'
              : t('voice.processing', 'Processing Voice Command...')
      }
    >
      <div className="space-y-5">
        {/* Voice Input Transcript Header */}
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200/80">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
            {t('voice.youSaid', 'Voice Input')}
          </p>
          <p className="text-lg font-medium text-slate-900 italic">
            &ldquo;{transcript || '...'}&rdquo;
          </p>
        </div>

        {/* Animated Processing Pipeline States */}
        {(voiceState === 'uploading' ||
          voiceState === 'transcribing' ||
          voiceState === 'understanding' ||
          voiceState === 'checking_db' ||
          voiceState === 'committing') && (
          <div className="flex flex-col items-center justify-center py-6 px-4">
            {/* Animated Pipeline Indicator */}
            <div className="flex items-center justify-between w-full max-w-sm mb-6 px-2">
              <div
                className={`flex flex-col items-center ${
                  voiceState === 'transcribing' || voiceState === 'uploading'
                    ? 'text-indigo-600 font-bold scale-105 transition-transform'
                    : 'text-slate-400'
                }`}
              >
                <div
                  className={`w-9 h-9 rounded-full flex items-center justify-center mb-1 text-sm border-2 ${
                    voiceState === 'transcribing' || voiceState === 'uploading'
                      ? 'border-indigo-600 bg-indigo-50 animate-pulse'
                      : 'border-slate-200 bg-white'
                  }`}
                >
                  <Mic className="w-4 h-4" />
                </div>
                <span className="text-[11px]">Processing</span>
              </div>

              <div className="h-0.5 w-6 bg-slate-200 -mt-4" />

              <div
                className={`flex flex-col items-center ${
                  voiceState === 'understanding'
                    ? 'text-indigo-600 font-bold scale-105 transition-transform'
                    : 'text-slate-400'
                }`}
              >
                <div
                  className={`w-9 h-9 rounded-full flex items-center justify-center mb-1 text-sm border-2 ${
                    voiceState === 'understanding'
                      ? 'border-indigo-600 bg-indigo-50 animate-pulse'
                      : 'border-slate-200 bg-white'
                  }`}
                >
                  <Brain className="w-4 h-4" />
                </div>
                <span className="text-[11px]">Understanding</span>
              </div>

              <div className="h-0.5 w-6 bg-slate-200 -mt-4" />

              <div
                className={`flex flex-col items-center ${
                  voiceState === 'checking_db' || voiceState === 'committing'
                    ? 'text-indigo-600 font-bold scale-105 transition-transform'
                    : 'text-slate-400'
                }`}
              >
                <div
                  className={`w-9 h-9 rounded-full flex items-center justify-center mb-1 text-sm border-2 ${
                    voiceState === 'checking_db' || voiceState === 'committing'
                      ? 'border-indigo-600 bg-indigo-50 animate-pulse'
                      : 'border-slate-200 bg-white'
                  }`}
                >
                  <Database className="w-4 h-4" />
                </div>
                <span className="text-[11px]">Database</span>
              </div>
            </div>

            <div className="w-10 h-10 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mb-3" />
            <p className="text-indigo-600 font-semibold text-sm">
              {voiceState === 'committing'
                ? 'Updating inventory database...'
                : voiceState === 'checking_db'
                  ? 'Searching inventory records...'
                  : voiceState === 'understanding'
                    ? 'Understanding query intent...'
                    : 'Analyzing speech input...'}
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

        {/* Conversational Result Card & Voice Output State */}
        {voiceState === 'completed' && (
          <div className="space-y-4">
            {/* 1. Metric Counter Card (e.g. Products Count, Transactions Count) */}
            {(queryType === 'COUNT_PRODUCTS' ||
              queryType === 'COUNT_PRODUCTS_ADDED' ||
              queryType === 'COUNT_TRANSACTIONS') && (
              <div className="bg-white border-2 border-indigo-100 rounded-2xl p-6 shadow-sm text-center">
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 mb-2 border border-indigo-100">
                  <Package className="w-3.5 h-3.5" />
                  <span>{parsedCommand?.title || 'Inventory Count'}</span>
                </div>
                <div className="text-6xl font-black text-indigo-950 tracking-tight my-2">
                  {structuredData.count ?? parsedCommand?.quantity ?? 0}
                </div>
                <div className="text-sm font-semibold uppercase tracking-wider text-slate-500">
                  {structuredData.operation
                    ? `${structuredData.operation.replace('_', ' ')} Transactions`
                    : structuredData.entity
                      ? structuredData.entity.replace('_', ' ')
                      : 'Items'}
                </div>
                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
                  <span className="capitalize">
                    Period: {structuredData.time_range?.replace('_', ' ') || 'All Time'}
                  </span>
                  <span className="inline-flex items-center gap-1 text-emerald-600 font-medium">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Live Database
                  </span>
                </div>
              </div>
            )}

            {/* 2. Itemized List Card (Low Stock, Out of Stock, Products Added) */}
            {(queryType === 'LIST_LOW_STOCK' ||
              queryType === 'LOW_STOCK_QUERY' ||
              queryType === 'LIST_OUT_OF_STOCK' ||
              queryType === 'LIST_PRODUCTS_ADDED') && (
              <div className="bg-white border-2 border-indigo-100 rounded-2xl p-5 shadow-sm text-left">
                <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-100">
                  <div className="flex items-center gap-2">
                    {queryType === 'LIST_OUT_OF_STOCK' ? (
                      <AlertCircle className="w-5 h-5 text-red-500" />
                    ) : queryType === 'LIST_PRODUCTS_ADDED' ? (
                      <Package className="w-5 h-5 text-indigo-500" />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-amber-500" />
                    )}
                    <h4 className="font-bold text-gray-900 text-base">
                      {parsedCommand?.title || 'Product List'}
                    </h4>
                  </div>
                  <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700">
                    {structuredData.items?.length ?? 0}{' '}
                    {structuredData.items?.length === 1 ? 'item' : 'items'}
                  </span>
                </div>

                {!structuredData.items || structuredData.items.length === 0 ? (
                  <div className="py-6 text-center text-slate-500 text-sm">
                    <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                    {parsedCommand?.display_text || 'No items to display.'}
                  </div>
                ) : (
                  <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                    {structuredData.items.map((item: any, idx: number) => {
                      const isLow = queryType?.includes('LOW');
                      const isOut = queryType?.includes('OUT');
                      return (
                        <div
                          key={idx}
                          className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100/80 transition-colors border border-slate-200/60"
                        >
                          <span className="font-semibold text-gray-900 text-sm">
                            {item.product_name || item.name}
                          </span>
                          <div className="flex items-center gap-2">
                            <span
                              className={`text-xs font-bold px-2 py-1 rounded-lg ${
                                isOut
                                  ? 'bg-red-100 text-red-800'
                                  : isLow
                                    ? 'bg-amber-100 text-amber-800'
                                    : 'bg-indigo-100 text-indigo-800'
                              }`}
                            >
                              {item.quantity != null
                                ? `${item.quantity} ${item.unit || item.base_unit || ''}`
                                : item.category || 'Active'}
                            </span>
                            {item.threshold != null && (
                              <span className="text-[11px] text-slate-400">
                                Reorder: {item.threshold}
                              </span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}

            {/* 3. Today's Activity Breakdown Grid */}
            {queryType === 'GET_TODAY_ACTIVITY' && (
              <div className="bg-white border-2 border-indigo-100 rounded-2xl p-5 shadow-sm">
                <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-100">
                  <div className="flex items-center gap-2">
                    <Activity className="w-5 h-5 text-indigo-600" />
                    <h4 className="font-bold text-gray-900 text-base">Today's Activity</h4>
                  </div>
                  <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700">
                    {structuredData.total_transactions ?? 0} transactions
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2.5 text-center">
                  <div className="p-3 bg-emerald-50 border border-emerald-100 rounded-xl">
                    <ArrowDownLeft className="w-4 h-4 text-emerald-600 mx-auto mb-1" />
                    <div className="text-2xl font-black text-emerald-800">
                      {structuredData.today_stock_in ?? 0}
                    </div>
                    <div className="text-[11px] font-semibold uppercase tracking-wider text-emerald-600 mt-0.5">
                      Stock In
                    </div>
                  </div>
                  <div className="p-3 bg-blue-50 border border-blue-100 rounded-xl">
                    <ArrowUpRight className="w-4 h-4 text-blue-600 mx-auto mb-1" />
                    <div className="text-2xl font-black text-blue-800">
                      {structuredData.today_stock_out ?? 0}
                    </div>
                    <div className="text-[11px] font-semibold uppercase tracking-wider text-blue-600 mt-0.5">
                      Stock Out
                    </div>
                  </div>
                  <div className="p-3 bg-purple-50 border border-purple-100 rounded-xl">
                    <Package className="w-4 h-4 text-purple-600 mx-auto mb-1" />
                    <div className="text-2xl font-black text-purple-800">
                      {structuredData.products_added ?? 0}
                    </div>
                    <div className="text-[11px] font-semibold uppercase tracking-wider text-purple-600 mt-0.5">
                      Added
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* 4. Recent Transactions Timeline */}
            {queryType === 'GET_RECENT_TRANSACTIONS' && (
              <div className="bg-white border-2 border-indigo-100 rounded-2xl p-5 shadow-sm text-left">
                <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-100">
                  <div className="flex items-center gap-2">
                    <Clock className="w-5 h-5 text-indigo-600" />
                    <h4 className="font-bold text-gray-900 text-base">Recent Transactions</h4>
                  </div>
                  <span className="text-xs font-semibold text-slate-500">Latest records</span>
                </div>
                {!structuredData.transactions || structuredData.transactions.length === 0 ? (
                  <div className="py-4 text-center text-slate-400 text-sm">
                    No recent transactions found.
                  </div>
                ) : (
                  <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                    {structuredData.transactions.map((tx: any, idx: number) => {
                      const isIn = tx.operation === 'STOCK_IN';
                      return (
                        <div
                          key={idx}
                          className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-200/60"
                        >
                          <div className="flex items-center gap-2.5">
                            <span
                              className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                                isIn ? 'bg-emerald-100 text-emerald-800' : 'bg-blue-100 text-blue-800'
                              }`}
                            >
                              {isIn ? '↓' : '↑'}
                            </span>
                            <div>
                              <span className="font-semibold text-gray-900 text-sm block">
                                {tx.product_name}
                              </span>
                              <span className="text-[11px] text-slate-400">
                                {tx.timestamp
                                  ? new Date(tx.timestamp).toLocaleTimeString([], {
                                      hour: '2-digit',
                                      minute: '2-digit',
                                    })
                                  : 'Recent'}
                              </span>
                            </div>
                          </div>
                          <span
                            className={`text-xs font-extrabold px-2 py-1 rounded-lg ${
                              isIn ? 'text-emerald-700 bg-emerald-50' : 'text-blue-700 bg-blue-50'
                            }`}
                          >
                            {isIn ? '+' : '-'}
                            {tx.quantity} {tx.unit}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}

            {/* 5. Product Stock Detail Card */}
            {(queryType === 'GET_PRODUCT_STOCK' ||
              (isQuery && !queryType && parsedCommand?.product)) && (
              <div className="bg-white border-2 border-indigo-100 rounded-2xl p-6 shadow-sm text-center">
                <span
                  className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold mb-2 ${
                    structuredData.status === 'OUT_OF_STOCK'
                      ? 'bg-red-50 text-red-700 border border-red-200'
                      : structuredData.status === 'LOW_STOCK'
                        ? 'bg-amber-50 text-amber-700 border border-amber-200'
                        : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  }`}
                >
                  {structuredData.status === 'OUT_OF_STOCK'
                    ? 'Out of Stock'
                    : structuredData.status === 'LOW_STOCK'
                      ? 'Low Stock'
                      : 'In Stock'}
                </span>
                <h3 className="text-xl font-extrabold text-gray-900">
                  {structuredData.product_name || parsedCommand?.product}
                </h3>
                <div className="text-5xl font-black text-indigo-950 tracking-tight my-2">
                  {structuredData.quantity ?? parsedCommand?.quantity ?? 0}
                  <span className="text-xl font-bold text-slate-500 ml-1.5">
                    {structuredData.unit || parsedCommand?.unit || ''}
                  </span>
                </div>
                {structuredData.threshold ? (
                  <p className="text-xs text-slate-400 mt-1">
                    Reorder Alert Threshold: {structuredData.threshold} {structuredData.unit}
                  </p>
                ) : null}
              </div>
            )}

            {/* 6. Top Stock Ranking Card */}
            {queryType === 'GET_TOP_STOCK_PRODUCTS' && (
              <div className="bg-white border-2 border-indigo-100 rounded-2xl p-5 shadow-sm text-left">
                <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-100">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-indigo-600" />
                    <h4 className="font-bold text-gray-900 text-base">
                      {parsedCommand?.title || 'Stock Ranking'}
                    </h4>
                  </div>
                  <span className="text-xs font-semibold text-indigo-700 bg-indigo-50 px-2.5 py-0.5 rounded-full capitalize">
                    {structuredData.order || 'Highest'}
                  </span>
                </div>
                <div className="space-y-2">
                  {(structuredData.items || []).map((it: any, idx: number) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-200/60"
                    >
                      <div className="flex items-center gap-2.5">
                        <span className="w-5 h-5 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-xs font-bold">
                          {idx + 1}
                        </span>
                        <span className="font-semibold text-gray-900 text-sm">
                          {it.product_name}
                        </span>
                      </div>
                      <span className="text-xs font-bold text-indigo-950 bg-indigo-50 px-2 py-1 rounded-lg">
                        {it.quantity} {it.unit}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 7. Category & General Store Insights Card */}
            {(queryType === 'CATEGORY_QUERY' ||
              queryType === 'GENERAL_QUERY' ||
              (![
                'COUNT_PRODUCTS',
                'COUNT_PRODUCTS_ADDED',
                'COUNT_TRANSACTIONS',
                'LIST_LOW_STOCK',
                'LOW_STOCK_QUERY',
                'LIST_OUT_OF_STOCK',
                'LIST_PRODUCTS_ADDED',
                'GET_TODAY_ACTIVITY',
                'GET_RECENT_TRANSACTIONS',
                'GET_PRODUCT_STOCK',
                'GET_TOP_STOCK_PRODUCTS',
              ].includes(queryType || '') &&
                isQuery &&
                parsedCommand?.display_text)) && (
              <div className="bg-white border-2 border-indigo-100 rounded-2xl p-5 shadow-sm text-left">
                <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-100">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-indigo-600" />
                    <h4 className="font-bold text-gray-900 text-base">
                      {parsedCommand?.title || 'Store Insights'}
                    </h4>
                  </div>
                  <span className="inline-flex items-center gap-1 text-xs text-emerald-600 font-medium bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-100">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Live Database
                  </span>
                </div>
                {parsedCommand?.display_text && (
                  <div className="p-3.5 bg-slate-50 border border-slate-200/60 rounded-xl">
                    <p className="text-base font-semibold text-gray-900 leading-relaxed">
                      {parsedCommand.display_text}
                    </p>
                  </div>
                )}
                {Array.isArray(structuredData.items) && structuredData.items.length > 0 && (
                  <div className="mt-3">
                    <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1.5">
                      Available Categories / Items
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {structuredData.items.map((item: any, idx: number) => {
                        const name = typeof item === 'string' ? item : item.name || item.product_name;
                        return (
                          <span
                            key={idx}
                            className="px-2.5 py-1 text-xs font-semibold bg-indigo-50 text-indigo-700 rounded-lg border border-indigo-100"
                          >
                            {name}
                          </span>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Voice Audio Visualizer & Spoken Sentence Box */}
            <div className="bg-gradient-to-b from-indigo-50/80 to-white border-2 border-indigo-200 rounded-2xl p-5 text-center shadow-xs">
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

              <div className="bg-white p-4 rounded-xl border border-indigo-100 shadow-xs my-3 text-left">
                <p className="text-xs font-semibold uppercase tracking-wider text-indigo-500 mb-1 flex items-center gap-1">
                  <Sparkles className="w-3.5 h-3.5" />
                  Spoken Answer
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
          </div>
        )}

        {/* Error / Fallback State */}
        {voiceState === 'error' && (
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 text-center">
            <AlertCircle className="h-12 w-12 text-amber-500 mx-auto mb-3" />
            <p className="text-amber-900 font-medium text-base mb-4">
              {error || t('voice.notUnderstood', 'Could not understand the command.')}
            </p>

            <form onSubmit={handleManualSubmit} className="mt-4 mb-4">
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder='Ask anything (e.g., "Products added today?" or "Rice stock?")'
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
