import React, { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (settings: any) => void;
}

export const SettingsPanel: React.FC<SettingsPanelProps> = ({ isOpen, onClose, onSave }) => {
  const [settings, setSettings] = useState<any>({
    llm: { url: 'http://127.0.0.1:11434/api/chat', model: 'qwen3.5:397b-cloud' },
    tts: { enabled: true, voice: 'vivian', speed: 0.9 },
    persona: { custom_prompt: 'You are a highly capable AI agent designed to assist with anything the user needs. Always be polite, concise, and helpful.' },
    plugins: { discord_bot: false, telegram_bot: false, openclaw_bridge: false }
  });
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('persona');

  useEffect(() => {
    if (isOpen) {
      loadSettings();
    }
  }, [isOpen]);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const jsonStr: string = await invoke('get_user_settings');
      const data = JSON.parse(jsonStr);
      
      // Merge with defaults to ensure all keys exist
      setSettings((prev: any) => ({
        llm: { ...prev.llm, ...(data.llm || {}) },
        tts: { ...prev.tts, ...(data.tts || {}) },
        persona: { ...prev.persona, ...(data.persona || {}) },
        plugins: { ...prev.plugins, ...(data.plugins || {}) }
      }));
    } catch (e) {
      console.error("Failed to load settings:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      await invoke('save_user_settings', { settings: JSON.stringify(settings, null, 2) });
      onSave(settings);
      onClose();
    } catch (e) {
      console.error("Failed to save settings:", e);
      alert("Failed to save settings. See console for details.");
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm transition-opacity">
      <div className="bg-[#121212] border border-[#2a2a2a] rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="flex justify-between items-center p-4 border-b border-[#2a2a2a] bg-[#1a1a1a]">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span className="text-[#a8b8ff]">⚙️</span> Aiko Customization
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors" title="Close settings">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
          </button>
        </div>

        {loading ? (
          <div className="p-8 text-center text-gray-400">Loading settings...</div>
        ) : (
          <div className="flex h-[500px]">
            {/* Sidebar */}
            <div className="w-1/3 border-r border-[#2a2a2a] bg-[#151515] p-2 flex flex-col gap-1">
              <TabButton active={activeTab === 'persona'} onClick={() => setActiveTab('persona')} icon="🎭" label="Persona" />
              <TabButton active={activeTab === 'llm'} onClick={() => setActiveTab('llm')} icon="🧠" label="AI Model" />
              <TabButton active={activeTab === 'tts'} onClick={() => setActiveTab('tts')} icon="🎙️" label="Voice & TTS" />
              <TabButton active={activeTab === 'plugins'} onClick={() => setActiveTab('plugins')} icon="🔌" label="Plugins" />
            </div>

            {/* Content Area */}
            <div className="w-2/3 p-6 overflow-y-auto bg-[#1a1a1a]">
              
              {activeTab === 'persona' && (
                <div className="space-y-4">
                  <h3 className="text-lg font-medium text-white mb-2">Custom Personality Injection</h3>
                  <p className="text-xs text-gray-400 mb-4">Write custom instructions to override or append to Aiko's default personality. You can tell her to act like a pirate, be extremely sarcastic, or focus only on coding.</p>
                  <textarea 
                    id="persona-prompt"
                    className="w-full h-64 bg-[#111] border border-[#333] rounded-lg p-3 text-sm text-white focus:border-[#a8b8ff] focus:ring-1 focus:ring-[#a8b8ff] outline-none resize-none"
                    value={settings.persona.custom_prompt}
                    onChange={e => setSettings({...settings, persona: {...settings.persona, custom_prompt: e.target.value}})}
                    placeholder="E.g., You are a highly professional assistant..."
                    aria-label="Custom Personality Injection"
                  />
                </div>
              )}

              {activeTab === 'llm' && (
                <div className="space-y-5">
                  <h3 className="text-lg font-medium text-white mb-2">LLM Configuration</h3>
                  <div>
                    <label className="block text-xs font-medium text-gray-400 mb-1">API URL (Ollama or OpenAI compatible)</label>
                    <input 
                      id="api-url"
                      type="text"
                      className="w-full bg-[#111] border border-[#333] rounded-lg p-2.5 text-sm text-white focus:border-[#a8b8ff] outline-none"
                      value={settings.llm.url}
                      onChange={e => setSettings({...settings, llm: {...settings.llm, url: e.target.value}})}
                      aria-label="API URL"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-400 mb-1">Model Name</label>
                    <input 
                      id="model-name"
                      type="text"
                      className="w-full bg-[#111] border border-[#333] rounded-lg p-2.5 text-sm text-white focus:border-[#a8b8ff] outline-none"
                      value={settings.llm.model}
                      onChange={e => setSettings({...settings, llm: {...settings.llm, model: e.target.value}})}
                      aria-label="Model Name"
                    />
                    <p className="text-xs text-gray-500 mt-1">E.g., "qwen3.5:397b-cloud" or "gpt-4o"</p>
                  </div>
                </div>
              )}

              {activeTab === 'tts' && (
                <div className="space-y-5">
                  <h3 className="text-lg font-medium text-white mb-2">Voice Synthesis</h3>
                  
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="w-4 h-4 rounded bg-[#111] border-[#333] text-[#a8b8ff] focus:ring-[#a8b8ff]"
                      checked={settings.tts.enabled}
                      onChange={e => setSettings({...settings, tts: {...settings.tts, enabled: e.target.checked}})}
                    />
                    <span className="text-sm font-medium text-white">Enable Aiko's Voice</span>
                  </label>

                  <div className={!settings.tts.enabled ? 'opacity-50 pointer-events-none' : ''}>
                    <label className="block text-xs font-medium text-gray-400 mb-1 mt-4">Voice Profile</label>
                    <select 
                      id="voice-profile"
                      className="w-full bg-[#111] border border-[#333] rounded-lg p-2.5 text-sm text-white focus:border-[#a8b8ff] outline-none"
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
              )}

              {activeTab === 'plugins' && (
                <div className="space-y-5">
                  <h3 className="text-lg font-medium text-white mb-2">Integrations</h3>
                  <p className="text-xs text-gray-400 mb-4">Enable external bridges. Requires restarting the application to take full effect.</p>
                  
                  <div className="space-y-3">
                    <Checkbox label="Discord Bot (Satellite)" checked={settings.plugins.discord_bot} onChange={v => setSettings({...settings, plugins: {...settings.plugins, discord_bot: v}})} />
                    <Checkbox label="Telegram Bot (Satellite)" checked={settings.plugins.telegram_bot} onChange={v => setSettings({...settings, plugins: {...settings.plugins, telegram_bot: v}})} />
                    <Checkbox label="OpenClaw PC Bridge" checked={settings.plugins.openclaw_bridge} onChange={v => setSettings({...settings, plugins: {...settings.plugins, openclaw_bridge: v}})} />
                  </div>
                </div>
              )}

            </div>
          </div>
        )}

        {/* Footer */}
        <div className="p-4 border-t border-[#2a2a2a] bg-[#1a1a1a] flex justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 rounded-lg text-sm font-medium text-gray-300 hover:bg-[#2a2a2a] transition-colors">
            Cancel
          </button>
          <button onClick={handleSave} className="px-6 py-2 rounded-lg text-sm font-medium bg-[#a8b8ff] text-black hover:bg-[#90a2ff] transition-colors shadow-[0_0_15px_rgba(168,184,255,0.3)]">
            Save & Apply
          </button>
        </div>
      </div>
    </div>
  );
};

// Helper Components
const TabButton = ({ active, onClick, icon, label }: any) => (
  <button 
    onClick={onClick}
    className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors text-left ${active ? 'bg-[#2a2a2a] text-[#a8b8ff]' : 'text-gray-400 hover:bg-[#222] hover:text-white'}`}
  >
    <span className="text-lg">{icon}</span>
    {label}
  </button>
);

const Checkbox = ({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void; }) => (
  <label className="flex items-center gap-3 cursor-pointer p-3 border border-[#2a2a2a] rounded-lg hover:border-[#444] transition-colors bg-[#111]">
    <input 
      type="checkbox" 
      className="w-4 h-4 rounded bg-[#111] border-[#333] text-[#a8b8ff] focus:ring-[#a8b8ff]"
      checked={checked}
      onChange={e => onChange(e.target.checked)}
    />
    <span className="text-sm font-medium text-white">{label}</span>
  </label>
);
