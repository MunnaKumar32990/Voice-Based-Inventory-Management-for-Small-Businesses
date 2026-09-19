import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { LayoutDashboard, Package, ArrowLeftRight, Bell } from 'lucide-react';

export const MobileNav: React.FC = () => {
  const { t } = useTranslation();

  const navItems = [
    { to: '/', icon: <LayoutDashboard className="h-6 w-6" />, label: t('nav.dashboard'), key: 'dashboard' },
    { to: '/products', icon: <Package className="h-6 w-6" />, label: t('nav.products'), key: 'products' },
    { to: '/transactions', icon: <ArrowLeftRight className="h-6 w-6" />, label: t('nav.transactions'), key: 'transactions' },
    { to: '/alerts', icon: <Bell className="h-6 w-6" />, label: t('nav.alerts'), key: 'alerts' },
  ];

  return (
    <div className="sm:hidden fixed bottom-0 w-full bg-white border-t border-gray-200 z-40 pb-[env(safe-area-inset-bottom)]">
      <div className="flex justify-around items-center h-16">
        {navItems.slice(0, 2).map((item) => (
          <NavLink
            key={item.key}
            to={item.to}
            className={({ isActive }) =>
              `flex flex-col items-center justify-center w-full h-full min-h-[64px] ${
                isActive ? 'text-indigo-600' : 'text-gray-500 hover:text-gray-900'
              }`
            }
          >
            {item.icon}
            <span className="text-[10px] mt-1 font-medium">{item.label}</span>
          </NavLink>
        ))}
        <div className="w-16" aria-hidden="true" />{/* Space for floating mic button */}
        {navItems.slice(2).map((item) => (
          <NavLink
            key={item.key}
            to={item.to}
            className={({ isActive }) =>
              `flex flex-col items-center justify-center w-full h-full min-h-[64px] ${
                isActive ? 'text-indigo-600' : 'text-gray-500 hover:text-gray-900'
              }`
            }
          >
            {item.icon}
            <span className="text-[10px] mt-1 font-medium">{item.label}</span>
          </NavLink>
        ))}
      </div>
    </div>
  );
};
