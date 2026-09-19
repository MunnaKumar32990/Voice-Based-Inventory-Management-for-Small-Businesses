// Backend-aligned types. API shapes:
//   GET /products/ -> { products: [{ id, display_name, category, base_unit,
//     reorder_threshold, quantity, status, ... }], total }
//   GET /inventory/transactions -> { transactions: [{ id, product_id,
//     product_name, operation: STOCK_IN|STOCK_OUT|ADJUSTMENT, quantity, unit,
//     source, created_at }], total }

export interface Product {
  id: string;
  display_name: string;
  name?: string;
  category: string;
  base_unit: string;
  allowed_units?: string[];
  reorder_threshold: number;
  quantity?: number;
  status?: string;
  aliases?: ProductAlias[];
  conversions?: UnitConversion[];
}

export interface ProductAlias {
  text: string;
  normalized?: string;
  language?: string;
}

export interface UnitConversion {
  from_unit: string;
  to_unit: string;
  factor: number;
}

export interface ProductFormData {
  display_name: string;
  category: string;
  base_unit: string;
  reorder_threshold: number;
  aliases: string[];
}
