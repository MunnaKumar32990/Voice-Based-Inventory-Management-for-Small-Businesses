import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { LanguageSelector } from '../LanguageSelector';
import { Mic, LogOut, Settings } from 'lucide-react';

const DESKTOP_LINKS = [
  { to: '/', label: 'Dashboard' },
  { to: '/products', label: 'Products' },
  { to: '/transactions', label: 'Transactions' },
  { to: '/alerts', label: 'Alerts' },
  { to: '/settings', label: 'Settings' },
];

export const Navbar: React.FC = () => {
  const shopName = useAuthStore((s) => s.shopName);
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="bg-white shadow-sm z-30 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <Link to="/" className="flex-shrink-0 flex items-center">
              <Mic className="h-8 w-8 text-indigo-600 mr-2" />
              <span className="font-bold text-xl text-gray-900 hidden sm:block">VoiceStock</span>
            </Link>
            <nav className="hidden md:ml-8 md:flex md:items-center md:space-x-4" aria-label="Primary">
              {DESKTOP_LINKS.map((l) => (
                <NavLink
                  key={l.to}
                  to={l.to}
                  className={({ isActive }) =>
                    `px-3 py-2 rounded-md text-sm font-medium ${isActive ? 'text-indigo-700 bg-indigo-50' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'}`
                  }
                >
                  {l.label}
                </NavLink>
              ))}
            </nav>
          </div>
          <div className="flex items-center space-x-3">
            <div className="hidden sm:flex flex-col text-right">
              <span className="text-sm font-bold text-gray-900">{user?.name || 'Owner'}</span>
              <span className="text-xs text-indigo-600 font-medium">{shopName || 'My Store'}</span>
            </div>
            <LanguageSelector />
            <NavLink
              to="/settings"
              aria-label="Settings"
              className="p-2 text-gray-400 hover:text-gray-500 rounded-full hover:bg-gray-100 min-h-[44px] min-w-[44px] flex items-center justify-center"
            >
              <Settings className="h-5 w-5" />
            </NavLink>
            <button 
              onClick={handleLogout}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-rose-600 hover:text-rose-700 bg-rose-50 hover:bg-rose-100 rounded-lg transition-all"
              aria-label="Logout"
              title="Sign Out"
            >
              <LogOut className="h-4 w-4" />
              <span className="hidden sm:inline">Sign Out</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
