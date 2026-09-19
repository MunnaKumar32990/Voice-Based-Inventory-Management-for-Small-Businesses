export const formatQuantity = (quantity: number, unit: string) => {
  return `${quantity.toLocaleString('en-IN', { maximumFractionDigits: 2 })} ${unit}`;
};

export const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount);
};

export const formatDate = (dateString: string) => {
  return new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(dateString));
};

export const getStockStatusColor = (current: number, threshold: number) => {
  if (current <= 0) return 'danger';
  if (current <= threshold) return 'warning';
  return 'success';
};

export const getStockStatusLabel = (current: number, threshold: number) => {
  if (current <= 0) return 'Out of Stock';
  if (current <= threshold) return 'Low Stock';
  return 'In Stock';
};
