import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { ArrowLeft, Save } from 'lucide-react';
import { UNITS } from '../../lib/constants';
import { api } from '../../lib/api';

interface Product {
  id: string;
  display_name: string;
  base_unit: string;
}

/** Manual stock entry — the offline/voice-failure fallback (A9). */
export const ManualEntryPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

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
      if (!productId) throw new Error('Select a product');
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
      navigate('/transactions');
    },
    onError: (e: unknown) => {
      const msg =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        (e as Error)?.message ||
        'Could not save. Please try again.';
      setFormError(typeof msg === 'string' ? msg : 'Could not save.');
    },
  });

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <div className="flex items-center space-x-4">
        <button
          onClick={() => navigate(-1)}
          className="p-2 rounded-full hover:bg-gray-100 text-gray-500 min-h-[44px] min-w-[44px] flex items-center justify-center"
          aria-label="Back"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <h1 className="text-2xl font-bold text-gray-900">{t('voice.manualEntry', 'Manual Entry')}</h1>
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
            <div className="rounded-xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700" role="alert">
              {formError}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Product</label>
            <select
              className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm min-h-[44px] px-3 border"
              value={productId}
              onChange={(e) => {
                setProductId(e.target.value);
                const p = products.find((x) => x.id === e.target.value);
                if (p) setUnit(p.base_unit);
              }}
              required
            >
              <option value="">Select a product…</option>
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.display_name}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Action</label>
              <select
                className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm min-h-[44px] px-3 border"
                value={operation}
                onChange={(e) => setOperation(e.target.value as typeof operation)}
              >
                <option value="STOCK_IN">{t('inventory.addStock', 'Add Stock')}</option>
                <option value="STOCK_OUT">{t('inventory.removeStock', 'Remove Stock')}</option>
                <option value="ADJUSTMENT">Set exact level</option>
              </select>
            </div>
            <Input
              label={t('inventory.quantity', 'Quantity')}
              type="number"
              min="0"
              step="any"
              required
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
            />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('inventory.unit', 'Unit')}</label>
              <select
                className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm min-h-[44px] px-3 border"
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
            label={t('inventory.reason', 'Reason (Optional)')}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="purchase / sale / damage…"
          />
          {selected && (
            <p className="text-xs text-gray-500">
              Base unit: {selected.base_unit}. Packaging units without a configured conversion are tracked as-is.
            </p>
          )}

          <div className="flex justify-end pt-2">
            <Button type="submit" variant="primary" isLoading={save.isPending}>
              <Save className="h-4 w-4 mr-2" />
              {t('common.save', 'Save')}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};
