import React, { useState, useEffect } from 'react';
import { X, Moon, Sun, Monitor, Save, AlertTriangle } from 'lucide-react';
import { api } from '../lib/api';
import { getUserId } from '../lib/user-session';
import { useQueryClient } from '@tanstack/react-query';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  theme: 'light' | 'dark' | 'system';
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
}

export default function SettingsModal({ isOpen, onClose, theme, setTheme }: SettingsModalProps) {
  const queryClient = useQueryClient();
  const [provider, setProvider] = useState('groq');
  const [apiKey, setApiKey] = useState('');
  const [model, setModel] = useState('');
  const [isWiping, setIsWiping] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    if (isOpen) {
      const configStr = localStorage.getItem('ai_config');
      if (configStr) {
        try {
          const config = JSON.parse(configStr);
          if (config.provider) setProvider(config.provider);
          if (config.apiKey) setApiKey(config.apiKey);
          if (config.model) setModel(config.model);
        } catch {}
      }
      setSaveSuccess(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSaveAIConfig = () => {
    const config = { provider, apiKey, model };
    localStorage.setItem('ai_config', JSON.stringify(config));
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 3000);
  };

  const handleWipeData = async () => {
    if (!window.confirm("Are you absolutely sure you want to delete ALL your records? This cannot be undone.")) {
      return;
    }
    const userId = getUserId();
    if (!userId) return;

    try {
      setIsWiping(true);
      await api.users.wipeData(userId);
      queryClient.invalidateQueries();
      alert("All data wiped successfully.");
      onClose();
      window.location.reload(); // Hard refresh to ensure everything is cleared from UI
    } catch (e: any) {
      alert("Failed to wipe data: " + e.message);
    } finally {
      setIsWiping(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
      <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-xl w-full max-w-md border border-slate-200 dark:border-slate-800 flex flex-col max-h-[90vh]">
        <div className="flex items-center justify-between p-4 border-b border-slate-100 dark:border-slate-800">
          <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100">Settings</h2>
          <button onClick={onClose} className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 rounded-lg transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="p-6 overflow-y-auto flex-1 space-y-8">
          {/* Appearance Section */}
          <section className="space-y-3">
            <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Appearance</h3>
            <div className="grid grid-cols-3 gap-2 p-1 bg-slate-100 dark:bg-slate-800/50 rounded-lg">
              <button
                onClick={() => setTheme('light')}
                className={`flex items-center justify-center gap-2 py-2 px-3 rounded-md text-sm font-medium transition-all ${
                  theme === 'light' ? 'bg-white dark:bg-slate-700 shadow-sm text-emerald-600 dark:text-emerald-400' : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                <Sun size={16} /> Light
              </button>
              <button
                onClick={() => setTheme('dark')}
                className={`flex items-center justify-center gap-2 py-2 px-3 rounded-md text-sm font-medium transition-all ${
                  theme === 'dark' ? 'bg-white dark:bg-slate-700 shadow-sm text-emerald-600 dark:text-emerald-400' : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                <Moon size={16} /> Dark
              </button>
              <button
                onClick={() => setTheme('system')}
                className={`flex items-center justify-center gap-2 py-2 px-3 rounded-md text-sm font-medium transition-all ${
                  theme === 'system' ? 'bg-white dark:bg-slate-700 shadow-sm text-emerald-600 dark:text-emerald-400' : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                <Monitor size={16} /> System
              </button>
            </div>
          </section>

          {/* AI Config Section */}
          <section className="space-y-4">
            <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">AI Provider Configuration</h3>
            
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Provider</label>
                <select
                  value={provider}
                  onChange={(e) => setProvider(e.target.value)}
                  className="w-full p-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-emerald-500 outline-none"
                >
                  <option value="groq">Groq</option>
                  <option value="openrouter">OpenRouter</option>
                  <option value="gemini">Gemini</option>
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">API Key</label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Leave blank to use server default"
                  className="w-full p-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-emerald-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Model Override</label>
                <input
                  type="text"
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  placeholder="e.g. gpt-4o, claude-3-5-sonnet-20241022"
                  className="w-full p-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-emerald-500 outline-none"
                />
              </div>

              <button
                onClick={handleSaveAIConfig}
                className="w-full flex items-center justify-center gap-2 py-2.5 bg-emerald-100 hover:bg-emerald-200 dark:bg-emerald-900/30 dark:hover:bg-emerald-800/50 text-emerald-700 dark:text-emerald-400 font-medium rounded-xl transition-colors"
              >
                <Save size={18} />
                {saveSuccess ? "Saved!" : "Save Configuration"}
              </button>
            </div>
          </section>

          {/* Danger Zone */}
          <section className="space-y-3 pt-4 border-t border-slate-100 dark:border-slate-800">
            <h3 className="text-sm font-semibold text-rose-500 uppercase tracking-wider flex items-center gap-2">
              <AlertTriangle size={16} /> Danger Zone
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Wiping your data will delete all activities, missions, and cached insights. This cannot be undone.
            </p>
            <button
              onClick={handleWipeData}
              disabled={isWiping}
              className="w-full py-2.5 bg-rose-100 hover:bg-rose-200 dark:bg-rose-900/30 dark:hover:bg-rose-800/50 text-rose-700 dark:text-rose-400 font-medium rounded-xl transition-colors disabled:opacity-50"
            >
              {isWiping ? "Deleting..." : "Delete All My Records"}
            </button>
          </section>
        </div>
      </div>
    </div>
  );
}
