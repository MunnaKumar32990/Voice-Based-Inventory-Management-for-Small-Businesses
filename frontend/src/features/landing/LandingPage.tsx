import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Mic,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Package,
  Zap,
  Globe2,
  BarChart3,
  Clock,
  ChevronRight,
  Database,
  Store,
} from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { useAuthStore } from '../../stores/authStore';
import { api } from '../../lib/api';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);
  const [isDemoLoading, setIsDemoLoading] = useState(false);

  const handleDemoLogin = async () => {
    setIsDemoLoading(true);
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
    } catch {
      navigate('/login');
    } finally {
      setIsDemoLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 selection:bg-indigo-500 selection:text-white flex flex-col">
      {/* Top Navigation */}
      <header className="sticky top-0 z-40 bg-white/90 backdrop-blur-md border-b border-slate-200/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center shadow-md shadow-indigo-200">
              <Mic className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-black text-xl tracking-tight text-slate-900 block leading-none">
                VoiceStock
              </span>
              <span className="text-[10px] font-bold uppercase tracking-widest text-indigo-600">
                Voice Inventory
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleDemoLogin}
              disabled={isDemoLoading}
              className="hidden sm:inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-bold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 rounded-xl border border-indigo-200/60 transition-colors cursor-pointer"
            >
              <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
              {isDemoLoading ? 'Loading Demo...' : 'Instant Demo'}
            </button>
            <Link to="/login">
              <Button variant="secondary" size="sm" className="font-bold">
                Sign In
              </Button>
            </Link>
            <Link to="/login?tab=signup">
              <Button variant="primary" size="sm" className="font-bold shadow-sm shadow-indigo-200">
                Get Started
                <ArrowRight className="w-4 h-4 ml-1.5" />
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-16 pb-20 sm:pt-24 sm:pb-28 overflow-hidden">
        {/* Subtle Background Glows */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-200/40 rounded-full blur-3xl pointer-events-none -z-10" />
        <div className="absolute top-1/3 left-1/4 w-[400px] h-[400px] bg-violet-200/30 rounded-full blur-3xl pointer-events-none -z-10" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-50 border border-indigo-200/80 text-xs font-bold text-indigo-700 mb-6 shadow-xs animate-in fade-in">
            <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
            <span>AI Voice Assistant for Small Business Inventory</span>
          </div>

          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-black text-slate-900 tracking-tight max-w-4xl mx-auto leading-[1.1]">
            Manage Your Inventory.{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 via-indigo-700 to-violet-600">
              Just Talk.
            </span>
          </h1>

          <p className="mt-6 text-lg sm:text-xl text-slate-600 max-w-2xl mx-auto leading-relaxed font-normal">
            A voice-powered inventory assistant built for small businesses. Track stock, understand
            your inventory, and get answers instantly—without complicated software.
          </p>

          {/* CTA Buttons */}
          <div className="mt-8 sm:mt-10 flex flex-col sm:flex-row items-center justify-center gap-3.5 max-w-md mx-auto">
            <Link to="/login?tab=signup" className="w-full sm:w-auto">
              <Button
                variant="primary"
                size="lg"
                className="w-full sm:w-auto text-base font-bold shadow-lg shadow-indigo-300/40 px-8"
              >
                Get Started Free
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
            <button
              onClick={handleDemoLogin}
              disabled={isDemoLoading}
              className="w-full sm:w-auto inline-flex items-center justify-center font-bold rounded-xl border-2 border-dashed border-indigo-300 bg-white hover:bg-indigo-50/50 text-indigo-700 h-13 px-6 text-base transition-all cursor-pointer shadow-xs"
            >
              <Sparkles className="w-5 h-5 mr-2 text-indigo-500" />
              {isDemoLoading ? 'Launching Demo...' : 'Try Instant Demo'}
            </button>
          </div>

          <p className="mt-3.5 text-xs text-slate-400 font-medium">
            ✓ No credit card required • Instant isolated workspace • Pre-loaded demo available
          </p>

          {/* Hero Product & Voice Mockup Preview */}
          <div className="mt-14 sm:mt-18 max-w-5xl mx-auto relative">
            <div className="rounded-3xl border border-slate-200/90 bg-white p-3 sm:p-5 shadow-2xl shadow-indigo-900/10">
              {/* Mockup Topbar */}
              <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-100 px-2">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-rose-400" />
                  <span className="w-3 h-3 rounded-full bg-amber-400" />
                  <span className="w-3 h-3 rounded-full bg-emerald-400" />
                  <span className="text-xs font-semibold text-slate-400 ml-2">VoiceStock Dashboard</span>
                </div>
                <div className="flex items-center gap-2 text-xs font-bold text-emerald-600 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  Live Connected
                </div>
              </div>

              {/* Mockup Content Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 text-left">
                {/* Left: Stat Cards Preview */}
                <div className="lg:col-span-7 space-y-4">
                  <div className="grid grid-cols-3 gap-3">
                    <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/60">
                      <div className="text-xs font-bold text-slate-500 uppercase">Products</div>
                      <div className="text-2xl font-black text-slate-900 mt-1">24</div>
                      <div className="text-[11px] font-semibold text-emerald-600 mt-0.5">Healthy catalog</div>
                    </div>
                    <div className="p-3.5 rounded-2xl bg-emerald-50/70 border border-emerald-100">
                      <div className="text-xs font-bold text-emerald-700 uppercase">Today In</div>
                      <div className="text-2xl font-black text-emerald-900 mt-1">+15</div>
                      <div className="text-[11px] font-semibold text-emerald-600 mt-0.5">Stock arrivals</div>
                    </div>
                    <div className="p-3.5 rounded-2xl bg-rose-50/70 border border-rose-100">
                      <div className="text-xs font-bold text-rose-700 uppercase">Low Stock</div>
                      <div className="text-2xl font-black text-rose-900 mt-1">2</div>
                      <div className="text-[11px] font-semibold text-rose-600 mt-0.5">Needs reorder</div>
                    </div>
                  </div>

                  {/* Product Rows Preview */}
                  <div className="rounded-2xl border border-slate-200/70 overflow-hidden bg-white">
                    <div className="p-3 bg-slate-50 border-b border-slate-100 text-xs font-bold text-slate-600 uppercase tracking-wider flex justify-between">
                      <span>Recent Inventory</span>
                      <span>Balance</span>
                    </div>
                    <div className="divide-y divide-slate-100 text-xs">
                      <div className="p-3 flex items-center justify-between hover:bg-slate-50">
                        <div>
                          <div className="font-bold text-slate-900">Basmati Rice (Premium)</div>
                          <div className="text-slate-400 text-[11px]">Grains • Reorder: 10 kg</div>
                        </div>
                        <span className="font-black text-slate-900 bg-slate-100 px-2.5 py-1 rounded-lg">
                          50 kg
                        </span>
                      </div>
                      <div className="p-3 flex items-center justify-between hover:bg-slate-50">
                        <div>
                          <div className="font-bold text-slate-900">Mustard Oil (Kachi Ghani)</div>
                          <div className="text-slate-400 text-[11px]">Oils • Reorder: 5 L</div>
                        </div>
                        <span className="font-black text-slate-900 bg-slate-100 px-2.5 py-1 rounded-lg">
                          15 litre
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Right: Active Voice Assistant Hero Showcase */}
                <div className="lg:col-span-5 rounded-2xl bg-gradient-to-b from-indigo-900 to-slate-950 p-5 text-white flex flex-col justify-between shadow-xl relative overflow-hidden">
                  <div className="absolute -right-8 -top-8 w-36 h-36 bg-indigo-500/20 rounded-full blur-2xl pointer-events-none" />

                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-indigo-500/30 text-indigo-200 border border-indigo-400/30">
                        <Mic className="w-3 h-3 text-indigo-300 animate-pulse" />
                        Voice Assistant
                      </span>
                      <span className="text-[10px] text-slate-400">English • हिन्दी • తెలుగు</span>
                    </div>

                    <div className="space-y-3">
                      <div className="p-3 rounded-xl bg-white/10 backdrop-blur-xs border border-white/10">
                        <p className="text-[11px] font-semibold text-indigo-300 uppercase tracking-wider mb-0.5">
                          You Spoke:
                        </p>
                        <p className="text-sm font-semibold italic text-white">
                          &ldquo;How much rice is available?&rdquo;
                        </p>
                      </div>

                      <div className="p-3.5 rounded-xl bg-indigo-600/30 border border-indigo-400/40">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-bold text-emerald-400 flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" /> In Stock
                          </span>
                          <span className="text-[10px] text-indigo-200">Live DB</span>
                        </div>
                        <div className="text-2xl font-black text-white">
                          50 kg{' '}
                          <span className="text-xs font-medium text-indigo-200">Basmati Rice</span>
                        </div>
                        <p className="text-xs text-indigo-100 mt-1">
                          🔊 &ldquo;50 kg of Basmati Rice is currently available.&rdquo;
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Pulsing Mic Indicator */}
                  <div className="mt-4 pt-3 border-t border-white/10 flex items-center justify-between text-xs text-indigo-200">
                    <span className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                      Ready for next query
                    </span>
                    <span className="text-[11px] text-indigo-300 font-semibold">
                      Speak or Type Anytime
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4 Feature Pillars */}
      <section className="py-16 sm:py-24 bg-white border-y border-slate-200/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-xs font-bold uppercase tracking-widest text-indigo-600 mb-2">
              Why VoiceStock
            </h2>
            <p className="text-3xl sm:text-4xl font-black text-slate-900 tracking-tight">
              Designed specifically for fast-paced retail and small businesses
            </p>
            <p className="text-slate-600 text-base mt-3">
              No complicated enterprise menus or steep learning curves. Just open and speak.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Pillar 1 */}
            <div className="p-6 rounded-2xl border border-slate-200/80 bg-slate-50/50 hover:bg-slate-50 hover:shadow-md transition-all">
              <div className="w-12 h-12 rounded-xl bg-indigo-100 text-indigo-600 flex items-center justify-center mb-5">
                <Globe2 className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">Multilingual Voice AI</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Talk in English, Hindi, Hinglish, or Telugu. Our AI understands colloquial phrases like
                &ldquo;total kitna products hai&rdquo; and &ldquo;aaj kitna bikri hua&rdquo;.
              </p>
            </div>

            {/* Pillar 2 */}
            <div className="p-6 rounded-2xl border border-slate-200/80 bg-slate-50/50 hover:bg-slate-50 hover:shadow-md transition-all">
              <div className="w-12 h-12 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center mb-5">
                <Package className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">Instant Stock In & Out</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Say &ldquo;Add 10 bags of sugar&rdquo; or &ldquo;Remove 2 bottles of oil&rdquo;. Stock
                balances update in milliseconds with full transaction audit logs.
              </p>
            </div>

            {/* Pillar 3 */}
            <div className="p-6 rounded-2xl border border-slate-200/80 bg-slate-50/50 hover:bg-slate-50 hover:shadow-md transition-all">
              <div className="w-12 h-12 rounded-xl bg-purple-100 text-purple-600 flex items-center justify-center mb-5">
                <Database className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">Database-Aware AI</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Ask about total counts, categories, low-stock items, or today&apos;s transactions. The AI
                queries your actual database rather than generic training data.
              </p>
            </div>

            {/* Pillar 4 */}
            <div className="p-6 rounded-2xl border border-slate-200/80 bg-slate-50/50 hover:bg-slate-50 hover:shadow-md transition-all">
              <div className="w-12 h-12 rounded-xl bg-amber-100 text-amber-600 flex items-center justify-center mb-5">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">Private Isolated Stores</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Every registered store has a strictly isolated database. Your inventory, pricing,
                and transactions are never visible to any other user.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works (3 Steps) */}
      <section className="py-16 sm:py-24 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-xs font-bold uppercase tracking-widest text-indigo-600 mb-2">
              Simple 3-Step Flow
            </h2>
            <p className="text-3xl sm:text-4xl font-black text-slate-900 tracking-tight">
              From spoken word to updated inventory in seconds
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
            <div className="bg-white p-7 rounded-2xl border border-slate-200/80 shadow-xs relative">
              <div className="w-10 h-10 rounded-full bg-indigo-600 text-white font-black flex items-center justify-center mb-5 text-sm">
                1
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">Tap Mic & Speak Naturally</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Use your phone or computer mic. Speak in your natural shop language without memorizing
                rigid syntax.
              </p>
            </div>

            <div className="bg-white p-7 rounded-2xl border border-slate-200/80 shadow-xs relative">
              <div className="w-10 h-10 rounded-full bg-indigo-600 text-white font-black flex items-center justify-center mb-5 text-sm">
                2
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">AI Parses & Queries DB</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Our hybrid NLP and Gemini Flash engine extracts the intent, product, quantity, and unit,
                then securely queries your store&apos;s data.
              </p>
            </div>

            <div className="bg-white p-7 rounded-2xl border border-slate-200/80 shadow-xs relative">
              <div className="w-10 h-10 rounded-full bg-indigo-600 text-white font-black flex items-center justify-center mb-5 text-sm">
                3
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">Instant Spoken & Visual Answer</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Hear the response spoken back in your dialect while viewing structured analytical
                cards with one-tap confirmation.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Business Benefits Section */}
      <section className="py-16 sm:py-24 bg-white border-t border-slate-200/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-indigo-50 text-indigo-700 mb-4 border border-indigo-100">
                <Store className="w-3.5 h-3.5" /> Built For Kirana & Small Retailers
              </div>
              <h2 className="text-3xl sm:text-4xl font-black text-slate-900 tracking-tight leading-tight">
                Save 2+ hours daily. Never lose track of stock again.
              </h2>
              <div className="mt-6 space-y-4">
                <div className="flex items-start gap-3">
                  <div className="p-1 rounded-full bg-emerald-100 text-emerald-600 mt-0.5">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-900 text-base">No Barcode Scanners or Registers</h4>
                    <p className="text-slate-600 text-sm mt-0.5">
                      Save thousands on hardware. Any phone, tablet, or laptop becomes your full inventory terminal.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="p-1 rounded-full bg-emerald-100 text-emerald-600 mt-0.5">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-900 text-base">Effortless for Non-Tech Staff</h4>
                    <p className="text-slate-600 text-sm mt-0.5">
                      Helpers and shop hands can simply speak in Hindi, Telugu, or English to record incoming bags and boxes.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="p-1 rounded-full bg-emerald-100 text-emerald-600 mt-0.5">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-900 text-base">Proactive Low-Stock Alerts</h4>
                    <p className="text-slate-600 text-sm mt-0.5">
                      Get flagged automatically before you run out of essential grains, oils, and daily essentials.
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-8 flex gap-3">
                <Link to="/login?tab=signup">
                  <Button variant="primary" size="md" className="font-bold shadow-md shadow-indigo-200">
                    Get Started Now
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </Button>
                </Link>
                <button
                  onClick={handleDemoLogin}
                  disabled={isDemoLoading}
                  className="px-4 py-2 text-sm font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors cursor-pointer"
                >
                  Test Demo Mode
                </button>
              </div>
            </div>

            <div className="bg-slate-50 p-8 rounded-3xl border border-slate-200/80 shadow-inner">
              <div className="space-y-4">
                <div className="p-4 bg-white rounded-2xl border border-slate-200/60 shadow-xs flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold">
                      <Clock className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="text-xs font-bold text-slate-500 uppercase">Daily Time Saved</div>
                      <div className="text-xl font-black text-slate-900">~2.5 Hours / Day</div>
                    </div>
                  </div>
                  <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full">
                    +85% Faster
                  </span>
                </div>

                <div className="p-4 bg-white rounded-2xl border border-slate-200/60 shadow-xs flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
                      <BarChart3 className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="text-xs font-bold text-slate-500 uppercase">Stock Accuracy</div>
                      <div className="text-xl font-black text-slate-900">99.8% Recorded</div>
                    </div>
                  </div>
                  <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full">
                    Audited
                  </span>
                </div>

                <div className="p-4 bg-white rounded-2xl border border-slate-200/60 shadow-xs flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center font-bold">
                      <Zap className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="text-xs font-bold text-slate-500 uppercase">Setup Time</div>
                      <div className="text-xl font-black text-slate-900">&lt; 60 Seconds</div>
                    </div>
                  </div>
                  <span className="text-xs font-bold text-purple-600 bg-purple-50 px-2.5 py-1 rounded-full">
                    Instant
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto bg-slate-900 text-slate-400 py-12 border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white">
                <Mic className="w-4 h-4" />
              </div>
              <span className="font-black text-lg text-white">VoiceStock</span>
              <span className="text-xs text-slate-500 ml-2">Voice-First Inventory Management</span>
            </div>

            <div className="flex items-center gap-6 text-sm">
              <Link to="/login" className="hover:text-white transition-colors">
                Sign In
              </Link>
              <Link to="/login?tab=signup" className="hover:text-white transition-colors">
                Sign Up
              </Link>
              <button
                onClick={handleDemoLogin}
                className="hover:text-white transition-colors cursor-pointer"
              >
                Instant Demo
              </button>
            </div>
          </div>

          <div className="mt-8 pt-8 border-t border-slate-800 text-xs text-slate-500 text-center sm:text-left flex flex-col sm:flex-row justify-between items-center gap-4">
            <p>© {new Date().getFullYear()} VoiceStock. All rights reserved.</p>
            <p>Empowering small businesses with voice-first technology.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};
