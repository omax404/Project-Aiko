import { useState } from 'react';
import { motion } from 'framer-motion';
import { useNeuralStore, getHubUrl, getAuthHeaders } from '../store/useNeuralStore';
import { ChevronLeft, ChevronRight, Cloud, Cpu, HardDrive, KeyRound, Sparkles, UserRound, Globe, Zap, Bot } from 'lucide-react';

export type ProviderId =
  | 'OpenRouter'
  | 'OpenAI'
  | 'Gemini'
  | 'DeepSeek'
  | 'Groq'
  | 'Anthropic'
  | 'Mistral'
  | 'Ollama'
  | 'Custom';

interface ProviderOption {
  id: ProviderId;
  title: string;
  badge?: string;
  description: string;
  detail: string;
  defaultUrl: string;
  defaultModel: string;
  keyPlaceholder: string;
  icon: typeof Cloud;
  requiresKey: boolean;
}

const providers: ProviderOption[] = [
  {
    id: 'OpenRouter',
    title: 'OpenRouter',
    badge: 'Popular',
    description: 'Access 200+ AI models (Claude, GPT-4o, Llama 3, Gemini) with one key.',
    detail: 'https://openrouter.ai/api/v1',
    defaultUrl: 'https://openrouter.ai/api/v1/chat/completions',
    defaultModel: 'anthropic/claude-3.5-sonnet',
    keyPlaceholder: 'sk-or-v1-...',
    icon: Cloud,
    requiresKey: true,
  },
  {
    id: 'OpenAI',
    title: 'OpenAI',
    badge: 'Standard',
    description: 'Direct access to GPT-4o, GPT-4o-mini, and o1.',
    detail: 'https://api.openai.com/v1',
    defaultUrl: 'https://api.openai.com/v1/chat/completions',
    defaultModel: 'gpt-4o',
    keyPlaceholder: 'sk-proj-...',
    icon: Sparkles,
    requiresKey: true,
  },
  {
    id: 'Gemini',
    title: 'Google Gemini',
    badge: 'Fast & High Context',
    description: 'Use Gemini 1.5 Pro, Flash, or 2.0 with generous limits.',
    detail: 'https://generativelanguage.googleapis.com/v1beta/openai',
    defaultUrl: 'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions',
    defaultModel: 'gemini-1.5-flash',
    keyPlaceholder: 'AIzaSy...',
    icon: Zap,
    requiresKey: true,
  },
  {
    id: 'DeepSeek',
    title: 'DeepSeek',
    badge: 'Reasoning & Coding',
    description: 'Ultra-low cost high intelligence with DeepSeek-V3 and R1.',
    detail: 'https://api.deepseek.com',
    defaultUrl: 'https://api.deepseek.com/chat/completions',
    defaultModel: 'deepseek-chat',
    keyPlaceholder: 'sk-...',
    icon: Cpu,
    requiresKey: true,
  },
  {
    id: 'Groq',
    title: 'Groq',
    badge: 'Blazing Fast (LPU)',
    description: 'Lightning-fast inference for Llama 3.3 70B, Mixtral, and Gemma 2.',
    detail: 'https://api.groq.com/openai/v1',
    defaultUrl: 'https://api.groq.com/openai/v1/chat/completions',
    defaultModel: 'llama-3.3-70b-versatile',
    keyPlaceholder: 'gsk_...',
    icon: Zap,
    requiresKey: true,
  },
  {
    id: 'Anthropic',
    title: 'Anthropic Claude',
    badge: 'Direct',
    description: 'Claude 3.5 Sonnet and Haiku via Anthropic API.',
    detail: 'https://api.anthropic.com/v1',
    defaultUrl: 'https://api.anthropic.com/v1/messages',
    defaultModel: 'claude-3-5-sonnet-20241022',
    keyPlaceholder: 'sk-ant-api...',
    icon: Bot,
    requiresKey: true,
  },
  {
    id: 'Mistral',
    title: 'Mistral AI',
    badge: 'European Frontier',
    description: 'Mistral Large, Codestral, and Pixtral endpoints.',
    detail: 'https://api.mistral.ai/v1',
    defaultUrl: 'https://api.mistral.ai/v1/chat/completions',
    defaultModel: 'mistral-large-latest',
    keyPlaceholder: '...',
    icon: Cloud,
    requiresKey: true,
  },
  {
    id: 'Ollama',
    title: 'Ollama (Local or Cloud)',
    badge: 'Local & Cloud',
    description: 'Run local models offline or use Ollama Cloud models (e.g. gemma4:31b-cloud).',
    detail: 'http://127.0.0.1:11434/api/chat',
    defaultUrl: 'http://127.0.0.1:11434/api/chat',
    defaultModel: 'gemma4:31b-cloud',
    keyPlaceholder: 'Optional — paste Ollama Cloud key or leave blank for local',
    icon: HardDrive,
    requiresKey: false,
  },
  {
    id: 'Custom',
    title: 'Custom / Any OpenAI-Compatible Provider',
    badge: 'Universal',
    description: 'Connect any AI server, self-hosted vLLM, Together, Perplexity, or local gateway.',
    detail: 'Any custom endpoint URL, model name, and API key.',
    defaultUrl: 'https://api.together.xyz/v1/chat/completions',
    defaultModel: 'meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo',
    keyPlaceholder: 'API key (if required)',
    icon: Globe,
    requiresKey: false,
  },
];

export function OnboardingWizard() {
  const [step, setStep] = useState(1);
  const [provider, setProvider] = useState<ProviderId>('OpenRouter');
  const [apiKey, setApiKey] = useState('');
  const [customUrl, setCustomUrl] = useState('');
  const [customModel, setCustomModel] = useState('');
  const [username, setUsername] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const updateApiConfig = useNeuralStore((s) => s.updateApiConfig);

  const selectedProviderOption: ProviderOption = providers.find((p) => p.id === provider) ?? providers[0]!;

  const handleComplete = async () => {
    const name = username.trim();
    if (!name) {
      setError('Add a name so Aiko knows what to call you.');
      return;
    }

    if (selectedProviderOption.requiresKey && !apiKey.trim()) {
      setError(`Enter an API key to connect ${selectedProviderOption.title}.`);
      return;
    }

    setSaving(true);
    setError('');

    try {
      const activeUrl = customUrl.trim() || selectedProviderOption.defaultUrl;
      const activeModel = customModel.trim() || selectedProviderOption.defaultModel;

      const configPatch: Record<string, any> = {
        username: name,
        PROVIDER: provider,
        API_KEY: apiKey.trim(),
        LLM_URL: activeUrl,
        MODEL_NAME: activeModel,
        llm: {
          provider,
          url: activeUrl,
          model: activeModel,
          api_key: apiKey.trim(),
        },
      };

      if (provider === 'DeepSeek') {
        configPatch.DEEPSEEK_API_KEY = apiKey.trim();
      } else if (provider === 'Gemini') {
        configPatch.GEMINI_API_KEY = apiKey.trim();
      }

      let headers = await getAuthHeaders({ 'Content-Type': 'application/json' });
      let response = await fetch(`${getHubUrl()}/api/settings`, {
        method: 'POST',
        headers,
        body: JSON.stringify(configPatch),
      });

      if (response.status === 401 || response.status === 403) {
        // Force refresh local token if stale or non-admin
        headers = await getAuthHeaders({ 'Content-Type': 'application/json' }, true);
        response = await fetch(`${getHubUrl()}/api/settings`, {
          method: 'POST',
          headers,
          body: JSON.stringify(configPatch),
        });
      }

      if (!response.ok) {
        throw new Error(`Aiko could not save setup (HTTP ${response.status}).`);
      }

      // Sync state in store
      updateApiConfig({
        provider,
        apiKey: apiKey.trim(),
        baseUrl: activeUrl,
        model: activeModel,
      });
    } catch (cause) {
      setError(
        cause instanceof Error
          ? `${cause.message} Check that Aiko is running, then try again.`
          : 'Aiko could not save setup. Check that Aiko is running, then try again.'
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      className="fixed inset-x-0 bottom-0 top-12 z-[100] flex items-center justify-center overflow-y-auto bg-[#0d0b12]/95 backdrop-blur-xl px-4 py-6 text-[var(--t1)]"
      role="dialog"
      aria-modal="true"
      aria-labelledby="setup-title"
    >
      <motion.section
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.25, ease: 'easeOut' }}
        className="relative mx-auto my-auto flex w-full max-w-4xl flex-col overflow-hidden rounded-[24px] border border-white/10 bg-[#14111b] shadow-2xl shadow-black/80 md:flex-row max-h-[90vh]"
      >
        {/* Left hero aesthetic column */}
        <div className="relative flex flex-col justify-between border-b border-white/10 bg-gradient-to-b from-[#1c1626] to-[#120e1a] p-8 md:w-[360px] md:shrink-0 md:border-b-0 md:border-r">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-[var(--accent)]/30 bg-[var(--accent)]/10 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-[var(--accent)]">
              <Sparkles size={13} /> Welcome to Aiko
            </div>
            <h1 id="setup-title" className="mt-5 text-2xl font-bold leading-tight text-white tracking-tight">
              Make room for a companion that feels like yours.
            </h1>
            <p className="mt-3 text-xs leading-relaxed text-white/60">
              Connect to any AI provider in the world—cloud, enterprise, or private local models—and customize her voice and personality.
            </p>
          </div>

          <div className="mt-8 space-y-4">
            <div className="flex items-center gap-3">
              <span
                className={`grid h-7 w-7 place-items-center rounded-full text-xs font-bold transition-colors ${
                  step === 1 ? 'bg-[var(--accent)] text-[#17121d]' : 'bg-white/10 text-white/50'
                }`}
              >
                1
              </span>
              <span className={`text-xs font-medium ${step === 1 ? 'text-white' : 'text-white/45'}`}>
                Choose Any AI Provider
              </span>
            </div>
            <div className="flex items-center gap-3">
              <span
                className={`grid h-7 w-7 place-items-center rounded-full text-xs font-bold transition-colors ${
                  step === 2 ? 'bg-[var(--accent)] text-[#17121d]' : 'bg-white/10 text-white/50'
                }`}
              >
                2
              </span>
              <span className={`text-xs font-medium ${step === 2 ? 'text-white' : 'text-white/45'}`}>
                Name & API Key Credentials
              </span>
            </div>
          </div>
        </div>

        {/* Right configuration area */}
        <div className="flex flex-1 flex-col overflow-y-auto p-6 md:p-8 custom-scrollbar">
          {step === 1 ? (
            <div>
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-white tracking-tight">Choose your AI Brain</h2>
                  <p className="mt-1 text-xs text-white/50">
                    Aiko supports any AI key or endpoint: OpenRouter, OpenAI, Gemini, Claude, DeepSeek, Groq, Ollama, or Custom.
                  </p>
                </div>
              </div>

              <div className="mt-5 grid grid-cols-1 gap-2.5 sm:grid-cols-2 max-h-[50vh] overflow-y-auto pr-1 custom-scrollbar">
                {providers.map((p) => {
                  const Icon = p.icon;
                  const isSelected = provider === p.id;
                  return (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => {
                        setProvider(p.id);
                        setCustomUrl(p.defaultUrl);
                        setCustomModel(p.defaultModel);
                        setError('');
                      }}
                      className={`group flex items-start gap-3 rounded-xl border p-3.5 text-left transition-all ${
                        isSelected
                          ? 'border-[var(--accent)] bg-[var(--accent)]/10 shadow-sm shadow-[var(--accent)]/10'
                          : 'border-white/5 bg-white/[0.02] hover:border-white/15 hover:bg-white/[0.05]'
                      }`}
                    >
                      <div
                        className={`mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-lg transition-colors ${
                          isSelected ? 'bg-[var(--accent)]/20 text-[var(--accent)]' : 'bg-white/5 text-white/60 group-hover:text-white'
                        }`}
                      >
                        <Icon size={17} />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center justify-between gap-1">
                          <span className="text-xs font-semibold text-white truncate">{p.title}</span>
                          {p.badge && (
                            <span className="shrink-0 rounded px-1.5 py-0.5 text-[9px] font-medium bg-white/10 text-white/70">
                              {p.badge}
                            </span>
                          )}
                        </div>
                        <p className="mt-0.5 text-[11px] leading-snug text-white/50 line-clamp-2">{p.description}</p>
                      </div>
                    </button>
                  );
                })}
              </div>

              <div className="mt-6 flex items-center justify-between border-t border-white/5 pt-4">
                <span className="text-xs text-white/40">You can switch or tweak models at any time in Settings.</span>
                <button
                  type="button"
                  onClick={() => setStep(2)}
                  className="inline-flex h-10 items-center gap-2 rounded-xl bg-[var(--accent)] px-5 text-xs font-bold text-[#14111b] transition hover:brightness-110 shadow-lg shadow-[var(--accent)]/20"
                >
                  Configure {selectedProviderOption.title} <ChevronRight size={15} />
                </button>
              </div>
            </div>
          ) : (
            <div>
              <button
                type="button"
                onClick={() => {
                  setStep(1);
                  setError('');
                }}
                className="mb-4 inline-flex items-center gap-1.5 text-xs font-medium text-white/50 transition hover:text-white"
              >
                <ChevronLeft size={14} /> Back to providers ({selectedProviderOption.title})
              </button>

              <h2 className="text-lg font-bold text-white tracking-tight">Configure {selectedProviderOption.title}</h2>
              <p className="mt-1 text-xs text-white/50">
                Personalize your companion and enter your credentials. All keys are encrypted locally on your machine.
              </p>

              {/* Your Name */}
              <div className="mt-5 space-y-1.5">
                <label htmlFor="setup-name" className="flex items-center gap-2 text-xs font-semibold text-white/80">
                  <UserRound size={13} className="text-[var(--accent)]" /> Aiko should call you...
                </label>
                <input
                  id="setup-name"
                  type="text"
                  autoComplete="nickname"
                  value={username}
                  onChange={(e) => {
                    setUsername(e.target.value);
                    setError('');
                  }}
                  className="h-10 w-full rounded-xl border border-white/10 bg-black/30 px-3.5 text-xs text-white outline-none transition placeholder:text-white/25 focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)]"
                  placeholder="Your name or nickname"
                />
              </div>

              {/* API Key (required for cloud, optional for Ollama Cloud / Custom) */}
              <div className="mt-4 space-y-1.5">
                <div className="flex items-center justify-between">
                  <label htmlFor="setup-api-key" className="flex items-center gap-2 text-xs font-semibold text-white/80">
                    <KeyRound size={13} className="text-[var(--accent)]" /> {selectedProviderOption.title} API Key
                    {!selectedProviderOption.requiresKey && (
                      <span className="text-[10px] font-normal text-white/45">(Optional for local)</span>
                    )}
                  </label>
                  <span className="text-[10px] text-white/40">Stored securely with OS encryption</span>
                </div>
                <input
                  id="setup-api-key"
                  type="password"
                  autoComplete="off"
                  spellCheck={false}
                  value={apiKey}
                  onChange={(e) => {
                    setApiKey(e.target.value);
                    setError('');
                  }}
                  className="h-10 w-full rounded-xl border border-white/10 bg-black/30 px-3.5 font-mono text-xs text-white outline-none transition placeholder:text-white/25 focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)]"
                  placeholder={selectedProviderOption.keyPlaceholder}
                />
              </div>

              {/* Endpoint URL (shown for Custom, or collapsible for advanced users) */}
              <div className="mt-4 space-y-1.5">
                <div className="flex items-center justify-between">
                  <label htmlFor="setup-url" className="flex items-center gap-2 text-xs font-semibold text-white/80">
                    <Globe size={13} className="text-[var(--accent)]" /> Endpoint URL
                  </label>
                  <span className="text-[10px] text-white/40">Default auto-set</span>
                </div>
                <input
                  id="setup-url"
                  type="text"
                  value={customUrl || selectedProviderOption.defaultUrl}
                  onChange={(e) => setCustomUrl(e.target.value)}
                  className="h-10 w-full rounded-xl border border-white/10 bg-black/30 px-3.5 font-mono text-xs text-white outline-none transition placeholder:text-white/25 focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)]"
                  placeholder={selectedProviderOption.defaultUrl}
                />
              </div>

              {/* Model Name */}
              <div className="mt-4 space-y-1.5">
                <div className="flex items-center justify-between">
                  <label htmlFor="setup-model" className="flex items-center gap-2 text-xs font-semibold text-white/80">
                    <Cpu size={13} className="text-[var(--accent)]" /> Model Identifier
                  </label>
                  <span className="text-[10px] text-white/40">E.g., claude-3-5-sonnet, gpt-4o, gemini-1.5-flash</span>
                </div>
                <input
                  id="setup-model"
                  type="text"
                  value={customModel || selectedProviderOption.defaultModel}
                  onChange={(e) => setCustomModel(e.target.value)}
                  className="h-10 w-full rounded-xl border border-white/10 bg-black/30 px-3.5 font-mono text-xs text-white outline-none transition placeholder:text-white/25 focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)]"
                  placeholder={selectedProviderOption.defaultModel}
                />
              </div>

              {error && (
                <p role="alert" className="mt-4 rounded-xl border border-red-500/20 bg-red-500/10 px-3.5 py-2.5 text-xs text-red-200">
                  {error}
                </p>
              )}

              <div className="mt-6 flex items-center justify-between border-t border-white/5 pt-4">
                <span className="text-[11px] text-white/40">Ready to activate your desktop companion</span>
                <button
                  type="button"
                  onClick={() => void handleComplete()}
                  disabled={saving}
                  className="inline-flex h-10 shrink-0 items-center gap-2 rounded-xl bg-[var(--accent)] px-5 text-xs font-bold text-[#14111b] transition hover:brightness-110 disabled:cursor-wait disabled:opacity-60 shadow-lg shadow-[var(--accent)]/20"
                >
                  {saving ? 'Connecting...' : 'Start with Aiko'} <ChevronRight size={15} />
                </button>
              </div>
            </div>
          )}
        </div>
      </motion.section>
    </div>
  );
}
