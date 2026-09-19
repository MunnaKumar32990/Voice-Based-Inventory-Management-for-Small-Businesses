import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { ArrowLeftRight, Plus, Undo2 } from 'lucide-react';
import { Badge } from '../../components/ui/Badge';
import { api } from '../../lib/api';

interface Txn {
  id: string;
  product_name: string;
  operation: string;
  quantity: number;
  unit: string;
  source: string;
  created_at: string;
}

export const TransactionHistoryPage: React.FC = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState('');

  const { data, isLoading, isError } = useQuery({
    queryKey: ['transactions'],
    queryFn: async () => (await api.get<{ transactions: Txn[] }>('/inventory/transactions', { params: { limit: 100 } })).data,
  });

  const reverseMutation = useMutation({
    mutationFn: async (txnId: string) => (await api.post(`/inventory/transactions/${txnId}/reverse`)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['transactions'] });
      await queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      await queryClient.invalidateQueries({ queryKey: ['products'] });
      await queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
  });

  const transactions = (data?.transactions ?? []).filter((tx) =>
    filter ? tx.product_name.toLowerCase().includes(filter.toLowerCase()) : true
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-gray-900">{t('nav.transactions')}</h1>
        <div className="flex gap-2">
          <Input placeholder={t('common.search')} value={filter} onChange={(e) => setFilter(e.target.value)} className="sm:w-56" />
          <Link to="/manual">
            <Button variant="primary" size="sm">
              <Plus className="h-4 w-4 mr-2" />
              {t('voice.manualEntry', 'Manual Entry')}
            </Button>
          </Link>
        </div>
      </div>

      <Card>
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="w-10 h-10 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
          </div>
        ) : isError ? (
          <p className="text-center text-red-600 py-8">{t('common.error')}: could not load transactions.</p>
        ) : transactions.length === 0 ? (
          <p className="text-center text-gray-500 py-8">{t('common.noData')}</p>
        ) : (
          <div className="space-y-4">
            {transactions.map((tx) => {
              const isIn = tx.operation === 'STOCK_IN';
              return (
                <div key={tx.id} className="flex items-center justify-between p-4 border border-gray-100 rounded-xl hover:bg-gray-50 transition-colors">
                  <div className="flex items-center space-x-4">
                    <div className={`p-3 rounded-full ${isIn ? 'bg-green-100 text-green-600' : 'bg-blue-100 text-blue-600'}`}>
                      <ArrowLeftRight className="h-6 w-6" />
                    </div>
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">{tx.product_name}</h3>
                      <div className="flex items-center space-x-2 mt-1">
                        <span className="text-sm text-gray-500">
                          {tx.created_at ? new Date(tx.created_at).toLocaleString() : ''}
                        </span>
                        <span className="text-gray-300">•</span>
                        <Badge variant={tx.source === 'voice' ? 'info' : 'secondary'}>
                          {tx.source}
                        </Badge>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className={`text-xl font-bold ${isIn ? 'text-green-600' : 'text-blue-600'}`}>
                      {isIn ? '+' : '-'}{tx.quantity} {tx.unit}
                    </div>
                    <button
                      onClick={() => reverseMutation.mutate(tx.id)}
                      disabled={reverseMutation.isPending}
                      className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-full"
                      title="Reverse transaction"
                      aria-label={`Reverse ${tx.product_name} transaction`}
                    >
                      <Undo2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>
    </div>
  );
};
