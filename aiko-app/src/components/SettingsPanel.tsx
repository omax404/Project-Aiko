import React, { useState, useEffect } from 'react';
import { Save, X, Settings, User, Palette, Brain, Volume2, Eye, Plug, Smartphone } from 'lucide-react';
import { useNeuralStore, getHubUrl } from '../store/useNeuralStore';

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onSave?: (settings: any) => void;
}

const isTauri = typeof window !== 'undefined' && !!(window as any).__TAURI__;
const HUB_URL = getHubUrl();

async function loadSettingsFromBackend(): Promise<any> {
  if (isTauri) {
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      const jsonStr: string = await invoke('get_user_settings');
      return JSON.parse(jsonStr);
    } catch (_) {
      // Fall through to HTTP
    }
  }
  try {
    const res = await fetch(`${HUB_URL}/api/settings`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (e) {
    console.warn('[Settings] Could not load from backend, using defaults:', e);
    return {};
  }
}

async function saveSettingsToBackend(settings: any): Promise<void> {
  if (isTauri) {
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      await invoke('save_user_settings', { settings: JSON.stringify(settings, null, 2) });
      return;
    } catch (_) {
      // Fall through to HTTP
    }
  }
  const res = await fetch(`${HUB_URL}/api/settings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => 'Unknown error');
    throw new Error(`Server error ${res.status}: ${text}`);
  }
}

export const SettingsPanel: React.FC<SettingsPanelProps> = ({ isOpen, onClose, onSave }) => {
  const defaultSettings = {
    llm: { url: 'http://127.0.0.1:11434/api/chat', model: 'qwen3.5:397b-cloud' },
    tts: { enabled: true, voice: 'vivian', speed: 0.9 },
    persona: { custom_prompt: 'You are a highly capable AI agent designed to assist with anything the user needs. Always be polite, concise, and helpful.' },
    plugins: { discord_bot: false, discord_token: '', telegram_bot: false, telegram_token: '', hermes_agent: true },
    vision: { provider: 'transformers', model: 'openbmb/MiniCPM-V-4.6', grid_overlay: true },
    appearance: {
      theme_color: '#C9A8D9',
      avatar_scale: 1.0,
      dynamics_intensity: 80,
      show_animated_assets: true
    }
  };

  const [settings, setSettings] = useState<any>(defaultSettings);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'ok' | 'err'>('idle');
  const [activeTab, setActiveTab] = useState('persona');
  const [localIp, setLocalIp] = useState<string>('');

  useEffect(() => {
    if (isOpen) {
      loadSettings();
      fetch(`${HUB_URL}/status`)
        .then(res => res.json())
        .then(data => {
          if (data && data.local_ip) {
            setLocalIp(data.local_ip);
          }
        })
        .catch(err => console.warn('Could not fetch status for local IP:', err));
    }
  }, [isOpen]);

  const loadSettings = async () => {
    setLoading(true);
    setSaveStatus('idle');
    try {
      const data = await loadSettingsFromBackend();
      setSettings((prev: any) => ({
        llm: { ...prev.llm, ...(data.llm || {}) },
        tts: { ...prev.tts, ...(data.tts || {}) },
        persona: { ...prev.persona, ...(data.persona || {}) },
        plugins: { ...prev.plugins, ...(data.plugins || {}) },
        vision: { ...prev.vision, ...(data.vision || {}) },
        appearance: { ...prev.appearance, ...(data.appearance || {}) }
      }));
    } catch (e) {
      console.error('Failed to load settings:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveStatus('idle');
    try {
      await saveSettingsToBackend(settings);
      setSaveStatus('ok');
      if (typeof onSave === 'function') onSave(settings);

      const store = useNeuralStore.getState();
      if (settings.appearance) {
        if (settings.appearance.theme_color) {
          store.setThemeColor(settings.appearance.theme_color);
        }
        store.updateSettings({
          avatarScale: settings.appearance.avatar_scale,
          dynamicsIntensity: settings.appearance.dynamics_intensity,
          showAnimatedAssets: settings.appearance.show_animated_assets,
        });
      }

      try {
        await fetch(`${HUB_URL}/api/settings/reload`, { method: 'POST' });
      } catch (_) {}
      setTimeout(() => {
        setSaveStatus('idle');
        onClose();
      }, 800);
    } catch (e: any) {
      console.error('Failed to save settings:', e);
      setSaveStatus('err');
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  const tabs = [
    { id: 'persona', label: 'Persona' },
    { id: 'appearance', label: 'Appearance' },
    { id: 'llm', label: 'AI Model' },
    { id: 'tts', label: 'Voice' },
    { id: 'vision', label: 'Vision' },
    { id: 'plugins', label: 'Plugins' },
    { id: 'mobile', label: 'Mobile Link' },
  ];

  const getTabIcon = (id: string) => {
    switch (id) {
      case 'persona': return <User size={14} strokeWidth={1.8} />;
      case 'appearance': return <Palette size={14} strokeWidth={1.8} />;
      case 'llm': return <Brain size={14} strokeWidth={1.8} />;
      case 'tts': return <Volume2 size={14} strokeWidth={1.8} />;
      case 'vision': return <Eye size={14} strokeWidth={1.8} />;
      case 'plugins': return <Plug size={14} strokeWidth={1.8} />;
      case 'mobile': return <Smartphone size={14} strokeWidth={1.8} />;
      default: return <Settings size={14} strokeWidth={1.8} />;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm transition-opacity">
      <div className="bg-[var(--bg-surface)] border border-white/[0.06] rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden">
        
        {/* Header */}
        <div className="flex justify-between items-center px-5 py-4 border-b border-white/[0.06] bg-[var(--bg-base)]">
          <h2 className="text-[16px] font-semibold text-[#f0ebe3] flex items-center gap-2">
            <Settings size={16} className="text-[var(--accent)]" />
            Aiko Settings
          </h2>
          <button 
            onClick={onClose} 
            className="text-[#5a5248] hover:text-[#f0ebe3] transition-colors" 
            title="Close settings" 
            aria-label="Close settings"
          >
            <X size={20} />
          </button>
        </div>

        {loading ? (
          <div className="p-8 text-center text-[#5a5248] text-[14px]">Loading settings...</div>
        ) : (
          <div className="flex h-[500px]">
            {/* Sidebar */}
            <div className="w-[200px] border-r border-white/[0.06] bg-[var(--bg-sidebar)] p-3 flex flex-col gap-1">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-[13px] font-medium transition-all text-left group ${
                    activeTab === tab.id
                      ? 'bg-white/[0.05] text-[var(--accent)]'
                      : 'text-[#9a8f7e] hover:bg-white/[0.03] hover:text-[#f0ebe3]'
                  }`}
                >
                  <span className={`shrink-0 flex items-center justify-center transition-colors ${
                    activeTab === tab.id ? 'text-[var(--accent)]' : 'text-[#5a5248] group-hover:text-[#f0ebe3]'
                  }`}>
                    {getTabIcon(tab.id)}
                  </span>
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Content Area */}
            <div className="flex-1 p-6 overflow-y-auto bg-[#181612] custom-scrollbar">
              
              {activeTab === 'persona' && (
                <div className="flex flex-col gap-4">
                  <h3 className="text-[16px] font-semibold text-[#f0ebe3]">Personality</h3>
                  <p className="text-[12px] text-[#9a8f7e] leading-relaxed">
                    Custom instructions override or append to Aiko's default personality. 
                    Tell her to focus on coding, be sarcastic, or adopt any persona you want.
                  </p>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[12px] font-medium text-[#9a8f7e]">Custom Personality Injection</label>
                    <textarea 
                      id="persona-prompt"
                      className="w-full h-48 bg-[var(--bg-base)] border border-white/[0.06] rounded-lg p-3 text-[13px] text-[#f0ebe3] focus:border-[var(--accent)]/50 focus:outline-none resize-none leading-relaxed"
                      value={settings.persona.custom_prompt}
                      onChange={e => setSettings({...settings, persona: {...settings.persona, custom_prompt: e.target.value}})}
                      placeholder="E.g., You are a highly professional assistant..."
                      aria-label="Custom Personality Injection"
                    />
                  </div>
                </div>
              )}

              {activeTab === 'appearance' && (
                <div className="flex flex-col gap-6">
                  <div>
                    <h3 className="text-[16px] font-semibold text-[#f0ebe3] mb-1">Appearance & Interface</h3>
                    <p className="text-[12px] text-[#9a8f7e] leading-relaxed">
                      Customize the visual style, accent color palette, mascot scale, and animations of the Aiko interface.
                    </p>
                  </div>

                  {/* Accent Colors */}
                  <div className="flex flex-col gap-2">
                    <label className="text-[12px] font-medium text-[#9a8f7e]">Accent Palette</label>
                    <div className="flex flex-wrap gap-2.5 p-3 rounded-lg bg-[var(--bg-base)] border border-white/[0.06]">
                      {[
                        { name: 'Lavender', color: '#C9A8D9' },
                        { name: 'Rose', color: '#f43f5e' },
                        { name: 'Emerald', color: '#10b981' },
                        { name: 'Azure', color: '#3b82f6' },
                        { name: 'Violet', color: '#8b5cf6' },
                        { name: 'Crimson', color: '#ef4444' }
                      ].map(preset => (
                        <button
                          key={preset.name}
                          type="button"
                          onClick={() => setSettings({
                            ...settings,
                            appearance: { ...settings.appearance, theme_color: preset.color }
                          })}
                          className={`group relative w-9 h-9 rounded-lg transition-all flex items-center justify-center border ${
                            settings.appearance?.theme_color === preset.color 
                              ? 'border-white/50 scale-105 shadow-md shadow-white/[0.05]' 
                              : 'border-transparent hover:scale-105'
                          }`}
                          style={{ backgroundColor: preset.color }}
                          title={preset.name}
                          aria-label={`Select ${preset.name} theme`}
                        >
                          {settings.appearance?.theme_color === preset.color && (
                            <div className="w-1.5 h-1.5 bg-white rounded-full" />
                          )}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Mascot Scale */}
                  <div className="flex flex-col gap-2 p-3 rounded-lg bg-[var(--bg-base)] border border-white/[0.06]">
                    <div className="flex justify-between items-center">
                      <label className="text-[12px] font-medium text-[#9a8f7e]">Mascot Scale</label>
                      <span className="text-[11px] font-mono text-[var(--accent)]">{Math.round((settings.appearance?.avatar_scale || 1.0) * 100)}%</span>
                    </div>
                    <input 
                      type="range" 
                      min="0.5" 
                      max="1.5" 
                      step="0.05"
                      value={settings.appearance?.avatar_scale || 1.0}
                      onChange={e => setSettings({
                        ...settings,
                        appearance: { ...settings.appearance, avatar_scale: parseFloat(e.target.value) }
                      })}
                      className="w-full accent-[var(--accent)] h-1 bg-white/10 rounded-lg appearance-none cursor-pointer"
                      aria-label="Mascot Scale Slider"
                    />
                  </div>

                  {/* Dynamics Intensity */}
                  <div className="flex flex-col gap-2 p-3 rounded-lg bg-[var(--bg-base)] border border-white/[0.06]">
                    <div className="flex justify-between items-center">
                      <label className="text-[12px] font-medium text-[#9a8f7e]">Dynamics Intensity</label>
                      <span className="text-[11px] font-mono text-[var(--accent)]">{settings.appearance?.dynamics_intensity || 80}%</span>
                    </div>
                    <input 
                      type="range" 
                      min="0" 
                      max="100" 
                      step="5"
                      value={settings.appearance?.dynamics_intensity || 80}
                      onChange={e => setSettings({
                        ...settings,
                        appearance: { ...settings.appearance, dynamics_intensity: parseInt(e.target.value) }
                      })}
                      className="w-full accent-[var(--accent)] h-1 bg-white/10 rounded-lg appearance-none cursor-pointer"
                      aria-label="Dynamics Intensity Slider"
                    />
                    <span className="text-[10px] text-[#5a5248] uppercase tracking-tight">Controls motion speed, hover transition times, and visual effects.</span>
                  </div>

                  {/* Animated UI Assets */}
                  <label className="flex items-center gap-3 cursor-pointer p-3 border border-white/[0.06] rounded-lg hover:border-white/[0.1] transition-colors bg-[var(--bg-base)]">
                    <input 
                      type="checkbox" 
                      className="w-4 h-4 rounded bg-[var(--bg-base)] border-white/[0.1] text-[var(--accent)] focus:ring-[var(--accent)]/50"
                      checked={settings.appearance?.show_animated_assets ?? true}
                      onChange={e => setSettings({
                        ...settings,
                        appearance: { ...settings.appearance, show_animated_assets: e.target.checked }
                      })}
                      aria-label="Toggle Animated Interface Elements"
                    />
                    <span className="text-[13px] font-medium text-[#f0ebe3]">Show Animated UI Elements</span>
                  </label>
                </div>
              )}

              {activeTab === 'llm' && (
                <div className="flex flex-col gap-5">
                  <h3 className="text-[16px] font-semibold text-[#f0ebe3]">AI Model</h3>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[12px] font-medium text-[#9a8f7e]">API URL</label>
                    <input 
                      id="api-url"
                      type="text"
                      className="w-full bg-[var(--bg-base)] border border-white/[0.06] rounded-lg px-3 py-2 text-[13px] text-[#f0ebe3] focus:border-[var(--accent)]/50 focus:outline-none"
                      value={settings.llm.url}
                      onChange={e => setSettings({...settings, llm: {...settings.llm, url: e.target.value}})}
                      aria-label="API URL"
                    />
                    <p className="text-[11px] text-[#5a5248]">Ollama or OpenAI-compatible endpoint</p>
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[12px] font-medium text-[#9a8f7e]">Model Name</label>
                    <input 
                      id="model-name"
                      type="text"
                      className="w-full bg-[var(--bg-base)] border border-white/[0.06] rounded-lg px-3 py-2 text-[13px] text-[#f0ebe3] focus:border-[var(--accent)]/50 focus:outline-none"
                      value={settings.llm.model}
                      onChange={e => setSettings({...settings, llm: {...settings.llm, model: e.target.value}})}
                      aria-label="Model Name"
                    />
                    <p className="text-[11px] text-[#5a5248]">E.g., qwen3.5:397b-cloud or gpt-4o</p>
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[12px] font-medium text-[#9a8f7e]">API Key</label>
                    <input 
                      id="api-key"
                      type="password"
                      className="w-full bg-[var(--bg-base)] border border-white/[0.06] rounded-lg px-3 py-2 text-[13px] text-[#f0ebe3] focus:border-[var(--accent)]/50 focus:outline-none"
                      value={settings.llm.api_key || ''}
                      onChange={e => setSettings({...settings, llm: {...settings.llm, api_key: e.target.value}})}
                      placeholder="sk-... or leave blank for local Ollama"
                      aria-label="API Key"
                    />
                    <p className="text-[11px] text-[#5a5248]">Required for cloud providers</p>
                  </div>
                </div>
              )}

              {activeTab === 'tts' && (
                <div className="flex flex-col gap-5">
                  <h3 className="text-[16px] font-semibold text-[#f0ebe3]">Voice</h3>
                  
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="w-4 h-4 rounded bg-[var(--bg-base)] border-white/[0.1] text-[var(--accent)] focus:ring-[var(--accent)]/50"
                      checked={settings.tts.enabled}
                      onChange={e => setSettings({...settings, tts: {...settings.tts, enabled: e.target.checked}})}
                      aria-label="Enable Aiko's Voice"
                    />
                    <span className="text-[13px] font-medium text-[#f0ebe3]">Enable Aiko's Voice</span>
                  </label>

                  <div className={!settings.tts.enabled ? 'opacity-40 pointer-events-none' : ''}>
                    <div className="flex flex-col gap-1.5">
                      <label className="text-[12px] font-medium text-[#9a8f7e]">Voice Profile</label>
                      <select 
                        id="voice-profile"
                        className="w-full bg-[var(--bg-base)] border border-white/[0.06] rounded-lg px-3 py-2 text-[13px] text-[#f0ebe3] focus:border-[var(--accent)]/50 focus:outline-none"
                        value={settings.tts.voice}
                        onChange={e => setSettings({...settings, tts: {...settings.tts, voice: e.target.value}})}
                        aria-label="Voice Profile"
                      >
                        <option value="vivian">Vivian (Default)</option>
                        <option value="fina">Fina</option>
                        <option value="lucia">Lucia</option>
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'vision' && (
                <div className="flex flex-col gap-5">
                  <h3 className="text-[16px] font-semibold text-[#f0ebe3]">Vision</h3>
                  <p className="text-[12px] text-[#9a8f7e] leading-relaxed">
                    Aiko can see your screen using a local vision model. 
                    Choose Ollama for CPU devices, or Transformers for GPU/high-end CPU.
                  </p>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[12px] font-medium text-[#9a8f7e]">Provider</label>
                    <select 
                      id="vision-provider"
                      className="w-full bg-[var(--bg-base)] border border-white/[0.06] rounded-lg px-3 py-2 text-[13px] text-[#f0ebe3] focus:border-[var(--accent)]/50 focus:outline-none"
                      value={settings.vision?.provider || 'transformers'}
                      onChange={e => setSettings({...settings, vision: {...(settings.vision || {}), provider: e.target.value}})}
                      aria-label="Vision Provider"
                    >
                      <option value="transformers">Transformers (MiniCPM-V-4.6)</option>
                      <option value="ollama">Ollama (minicpm-v / llava)</option>
                      <option value="openai">OpenAI / LM Studio</option>
                    </select>
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[12px] font-medium text-[#9a8f7e]">Model Name</label>
                    <input 
                      id="vision-model-name"
                      type="text"
                      className="w-full bg-[var(--bg-base)] border border-white/[0.06] rounded-lg px-3 py-2 text-[13px] text-[#f0ebe3] focus:border-[var(--accent)]/50 focus:outline-none"
                      value={settings.vision?.model || 'openbmb/MiniCPM-V-4.6'}
                      onChange={e => setSettings({...settings, vision: {...(settings.vision || {}), model: e.target.value}})}
                      aria-label="Vision Model Name"
                    />
                    <p className="text-[11px] text-[#5a5248]">Model identifier for the chosen provider</p>
                  </div>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="w-4 h-4 rounded bg-[var(--bg-base)] border-white/[0.1] text-[var(--accent)] focus:ring-[var(--accent)]/50"
                      checked={settings.vision?.grid_overlay ?? true}
                      onChange={e => setSettings({...settings, vision: {...(settings.vision || {}), grid_overlay: e.target.checked}})}
                      aria-label="Enable Screen Coordinates Overlay Grid"
                    />
                    <span className="text-[13px] font-medium text-[#f0ebe3]">Show Grid Overlay</span>
                  </label>
                </div>
              )}

              {activeTab === 'plugins' && (
                <div className="flex flex-col gap-5">
                  <h3 className="text-[16px] font-semibold text-[#f0ebe3]">Integrations</h3>
                  <p className="text-[12px] text-[#9a8f7e] leading-relaxed">
                    Enable external bridges. Requires restarting the application to take full effect.
                  </p>
                  
                  <div className="flex flex-col gap-4">
                    <div className="flex flex-col gap-2">
                      <Checkbox label="Discord Bot (Satellite)" checked={settings.plugins.discord_bot} onChange={v => setSettings({...settings, plugins: {...settings.plugins, discord_bot: v}})} />
                      {settings.plugins.discord_bot && (
                        <div className="ml-7 flex flex-col gap-1.5">
                          <label className="text-[11px] font-medium text-[#9a8f7e]">Discord Bot Token</label>
                          <input 
                            type="password"
                            className="w-full bg-[var(--bg-base)] border border-white/[0.06] rounded-lg px-3 py-1.5 text-[12px] text-[#f0ebe3] focus:border-[var(--accent)]/50 focus:outline-none font-mono"
                            value={settings.plugins.discord_token || ''}
                            onChange={e => setSettings({...settings, plugins: {...settings.plugins, discord_token: e.target.value}})}
                            placeholder="MTE..."
                            aria-label="Discord Bot Token"
                          />
                        </div>
                      )}
                    </div>

                    <div className="flex flex-col gap-2">
                      <Checkbox label="Telegram Bot (Satellite)" checked={settings.plugins.telegram_bot} onChange={v => setSettings({...settings, plugins: {...settings.plugins, telegram_bot: v}})} />
                      {settings.plugins.telegram_bot && (
                        <div className="ml-7 flex flex-col gap-1.5">
                          <label className="text-[11px] font-medium text-[#9a8f7e]">Telegram Bot Token</label>
                          <input 
                            type="password"
                            className="w-full bg-[var(--bg-base)] border border-white/[0.06] rounded-lg px-3 py-1.5 text-[12px] text-[#f0ebe3] focus:border-[var(--accent)]/50 focus:outline-none font-mono"
                            value={settings.plugins.telegram_token || ''}
                            onChange={e => setSettings({...settings, plugins: {...settings.plugins, telegram_token: e.target.value}})}
                            placeholder="123456:ABC..."
                            aria-label="Telegram Bot Token"
                          />
                        </div>
                      )}
                    </div>

                    <Checkbox label="Hermes AI Agent (Cognitive Bridge)" checked={settings.plugins.hermes_agent} onChange={v => setSettings({...settings, plugins: {...settings.plugins, hermes_agent: v}})} />
                  </div>
                </div>
              )}

              {activeTab === 'mobile' && (
                <div className="flex flex-col gap-4 items-center text-center">
                  <h3 className="text-[16px] font-semibold text-[#f0ebe3] self-start text-left">Mobile Companion Link</h3>
                  <p className="text-[12px] text-[#9a8f7e] leading-relaxed self-start text-left">
                    Scan this QR code using the Aiko Mobile App to instantly pair your phone with this desktop hub.
                    Make sure both devices are connected to the same local Wi-Fi network.
                  </p>
                  
                  {localIp ? (
                    (() => {
                      const activePort = new URL(HUB_URL).port || '8000';
                      return (
                        <div className="flex flex-col items-center gap-4 bg-white/[0.02] border border-white/[0.06] rounded-xl p-6 mt-4">
                          <img 
                            src={`https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=http://${localIp}:${activePort}`} 
                            alt="Pairing QR Code"
                            className="w-48 h-48 rounded-lg border border-white/[0.1] bg-white p-2"
                          />
                          <div className="flex flex-col gap-1">
                            <span className="text-[11px] font-semibold uppercase tracking-[0.1em] text-[#5a5248]">Desktop Server Address</span>
                            <span className="text-[13px] font-mono text-[var(--accent)] font-medium">http://{localIp}:{activePort}</span>
                          </div>
                        </div>
                      );
                    })()
                  ) : (
                    <div className="p-8 text-[#5a5248] text-[13px]">
                      Fetching server local network address...
                    </div>
                  )}
                </div>
              )}

            </div>
          </div>
        )}

        {/* Footer */}
        <div className="px-5 py-4 border-t border-white/[0.06] bg-[var(--bg-base)] flex justify-between items-center">
          <span className={`text-[13px] transition-all ${
            saveStatus === 'ok' ? 'text-[#4ade80]' :
            saveStatus === 'err' ? 'text-[#f87171]' : 'text-transparent'
          }`}>
            {saveStatus === 'ok' ? '✓ Settings saved!' : saveStatus === 'err' ? '✗ Save failed — is the Neural Hub running?' : '.'}
          </span>
          <div className="flex gap-3">
            <button 
              onClick={onClose} 
              className="px-4 py-2 rounded-lg text-[13px] font-medium text-[#9a8f7e] hover:bg-white/[0.05] hover:text-[#f0ebe3] transition-all" 
              title="Cancel" 
              aria-label="Cancel"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-5 py-2 rounded-lg text-[13px] font-medium bg-[var(--accent)] text-[var(--bg-base)] hover:bg-[var(--accent)]/80 transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center gap-2"
              title="Save & Apply"
              aria-label="Save & Apply"
            >
              {saving ? 'Saving...' : <><Save size={14} /> Save & Apply</>}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const Checkbox = ({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void; }) => (
  <label className="flex items-center gap-3 cursor-pointer p-3 border border-white/[0.06] rounded-lg hover:border-white/[0.1] transition-colors bg-[var(--bg-base)]">
    <input 
      type="checkbox" 
      className="w-4 h-4 rounded bg-[var(--bg-base)] border-white/[0.1] text-[var(--accent)] focus:ring-[var(--accent)]/50"
      checked={checked}
      onChange={e => onChange(e.target.checked)}
    />
    <span className="text-[13px] font-medium text-[#f0ebe3]">{label}</span>
  </label>
);
