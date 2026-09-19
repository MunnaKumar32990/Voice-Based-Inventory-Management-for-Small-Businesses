import React from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import {
  Package,
  ArrowDownRight,
  ArrowUpRight,
  AlertTriangle,
  Plus,
  ArrowLeftRight,
  Clock,
  CheckCircle2,
  ChevronRight,
  Mic,
} from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
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
  source?: string;
  created_at: string;
}

export const DashboardPage: React.FC = () => {
  const { t } = useTranslation();
  const shopName = useAuthStore((s) => s.shopName);
  const user = useAuthStore((s) => s.user);

  const { data: summary, isLoading, isError } = useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => (await api.get<DashboardSummary>('/dashboard/summary')).data,
  });

  const { data: recent } = useQuery({
    queryKey: ['transactions', 'recent'],
    queryFn: async () =>
      (await api.get<{ transactions: Txn[] }>('/inventory/transactions', { params: { limit: 6 } })).data,
  });

  // Skeleton Loader for smooth initial render
  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="h-8 bg-slate-200 rounded-xl w-64" />
          <div className="flex gap-2">
            <div className="h-10 bg-slate-200 rounded-xl w-32" />
            <div className="h-10 bg-slate-200 rounded-xl w-32" />
          </div>
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-slate-200 rounded-2xl" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-72 bg-slate-200 rounded-2xl" />
          <div className="h-72 bg-slate-200 rounded-2xl" />
        </div>
      </div>
    );
  }

  if (isError || !summary) {
    return (
      <div className="rounded-2xl bg-rose-50 border border-rose-200 p-8 text-center max-w-lg mx-auto my-12 shadow-sm">
        <AlertTriangle className="w-10 h-10 text-rose-500 mx-auto mb-3" />
        <h3 className="text-lg font-bold text-rose-950 mb-1">Could not load dashboard data</h3>
        <p className="text-sm text-rose-700 mb-5">
          Please check that the backend server is running and your session is valid.
        </p>
        <Button variant="secondary" onClick={() => window.location.reload()}>
          Retry Connection
        </Button>
      </div>
    );
  }

  const products = summary.products || [];
  const lowStockItems = products.filter((p) => p.status === 'LOW' || p.status === 'OUT');
  const recentTransactions = recent?.transactions ?? [];

  // Health distribution calculations
  const outCount = products.filter((p) => p.status === 'OUT' || p.quantity <= 0).length;
  const lowCount = products.filter((p) => p.status === 'LOW' && p.quantity > 0).length;
  const healthyCount = Math.max(0, summary.total_products - outCount - lowCount);

  const healthyPct = summary.total_products > 0 ? (healthyCount / summary.total_products) * 100 : 100;
  const lowPct = summary.total_products > 0 ? (lowCount / summary.total_products) * 100 : 0;
  const outPct = summary.total_products > 0 ? (outCount / summary.total_products) * 100 : 0;

  return (
    <div className="space-y-8">
      {/* Dashboard Command Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200/80">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
              {shopName || 'My Store'}
            </h1>
            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Active Store
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Welcome back, <span className="font-semibold text-slate-700">{user?.name || 'Owner'}</span>.
            Here is your live inventory status.
          </p>
        </div>

        {/* Quick Action Toolbar */}
        <div className="flex items-center gap-2.5 flex-wrap">
          <Link to="/products/new">
            <Button variant="primary" size="sm" className="font-bold shadow-xs shadow-indigo-200">
              <Plus className="w-4 h-4 mr-1.5" />
              Add Product
            </Button>
          </Link>
          <Link to="/manual">
            <Button variant="secondary" size="sm" className="font-bold">
              <ArrowLeftRight className="w-4 h-4 mr-1.5 text-slate-500" />
              Manual Stock In/Out
            </Button>
          </Link>
        </div>
      </div>

      {/* 4 Stat Overview Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Products */}
        <Card hover className="bg-white border-slate-200/80">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              {t('dashboard.totalProducts', 'Total Products')}
            </span>
            <div className="w-8 h-8 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <Package className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-black text-slate-900 tracking-tight">
            {summary.total_products}
          </div>
          <div className="mt-2 flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-100">
            <span>{healthyCount} in healthy stock</span>
            <span className="font-semibold text-indigo-600">Active</span>
          </div>
        </Card>

        {/* Today's Stock In */}
        <Card hover className="bg-white border-slate-200/80">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-700">
              {t('dashboard.todayIn', "Today's Stock In")}
            </span>
            <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <ArrowDownRight className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-black text-emerald-700 tracking-tight">
            +{summary.today_stock_in}
          </div>
          <div className="mt-2 flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-100">
            <span>Incoming inventory</span>
            <span className="font-semibold text-emerald-600">Today</span>
          </div>
        </Card>

        {/* Today's Stock Out */}
        <Card hover className="bg-white border-slate-200/80">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-700">
              {t('dashboard.todayOut', "Today's Stock Out")}
            </span>
            <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
              <ArrowUpRight className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-black text-blue-700 tracking-tight">
            -{summary.today_stock_out}
          </div>
          <div className="mt-2 flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-100">
            <span>Sales & dispatches</span>
            <span className="font-semibold text-blue-600">Today</span>
          </div>
        </Card>

        {/* Low Stock Urgent */}
        <Card hover className="bg-white border-slate-200/80">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-rose-700">
              {t('dashboard.lowStock', 'Low Stock Items')}
            </span>
            <div className="w-8 h-8 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-black text-rose-700 tracking-tight">
            {summary.low_stock_count}
          </div>
          <div className="mt-2 flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-100">
            <span>Needs reorder</span>
            <span className={summary.low_stock_count > 0 ? 'font-bold text-rose-600' : 'text-slate-400'}>
              {summary.low_stock_count > 0 ? 'Urgent' : 'All Good'}
            </span>
          </div>
        </Card>
      </div>

      {/* Visual Stock Health & Activity Bar */}
      {summary.total_products > 0 && (
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Inventory Health Breakdown</h3>
              <p className="text-xs text-slate-500">Live stock health across all active catalog items</p>
            </div>
            <div className="flex items-center gap-4 text-xs font-bold">
              <span className="flex items-center gap-1.5 text-emerald-700">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                Healthy ({healthyCount})
              </span>
              <span className="flex items-center gap-1.5 text-amber-700">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                Low ({lowCount})
              </span>
              <span className="flex items-center gap-1.5 text-rose-700">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
                Out of Stock ({outCount})
              </span>
            </div>
          </div>

          {/* Multi-segment Progress Bar */}
          <div className="w-full h-3 rounded-full bg-slate-100 overflow-hidden flex gap-0.5">
            <div
              style={{ width: `${healthyPct}%` }}
              className="h-full bg-emerald-500 transition-all duration-500"
              title={`Healthy: ${healthyCount}`}
            />
            <div
              style={{ width: `${lowPct}%` }}
              className="h-full bg-amber-400 transition-all duration-500"
              title={`Low Stock: ${lowCount}`}
            />
            <div
              style={{ width: `${outPct}%` }}
              className="h-full bg-rose-500 transition-all duration-500"
              title={`Out of Stock: ${outCount}`}
            />
          </div>
        </div>
      )}

      {/* Main 2 Columns: Low Stock Alerts & Recent Transactions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Low Stock Items Card */}
        <Card
          title={
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-rose-500" />
              <span>Low Stock & Reorder Alerts</span>
            </div>
          }
          action={
            <Link to="/alerts" className="text-xs font-bold text-indigo-600 hover:text-indigo-800 flex items-center">
              View All Alerts <ChevronRight className="w-3.5 h-3.5 ml-0.5" />
            </Link>
          }
        >
          {lowStockItems.length > 0 ? (
            <div className="divide-y divide-slate-100">
              {lowStockItems.map((item) => (
                <div key={item.id} className="py-3.5 flex items-center justify-between gap-3">
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">{item.name}</h4>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Threshold: <span className="font-semibold">{item.reorder_threshold} {item.unit}</span>
                      {item.category && ` • ${item.category}`}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={item.quantity <= 0 ? 'danger' : 'warning'} dot>
                      {item.quantity} {item.unit}
                    </Badge>
                    <Link to="/manual">
                      <Button variant="subtle" size="sm" className="h-8 px-2.5 text-xs">
                        + Restock
                      </Button>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-10 text-center text-slate-500">
              <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-2 opacity-80" />
              <h4 className="font-bold text-slate-900 text-sm">All products are healthy!</h4>
              <p className="text-xs text-slate-500 mt-0.5">No products are currently below reorder threshold.</p>
            </div>
          )}
        </Card>

        {/* Recent Transactions Card */}
        <Card
          title={
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-indigo-600" />
              <span>Recent Stock Movements</span>
            </div>
          }
          action={
            <Link to="/transactions" className="text-xs font-bold text-indigo-600 hover:text-indigo-800 flex items-center">
              Full History <ChevronRight className="w-3.5 h-3.5 ml-0.5" />
            </Link>
          }
        >
          {recentTransactions.length > 0 ? (
            <div className="divide-y divide-slate-100">
              {recentTransactions.map((tx) => {
                const isIn = tx.operation === 'STOCK_IN';
                return (
                  <div key={tx.id} className="py-3 flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
                          isIn ? 'bg-emerald-100 text-emerald-700' : 'bg-blue-100 text-blue-700'
                        }`}
                      >
                        {isIn ? <ArrowDownRight className="w-4 h-4" /> : <ArrowUpRight className="w-4 h-4" />}
                      </div>
                      <div>
                        <p className="text-sm font-bold text-slate-900 leading-snug">{tx.product_name}</p>
                        <div className="flex items-center gap-2 text-[11px] text-slate-400 mt-0.5">
                          <span>
                            {tx.created_at
                              ? new Date(tx.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                              : 'Recent'}
                          </span>
                          {tx.source && (
                            <>
                              <span>•</span>
                              <span className="capitalize">{tx.source}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className={`text-sm font-black ${isIn ? 'text-emerald-700' : 'text-blue-700'}`}>
                      {isIn ? '+' : '-'}{tx.quantity} {tx.unit}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="py-10 text-center text-slate-500">
              <Package className="w-10 h-10 text-slate-300 mx-auto mb-2" />
              <h4 className="font-bold text-slate-900 text-sm">No transactions yet</h4>
              <p className="text-xs text-slate-500 mt-0.5">
                Use voice assistant or the manual entry form to record transactions.
              </p>
            </div>
          )}
        </Card>
      </div>

      {/* Voice Assistant Promo Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-indigo-900 via-indigo-800 to-slate-900 p-6 text-white shadow-lg flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-white/10 backdrop-blur-md flex items-center justify-center shrink-0 border border-white/20">
            <Mic className="w-6 h-6 text-indigo-300" />
          </div>
          <div>
            <h4 className="text-base font-bold text-white">Voice Assistant is Ready</h4>
            <p className="text-xs text-indigo-200 mt-0.5">
              Tap the floating microphone below anytime to add stock or ask database queries in Hindi, English, or Telugu.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs font-semibold text-indigo-200 shrink-0">
          <span className="px-3 py-1.5 rounded-xl bg-white/10 border border-white/10">
            &ldquo;Total kitna products hai?&rdquo;
          </span>
          <span className="px-3 py-1.5 rounded-xl bg-white/10 border border-white/10 hidden md:inline">
            &ldquo;Rice kitna bacha hai?&rdquo;
          </span>
        </div>
      </div>
    </div>
  );
};
