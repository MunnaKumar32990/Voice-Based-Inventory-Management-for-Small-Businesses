import React from 'react';
import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { LayoutDashboard, Package, ArrowLeftRight, Bell } from 'lucide-react';

export const MobileNav: React.FC = () => {
  const { t } = useTranslation();

  const navItems = [
    { to: '/', icon: LayoutDashboard, label: t('nav.dashboard', 'Dashboard'), key: 'dashboard' },
    { to: '/products', icon: Package, label: t('nav.products', 'Inventory'), key: 'products' },
    { to: '/transactions', icon: ArrowLeftRight, label: t('nav.transactions', 'Transactions'), key: 'transactions' },
    { to: '/alerts', icon: Bell, label: t('nav.alerts', 'Alerts'), key: 'alerts' },
  ];

  return (
    <nav
      className="sm:hidden fixed bottom-0 w-full bg-white/95 backdrop-blur-md border-t border-slate-200/80 z-40 pb-[env(safe-area-inset-bottom)]"
      aria-label="Mobile Navigation"
    >
      <div className="flex justify-around items-center h-16 px-2">
        {navItems.slice(0, 2).map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.key}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex flex-col items-center justify-center w-full h-full min-h-[56px] transition-colors ${
                  isActive ? 'text-indigo-600 font-bold' : 'text-slate-500 hover:text-slate-900'
                }`
              }
            >
              <Icon className="h-5 w-5" />
              <span className="text-[10px] mt-1 font-semibold tracking-tight">{item.label}</span>
            </NavLink>
          );
        })}

        {/* Space for central floating mic button */}
        <div className="w-18 shrink-0" aria-hidden="true" />

        {navItems.slice(2).map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.key}
              to={item.to}
              className={({ isActive }) =>
                `flex flex-col items-center justify-center w-full h-full min-h-[56px] transition-colors ${
                  isActive ? 'text-indigo-600 font-bold' : 'text-slate-500 hover:text-slate-900'
                }`
              }
            >
              <Icon className="h-5 w-5" />
              <span className="text-[10px] mt-1 font-semibold tracking-tight">{item.label}</span>
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
};
