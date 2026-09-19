// Backend-aligned inventory types.
export type Operation = 'STOCK_IN' | 'STOCK_OUT' | 'ADJUSTMENT';

export interface Transaction {
  id: string;
  product_id: string;
  product_name?: string;
  operation: Operation;
  quantity: number;
  unit: string;
  source: 'voice' | 'manual' | 'system';
  reason?: string;
  price_total?: number;
  created_at: string;
}

export interface StockBalance {
  product_id: string;
  product_name?: string;
  quantity: number;
  unit: string;
  reorder_threshold?: number;
  status?: string;
}

export interface DashboardProduct {
  id: string;
  name: string;
  quantity: number;
  unit: string;
  reorder_threshold: number;
  category?: string;
  status: string;
}

export interface DashboardSummary {
  today_stock_in: number;
  today_stock_out: number;
  low_stock_count: number;
  total_products: number;
  products: DashboardProduct[];
}
