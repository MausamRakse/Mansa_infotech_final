import { useState } from 'react';
import toast from 'react-hot-toast';

const Settings = () => {
  const [platformName, setPlatformName] = useState(() => localStorage.getItem('platform_name') || 'Voice AI Platform');
  const [defaultLanguage, setDefaultLanguage] = useState(() => localStorage.getItem('default_language') || 'en');
  const [defaultVoice, setDefaultVoice] = useState(() => localStorage.getItem('default_voice') || '1');
  const [saving, setSaving] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setTimeout(() => {
      localStorage.setItem('platform_name', platformName);
      localStorage.setItem('default_language', defaultLanguage);
      localStorage.setItem('default_voice', defaultVoice);
      setSaving(false);
      toast.success('Settings saved successfully!');
    }, 500);
  };

  return (
    <div className="max-w-3xl mx-auto h-full flex flex-col animate-in fade-in duration-500">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-surface-foreground tracking-tight">Settings</h1>
        <p className="text-textMuted mt-1">Configure your personal dashboard preferences.</p>
      </div>

      <div className="bg-surface rounded-[12px] border border-border card-shadow">
        <div className="px-6 py-5 border-b border-border">
          <h2 className="text-[16px] font-bold text-surface-foreground">Platform Settings</h2>
        </div>
        <form onSubmit={handleSave} className="p-6 flex flex-col gap-6">
          
          <div className="flex flex-col gap-2">
            <label className="text-[14px] font-semibold text-surface-foreground">Platform Name</label>
            <p className="text-[12px] text-textMuted mb-1">Customize the display name in the sidebar.</p>
            <input 
              type="text"
              value={platformName}
              onChange={e => setPlatformName(e.target.value)}
              className="border border-border rounded-[8px] px-3 py-2 text-[14px] bg-muted/30 text-surface-foreground outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all w-full max-w-md"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-md">
            <div className="flex flex-col gap-2">
              <label className="text-[14px] font-semibold text-surface-foreground">Default Language</label>
              <select 
                value={defaultLanguage}
                onChange={e => setDefaultLanguage(e.target.value)}
                className="border border-border rounded-[8px] px-3 py-2 text-[14px] bg-muted/30 text-surface-foreground outline-none focus:border-primary w-full"
              >
                <option value="en">English (en)</option>
                <option value="hi">Hindi (hi)</option>
                <option value="es">Spanish (es)</option>
                <option value="fr">French (fr)</option>
              </select>
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-[14px] font-semibold text-surface-foreground">Default Voice</label>
              <select 
                value={defaultVoice}
                onChange={e => setDefaultVoice(e.target.value)}
                className="border border-border rounded-[8px] px-3 py-2 text-[14px] bg-muted/30 text-surface-foreground outline-none focus:border-primary w-full"
              >
                <option value="1">Voice 1 (Female)</option>
                <option value="2">Voice 2 (Male)</option>
                <option value="3">Voice 3 (Neutral)</option>
              </select>
            </div>
          </div>

          <div className="pt-4 border-t border-border mt-2">
            <button type="submit" disabled={saving} className="btn-primary min-w-[140px]">
              {saving ? 'Saving...' : 'Save Preferences'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Settings;
