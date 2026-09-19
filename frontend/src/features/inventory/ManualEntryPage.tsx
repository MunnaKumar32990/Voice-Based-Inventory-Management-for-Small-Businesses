import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { useToast } from '../../components/ui/Toast';
import { ArrowLeft, Save, ArrowDownRight, ArrowUpRight, Sliders } from 'lucide-react';
import { UNITS } from '../../lib/constants';
import { api } from '../../lib/api';

interface Product {
  id: string;
  display_name: string;
  base_unit: string;
}

export const ManualEntryPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();

  const [productId, setProductId] = useState('');
  const [operation, setOperation] = useState<'STOCK_IN' | 'STOCK_OUT' | 'ADJUSTMENT'>('STOCK_IN');
  const [quantity, setQuantity] = useState('1');
  const [unit, setUnit] = useState('kg');
  const [reason, setReason] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  const { data } = useQuery({
    queryKey: ['products'],
    queryFn: async () => (await api.get<{ products: Product[] }>('/products/')).data,
  });
  const products = data?.products ?? [];
  const selected = products.find((p) => p.id === productId);

  const save = useMutation({
    mutationFn: async () => {
      const qty = Number(quantity);
      if (!productId) throw new Error('Please select a product');
      if (!qty || qty <= 0) throw new Error('Quantity must be greater than 0');
      return (
        await api.post('/inventory/transactions', {
          product_id: productId,
          operation,
          quantity: qty,
          unit,
          reason,
          client_request_id: `manual_${Date.now()}_${productId}`,
        })
      ).data;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      await queryClient.invalidateQueries({ queryKey: ['products'] });
      await queryClient.invalidateQueries({ queryKey: ['transactions'] });
      await queryClient.invalidateQueries({ queryKey: ['alerts'] });

      const opLabel =
        operation === 'STOCK_IN'
          ? 'Stock In Added'
          : operation === 'STOCK_OUT'
            ? 'Stock Out Recorded'
            : 'Stock Level Adjusted';

      success(opLabel, `${quantity} ${unit} recorded for ${selected?.display_name || 'product'}.`);
      navigate('/transactions');
    },
    onError: (e: unknown) => {
      const msg =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        (e as Error)?.message ||
        'Could not save transaction. Please try again.';
      setFormError(typeof msg === 'string' ? msg : 'Could not save.');
      toastError('Transaction Failed', typeof msg === 'string' ? msg : 'Please check quantity and stock.');
    },
  });

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      {/* Header */}
      <div className="flex items-center space-x-4 pb-2 border-b border-slate-200/80">
        <button
          onClick={() => navigate(-1)}
          className="p-2 rounded-xl hover:bg-slate-100 text-slate-500 transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center cursor-pointer"
          aria-label="Back"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">
            {t('voice.manualEntry', 'Manual Stock Entry')}
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Record manual stock movements, purchases, or adjustments without voice.
          </p>
        </div>
      </div>

      <Card>
        <form
          className="space-y-5"
          onSubmit={(e) => {
            e.preventDefault();
            setFormError(null);
            save.mutate();
          }}
        >
          {formError && (
            <div
              className="rounded-xl bg-rose-50 border border-rose-200 px-4 py-3 text-sm text-rose-700 font-medium"
              role="alert"
            >
              {formError}
            </div>
          )}

          {/* Product Select */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
              Select Product
            </label>
            <select
              className="block w-full rounded-xl border border-slate-200 bg-white text-slate-900 text-sm focus:outline-none focus:border-indigo-500 focus:ring-3 focus:ring-indigo-100 min-h-[44px] px-3.5 font-medium cursor-pointer"
              value={productId}
              onChange={(e) => {
                setProductId(e.target.value);
                const p = products.find((x) => x.id === e.target.value);
                if (p) setUnit(p.base_unit);
              }}
              required
            >
              <option value="">Choose a product from inventory…</option>
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.display_name} ({p.base_unit})
                </option>
              ))}
            </select>
          </div>

          {/* Operation Selector Tabs */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
              Action Type
            </label>
            <div className="grid grid-cols-3 gap-2 bg-slate-100 p-1.5 rounded-2xl border border-slate-200/60">
              <button
                type="button"
                onClick={() => setOperation('STOCK_IN')}
                className={`py-2 px-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
                  operation === 'STOCK_IN'
                    ? 'bg-white text-emerald-700 shadow-xs border border-slate-200/60'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <ArrowDownRight className="w-4 h-4" />
                Stock In
              </button>

              <button
                type="button"
                onClick={() => setOperation('STOCK_OUT')}
                className={`py-2 px-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
                  operation === 'STOCK_OUT'
                    ? 'bg-white text-blue-700 shadow-xs border border-slate-200/60'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <ArrowUpRight className="w-4 h-4" />
                Stock Out
              </button>

              <button
                type="button"
                onClick={() => setOperation('ADJUSTMENT')}
                className={`py-2 px-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
                  operation === 'ADJUSTMENT'
                    ? 'bg-white text-indigo-700 shadow-xs border border-slate-200/60'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Sliders className="w-4 h-4" />
                Set Exact
              </button>
            </div>
          </div>

          {/* Quantity and Unit */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label={t('inventory.quantity', 'Quantity')}
              type="number"
              min="0.01"
              step="any"
              required
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
            />
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                {t('inventory.unit', 'Unit')}
              </label>
              <select
                className="block w-full rounded-xl border border-slate-200 bg-white text-slate-900 text-sm focus:outline-none focus:border-indigo-500 focus:ring-3 focus:ring-indigo-100 min-h-[44px] px-3.5 font-medium cursor-pointer"
                value={unit}
                onChange={(e) => setUnit(e.target.value)}
              >
                {UNITS.map((u) => (
                  <option key={u.value} value={u.value}>
                    {u.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <Input
            label={t('inventory.reason', 'Reason or Note (Optional)')}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="e.g. New delivery, daily sales, damage..."
          />

          <div className="flex justify-end pt-3 border-t border-slate-100">
            <Button
              type="submit"
              variant="primary"
              className="font-bold shadow-md shadow-indigo-200 px-6"
              isLoading={save.isPending}
            >
              <Save className="h-4 w-4 mr-2" />
              Save Transaction
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};
