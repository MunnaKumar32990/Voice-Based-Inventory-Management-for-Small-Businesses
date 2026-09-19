import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { useAuthStore } from '../../stores/authStore';
import { useToast } from '../../components/ui/Toast';
import { Save, Store, Globe2, Mic } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const { t, i18n } = useTranslation();
  const shopName = useAuthStore((s) => s.shopName);
  const user = useAuthStore((s) => s.user);
  const { success } = useToast();

  const [name, setName] = useState(shopName || '');
  const [ownerName, setOwnerName] = useState(user?.name || '');

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    const current = useAuthStore.getState();
    if (current.token) {
      current.login(
        current.token,
        { id: current.user?.id || 'user', name: ownerName.trim() || 'Owner', email: current.user?.email },
        current.shopId || 'shop',
        name.trim() || 'My Shop'
      );
    }
    success('Settings Saved', 'Shop profile and preferences updated successfully.');
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="pb-2 border-b border-slate-200/80">
        <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
          {t('nav.settings', 'Store Settings')}
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Configure your store profile, default language, and voice recognition options.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Shop Profile Card */}
        <Card
          title={
            <div className="flex items-center gap-2">
              <Store className="w-5 h-5 text-indigo-600" />
              <span>Shop Profile</span>
            </div>
          }
        >
          <form className="space-y-4" onSubmit={handleSave}>
            <Input
              label="Shop Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              placeholder="e.g. Kumar General Store"
            />
            <Input
              label="Owner / Manager Name"
              value={ownerName}
              onChange={(e) => setOwnerName(e.target.value)}
              placeholder="e.g. Ramesh Kumar"
            />
            <Input
              label="Contact Email"
              defaultValue={user?.email || 'owner@store.com'}
              disabled
              helperText="Managed by your login authentication."
            />
            <div className="pt-2">
              <Button type="submit" variant="primary" className="w-full sm:w-auto font-bold">
                <Save className="h-4 w-4 mr-2" />
                {t('common.save', 'Save Changes')}
              </Button>
            </div>
          </form>
        </Card>

        {/* Preferences Card */}
        <div className="space-y-6">
          <Card
            title={
              <div className="flex items-center gap-2">
                <Globe2 className="w-5 h-5 text-indigo-600" />
                <span>Language & Dialect</span>
              </div>
            }
          >
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                  Default Spoken Language
                </label>
                <select
                  className="block w-full rounded-xl border border-slate-200 bg-white text-slate-900 text-sm focus:outline-none focus:border-indigo-500 focus:ring-3 focus:ring-indigo-100 min-h-[44px] px-3.5 font-medium cursor-pointer"
                  value={i18n.language}
                  onChange={(e) => {
                    i18n.changeLanguage(e.target.value);
                    success('Language Changed', `Voice assistant set to ${e.target.value.toUpperCase()}.`);
                  }}
                >
                  <option value="en">English (India / International)</option>
                  <option value="hi">हिन्दी (Hindi / Hinglish)</option>
                  <option value="te">తెలుగు (Telugu / Telugish)</option>
                </select>
                <p className="mt-2 text-xs text-slate-500">
                  Voice assistant responds in this language and recognizes regional store phrasing.
                </p>
              </div>
            </div>
          </Card>

          {/* Voice Command Cheat Sheet */}
          <Card
            title={
              <div className="flex items-center gap-2">
                <Mic className="w-5 h-5 text-indigo-600" />
                <span>Voice Command Guide</span>
              </div>
            }
          >
            <div className="space-y-2.5 text-xs">
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200/60">
                <div className="font-bold text-slate-900">&ldquo;Total kitna products hai?&rdquo;</div>
                <div className="text-slate-500 text-[11px]">Queries total catalog count across categories.</div>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200/60">
                <div className="font-bold text-slate-900">&ldquo;How much rice is available?&rdquo;</div>
                <div className="text-slate-500 text-[11px]">Reports exact stock balance and reorder status.</div>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200/60">
                <div className="font-bold text-slate-900">&ldquo;Add 10 kg sugar&rdquo;</div>
                <div className="text-slate-500 text-[11px]">Performs instant stock-in with confirmation.</div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
