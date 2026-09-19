import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Card } from '../../components/ui/Card';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { ArrowLeft, Save, Plus, X } from 'lucide-react';
import { UNITS, CATEGORIES } from '../../lib/constants';
import { api } from '../../lib/api';

export const ProductFormPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id } = useParams();
  const isEditing = !!id;
  const queryClient = useQueryClient();

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
      setAliases(a.length > 0 ? a.map((x: { text?: string } | string) => (typeof x === 'string' ? x : x.text || '')) : ['']);
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
        return (await api.patch(`/products/${id}`, {
          display_name: payload.display_name,
          category: payload.category,
          base_unit: payload.base_unit,
          reorder_threshold: payload.reorder_threshold,
        })).data;
      }
      return (await api.post('/products/', payload)).data;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['products'] });
      await queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      navigate('/products');
    },
    onError: (e: unknown) => {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Could not save product.';
      setFormError(typeof msg === 'string' ? msg : 'Could not save product.');
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
      <div className="flex items-center space-x-4">
        <button 
          onClick={() => navigate('/products')}
          className="p-2 rounded-full hover:bg-gray-100 text-gray-500 min-h-[44px] min-w-[44px] flex items-center justify-center"
          aria-label="Back to products"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <h1 className="text-2xl font-bold text-gray-900">
          {isEditing ? t('products.editProduct') : t('products.addProduct')}
        </h1>
      </div>

      <Card>
        <form className="space-y-6" onSubmit={(e) => { e.preventDefault(); setFormError(null); saveMutation.mutate(); }}>
          {formError && (
            <div className="rounded-xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700" role="alert">
              {formError}
            </div>
          )}
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <Input label={t('products.name')} required value={name} onChange={(e) => setName(e.target.value)} />
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('products.category')}</label>
              <select
                className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm min-h-[44px] px-3 border"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
              >
                {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('products.unit')}</label>
              <select
                className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm min-h-[44px] px-3 border"
                value={unit}
                onChange={(e) => setUnit(e.target.value)}
              >
                {UNITS.map(u => <option key={u.value} value={u.value}>{u.label}</option>)}
              </select>
            </div>

            <Input label={t('products.threshold')} type="number" min="0" required value={String(threshold)} onChange={(e) => setThreshold(Number(e.target.value))} />
          </div>

          <div className="border-t border-gray-200 pt-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">{t('products.aliases')}</h3>
              <Button type="button" variant="secondary" size="sm" onClick={addAlias}>
                <Plus className="h-4 w-4 mr-2" />
                Add Alias
              </Button>
            </div>
            <p className="text-sm text-gray-500 mb-4">
              Add local names or voice terms people use for this product.
            </p>
            
            <div className="space-y-3">
              {aliases.map((alias, index) => (
                <div key={index} className="flex items-center space-x-2">
                  <Input 
                    value={alias}
                    onChange={(e) => updateAlias(index, e.target.value)}
                    placeholder={`e.g., Local Name ${index + 1}`}
                    className="flex-1"
                  />
                  <button
                    type="button"
                    onClick={() => removeAlias(index)}
                    className="p-2 text-red-500 hover:bg-red-50 rounded-lg min-h-[44px] min-w-[44px] flex items-center justify-center"
                    disabled={aliases.length === 1}
                    aria-label="Remove alias"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
            <Button type="button" variant="secondary" onClick={() => navigate('/products')}>
              {t('common.cancel')}
            </Button>
            <Button type="submit" variant="primary" isLoading={saveMutation.isPending}>
              <Save className="h-4 w-4 mr-2" />
              {t('common.save')}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};
