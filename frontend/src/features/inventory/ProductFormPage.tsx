import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Card } from '../../components/ui/Card';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { useToast } from '../../components/ui/Toast';
import { ArrowLeft, Save, Plus, X, Sparkles } from 'lucide-react';
import { UNITS, CATEGORIES } from '../../lib/constants';
import { api } from '../../lib/api';

export const ProductFormPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id } = useParams();
  const isEditing = !!id;
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();

  const [name, setName] = useState('');
  const [category, setCategory] = useState(CATEGORIES[0]);
  const [unit, setUnit] = useState('kg');
  const [threshold, setThreshold] = useState<number>(10);
  const [aliases, setAliases] = useState<string[]>(['']);
  const [formError, setFormError] = useState<string | null>(null);

  const { data: existing } = useQuery({
    queryKey: ['product', id],
    queryFn: async () => (await api.get(`/products/${id}`)).data,
    enabled: isEditing,
  });

  useEffect(() => {
    if (existing) {
      setName(existing.display_name || existing.name || '');
      setCategory(existing.category || CATEGORIES[0]);
      setUnit(existing.base_unit || 'kg');
      setThreshold(existing.reorder_threshold ?? 10);
      const a = existing.aliases || [];
      setAliases(
        a.length > 0
          ? a.map((x: { text?: string } | string) => (typeof x === 'string' ? x : x.text || ''))
          : ['']
      );
    }
  }, [existing]);

  const saveMutation = useMutation({
    mutationFn: async () => {
      const payload = {
        display_name: name.trim(),
        category,
        base_unit: unit,
        allowed_units: [unit],
        reorder_threshold: Number(threshold) || 0,
        aliases: aliases.filter((a) => a.trim()).map((a) => ({ text: a.trim(), language: 'en' })),
        conversions: [],
        opening_balance: 0,
      };
      if (isEditing) {
        return (
          await api.patch(`/products/${id}`, {
            display_name: payload.display_name,
            category: payload.category,
            base_unit: payload.base_unit,
            reorder_threshold: payload.reorder_threshold,
          })
        ).data;
      }
      return (await api.post('/products/', payload)).data;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['products'] });
      await queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      success(
        isEditing ? 'Product Updated' : 'Product Added',
        `"${name.trim()}" has been saved to your catalog.`
      );
      navigate('/products');
    },
    onError: (e: unknown) => {
      const msg =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Could not save product.';
      setFormError(typeof msg === 'string' ? msg : 'Could not save product.');
      toastError('Save Failed', typeof msg === 'string' ? msg : 'Please check product fields.');
    },
  });

  const addAlias = () => setAliases([...aliases, '']);
  const updateAlias = (index: number, value: string) => {
    const newAliases = [...aliases];
    newAliases[index] = value;
    setAliases(newAliases);
  };
  const removeAlias = (index: number) => {
    setAliases(aliases.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center space-x-4 pb-2 border-b border-slate-200/80">
        <button
          onClick={() => navigate('/products')}
          className="p-2 rounded-xl hover:bg-slate-100 text-slate-500 transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center cursor-pointer"
          aria-label="Back to products"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">
            {isEditing ? t('products.editProduct', 'Edit Product') : t('products.addProduct', 'Add New Product')}
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            {isEditing ? 'Update catalog details and reorder thresholds.' : 'Add an item to your store inventory.'}
          </p>
        </div>
      </div>

      <Card>
        <form
          className="space-y-6"
          onSubmit={(e) => {
            e.preventDefault();
            setFormError(null);
            saveMutation.mutate();
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

          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <Input
              label={t('products.name', 'Product Name')}
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Basmati Rice 1kg"
            />

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                {t('products.category', 'Category')}
              </label>
              <select
                className="block w-full rounded-xl border border-slate-200 bg-white text-slate-900 text-sm focus:outline-none focus:border-indigo-500 focus:ring-3 focus:ring-indigo-100 min-h-[44px] px-3.5 font-medium cursor-pointer"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                {t('products.unit', 'Base Unit')}
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

            <Input
              label={t('products.threshold', 'Reorder Alert Threshold')}
              type="number"
              min="0"
              required
              value={String(threshold)}
              onChange={(e) => setThreshold(Number(e.target.value))}
              helperText="Alerts trigger when stock falls below this quantity."
            />
          </div>

          {/* Voice Aliases Section */}
          <div className="border-t border-slate-100 pt-6">
            <div className="flex items-center justify-between mb-2">
              <div>
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-indigo-600" />
                  {t('products.aliases', 'Voice Aliases & Local Terms')}
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Add dialect terms or alternative names customers or staff use (e.g. &ldquo;Chawal&rdquo; for Rice).
                </p>
              </div>
              <Button type="button" variant="subtle" size="sm" onClick={addAlias} className="font-bold">
                <Plus className="h-3.5 w-3.5 mr-1" />
                Add Alias
              </Button>
            </div>

            <div className="space-y-3 mt-4">
              {aliases.map((alias, index) => (
                <div key={index} className="flex items-center space-x-2">
                  <Input
                    value={alias}
                    onChange={(e) => updateAlias(index, e.target.value)}
                    placeholder={`e.g. Local name / Hindi term ${index + 1}`}
                    className="flex-1"
                  />
                  <button
                    type="button"
                    onClick={() => removeAlias(index)}
                    className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl min-h-[44px] min-w-[44px] flex items-center justify-center cursor-pointer transition-colors"
                    disabled={aliases.length === 1}
                    aria-label="Remove alias"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-6 border-t border-slate-100">
            <Button type="button" variant="secondary" onClick={() => navigate('/products')}>
              {t('common.cancel', 'Cancel')}
            </Button>
            <Button
              type="submit"
              variant="primary"
              className="font-bold shadow-md shadow-indigo-200"
              isLoading={saveMutation.isPending}
            >
              <Save className="h-4 w-4 mr-2" />
              {t('common.save', 'Save Product')}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};
