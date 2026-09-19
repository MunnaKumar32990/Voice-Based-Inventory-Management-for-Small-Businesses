import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { Mic, LogIn, UserPlus, Sparkles, Eye, EyeOff, ArrowLeft, Store } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { useAuthStore } from '../../stores/authStore';
import { useToast } from '../../components/ui/Toast';
import { api } from '../../lib/api';

export const LoginPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const initialTab = searchParams.get('tab') === 'signup' ? 'signup' : 'login';
  const [tab, setTab] = useState<'login' | 'signup'>(initialTab);

  // Login form state
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [showLoginPassword, setShowLoginPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);

  // Signup form state
  const [signupName, setSignupName] = useState('');
  const [signupEmail, setSignupEmail] = useState('');
  const [signupPassword, setSignupPassword] = useState('');
  const [signupConfirmPassword, setSignupConfirmPassword] = useState('');
  const [signupShopName, setSignupShopName] = useState('');
  const [showSignupPassword, setShowSignupPassword] = useState(false);

  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const login = useAuthStore((state) => state.login);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const navigate = useNavigate();
  const { success, error } = useToast();

  useEffect(() => {
    if (searchParams.get('tab') === 'signup') {
      setTab('signup');
    }
  }, [searchParams]);

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
        email: loginEmail.trim(),
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
      success('Welcome Back!', `Logged in as ${data.name || 'Owner'}`);
      navigate('/');
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Invalid email or password.';
      setErrorMsg(typeof msg === 'string' ? msg : 'Login failed. Please try again.');
      error('Login Failed', typeof msg === 'string' ? msg : 'Check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignupSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg(null);

    if (signupPassword !== signupConfirmPassword) {
      setErrorMsg('Passwords do not match. Please re-enter your password.');
      setIsLoading(false);
      return;
    }

    if (signupPassword.length < 6) {
      setErrorMsg('Password must be at least 6 characters.');
      setIsLoading(false);
      return;
    }

    try {
      const response = await api.post('/auth/signup', {
        name: signupName.trim(),
        email: signupEmail.trim(),
        password: signupPassword,
        shop_name: signupShopName.trim(),
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
      success('Account Created!', `Welcome to VoiceStock, ${data.name || 'Owner'}!`);
      navigate('/');
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Signup failed. Please try again.';
      setErrorMsg(typeof msg === 'string' ? msg : 'Registration failed.');
      error('Registration Failed', typeof msg === 'string' ? msg : 'Please try again.');
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
      success('Demo Mode Active', 'Loaded pre-seeded Kumar General Store inventory.');
      navigate('/');
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Demo login failed.';
      setErrorMsg(typeof msg === 'string' ? msg : 'Demo login failed.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 py-12 px-4 sm:px-6 lg:px-8 relative selection:bg-indigo-500 selection:text-white">
      {/* Background Ambience */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-indigo-200/30 rounded-full blur-3xl pointer-events-none -z-10" />

      {/* Back to Home Link */}
      <div className="w-full max-w-md mb-4 flex justify-between items-center px-1">
        <Link
          to="/landing"
          className="inline-flex items-center gap-1 text-xs font-bold text-slate-500 hover:text-indigo-600 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Overview
        </Link>
        <span className="text-xs text-slate-400 font-medium">Multi-tenant AI Inventory</span>
      </div>

      <div className="max-w-md w-full space-y-6 bg-white p-8 sm:p-10 rounded-3xl shadow-xl shadow-slate-200/60 border border-slate-200/80 transition-all">
        {/* Brand Header */}
        <div className="text-center">
          <div className="mx-auto h-16 w-16 bg-indigo-600 rounded-2xl flex items-center justify-center shadow-lg shadow-indigo-200 mb-4">
            <Mic className="h-8 w-8 text-white" />
          </div>
          <h2 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            {tab === 'login' ? 'Welcome Back' : 'Create Store Account'}
          </h2>
          <p className="mt-1 text-xs sm:text-sm text-slate-500">
            {tab === 'login'
              ? 'Sign in to access your personal inventory & voice assistant.'
              : 'Start managing your store inventory with voice in seconds.'}
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex bg-slate-100 p-1.5 rounded-2xl border border-slate-200/60">
          <button
            type="button"
            onClick={() => {
              setTab('login');
              setErrorMsg(null);
            }}
            className={`flex-1 py-2 text-xs sm:text-sm font-bold rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer ${
              tab === 'login'
                ? 'bg-white text-indigo-700 shadow-xs border border-slate-200/60'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <LogIn className="w-4 h-4" />
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setTab('signup');
              setErrorMsg(null);
            }}
            className={`flex-1 py-2 text-xs sm:text-sm font-bold rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer ${
              tab === 'signup'
                ? 'bg-white text-indigo-700 shadow-xs border border-slate-200/60'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <UserPlus className="w-4 h-4" />
            Sign Up
          </button>
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div
            className="rounded-xl bg-rose-50 border border-rose-200 px-4 py-3 text-xs sm:text-sm text-rose-700 font-medium animate-in fade-in"
            role="alert"
          >
            {errorMsg}
          </div>
        )}

        {/* Login Form */}
        {tab === 'login' && (
          <form className="space-y-4" onSubmit={handleLoginSubmit}>
            <div>
              <Input
                label="Email Address"
                type="email"
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
                required
                placeholder="you@store.com"
                autoComplete="email"
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                Password
              </label>
              <div className="relative">
                <input
                  type={showLoginPassword ? 'text' : 'password'}
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  required
                  className="block w-full rounded-xl border border-slate-200 bg-white text-slate-900 text-sm placeholder:text-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-3 focus:ring-indigo-100 transition-all min-h-[44px] px-3.5 pr-11"
                  placeholder="••••••••"
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowLoginPassword((v) => !v)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600 cursor-pointer"
                  aria-label={showLoginPassword ? 'Hide password' : 'Show password'}
                >
                  {showLoginPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between text-xs">
              <label className="flex items-center gap-2 text-slate-600 cursor-pointer">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                />
                <span>Remember session</span>
              </label>
              <span className="text-slate-400">Secure JWT Session</span>
            </div>

            <Button
              type="submit"
              variant="primary"
              className="w-full py-3 px-4 rounded-xl text-sm font-bold shadow-md shadow-indigo-200 min-h-[48px]"
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
              <Input
                label="Full Name"
                type="text"
                value={signupName}
                onChange={(e) => setSignupName(e.target.value)}
                required
                placeholder="e.g. Ramesh Kumar"
                autoComplete="name"
              />
            </div>

            <div>
              <Input
                label="Store / Business Name"
                type="text"
                value={signupShopName}
                onChange={(e) => setSignupShopName(e.target.value)}
                placeholder="e.g. Kumar General Store"
                helperText="A private isolated workspace will be created for this shop."
                leftIcon={<Store className="w-4 h-4" />}
              />
            </div>

            <div>
              <Input
                label="Email Address"
                type="email"
                value={signupEmail}
                onChange={(e) => setSignupEmail(e.target.value)}
                required
                placeholder="you@example.com"
                autoComplete="email"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                  Password
                </label>
                <div className="relative">
                  <input
                    type={showSignupPassword ? 'text' : 'password'}
                    value={signupPassword}
                    onChange={(e) => setSignupPassword(e.target.value)}
                    required
                    minLength={6}
                    className="block w-full rounded-xl border border-slate-200 bg-white text-slate-900 text-sm placeholder:text-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-3 focus:ring-indigo-100 transition-all min-h-[44px] px-3.5 pr-10"
                    placeholder="••••••••"
                    autoComplete="new-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowSignupPassword((v) => !v)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 cursor-pointer"
                  >
                    {showSignupPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                  Confirm Password
                </label>
                <input
                  type={showSignupPassword ? 'text' : 'password'}
                  value={signupConfirmPassword}
                  onChange={(e) => setSignupConfirmPassword(e.target.value)}
                  required
                  minLength={6}
                  className="block w-full rounded-xl border border-slate-200 bg-white text-slate-900 text-sm placeholder:text-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-3 focus:ring-indigo-100 transition-all min-h-[44px] px-3.5"
                  placeholder="••••••••"
                  autoComplete="new-password"
                />
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              className="w-full py-3 px-4 rounded-xl text-sm font-bold shadow-md shadow-indigo-200 min-h-[48px]"
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
            <span className="bg-white px-3 text-slate-400 font-bold tracking-wider">
              Or Instant Evaluation
            </span>
          </div>
        </div>

        {/* Demo Mode Button */}
        <button
          type="button"
          onClick={handleDemoLogin}
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-2xl border-2 border-dashed border-indigo-200 bg-indigo-50/60 hover:bg-indigo-50 text-indigo-700 font-bold text-xs sm:text-sm transition-all hover:border-indigo-300 cursor-pointer shadow-xs"
        >
          <Sparkles className="w-4 h-4 text-indigo-600" />
          <span>Launch Demo Store (Pre-loaded items)</span>
        </button>

        {/* Feature Highlights */}
        <div className="pt-2 text-center text-xs text-slate-400 flex items-center justify-center gap-3">
          <span>🔒 Private Tenant Isolation</span>
          <span>•</span>
          <span>🎙️ Multilingual AI</span>
        </div>
      </div>
    </div>
  );
};
