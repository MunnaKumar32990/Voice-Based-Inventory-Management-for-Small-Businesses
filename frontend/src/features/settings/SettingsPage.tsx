import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { useAuthStore } from '../../stores/authStore';
import { Save } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const { t, i18n } = useTranslation();
  const shopName = useAuthStore((s) => s.shopName);
  const [name, setName] = useState(shopName || '');
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    // Demo backend has no shop-profile endpoint; persist locally so the
    // dashboard/navbar reflect the name immediately.
    const current = useAuthStore.getState();
    if (current.token) {
      current.login(current.token, current.user || { id: 'demo', name: 'Demo User' }, current.shopId || 'demo', name.trim() || 'My Shop');
    }
    setSaved(true);
    window.setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">{t('nav.settings')}</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card title="Shop Profile">
          <form className="space-y-4" onSubmit={handleSave}>
            <Input label="Shop Name" value={name} onChange={(e) => setName(e.target.value)} required />
            <Input label="Owner Name" defaultValue="Demo User" />
            <Input label="Phone Number" defaultValue="+91 9876543210" />
            {saved && <p className="text-sm text-green-700" role="status">{t('common.success')}</p>}
            <Button type="submit" variant="primary" className="w-full sm:w-auto mt-4">
              <Save className="h-4 w-4 mr-2" />
              {t('common.save')}
            </Button>
          </form>
        </Card>

        <Card title="Preferences">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Language
              </label>
              <select 
                className="mt-1 block w-full rounded-md border-gray-300 py-2 pl-3 pr-10 text-base focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm min-h-[44px] border"
                value={i18n.language}
                onChange={(e) => i18n.changeLanguage(e.target.value)}
              >
                <option value="en">English</option>
                <option value="hi">हिन्दी (Hindi)</option>
                <option value="te">తెలుగు (Telugu)</option>
              </select>
              <p className="mt-2 text-xs text-gray-500">
                {t('voice.exampleCommands')}
              </p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
