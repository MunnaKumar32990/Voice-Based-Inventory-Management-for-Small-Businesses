import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Badge } from '../../components/ui/Badge';
import { useToast } from '../../components/ui/Toast';
import {
  Plus,
  Undo2,
  Search,
  ArrowDownRight,
  ArrowUpRight,
  History,
} from 'lucide-react';
import { api } from '../../lib/api';

interface Txn {
  id: string;
  product_name: string;
  operation: string;
  quantity: number;
  unit: string;
  source: string;
  created_at: string;
  reason?: string;
}

export const TransactionHistoryPage: React.FC = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();

  const [filter, setFilter] = useState('');
  const [opFilter, setOpFilter] = useState<'ALL' | 'STOCK_IN' | 'STOCK_OUT'>('ALL');

  const { data, isLoading, isError } = useQuery({
    queryKey: ['transactions'],
    queryFn: async () =>
      (await api.get<{ transactions: Txn[] }>('/inventory/transactions', { params: { limit: 100 } })).data,
  });

  const reverseMutation = useMutation({
    mutationFn: async (txnId: string) => (await api.post(`/inventory/transactions/${txnId}/reverse`)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['transactions'] });
      await queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      await queryClient.invalidateQueries({ queryKey: ['products'] });
      await queryClient.invalidateQueries({ queryKey: ['alerts'] });
      success('Transaction Reversed', 'Stock balances have been adjusted back.');
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.detail || 'Could not reverse transaction.';
      toastError('Reverse Failed', typeof msg === 'string' ? msg : 'Please try again.');
    },
  });

  const allTxns = data?.transactions ?? [];

  const filtered = allTxns.filter((tx) => {
    const matchesText = filter ? tx.product_name.toLowerCase().includes(filter.toLowerCase()) : true;
    const matchesOp = opFilter === 'ALL' || tx.operation === opFilter;
    return matchesText && matchesOp;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200/80">
        <div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            {t('nav.transactions', 'Stock Movements')}
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Complete audit trail of all voice and manual inventory transactions.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <Link to="/manual">
            <Button variant="primary" size="sm" className="font-bold shadow-md shadow-indigo-200">
              <Plus className="h-4 w-4 mr-1.5" />
              {t('voice.manualEntry', 'Manual Entry')}
            </Button>
          </Link>
        </div>
      </div>

      {/* Filter Toolbar */}
      <Card className="p-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="w-full sm:w-72">
            <Input
              placeholder="Search by product..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              leftIcon={<Search className="w-4 h-4" />}
            />
          </div>

          <div className="flex items-center gap-1.5 w-full sm:w-auto bg-slate-100 p-1 rounded-xl border border-slate-200/60">
            <button
              onClick={() => setOpFilter('ALL')}
              className={`flex-1 sm:flex-none px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                opFilter === 'ALL'
                  ? 'bg-white text-slate-900 shadow-xs border border-slate-200/60'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              All Movements
            </button>
            <button
              onClick={() => setOpFilter('STOCK_IN')}
              className={`flex-1 sm:flex-none px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                opFilter === 'STOCK_IN'
                  ? 'bg-white text-emerald-700 shadow-xs border border-slate-200/60'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Stock In
            </button>
            <button
              onClick={() => setOpFilter('STOCK_OUT')}
              className={`flex-1 sm:flex-none px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                opFilter === 'STOCK_OUT'
                  ? 'bg-white text-blue-700 shadow-xs border border-slate-200/60'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Stock Out
            </button>
          </div>
        </div>

        {/* Transactions List */}
        <div className="mt-6">
          {isLoading ? (
            <div className="space-y-3 py-4 animate-pulse">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="h-16 bg-slate-100 rounded-2xl" />
              ))}
            </div>
          ) : isError ? (
            <p className="text-center text-rose-600 py-10 font-medium">
              Could not load transactions. Please check server connection.
            </p>
          ) : filtered.length === 0 ? (
            <div className="py-16 text-center text-slate-400">
              <History className="w-10 h-10 mx-auto mb-2 text-slate-300" />
              <h4 className="font-bold text-slate-900 text-sm">No transactions found</h4>
              <p className="text-xs text-slate-400 mt-1">
                {filter ? `No movements matching "${filter}"` : 'Transactions will appear here as stock changes.'}
              </p>
            </div>
          ) : (
            <div className="space-y-2.5">
              {filtered.map((tx) => {
                const isIn = tx.operation === 'STOCK_IN';
                return (
                  <div
                    key={tx.id}
                    className="flex items-center justify-between p-3.5 sm:p-4 border border-slate-200/80 rounded-2xl hover:bg-slate-50/80 transition-all bg-white shadow-xs"
                  >
                    <div className="flex items-center space-x-3.5">
                      <div
                        className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                          isIn ? 'bg-emerald-100 text-emerald-700' : 'bg-blue-100 text-blue-700'
                        }`}
                      >
                        {isIn ? <ArrowDownRight className="h-5 w-5" /> : <ArrowUpRight className="h-5 w-5" />}
                      </div>
                      <div>
                        <h3 className="text-sm sm:text-base font-bold text-slate-900">{tx.product_name}</h3>
                        <div className="flex items-center space-x-2 mt-0.5 text-xs text-slate-500">
                          <span>
                            {tx.created_at
                              ? new Date(tx.created_at).toLocaleString([], {
                                  dateStyle: 'medium',
                                  timeStyle: 'short',
                                })
                              : 'Recent'}
                          </span>
                          <span>•</span>
                          <Badge variant={tx.source === 'voice' ? 'info' : 'secondary'} size="sm">
                            {tx.source === 'voice' ? '🎙️ Voice' : '✍️ Manual'}
                          </Badge>
                          {tx.reason && (
                            <>
                              <span className="hidden sm:inline">•</span>
                              <span className="hidden sm:inline text-slate-400 italic text-[11px]">
                                {tx.reason}
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <div
                        className={`text-base sm:text-lg font-black ${
                          isIn ? 'text-emerald-700' : 'text-blue-700'
                        }`}
                      >
                        {isIn ? '+' : '-'}{tx.quantity} {tx.unit}
                      </div>
                      <button
                        onClick={() => reverseMutation.mutate(tx.id)}
                        disabled={reverseMutation.isPending}
                        className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-colors cursor-pointer"
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
        </div>
      </Card>
    </div>
  );
};
