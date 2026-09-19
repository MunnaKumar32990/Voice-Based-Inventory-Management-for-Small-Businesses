import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mic, LogIn, UserPlus, Sparkles } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { useAuthStore } from '../../stores/authStore';
import { api } from '../../lib/api';

export const LoginPage: React.FC = () => {
  const [tab, setTab] = useState<'login' | 'signup'>('login');
  
  // Login form state
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');

  // Signup form state
  const [signupName, setSignupName] = useState('');
  const [signupEmail, setSignupEmail] = useState('');
  const [signupPassword, setSignupPassword] = useState('');
  const [signupShopName, setSignupShopName] = useState('');

  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  
  const login = useAuthStore((state) => state.login);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const navigate = useNavigate();

  // If already authenticated, redirect to dashboard
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg(null);

    try {
      const response = await api.post('/auth/login', {
        email: loginEmail,
        password: loginPassword,
      });
      const data = response.data;
      const token = data.access_token;
      if (!token) throw new Error('No token returned from server');

      login(
        token,
        { id: data.user_id, name: data.name, email: data.email },
        data.shop_id,
        data.shop_name || 'My Store'
      );
      navigate('/');
    } catch (error: any) {
      const msg = error?.response?.data?.detail || 'Login failed. Please check your credentials.';
      setErrorMsg(typeof msg === 'string' ? msg : 'Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignupSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg(null);

    try {
      const response = await api.post('/auth/signup', {
        name: signupName,
        email: signupEmail,
        password: signupPassword,
        shop_name: signupShopName,
      });
      const data = response.data;
      const token = data.access_token;
      if (!token) throw new Error('No token returned from server');

      login(
        token,
        { id: data.user_id, name: data.name, email: data.email },
        data.shop_id,
        data.shop_name || `${signupName}'s Store`
      );
      navigate('/');
    } catch (error: any) {
      const msg = error?.response?.data?.detail || 'Signup failed. Please try again.';
      setErrorMsg(typeof msg === 'string' ? msg : 'Registration failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setIsLoading(true);
    setErrorMsg(null);

    try {
      const response = await api.post('/auth/demo-login', { shop_name: 'Kumar General Store' });
      const data = response.data;
      const token = data.access_token || data.token;
      if (!token) throw new Error('No token returned');

      login(
        token,
        { id: data.user_id || 'demo-user', name: data.name || 'Demo User' },
        data.shop_id || 'demo-shop',
        data.shop_name || 'Kumar General Store'
      );
      navigate('/');
    } catch (error: any) {
      const msg = error?.response?.data?.detail || 'Demo login failed.';
      setErrorMsg(typeof msg === 'string' ? msg : 'Demo login failed.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-6 bg-white p-8 sm:p-10 rounded-3xl shadow-xl border border-slate-100">
        
        {/* Brand Header */}
        <div className="text-center">
          <div className="mx-auto h-20 w-20 bg-indigo-600 rounded-2xl flex items-center justify-center shadow-lg shadow-indigo-200">
            <Mic className="h-10 w-10 text-white" />
          </div>
          <h2 className="mt-4 text-3xl font-extrabold text-gray-900 tracking-tight">
            VoiceStock
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Multilingual Voice-Powered Inventory Platform
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex bg-slate-100 p-1.5 rounded-2xl">
          <button
            type="button"
            onClick={() => { setTab('login'); setErrorMsg(null); }}
            className={`flex-1 py-2 text-sm font-bold rounded-xl transition-all flex items-center justify-center gap-2 ${
              tab === 'login'
                ? 'bg-white text-indigo-700 shadow-sm'
                : 'text-slate-600 hover:text-gray-900'
            }`}
          >
            <LogIn className="w-4 h-4" />
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setTab('signup'); setErrorMsg(null); }}
            className={`flex-1 py-2 text-sm font-bold rounded-xl transition-all flex items-center justify-center gap-2 ${
              tab === 'signup'
                ? 'bg-white text-indigo-700 shadow-sm'
                : 'text-slate-600 hover:text-gray-900'
            }`}
          >
            <UserPlus className="w-4 h-4" />
            Sign Up
          </button>
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div className="rounded-xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700 font-medium animate-in fade-in" role="alert">
            {errorMsg}
          </div>
        )}

        {/* Login Form */}
        {tab === 'login' && (
          <form className="space-y-4" onSubmit={handleLoginSubmit}>
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                Email / Username
              </label>
              <Input
                type="email"
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
                required
                className="rounded-xl"
                placeholder="you@example.com"
                autoComplete="email"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                Password
              </label>
              <Input
                type="password"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
                required
                className="rounded-xl"
                placeholder="••••••••"
                autoComplete="current-password"
              />
            </div>

            <Button
              type="submit"
              className="w-full flex justify-center py-3.5 px-4 border border-transparent rounded-xl text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 shadow-md shadow-indigo-100 min-h-[50px]"
              isLoading={isLoading}
            >
              Sign In to Your Inventory
            </Button>
          </form>
        )}

        {/* Signup Form */}
        {tab === 'signup' && (
          <form className="space-y-4" onSubmit={handleSignupSubmit}>
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                Your Full Name
              </label>
              <Input
                type="text"
                value={signupName}
                onChange={(e) => setSignupName(e.target.value)}
                required
                className="rounded-xl"
                placeholder="e.g. Ramesh Kumar"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                Email Address
              </label>
              <Input
                type="email"
                value={signupEmail}
                onChange={(e) => setSignupEmail(e.target.value)}
                required
                className="rounded-xl"
                placeholder="you@example.com"
                autoComplete="email"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                Password (min 6 chars)
              </label>
              <Input
                type="password"
                value={signupPassword}
                onChange={(e) => setSignupPassword(e.target.value)}
                required
                minLength={6}
                className="rounded-xl"
                placeholder="••••••••"
                autoComplete="new-password"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                Shop / Business Name <span className="text-gray-400 font-normal">(optional)</span>
              </label>
              <Input
                type="text"
                value={signupShopName}
                onChange={(e) => setSignupShopName(e.target.value)}
                className="rounded-xl"
                placeholder="e.g. Kumar General Store"
              />
            </div>

            <Button
              type="submit"
              className="w-full flex justify-center py-3.5 px-4 border border-transparent rounded-xl text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 shadow-md shadow-indigo-100 min-h-[50px]"
              isLoading={isLoading}
            >
              Create Account & Workspace
            </Button>
          </form>
        )}

        {/* Divider */}
        <div className="relative my-4">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-slate-200" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-white px-2 text-slate-400 font-semibold">Or Instant Testing</span>
          </div>
        </div>

        {/* Demo Mode Button */}
        <button
          type="button"
          onClick={handleDemoLogin}
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl border-2 border-dashed border-indigo-200 bg-indigo-50/50 hover:bg-indigo-50 text-indigo-700 font-semibold text-sm transition-all hover:border-indigo-300"
        >
          <Sparkles className="w-4 h-4 text-indigo-500" />
          <span>Launch Demo Store (Pre-loaded items)</span>
        </button>

        {/* Features preview */}
        <div className="pt-2 text-center text-xs text-gray-400 flex justify-center gap-4">
          <span>🔒 User-Isolated Inventory</span>
          <span>•</span>
          <span>🎤 Multilingual Voice AI</span>
        </div>
      </div>
    </div>
  );
};

