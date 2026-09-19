import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppLayout } from './components/layout/AppLayout';
import { LoginPage } from './features/auth/LoginPage';
import { DashboardPage } from './features/dashboard/DashboardPage';
import { VoiceButton } from './features/voice/VoiceButton';
import { VoiceModal } from './features/voice/VoiceModal';
import { ProductListPage } from './features/inventory/ProductListPage';
import { ProductFormPage } from './features/inventory/ProductFormPage';
import { TransactionHistoryPage } from './features/inventory/TransactionHistoryPage';
import { ManualEntryPage } from './features/inventory/ManualEntryPage';
import { AlertsPage } from './features/alerts/AlertsPage';
import { SettingsPage } from './features/settings/SettingsPage';
import { useAuthStore } from './stores/authStore';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false, staleTime: 15_000 },
  },
});

function VoiceOverlays() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  if (!isAuthenticated) return null;
  return (
    <>
      <VoiceButton />
      <VoiceModal />
    </>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<AppLayout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/products" element={<ProductListPage />} />
            <Route path="/products/new" element={<ProductFormPage />} />
            <Route path="/products/:id/edit" element={<ProductFormPage />} />
            <Route path="/transactions" element={<TransactionHistoryPage />} />
            <Route path="/manual" element={<ManualEntryPage />} />
            <Route path="/alerts" element={<AlertsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        
        {/* Global Voice Components (authenticated only) */}
        <VoiceOverlays />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
