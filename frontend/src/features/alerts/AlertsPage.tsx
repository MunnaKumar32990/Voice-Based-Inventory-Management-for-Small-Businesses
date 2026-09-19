import React from 'react';
import { useTranslation } from 'react-i18next';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { AlertTriangle, Check, CheckCircle2, ArrowDownRight } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { useToast } from '../../components/ui/Toast';
import { api } from '../../lib/api';

interface Alert {
  id: string;
  product_name: string;
  current_quantity: number;
  threshold: number;
  type: string;
  status: string;
}

export const AlertsPage: React.FC = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();

  const { data, isLoading, isError } = useQuery({
    queryKey: ['alerts'],
    queryFn: async () => (await api.get<{ alerts: Alert[] }>('/alerts/')).data,
  });

  const resolveMutation = useMutation({
    mutationFn: async (alertId: string) => (await api.post(`/alerts/${alertId}/resolve`)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['alerts'] });
      await queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      success('Alert Resolved', 'The low-stock notice has been acknowledged.');
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.detail || 'Could not resolve alert.';
      toastError('Action Failed', typeof msg === 'string' ? msg : 'Please try again.');
    },
  });

  const alerts = data?.alerts ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200/80">
        <div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            {t('alerts.title', 'Stock Alerts & Notifications')}
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Real-time warnings when items fall below their minimum configured reorder thresholds.
          </p>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-3 py-6 animate-pulse">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 bg-slate-100 rounded-2xl" />
          ))}
        </div>
      ) : isError ? (
        <p className="text-center text-rose-600 py-10 font-medium">
          Could not load alerts. Please check server connection.
        </p>
      ) : alerts.length === 0 ? (
        <Card className="py-16 text-center">
          <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto mb-3 opacity-90" />
          <h3 className="text-lg font-bold text-slate-900 mb-1">No Active Alerts</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            All products in your store are currently at or above their configured reorder thresholds.
          </p>
        </Card>
      ) : (
        <div className="space-y-3.5">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className="p-5 rounded-2xl bg-white border border-rose-200 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-l-4 border-l-rose-500"
            >
              <div className="flex items-start space-x-4">
                <div className="p-2.5 bg-rose-50 rounded-xl text-rose-600 shrink-0 mt-0.5">
                  <AlertTriangle className="h-5 w-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-bold text-slate-900">{alert.product_name}</h3>
                    <Badge variant="danger" dot size="sm">
                      Low Stock
                    </Badge>
                  </div>
                  <p className="text-xs text-slate-600 mt-1">
                    Current balance is{' '}
                    <span className="font-bold text-rose-700">{alert.current_quantity}</span>, below reorder threshold of{' '}
                    <span className="font-bold text-slate-800">{alert.threshold}</span>.
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2 w-full sm:w-auto">
                <Link to="/manual" className="flex-1 sm:flex-none">
                  <Button variant="primary" size="sm" className="w-full font-bold bg-emerald-600 hover:bg-emerald-700">
                    <ArrowDownRight className="w-4 h-4 mr-1.5" />
                    Restock Now
                  </Button>
                </Link>
                <Button
                  variant="secondary"
                  size="sm"
                  className="flex-1 sm:flex-none"
                  onClick={() => resolveMutation.mutate(alert.id)}
                  isLoading={resolveMutation.isPending}
                >
                  <Check className="h-4 w-4 mr-1.5" />
                  Dismiss
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
