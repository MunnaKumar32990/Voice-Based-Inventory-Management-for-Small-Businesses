import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '../../stores/authStore';
import { Package, ArrowDownRight, ArrowUpRight, AlertTriangle } from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { api } from '../../lib/api';

interface DashboardProduct {
  id: string;
  name: string;
  quantity: number;
  unit: string;
  reorder_threshold: number;
  category?: string;
  status: string;
}

interface DashboardSummary {
  today_stock_in: number;
  today_stock_out: number;
  low_stock_count: number;
  total_products: number;
  products: DashboardProduct[];
}

interface Txn {
  id: string;
  product_name: string;
  operation: string;
  quantity: number;
  unit: string;
  created_at: string;
}

export const DashboardPage: React.FC = () => {
  const { t } = useTranslation();
  const shopName = useAuthStore((s) => s.shopName);

  const { data: summary, isLoading, isError } = useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => (await api.get<DashboardSummary>('/dashboard/summary')).data,
  });

  const { data: recent } = useQuery({
    queryKey: ['transactions', 'recent'],
    queryFn: async () => (await api.get<{ transactions: Txn[] }>('/inventory/transactions', { params: { limit: 5 } })).data,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
        <span className="ml-3 text-indigo-600 font-medium">{t('common.loading')}</span>
      </div>
    );
  }

  if (isError || !summary) {
    return (
      <div className="rounded-xl bg-red-50 border border-red-200 p-6 text-center text-red-700">
        {t('common.error')}: could not load dashboard. Check backend connection.
      </div>
    );
  }

  const lowStockItems = summary.products.filter((p) => p.status === 'LOW' || p.status === 'OUT');
  const recentTransactions = recent?.transactions ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome to {shopName}
        </h1>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-indigo-50 border-indigo-100">
          <div className="flex items-center space-x-3 mb-2">
            <div className="p-2 bg-indigo-100 rounded-lg">
              <Package className="h-5 w-5 text-indigo-600" />
            </div>
            <h3 className="text-sm font-medium text-indigo-900">{t('dashboard.totalProducts')}</h3>
          </div>
          <p className="text-2xl font-bold text-indigo-700">{summary.total_products}</p>
        </Card>

        <Card className="bg-green-50 border-green-100">
          <div className="flex items-center space-x-3 mb-2">
            <div className="p-2 bg-green-100 rounded-lg">
              <ArrowDownRight className="h-5 w-5 text-green-600" />
            </div>
            <h3 className="text-sm font-medium text-green-900">{t('dashboard.todayIn')}</h3>
          </div>
          <p className="text-2xl font-bold text-green-700">+{summary.today_stock_in}</p>
        </Card>

        <Card className="bg-blue-50 border-blue-100">
          <div className="flex items-center space-x-3 mb-2">
            <div className="p-2 bg-blue-100 rounded-lg">
              <ArrowUpRight className="h-5 w-5 text-blue-600" />
            </div>
            <h3 className="text-sm font-medium text-blue-900">{t('dashboard.todayOut')}</h3>
          </div>
          <p className="text-2xl font-bold text-blue-700">-{summary.today_stock_out}</p>
        </Card>

        <Card className="bg-red-50 border-red-100">
          <div className="flex items-center space-x-3 mb-2">
            <div className="p-2 bg-red-100 rounded-lg">
              <AlertTriangle className="h-5 w-5 text-red-600" />
            </div>
            <h3 className="text-sm font-medium text-red-900">{t('dashboard.lowStock')}</h3>
          </div>
          <p className="text-2xl font-bold text-red-700">{summary.low_stock_count}</p>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title={t('dashboard.lowStock')}>
          {lowStockItems.length > 0 ? (
            <ul className="divide-y divide-gray-100">
              {lowStockItems.map((item) => (
                <li key={item.id} className="py-3 flex justify-between items-center">
                  <div>
                    <p className="font-medium text-gray-900">{item.name}</p>
                    <p className="text-sm text-gray-500">Threshold: {item.reorder_threshold} {item.unit}</p>
                  </div>
                  <div className="text-right">
                    <span className="inline-flex items-center rounded-full bg-red-100 px-2.5 py-0.5 text-sm font-medium text-red-800">
                      {item.quantity} {item.unit}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-500 py-4 text-center">{t('common.noData')}</p>
          )}
        </Card>

        <Card title={t('dashboard.recentTransactions')}>
          {recentTransactions.length > 0 ? (
            <ul className="divide-y divide-gray-100">
              {recentTransactions.map((tx) => {
                const isIn = tx.operation === 'STOCK_IN';
                return (
                  <li key={tx.id} className="py-3 flex justify-between items-center">
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 rounded-full ${isIn ? 'bg-green-100 text-green-600' : 'bg-blue-100 text-blue-600'}`}>
                        {isIn ? <ArrowDownRight className="h-4 w-4" /> : <ArrowUpRight className="h-4 w-4" />}
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">{tx.product_name}</p>
                        <p className="text-xs text-gray-500">
                          {tx.created_at ? new Date(tx.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                        </p>
                      </div>
                    </div>
                    <div className={`font-semibold ${isIn ? 'text-green-600' : 'text-blue-600'}`}>
                      {isIn ? '+' : '-'}{tx.quantity} {tx.unit}
                    </div>
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="text-gray-500 py-4 text-center">{t('common.noData')}</p>
          )}
        </Card>
      </div>
    </div>
  );
};
