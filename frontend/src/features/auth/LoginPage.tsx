import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mic } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { useAuthStore } from '../../stores/authStore';
import { api } from '../../lib/api';

export const LoginPage: React.FC = () => {
  const [shopName, setShopName] = useState('Kumar General Store');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const login = useAuthStore((state) => state.login);
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg(null);
    
    try {
      const response = await api.post('/auth/demo-login', { shop_name: shopName });
      const data = response.data;
      const token: string = data.access_token || data.token;
      if (!token) {
        throw new Error('Login response did not include a token');
      }
      login(
        token,
        { id: data.user_id || 'demo-user', name: 'Demo User' },
        data.shop_id || 'demo-shop',
        data.shop_name || shopName
      );
      navigate('/');
    } catch (error: unknown) {
      console.error('Login failed', error);
      const msg =
        (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Could not reach the backend. Start the FastAPI server (uvicorn app.main:app) and MongoDB, then try again.';
      setErrorMsg(typeof msg === 'string' ? msg : 'Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-2xl shadow-xl">
        <div className="text-center">
          <div className="mx-auto h-24 w-24 bg-indigo-100 rounded-full flex items-center justify-center">
            <Mic className="h-12 w-12 text-indigo-600" />
          </div>
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            VoiceStock
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Voice-Based Inventory Management for Local Shops
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleLogin}>
          <div className="rounded-md shadow-sm -space-y-px">
            <Input
              label="Shop Name"
              value={shopName}
              onChange={(e) => setShopName(e.target.value)}
              required
              className="rounded-xl"
              placeholder="Enter your shop name"
            />
          </div>

          {errorMsg && (
            <div className="rounded-xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700" role="alert">
              {errorMsg}
            </div>
          )}

          <div>
            <Button
              type="submit"
              className="w-full flex justify-center py-3 px-4 border border-transparent rounded-xl text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 min-h-[56px]"
              isLoading={isLoading}
            >
              Start Demo
            </Button>
          </div>
        </form>
        
        <div className="mt-6 text-center text-sm text-gray-500">
          <p>Features include:</p>
          <ul className="mt-2 space-y-1">
            <li>🎤 Voice Commands (English, Hindi, Telugu)</li>
            <li>📦 Instant Stock Updates</li>
            <li>⚠️ Low Stock Alerts</li>
          </ul>
        </div>
      </div>
    </div>
  );
};
