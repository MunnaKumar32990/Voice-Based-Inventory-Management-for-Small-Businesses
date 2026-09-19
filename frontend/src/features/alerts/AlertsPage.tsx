import { useTranslation } from 'react-i18next';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Card } from '../../components/ui/Card';
import { AlertTriangle, Check } from 'lucide-react';
import { Button } from '../../components/ui/Button';
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

  const { data, isLoading, isError } = useQuery({
    queryKey: ['alerts'],
    queryFn: async () => (await api.get<{ alerts: Alert[] }>('/alerts/')).data,
  });

  const resolveMutation = useMutation({
    mutationFn: async (alertId: string) => (await api.post(`/alerts/${alertId}/resolve`)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['alerts'] });
      await queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });

  const alerts = data?.alerts ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">{t('alerts.title')}</h1>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="w-10 h-10 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
        </div>
      ) : isError ? (
        <p className="text-center text-red-600 py-8">{t('common.error')}: could not load alerts.</p>
      ) : alerts.length === 0 ? (
        <Card>
          <p className="text-center text-gray-500 py-8">{t('common.noData')}</p>
        </Card>
      ) : (
        <div className="space-y-4">
          {alerts.map((alert) => (
            <Card key={alert.id} className="border-l-4 border-l-red-500">
              <div className="flex items-start sm:items-center justify-between flex-col sm:flex-row gap-4">
                <div className="flex items-start space-x-4">
                  <div className="p-2 bg-red-100 rounded-full mt-1 sm:mt-0">
                    <AlertTriangle className="h-6 w-6 text-red-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{alert.product_name}</h3>
                    <p className="text-gray-600 mt-1">
                      Current stock ({alert.current_quantity}) is below reorder threshold ({alert.threshold}).
                    </p>
                  </div>
                </div>
                <div className="w-full sm:w-auto">
                  <Button
                    variant="secondary"
                    className="w-full sm:w-auto"
                    onClick={() => resolveMutation.mutate(alert.id)}
                    isLoading={resolveMutation.isPending}
                  >
                    <Check className="h-4 w-4 mr-2" />
                    {t('alerts.resolve')}
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
