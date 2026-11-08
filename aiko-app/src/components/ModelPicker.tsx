import { useCallback, useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import { Check, ChevronUp } from 'lucide-react';
import { getHubUrl, getAuthHeaders } from '../store/hubClient';

interface ModelList {
  current: string;
  fallback: string;
  models: string[];
  local_reachable: boolean;
}

/**
 * Chat-bar model picker. Pick the main model (local or cloud, such as
 * gemma4:31b-cloud) and a backup model that Aiko switches to automatically
 * when the main one cannot answer (for example when the cloud is down).
 */
export function ModelPicker({ fallbackLabel, icon }: { fallbackLabel: string; icon: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<ModelList | null>(null);
  const [status, setStatus] = useState('');
  const [busy, setBusy] = useState(false);
  const boxRef = useRef<HTMLDivElement>(null);

  const load = useCallback(async () => {
    try {
      const headers = await getAuthHeaders();
      const res = await fetch(`${getHubUrl()}/api/models`, { headers });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setData(await res.json());
    } catch (e: any) {
      setStatus(`Could not load models: ${e?.message || e}`);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (!open) return;
    setStatus('');
    load();
    const onDown = (e: MouseEvent) => {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', onDown);
    return () => document.removeEventListener('mousedown', onDown);
  }, [open, load]);

  const saveLlm = async (patch: Record<string, string>, done: string) => {
    setBusy(true);
    setStatus('');
    try {
      const headers = await getAuthHeaders({ 'Content-Type': 'application/json' });
      const res = await fetch(`${getHubUrl()}/api/settings`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ llm: patch }),
      });
      if (!res.ok) {
        throw new Error(res.status === 403 ? 'Open the Aiko desktop app to change models' : `HTTP ${res.status}`);
      }
      setStatus(done);
      await load();
    } catch (e: any) {
      setStatus(e?.message || String(e));
    } finally {
      setBusy(false);
    }
  };

  const current = data?.current || fallbackLabel;

  return (
    <div ref={boxRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-[var(--p-accent-soft)] border border-[var(--b1)] hover:brightness-125 transition"
        aria-haspopup="listbox"
        aria-expanded={open}
        title="Switch model"
      >
        {icon}
        <span className="text-[11px] font-semibold text-[var(--p-accent)] tracking-wide truncate max-w-[140px]">
          {current}
        </span>
        <ChevronUp size={10} className={`text-[var(--p-accent)] transition-transform ${open ? '' : 'rotate-180'}`} />
      </button>

      {open && (
        <div className="absolute bottom-full left-0 mb-2 w-72 z-50 rounded-xl bg-[#14111c] border border-white/10 shadow-2xl p-2">
          <div className="px-2 pb-1 text-[10px] uppercase tracking-wider text-white/40">Model</div>
          <div className="max-h-56 overflow-y-auto flex flex-col" role="listbox">
            {(data?.models || []).map((name) => (
              <button
                key={name}
                type="button"
                role="option"
                aria-selected={name === data?.current}
                disabled={busy}
                onClick={() => name !== data?.current && saveLlm({ model: name }, `Now using ${name}`)}
                className="flex items-center justify-between gap-2 px-2 py-1.5 rounded-lg text-left text-[12px] text-white/80 hover:bg-white/[0.06] disabled:opacity-50"
              >
                <span className="truncate">{name}</span>
                {name === data?.current && <Check size={12} className="text-[var(--p-accent)] shrink-0" />}
              </button>
            ))}
            {data && data.models.length === 0 && (
              <div className="px-2 py-1.5 text-[12px] text-white/40">No models found</div>
            )}
          </div>

          <div className="mt-2 pt-2 border-t border-white/10 px-2">
            <label className="block text-[10px] uppercase tracking-wider text-white/40 mb-1">
              Backup if the main model fails
            </label>
            <select
              value={data?.fallback || ''}
              disabled={busy}
              onChange={(e) =>
                saveLlm(
                  { fallback_model: e.target.value },
                  e.target.value ? `Backup: ${e.target.value}` : 'Backup turned off',
                )
              }
              className="w-full bg-[#181612] border border-white/10 rounded-lg px-2 py-1.5 text-[12px] text-white/80 focus:outline-none focus:border-[var(--p-accent)]/50"
            >
              <option value="">None</option>
              {(data?.models || [])
                .filter((m) => m !== data?.current)
                .map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
            </select>
            {data && !data.local_reachable && (
              <p className="mt-1 text-[11px] text-[#f0c674]">Local Ollama was not found, so the list may be short.</p>
            )}
          </div>

          {status && <p className="px-2 pt-2 text-[11px] text-[#f0c674]">{status}</p>}
        </div>
      )}
    </div>
  );
}
