import os

files = {
    "app/(dashboard)/admin/settings/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Save, Settings as SettingsIcon, Globe, Shield, Banknote } from 'lucide-react';
import Swal from 'sweetalert2';
import { getClientPolicy } from '@/lib/clientCookie';
import { useRouter } from 'next/navigation';

export default function SettingsPage() {
  const [settings, setSettings] = useState({ 
      site_name: '', 
      site_logo: '', 
      contact_email: '', 
      max_transfer_limit: '' 
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [canManage, setCanManage] = useState(false);
  const router = useRouter();

  useEffect(() => {
    // 1. ROBUST PERMISSION CHECK
    const policy = getClientPolicy();
    const isAdmin = policy.role === 'admin' || policy.role === 'SuperAdmin';
    const hasView = isAdmin || (policy.permissions && policy.permissions.includes('SettingsView'));
    const hasManage = isAdmin || (policy.permissions && policy.permissions.includes('SettingsManage'));

    if (!hasView) {
        Swal.fire({ 
            toast: true, position: 'top-end', icon: 'error', 
            title: 'ACCESS DENIED', text: 'You do not have permission to view Settings.' 
        });
        router.push('/admin');
        return;
    }
    
    setCanManage(hasManage);

    // 2. FETCH SETTINGS
    fetch('/api/admin/settings')
      .then(res => res.json())
      .then(data => {
          setSettings({
              site_name: data.site_name || '',
              site_logo: data.site_logo || '',
              contact_email: data.contact_email || '',
              max_transfer_limit: data.max_transfer_limit || ''
          });
          setLoading(false);
      })
      .catch(() => {
          Swal.fire('Error', 'Failed to load settings', 'error');
          setLoading(false);
      });
  }, [router]);

  const handleSave = async (e: React.FormEvent) => {
      e.preventDefault();
      if (!canManage) {
          return Swal.fire('Forbidden', 'You only have view access. You cannot save changes.', 'warning');
      }

      setSaving(true);
      const res = await fetch('/api/admin/settings', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(settings)
      });
      setSaving(false);

      if (res.ok) {
          Swal.fire('Saved', 'Master settings updated successfully. Reload to see changes.', 'success');
      } else {
          Swal.fire('Error', 'Failed to save settings.', 'error');
      }
  };

  if (loading) return <div className="p-12 text-center text-slate-400 animate-pulse">Loading System Configurations...</div>;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
          <h2 className="text-3xl font-bold dark:text-white flex items-center gap-2">
              <SettingsIcon className="text-blue-600"/> Master Settings
          </h2>
          <p className="text-slate-500 mt-1">Configure global application parameters and branding.</p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* BRANDING CARD */}
              <Card className="p-6 border-t-4 border-blue-500 shadow-lg">
                  <div className="flex items-center gap-2 mb-6 text-slate-800 dark:text-white">
                      <Globe size={20} className="text-blue-500"/>
                      <h3 className="font-bold text-lg">Branding & Identity</h3>
                  </div>
                  <div className="space-y-4">
                      <Input 
                          label="Bank Name" 
                          placeholder="e.g. Babji Bank" 
                          value={settings.site_name} 
                          onChange={e => setSettings({...settings, site_name: e.target.value})} 
                          disabled={!canManage}
                      />
                      <Input 
                          label="Logo URL" 
                          placeholder="https://example.com/logo.png" 
                          value={settings.site_logo} 
                          onChange={e => setSettings({...settings, site_logo: e.target.value})} 
                          disabled={!canManage}
                      />
                      {settings.site_logo && (
                          <div className="mt-2 p-4 bg-slate-50 dark:bg-slate-800 rounded-lg flex justify-center">
                              <img src={settings.site_logo} alt="Logo Preview" className="h-12 object-contain" />
                          </div>
                      )}
                  </div>
              </Card>

              {/* SYSTEM CARD */}
              <Card className="p-6 border-t-4 border-purple-500 shadow-lg">
                  <div className="flex items-center gap-2 mb-6 text-slate-800 dark:text-white">
                      <Shield size={20} className="text-purple-500"/>
                      <h3 className="font-bold text-lg">System Configurations</h3>
                  </div>
                  <div className="space-y-4">
                      <Input 
                          label="Support Contact Email" 
                          type="email"
                          placeholder="support@bank.com" 
                          value={settings.contact_email} 
                          onChange={e => setSettings({...settings, contact_email: e.target.value})} 
                          disabled={!canManage}
                      />
                      <div className="relative">
                          <Banknote size={16} className="absolute top-[38px] left-3 text-slate-400"/>
                          <Input 
                              label="Max Transfer Limit ($)" 
                              type="number"
                              placeholder="50000" 
                              value={settings.max_transfer_limit} 
                              onChange={e => setSettings({...settings, max_transfer_limit: e.target.value})} 
                              className="pl-9"
                              disabled={!canManage}
                          />
                      </div>
                  </div>
              </Card>
          </div>

          {canManage && (
              <Button type="submit" disabled={saving} className="w-full py-4 text-lg shadow-xl shadow-blue-500/20 flex justify-center items-center gap-2">
                  <Save size={20}/> {saving ? 'Saving Configuration...' : 'Save All Settings'}
              </Button>
          )}
      </form>
    </div>
  );
}
"""
}

def fix_master_settings():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("✅ Master Settings Page rebuilt! Permission kick-out loop is fixed.")

if __name__ == "__main__":
    fix_master_settings()