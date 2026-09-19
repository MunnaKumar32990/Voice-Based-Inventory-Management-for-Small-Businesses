import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Modal } from '../../components/ui/Modal';
import { useToast } from '../../components/ui/Toast';
import {
  Plus,
  Search,
  Edit2,
  Package,
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  Eye,
  X,
  History,
} from 'lucide-react';
import { api } from '../../lib/api';

interface Product {
  id: string;
  display_name: string;
  category: string;
  quantity: number;
  reorder_threshold: number;
  base_unit: string;
  status: string;
  aliases?: Array<{ text: string; language: string }>;
}

interface Txn {
  id: string;
  product_name: string;
  operation: string;
  quantity: number;
  unit: string;
  created_at: string;
  source?: string;
}

export const ProductListPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();

  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'HEALTHY' | 'LOW' | 'OUT'>('ALL');

  // Product Details Modal State
  const [activeProduct, setActiveProduct] = useState<Product | null>(null);
  const [quickQty, setQuickQty] = useState<string>('5');

  const { data, isLoading, isError } = useQuery({
    queryKey: ['products', search],
    queryFn: async () =>
      (await api.get<{ products: Product[] }>('/products/', { params: search ? { search } : {} })).data,
  });

  // Recent transactions for the active product in detail modal
  const { data: productTxns } = useQuery({
    queryKey: ['transactions', activeProduct?.id],
    queryFn: async () =>
      (await api.get<{ transactions: Txn[] }>('/inventory/transactions', { params: { product_id: activeProduct?.id, limit: 10 } })).data,
    enabled: !!activeProduct?.id,
  });

  // Quick Stock mutation (In or Out)
  const quickStockMutation = useMutation({
    mutationFn: async ({ productId, operation, quantity, unit }: { productId: string; operation: 'STOCK_IN' | 'STOCK_OUT'; quantity: number; unit: string }) => {
      return (
        await api.post('/inventory/transactions', {
          product_id: productId,
          operation,
          quantity,
          unit,
          reason: `Quick ${operation === 'STOCK_IN' ? 'Restock' : 'Dispatch'}`,
          client_request_id: `quick_${Date.now()}_${productId}`,
        })
      ).data;
    },
    onSuccess: async (_, variables) => {
      await queryClient.invalidateQueries({ queryKey: ['products'] });
      await queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      await queryClient.invalidateQueries({ queryKey: ['transactions'] });
      await queryClient.invalidateQueries({ queryKey: ['alerts'] });

      const opName = variables.operation === 'STOCK_IN' ? 'Stock Added' : 'Stock Removed';
      success(opName, `${variables.quantity} ${variables.unit} updated successfully.`);

      // Update local modal view if open
      if (activeProduct && activeProduct.id === variables.productId) {
        const delta = variables.operation === 'STOCK_IN' ? variables.quantity : -variables.quantity;
        const newQty = Math.max(0, activeProduct.quantity + delta);
        setActiveProduct({
          ...activeProduct,
          quantity: newQty,
          status: newQty <= 0 ? 'OUT' : newQty <= activeProduct.reorder_threshold ? 'LOW' : 'OK',
        });
      }
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.detail || 'Stock update failed.';
      toastError('Update Failed', typeof msg === 'string' ? msg : 'Check stock availability.');
    },
  });

  const allProducts = data?.products ?? [];

  // Extract unique categories
  const categories = ['ALL', ...Array.from(new Set(allProducts.map((p) => p.category).filter(Boolean)))];

  // Filtering
  const filteredProducts = allProducts.filter((p) => {
    const matchesCategory = selectedCategory === 'ALL' || p.category === selectedCategory;
    const isOut = p.status === 'OUT' || p.quantity <= 0;
    const isLow = p.status === 'LOW' && p.quantity > 0;
    const isHealthy = !isOut && !isLow;

    const matchesStatus =
      statusFilter === 'ALL' ||
      (statusFilter === 'HEALTHY' && isHealthy) ||
      (statusFilter === 'LOW' && isLow) ||
      (statusFilter === 'OUT' && isOut);

    return matchesCategory && matchesStatus;
  });

  // Summary counts
  const totalCount = allProducts.length;
  const outCount = allProducts.filter((p) => p.status === 'OUT' || p.quantity <= 0).length;
  const lowCount = allProducts.filter((p) => p.status === 'LOW' && p.quantity > 0).length;
  const healthyCount = Math.max(0, totalCount - outCount - lowCount);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200/80">
        <div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            {t('products.title', 'Inventory Catalog')}
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Manage your store catalog, check live stock balances, and configure reorder levels.
          </p>
        </div>
        <Link to="/products/new" className="w-full sm:w-auto">
          <Button variant="primary" className="w-full sm:w-auto font-bold shadow-md shadow-indigo-200">
            <Plus className="h-4 w-4 mr-2" />
            {t('products.addProduct', 'Add New Product')}
          </Button>
        </Link>
      </div>

      {/* Summary KPI Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <button
          onClick={() => setStatusFilter('ALL')}
          className={`p-3.5 rounded-2xl border text-left transition-all cursor-pointer ${
            statusFilter === 'ALL'
              ? 'bg-indigo-50/80 border-indigo-300 ring-2 ring-indigo-500/20 shadow-xs'
              : 'bg-white border-slate-200 hover:bg-slate-50'
          }`}
        >
          <div className="text-xs font-bold uppercase tracking-wider text-slate-500">All Items</div>
          <div className="text-2xl font-black text-slate-900 mt-0.5">{totalCount}</div>
        </button>

        <button
          onClick={() => setStatusFilter('HEALTHY')}
          className={`p-3.5 rounded-2xl border text-left transition-all cursor-pointer ${
            statusFilter === 'HEALTHY'
              ? 'bg-emerald-50/80 border-emerald-300 ring-2 ring-emerald-500/20 shadow-xs'
              : 'bg-white border-slate-200 hover:bg-slate-50'
          }`}
        >
          <div className="text-xs font-bold uppercase tracking-wider text-emerald-700">Healthy Stock</div>
          <div className="text-2xl font-black text-emerald-700 mt-0.5">{healthyCount}</div>
        </button>

        <button
          onClick={() => setStatusFilter('LOW')}
          className={`p-3.5 rounded-2xl border text-left transition-all cursor-pointer ${
            statusFilter === 'LOW'
              ? 'bg-amber-50/80 border-amber-300 ring-2 ring-amber-500/20 shadow-xs'
              : 'bg-white border-slate-200 hover:bg-slate-50'
          }`}
        >
          <div className="text-xs font-bold uppercase tracking-wider text-amber-700">Low Stock</div>
          <div className="text-2xl font-black text-amber-700 mt-0.5">{lowCount}</div>
        </button>

        <button
          onClick={() => setStatusFilter('OUT')}
          className={`p-3.5 rounded-2xl border text-left transition-all cursor-pointer ${
            statusFilter === 'OUT'
              ? 'bg-rose-50/80 border-rose-300 ring-2 ring-rose-500/20 shadow-xs'
              : 'bg-white border-slate-200 hover:bg-slate-50'
          }`}
        >
          <div className="text-xs font-bold uppercase tracking-wider text-rose-700">Out of Stock</div>
          <div className="text-2xl font-black text-rose-700 mt-0.5">{outCount}</div>
        </button>
      </div>

      {/* Search & Category Filter Toolbar */}
      <Card className="p-4 sm:p-5">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1 relative">
            <Input
              placeholder="Search products by name or alias (e.g. Rice, Chawal)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              leftIcon={<Search className="h-4 w-4" />}
              rightIcon={
                search ? (
                  <button
                    onClick={() => setSearch('')}
                    className="text-slate-400 hover:text-slate-600 p-1 cursor-pointer"
                  >
                    <X className="h-4 w-4" />
                  </button>
                ) : undefined
              }
            />
          </div>

          <div className="sm:w-56">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="block w-full rounded-xl border border-slate-200 bg-white text-slate-900 text-sm focus:outline-none focus:border-indigo-500 focus:ring-3 focus:ring-indigo-100 min-h-[44px] px-3.5 font-medium cursor-pointer"
            >
              {categories.map((c) => (
                <option key={c} value={c}>
                  {c === 'ALL' ? 'All Categories' : c}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Product Table or Grid */}
        <div className="mt-6">
          {isLoading ? (
            <div className="space-y-3 py-4 animate-pulse">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="h-14 bg-slate-100 rounded-xl" />
              ))}
            </div>
          ) : isError ? (
            <div className="text-center py-12 text-rose-600">
              <AlertTriangle className="w-8 h-8 mx-auto mb-2 text-rose-500" />
              <p className="font-bold text-sm">Could not load products. Please check server connection.</p>
            </div>
          ) : allProducts.length === 0 ? (
            /* Empty Inventory State */
            <div className="py-16 text-center max-w-sm mx-auto">
              <div className="w-16 h-16 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto mb-4">
                <Package className="w-8 h-8" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-1">Your inventory is empty</h3>
              <p className="text-xs text-slate-500 mb-6 leading-relaxed">
                Add your first product manually or tap the microphone to tell the assistant what you want to add.
              </p>
              <Link to="/products/new">
                <Button variant="primary" size="md" className="font-bold">
                  <Plus className="w-4 h-4 mr-1.5" />
                  Add Your First Product
                </Button>
              </Link>
            </div>
          ) : filteredProducts.length === 0 ? (
            /* No Search Results */
            <div className="py-12 text-center text-slate-500">
              <Search className="w-8 h-8 text-slate-300 mx-auto mb-2" />
              <h4 className="font-bold text-slate-900 text-sm">No products found</h4>
              <p className="text-xs text-slate-400 mt-1">
                No products match &ldquo;{search}&rdquo; in the selected filter.
              </p>
              <Button
                variant="secondary"
                size="sm"
                className="mt-4"
                onClick={() => {
                  setSearch('');
                  setSelectedCategory('ALL');
                  setStatusFilter('ALL');
                }}
              >
                Reset Filters
              </Button>
            </div>
          ) : (
            <>
              {/* Desktop Table View */}
              <div className="hidden md:block overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-100">
                  <thead>
                    <tr className="text-left text-xs font-bold uppercase tracking-wider text-slate-400">
                      <th scope="col" className="pb-3 pl-3">Product Name</th>
                      <th scope="col" className="pb-3 px-4">Category</th>
                      <th scope="col" className="pb-3 px-4">Current Stock</th>
                      <th scope="col" className="pb-3 px-4">Reorder Level</th>
                      <th scope="col" className="pb-3 px-4">Status</th>
                      <th scope="col" className="pb-3 pr-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-sm">
                    {filteredProducts.map((p) => {
                      const isOut = p.status === 'OUT' || p.quantity <= 0;
                      const isLow = p.status === 'LOW' && p.quantity > 0;
                      const statusVariant = isOut ? 'danger' : isLow ? 'warning' : 'success';
                      const statusLabel = isOut ? 'Out of Stock' : isLow ? 'Low Stock' : 'Healthy';

                      return (
                        <tr
                          key={p.id}
                          className="hover:bg-slate-50/80 transition-colors group cursor-pointer"
                          onClick={() => setActiveProduct(p)}
                        >
                          <td className="py-3.5 pl-3">
                            <div className="font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                              {p.display_name}
                            </div>
                            {p.aliases && p.aliases.length > 0 && (
                              <div className="text-[11px] text-slate-400">
                                Aliases: {p.aliases.map((a) => a.text).join(', ')}
                              </div>
                            )}
                          </td>
                          <td className="py-3.5 px-4 text-slate-600 font-medium">
                            <span className="px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 text-xs font-semibold">
                              {p.category || 'General'}
                            </span>
                          </td>
                          <td className="py-3.5 px-4">
                            <span className="font-black text-slate-900 text-base">
                              {p.quantity} <span className="text-xs font-medium text-slate-500">{p.base_unit}</span>
                            </span>
                          </td>
                          <td className="py-3.5 px-4 text-slate-500 font-medium text-xs">
                            {p.reorder_threshold} {p.base_unit}
                          </td>
                          <td className="py-3.5 px-4">
                            <Badge variant={statusVariant} dot>
                              {statusLabel}
                            </Badge>
                          </td>
                          <td className="py-3.5 pr-3 text-right" onClick={(e) => e.stopPropagation()}>
                            <div className="flex items-center justify-end gap-1.5">
                              <button
                                onClick={() => setActiveProduct(p)}
                                className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors cursor-pointer"
                                title="View Details"
                              >
                                <Eye className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => navigate(`/products/${p.id}/edit`)}
                                className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors cursor-pointer"
                                title="Edit Product"
                              >
                                <Edit2 className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() =>
                                  quickStockMutation.mutate({
                                    productId: p.id,
                                    operation: 'STOCK_IN',
                                    quantity: 5,
                                    unit: p.base_unit,
                                  })
                                }
                                disabled={quickStockMutation.isPending}
                                className="p-1.5 text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors font-bold text-xs flex items-center cursor-pointer"
                                title="Quick Restock (+5)"
                              >
                                +5
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Mobile Card Grid View */}
              <div className="md:hidden space-y-3">
                {filteredProducts.map((p) => {
                  const isOut = p.status === 'OUT' || p.quantity <= 0;
                  const isLow = p.status === 'LOW' && p.quantity > 0;
                  const statusVariant = isOut ? 'danger' : isLow ? 'warning' : 'success';
                  const statusLabel = isOut ? 'Out of Stock' : isLow ? 'Low Stock' : 'Healthy';

                  return (
                    <div
                      key={p.id}
                      onClick={() => setActiveProduct(p)}
                      className="p-4 rounded-2xl border border-slate-200 bg-white hover:border-slate-300 transition-all cursor-pointer shadow-xs space-y-3"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <h4 className="font-bold text-slate-900 text-base">{p.display_name}</h4>
                          <span className="text-xs text-slate-500 font-medium">
                            {p.category || 'General'}
                          </span>
                        </div>
                        <Badge variant={statusVariant} dot>
                          {statusLabel}
                        </Badge>
                      </div>

                      <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                        <div>
                          <div className="text-[10px] uppercase font-bold text-slate-400">Current Stock</div>
                          <div className="text-lg font-black text-slate-900">
                            {p.quantity} <span className="text-xs font-normal text-slate-500">{p.base_unit}</span>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-[10px] uppercase font-bold text-slate-400">Reorder Level</div>
                          <div className="text-sm font-semibold text-slate-600">
                            {p.reorder_threshold} {p.base_unit}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center justify-between pt-2 border-t border-slate-100" onClick={(e) => e.stopPropagation()}>
                        <span className="text-xs font-bold text-indigo-600 flex items-center">
                          Tap for details <Eye className="w-3.5 h-3.5 ml-1" />
                        </span>
                        <div className="flex items-center gap-1.5">
                          <button
                            onClick={() => navigate(`/products/${p.id}/edit`)}
                            className="p-1.5 text-slate-500 hover:text-indigo-600 hover:bg-slate-100 rounded-lg text-xs font-semibold"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() =>
                              quickStockMutation.mutate({
                                productId: p.id,
                                operation: 'STOCK_IN',
                                quantity: 5,
                                unit: p.base_unit,
                              })
                            }
                            className="px-2.5 py-1 text-xs font-bold text-emerald-700 bg-emerald-50 rounded-lg border border-emerald-200"
                          >
                            +5 Restock
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>
      </Card>

      {/* Product Details & Quick Stock Modal */}
      {activeProduct && (
        <Modal
          isOpen={!!activeProduct}
          onClose={() => setActiveProduct(null)}
          size="lg"
          title={
            <div className="flex items-center gap-2">
              <Package className="w-5 h-5 text-indigo-600" />
              <span>{activeProduct.display_name}</span>
            </div>
          }
        >
          <div className="space-y-6">
            {/* Top Product Meta & Stock Highlight */}
            <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200/80 flex flex-col sm:flex-row items-center justify-between gap-4 text-center sm:text-left">
              <div>
                <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-white text-slate-700 border border-slate-200">
                  {activeProduct.category || 'General'}
                </span>
                <h3 className="text-2xl font-black text-slate-900 mt-2">
                  {activeProduct.display_name}
                </h3>
                <p className="text-xs text-slate-500 mt-1">
                  Reorder Threshold: <span className="font-bold text-slate-700">{activeProduct.reorder_threshold} {activeProduct.base_unit}</span>
                </p>
              </div>

              <div className="text-center sm:text-right">
                <div className="text-xs font-bold uppercase tracking-wider text-slate-400">Current Balance</div>
                <div className="text-4xl font-black text-slate-900 tracking-tight my-1">
                  {activeProduct.quantity}{' '}
                  <span className="text-base font-bold text-slate-500">{activeProduct.base_unit}</span>
                </div>
                <Badge
                  variant={
                    activeProduct.quantity <= 0
                      ? 'danger'
                      : activeProduct.quantity <= activeProduct.reorder_threshold
                        ? 'warning'
                        : 'success'
                  }
                  dot
                >
                  {activeProduct.quantity <= 0
                    ? 'Out of Stock'
                    : activeProduct.quantity <= activeProduct.reorder_threshold
                      ? 'Low Stock Alert'
                      : 'Healthy Stock'}
                </Badge>
              </div>
            </div>

            {/* Quick Stock In / Stock Out Action Card */}
            <div className="p-5 rounded-2xl border-2 border-indigo-100 bg-white shadow-xs">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                Quick Stock Adjustment
              </h4>
              <div className="flex flex-col sm:flex-row items-center gap-3">
                <div className="w-full sm:w-32">
                  <Input
                    label="Quantity"
                    type="number"
                    min="1"
                    step="any"
                    value={quickQty}
                    onChange={(e) => setQuickQty(e.target.value)}
                  />
                </div>

                <div className="flex gap-2 w-full sm:w-auto sm:mt-5">
                  <Button
                    variant="primary"
                    className="flex-1 sm:flex-none bg-emerald-600 hover:bg-emerald-700 text-white font-bold"
                    isLoading={quickStockMutation.isPending}
                    onClick={() => {
                      const q = Number(quickQty);
                      if (!q || q <= 0) return;
                      quickStockMutation.mutate({
                        productId: activeProduct.id,
                        operation: 'STOCK_IN',
                        quantity: q,
                        unit: activeProduct.base_unit,
                      });
                    }}
                  >
                    <ArrowDownRight className="w-4 h-4 mr-1.5" />
                    + Stock In
                  </Button>

                  <Button
                    variant="secondary"
                    className="flex-1 sm:flex-none text-blue-600 border-blue-200 hover:bg-blue-50 font-bold"
                    isLoading={quickStockMutation.isPending}
                    onClick={() => {
                      const q = Number(quickQty);
                      if (!q || q <= 0) return;
                      quickStockMutation.mutate({
                        productId: activeProduct.id,
                        operation: 'STOCK_OUT',
                        quantity: q,
                        unit: activeProduct.base_unit,
                      });
                    }}
                  >
                    <ArrowUpRight className="w-4 h-4 mr-1.5" />
                    - Stock Out
                  </Button>
                </div>
              </div>
            </div>

            {/* Recent Product Stock Movements */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                  <History className="w-4 h-4 text-indigo-600" />
                  Product Transaction History
                </h4>
                <span className="text-xs text-slate-400">Latest records</span>
              </div>

              {productTxns?.transactions && productTxns.transactions.length > 0 ? (
                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {productTxns.transactions.map((tx) => {
                    const isIn = tx.operation === 'STOCK_IN';
                    return (
                      <div
                        key={tx.id}
                        className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-200/60 text-xs"
                      >
                        <div className="flex items-center gap-2">
                          <span
                            className={`w-5 h-5 rounded-full flex items-center justify-center font-bold text-[10px] ${
                              isIn ? 'bg-emerald-100 text-emerald-800' : 'bg-blue-100 text-blue-800'
                            }`}
                          >
                            {isIn ? '↓' : '↑'}
                          </span>
                          <span className="text-slate-500">
                            {tx.created_at
                              ? new Date(tx.created_at).toLocaleDateString([], {
                                  month: 'short',
                                  day: 'numeric',
                                  hour: '2-digit',
                                  minute: '2-digit',
                                })
                              : 'Recent'}
                          </span>
                        </div>
                        <span
                          className={`font-bold px-2 py-0.5 rounded ${
                            isIn ? 'text-emerald-700 bg-emerald-50' : 'text-blue-700 bg-blue-50'
                          }`}
                        >
                          {isIn ? '+' : '-'}{tx.quantity} {tx.unit}
                        </span>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-xs text-slate-400 py-3 text-center bg-slate-50 rounded-xl">
                  No stock movements recorded for this item yet.
                </p>
              )}
            </div>

            {/* Footer Actions */}
            <div className="flex justify-between items-center pt-2 border-t border-slate-100">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => navigate(`/products/${activeProduct.id}/edit`)}
              >
                <Edit2 className="w-3.5 h-3.5 mr-1.5" />
                Edit Full Details
              </Button>
              <Button variant="primary" size="sm" onClick={() => setActiveProduct(null)}>
                Close
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
