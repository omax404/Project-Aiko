import { useState } from 'react';
import { motion } from 'framer-motion';
import { useNeuralStore, getHubUrl, getAuthHeaders } from '../store/useNeuralStore';
import { Check, ChevronLeft, ChevronRight, Cloud, HardDrive, KeyRound, Sparkles, UserRound } from 'lucide-react';

type Provider = 'Ollama' | 'OpenRouter' | 'DeepSeek';

const providers: { id: Provider; title: string; description: string; detail: string; icon: typeof HardDrive }[] = [
  {
    id: 'Ollama',
    title: 'Run locally',
    description: 'Your conversations stay on this computer.',
    detail: 'Requires Ollama to be installed and running.',
    icon: HardDrive,
  },
  {
    id: 'OpenRouter',
    title: 'Use OpenRouter',
    description: 'Choose from models by several providers.',
    detail: 'Uses your OpenRouter API key.',
    icon: Cloud,
  },
  {
    id: 'DeepSeek',
    title: 'Use DeepSeek',
    description: 'Connect directly to DeepSeek models.',
    detail: 'Uses your DeepSeek API key.',
    icon: Cloud,
  },
];

export function OnboardingWizard() {
  const [step, setStep] = useState(1);
  const [provider, setProvider] = useState<Provider | null>(null);
  const [apiKey, setApiKey] = useState('');
  const [username, setUsername] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const updateApiConfig = useNeuralStore((s) => s.updateApiConfig);

  const handleComplete = async () => {
    const name = username.trim();
    if (!provider) return;
    if (!name) { setError('Add a name so Aiko knows what to call you.'); return; }
    if (provider !== 'Ollama' && !apiKey.trim()) { setError('Enter an API key to connect this provider.'); return; }

    setSaving(true);
    setError('');
    try {
      const configPatch: Record<string, string> = { username: name, PROVIDER: provider };
      if (provider === 'OpenRouter') configPatch.API_KEY = apiKey.trim();
      if (provider === 'DeepSeek') configPatch.DEEPSEEK_API_KEY = apiKey.trim();

      const headers = await getAuthHeaders({ 'Content-Type': 'application/json' });
      const response = await fetch(`${getHubUrl()}/api/settings`, {
        method: 'POST',
        headers,
        body: JSON.stringify(configPatch),
      });
      if (!response.ok) throw new Error(`Aiko could not save setup (HTTP ${response.status}).`);

      // The hub owns provider configuration. Keep the UI in sync after it confirms the save.
      updateApiConfig({ provider, apiKey: provider === 'Ollama' ? '' : apiKey.trim() });
    } catch (cause) {
      setError(cause instanceof Error
        ? `${cause.message} Check that Aiko is running, then try again.`
        : 'Aiko could not save setup. Check that Aiko is running, then try again.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      className="fixed inset-x-0 bottom-0 top-12 z-[100] flex items-center justify-center overflow-y-auto bg-[#100d14] px-4 py-6 text-[var(--t1)]"
      role="dialog"
      aria-modal="true"
      aria-labelledby="setup-title"
    >
      <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
        <div className="absolute -left-40 top-[-12rem] h-[34rem] w-[34rem] rounded-full bg-[var(--accent)]/[0.08] blur-[100px]" />
        <div className="absolute -bottom-72 -right-24 h-[36rem] w-[36rem] rounded-full bg-[#73558b]/[0.12] blur-[120px]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_15%,#100d14_80%)]" />
      </div>

      <motion.section
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative grid w-full max-w-5xl overflow-hidden rounded-3xl border border-white/[0.09] bg-[#15121a]/95 shadow-[0_28px_100px_rgba(0,0,0,0.45)] md:min-h-[570px] md:grid-cols-[0.85fr_1.15fr]"
      >
        <aside className="relative flex flex-col justify-between overflow-hidden border-b border-white/[0.07] bg-white/[0.018] p-7 sm:p-10 md:border-b-0 md:border-r">
          <div className="absolute -bottom-20 -left-20 h-64 w-64 rounded-full border border-[var(--accent)]/[0.10]" aria-hidden="true" />
          <div className="absolute -bottom-10 -left-10 h-44 w-44 rounded-full border border-[var(--accent)]/[0.10]" aria-hidden="true" />
          <div className="relative">
            <div className="mb-12 flex items-center gap-3">
              <div className="grid h-10 w-10 place-items-center rounded-2xl border border-[var(--accent)]/25 bg-[var(--accent)]/[0.10] text-[var(--accent)]">
                <Sparkles size={18} />
              </div>
              <span className="text-sm font-semibold tracking-wide text-white">Aiko</span>
            </div>
            <p className="mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--accent)]">A good place to begin</p>
            <h1 id="setup-title" className="max-w-sm text-3xl font-semibold leading-tight tracking-[-0.04em] text-white sm:text-4xl">
              Make room for a companion that feels like yours.
            </h1>
            <p className="mt-5 max-w-sm text-sm leading-6 text-white/55">
              Choose how Aiko thinks, then tell her what to call you. You can change these settings any time.
            </p>
          </div>

          <div className="relative mt-8 flex items-center gap-3 text-xs text-white/45">
            <span className={`grid h-7 w-7 place-items-center rounded-full border ${step === 1 ? 'border-[var(--accent)]/50 bg-[var(--accent)]/10 text-[var(--accent)]' : 'border-white/10 text-white/45'}`}>
              {step > 1 ? <Check size={14} /> : '1'}
            </span>
            <span className={step === 1 ? 'text-white/80' : ''}>Choose a model</span>
            <span className="h-px w-7 bg-white/10" />
            <span className={`grid h-7 w-7 place-items-center rounded-full border ${step === 2 ? 'border-[var(--accent)]/50 bg-[var(--accent)]/10 text-[var(--accent)]' : 'border-white/10 text-white/45'}`}>2</span>
            <span className={step === 2 ? 'text-white/80' : ''}>Make it yours</span>
          </div>
        </aside>

        <div className="relative flex flex-col justify-center p-6 sm:p-10 lg:p-12">
          {step === 1 ? (
            <div>
              <h2 className="text-xl font-semibold text-white">Where should Aiko think?</h2>
              <p className="mt-2 text-sm leading-6 text-white/50">Pick the setup that works for you. You can switch providers later.</p>
              <div className="mt-7 grid gap-3">
                {providers.map(({ id, title, description, detail, icon: Icon }) => {
                  const selected = provider === id;
                  return (
                    <button
                      key={id}
                      type="button"
                      onClick={() => { setProvider(id); setError(''); }}
                      aria-pressed={selected}
                      className={`group flex w-full items-start gap-4 rounded-2xl border p-4 text-left transition-colors ${selected ? 'border-[var(--accent)]/55 bg-[var(--accent)]/[0.09]' : 'border-white/[0.08] bg-white/[0.025] hover:border-white/20 hover:bg-white/[0.045]'}`}
                    >
                      <span className={`mt-0.5 grid h-10 w-10 shrink-0 place-items-center rounded-xl ${selected ? 'bg-[var(--accent)]/15 text-[var(--accent)]' : 'bg-white/[0.05] text-white/55 group-hover:text-white/80'}`}>
                        <Icon size={18} />
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block text-sm font-medium text-white">{title}</span>
                        <span className="mt-1 block text-sm text-white/55">{description}</span>
                        <span className="mt-1.5 block text-xs text-white/35">{detail}</span>
                      </span>
                      <span className={`mt-1 grid h-5 w-5 shrink-0 place-items-center rounded-full border ${selected ? 'border-[var(--accent)] bg-[var(--accent)] text-[#17121d]' : 'border-white/15'}`}>
                        {selected && <Check size={12} strokeWidth={3} />}
                      </span>
                    </button>
                  );
                })}
              </div>
              <div className="mt-7 flex justify-end">
                <button
                  type="button"
                  onClick={() => setStep(2)}
                  disabled={!provider}
                  className="inline-flex h-11 items-center gap-2 rounded-xl bg-[var(--accent)] px-5 text-sm font-semibold text-[#17121d] transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-35"
                >
                  Continue <ChevronRight size={16} />
                </button>
              </div>
            </div>
          ) : (
            <div>
              <button type="button" onClick={() => { setStep(1); setError(''); }} className="mb-6 inline-flex items-center gap-1.5 text-xs text-white/45 transition hover:text-white/80">
                <ChevronLeft size={14} /> Change model choice
              </button>
              <h2 className="text-xl font-semibold text-white">Aiko should call you…</h2>
              <p className="mt-2 text-sm leading-6 text-white/50">A name or nickname is perfect. This stays on your Aiko setup.</p>

              <label htmlFor="setup-name" className="mb-2 mt-7 flex items-center gap-2 text-xs font-medium text-white/75">
                <UserRound size={14} className="text-[var(--accent)]" /> Your name
              </label>
              <input
                id="setup-name"
                type="text"
                autoComplete="nickname"
                value={username}
                onChange={(event) => { setUsername(event.target.value); setError(''); }}
                onKeyDown={(event) => { if (event.key === 'Enter' && provider === 'Ollama') void handleComplete(); }}
                className="h-12 w-full rounded-xl border border-white/10 bg-black/20 px-4 text-sm text-white outline-none transition placeholder:text-white/25 focus:border-[var(--accent)]/55 focus:ring-2 focus:ring-[var(--accent)]/10"
                placeholder="What do you go by?"
              />

              {provider !== 'Ollama' && (
                <>
                  <label htmlFor="setup-api-key" className="mb-2 mt-6 flex items-center gap-2 text-xs font-medium text-white/75">
                    <KeyRound size={14} className="text-[var(--accent)]" /> {provider} API key
                  </label>
                  <input
                    id="setup-api-key"
                    type="password"
                    autoComplete="off"
                    spellCheck={false}
                    value={apiKey}
                    onChange={(event) => { setApiKey(event.target.value); setError(''); }}
                    className="h-12 w-full rounded-xl border border-white/10 bg-black/20 px-4 font-mono text-sm text-white outline-none transition placeholder:text-white/25 focus:border-[var(--accent)]/55 focus:ring-2 focus:ring-[var(--accent)]/10"
                    placeholder="Paste your API key"
                  />
                  <p className="mt-2 text-xs leading-5 text-white/40">The key is saved in your local Aiko configuration and sent to the provider you selected.</p>
                </>
              )}

              {provider === 'Ollama' && (
                <div className="mt-5 rounded-xl border border-white/[0.07] bg-white/[0.025] p-3.5 text-xs leading-5 text-white/45">
                  Before continuing, make sure Ollama is installed, running, and has at least one model downloaded.
                </div>
              )}

              {error && <p role="alert" className="mt-5 rounded-xl border border-red-400/20 bg-red-400/[0.06] px-3.5 py-3 text-sm leading-5 text-red-200/90">{error}</p>}

              <div className="mt-7 flex items-center justify-between gap-4">
                <p className="text-xs text-white/30">You can change providers later in Settings.</p>
                <button
                  type="button"
                  onClick={() => void handleComplete()}
                  disabled={saving}
                  className="inline-flex h-11 shrink-0 items-center gap-2 rounded-xl bg-[var(--accent)] px-5 text-sm font-semibold text-[#17121d] transition hover:brightness-110 disabled:cursor-wait disabled:opacity-65"
                >
                  {saving ? 'Saving…' : 'Start with Aiko'} <ChevronRight size={16} />
                </button>
              </div>
            </div>
          )}
        </div>
      </motion.section>
    </div>
  );
}
