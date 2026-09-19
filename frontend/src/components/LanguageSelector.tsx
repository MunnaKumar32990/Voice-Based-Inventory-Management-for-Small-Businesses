import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Globe } from 'lucide-react';

export const LanguageSelector: React.FC = () => {
  const { i18n } = useTranslation();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
    setOpen(false);
  };

  useEffect(() => {
    const onDocClick = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', onDocClick);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDocClick);
      document.removeEventListener('keydown', onKey);
    };
  }, []);

  return (
    <div className="relative" ref={rootRef}>
      <button
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        className="flex items-center space-x-1 text-gray-700 hover:text-indigo-600 focus:outline-none min-h-[44px] px-2"
      >
        <Globe className="h-5 w-5" />
        <span className="hidden sm:inline-block text-sm font-medium uppercase">{i18n.language}</span>
      </button>
      
      <div
        role="menu"
        className={`absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 transition-all duration-200 z-50 ${open ? 'opacity-100 visible' : 'opacity-0 invisible'}`}
      >
        <div className="py-1" role="none" aria-orientation="vertical">
          <button
            onClick={() => changeLanguage('en')}
            className={`block w-full text-left px-4 py-3 text-sm min-h-[44px] ${i18n.language === 'en' ? 'bg-indigo-50 text-indigo-700' : 'text-gray-700 hover:bg-gray-100'}`}
            role="menuitem"
          >
            English
          </button>
          <button
            onClick={() => changeLanguage('hi')}
            className={`block w-full text-left px-4 py-3 text-sm min-h-[44px] ${i18n.language === 'hi' ? 'bg-indigo-50 text-indigo-700' : 'text-gray-700 hover:bg-gray-100'}`}
            role="menuitem"
          >
            हिन्दी (Hindi)
          </button>
          <button
            onClick={() => changeLanguage('te')}
            className={`block w-full text-left px-4 py-3 text-sm min-h-[44px] ${i18n.language === 'te' ? 'bg-indigo-50 text-indigo-700' : 'text-gray-700 hover:bg-gray-100'}`}
            role="menuitem"
          >
            తెలుగు (Telugu)
          </button>
        </div>
      </div>
    </div>
  );
};
