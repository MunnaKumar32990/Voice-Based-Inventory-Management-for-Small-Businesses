import React from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { LanguageSelector } from '../LanguageSelector';
import {
  Mic,
  LogOut,
  Settings,
  Store,
  LayoutDashboard,
  Package,
  ArrowLeftRight,
  Bell,
} from 'lucide-react';
import { useToast } from '../ui/Toast';

const DESKTOP_LINKS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/products', label: 'Inventory', icon: Package },
  { to: '/transactions', label: 'Transactions', icon: ArrowLeftRight },
  { to: '/alerts', label: 'Alerts', icon: Bell },
  { to: '/settings', label: 'Settings', icon: Settings },
];

export const Navbar: React.FC = () => {
  const shopName = useAuthStore((s) => s.shopName);
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();
  const { info } = useToast();

  const handleLogout = () => {
    logout();
    info('Signed Out', 'You have been logged out of your session.');
    navigate('/login');
  };

  // Get user initials for avatar
  const initials = (user?.name || 'Owner')
    .split(' ')
    .map((n) => n[0])
    .join('')
    .substring(0, 2)
    .toUpperCase();

  return (
    <header className="sticky top-0 bg-white/90 backdrop-blur-md border-b border-slate-200/80 z-30 transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Brand & Desktop Navigation */}
          <div className="flex items-center">
            <Link to="/" className="shrink-0 flex items-center gap-2.5 group">
              <div className="w-9 h-9 rounded-xl bg-indigo-600 group-hover:bg-indigo-700 flex items-center justify-center shadow-md shadow-indigo-200 transition-colors">
                <Mic className="h-5 w-5 text-white" />
              </div>
              <div>
                <span className="font-black text-lg text-slate-900 tracking-tight block leading-none">
                  VoiceStock
                </span>
                <span className="text-[10px] font-bold uppercase tracking-widest text-indigo-600">
                  Voice Inventory
                </span>
              </div>
            </Link>

            <nav className="hidden md:ml-8 md:flex md:items-center md:space-x-1" aria-label="Primary Navigation">
              {DESKTOP_LINKS.map((link) => {
                const Icon = link.icon;
                return (
                  <NavLink
                    key={link.to}
                    to={link.to}
                    end={link.to === '/'}
                    className={({ isActive }) =>
                      `flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
                        isActive
                          ? 'text-indigo-600 bg-indigo-50/80 shadow-xs border border-indigo-100/60'
                          : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
                      }`
                    }
                  >
                    <Icon className="w-4 h-4" />
                    <span>{link.label}</span>
                  </NavLink>
                );
              })}
            </nav>
          </div>

          {/* User Profile & Actions */}
          <div className="flex items-center space-x-3">
            {/* Store & User Profile Badge */}
            <div className="hidden sm:flex items-center gap-2.5 px-3 py-1.5 rounded-xl bg-slate-50 border border-slate-200/70">
              <div className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-700 font-bold flex items-center justify-center text-xs">
                {initials}
              </div>
              <div className="flex flex-col text-left">
                <span className="text-xs font-bold text-slate-900 leading-tight">
                  {user?.name || 'Owner'}
                </span>
                <span className="text-[10px] text-slate-500 font-medium flex items-center gap-1">
                  <Store className="w-3 h-3 text-indigo-500" />
                  {shopName || 'My Store'}
                </span>
              </div>
            </div>

            <LanguageSelector />

            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-rose-600 hover:text-rose-700 bg-rose-50 hover:bg-rose-100 rounded-xl border border-rose-100 transition-all cursor-pointer"
              aria-label="Logout"
              title="Sign Out"
            >
              <LogOut className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Sign Out</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
