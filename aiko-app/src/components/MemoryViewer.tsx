import { useCallback, useEffect, useState } from 'react';
import { Plus, RefreshCw, Save, Trash2 } from 'lucide-react';
import { getHubUrl, getAuthHeaders } from '../store/hubClient';

type Row = { id: number; key: string; text: string; isString: boolean };

let nextId = 1;

function toRows(profile: Record<string, unknown>): Row[] {
  return Object.entries(profile).map(([key, value]) => ({
    id: nextId++,
    key,
    isString: typeof value === 'string',
    text: typeof value === 'string' ? value : JSON.stringify(value, null, 2),
  }));
}

/** Settings > Memory: see, edit and delete what Aiko has learned about you. */
export function MemoryViewer() {
  const [rows, setRows] = useState<Row[]>([]);
  const [status, setStatus] = useState('');
  const [busy, setBusy] = useState(false);
  const [dirty, setDirty] = useState(false);

  const load = useCallback(async () => {
    setBusy(true);
    setStatus('');
    try {
      const headers = await getAuthHeaders();
      const res = await fetch(`${getHubUrl()}/api/memory/profile`, { headers });
      if (!res.ok) throw new Error(res.status === 403 ? 'Administrator access required' : `HTTP ${res.status}`);
      const data = await res.json();
      setRows(toRows(data.profile || {}));
      setDirty(false);
    } catch (e: any) {
      setStatus(`Could not load memory: ${e?.message || e}`);
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const update = (id: number, patch: Partial<Row>) => {
    setRows((prev) => prev.map((r) => (r.id === id ? { ...r, ...patch } : r)));
    setDirty(true);
  };

  const remove = (id: number) => {
    setRows((prev) => prev.filter((r) => r.id !== id));
    setDirty(true);
  };

  const add = () => {
    setRows((prev) => [...prev, { id: nextId++, key: '', text: '', isString: true }]);
    setDirty(true);
  };

  const save = async (override?: Row[]) => {
    const source = override ?? rows;
    const profile: Record<string, unknown> = {};
    for (const row of source) {
      const key = row.key.trim();
      if (!key) continue;
      if (key in profile) {
        setStatus(`Duplicate name: "${key}"`);
        return;
      }
      if (row.isString) {
        profile[key] = row.text;
      } else {
        try {
          profile[key] = JSON.parse(row.text);
        } catch {
          setStatus(`"${key}" is not valid JSON. Fix it or delete it.`);
          return;
        }
      }
    }
    setBusy(true);
    try {
      const headers = await getAuthHeaders({ 'Content-Type': 'application/json' });
      const res = await fetch(`${getHubUrl()}/api/memory/profile`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ profile }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setRows(toRows(data.profile || {}));
      setDirty(false);
      setStatus('Saved.');
    } catch (e: any) {
      setStatus(`Could not save: ${e?.message || e}`);
    } finally {
      setBusy(false);
    }
  };

  const forgetAll = async () => {
    if (!window.confirm('Make Aiko forget everything she has learned about you? This cannot be undone.')) return;
    await save([]);
  };

  return (
    <section className="p-4 rounded-xl bg-[var(--bg-base)] border border-white/[0.06]">
      <div className="flex items-center justify-between gap-3 mb-1">
        <span className="text-[13px] font-medium text-[#f0ebe3]">What Aiko remembers about you</span>
        <button
          type="button"
          onClick={load}
          disabled={busy}
          className="p-1.5 text-[#9a8f7e] hover:text-[var(--accent)] disabled:opacity-40"
          aria-label="Reload memory"
          title="Reload"
        >
          <RefreshCw size={14} className={busy ? 'animate-spin' : ''} />
        </button>
      </div>
      <p className="text-[12px] text-[#9a8f7e] mb-3">
        Aiko builds this from your chats. Edit a value, delete an entry, or add your own. Changes apply to future
        replies.
      </p>

      <div className="flex flex-col gap-3">
        {rows.length === 0 && !busy && (
          <p className="text-[12px] text-[#5a5248]">Nothing saved yet.</p>
        )}
        {rows.map((row) => (
          <div key={row.id} className="flex items-start gap-2">
            <div className="flex-1 flex flex-col gap-1.5">
              <input
                value={row.key}
                onChange={(e) => update(row.id, { key: e.target.value })}
                placeholder="Name (e.g. likes)"
                aria-label="Memory name"
                className="bg-[#181612] border border-white/[0.06] rounded-lg px-2 py-1.5 text-[12px] font-medium text-[var(--accent)] focus:border-[var(--accent)]/50 focus:outline-none"
              />
              <textarea
                value={row.text}
                onChange={(e) => update(row.id, { text: e.target.value })}
                aria-label={`Memory value for ${row.key || 'new entry'}`}
                rows={row.isString ? 2 : Math.min(8, row.text.split('\n').length + 1)}
                spellCheck={false}
                className={`bg-[#181612] border border-white/[0.06] rounded-lg p-2 text-[12px] text-[#f0ebe3] focus:border-[var(--accent)]/50 focus:outline-none resize-y ${
                  row.isString ? '' : 'font-mono'
                }`}
              />
            </div>
            <button
              type="button"
              onClick={() => remove(row.id)}
              className="p-2 text-[#9a8f7e] hover:text-[#f87171]"
              aria-label={`Delete ${row.key || 'entry'}`}
              title="Delete"
            >
              <Trash2 size={14} />
            </button>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-3 mt-4 pt-3 border-t border-white/[0.08]">
        <button
          type="button"
          onClick={add}
          className="flex items-center gap-1.5 text-[12px] text-[var(--accent)] hover:opacity-80"
        >
          <Plus size={14} /> Add entry
        </button>
        <button
          type="button"
          onClick={() => save()}
          disabled={busy || !dirty}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[var(--accent)]/15 border border-[var(--accent)]/40 text-[12px] text-[var(--accent)] disabled:opacity-40"
        >
          <Save size={13} /> Save changes
        </button>
        <button
          type="button"
          onClick={forgetAll}
          disabled={busy || rows.length === 0}
          className="ml-auto text-[12px] text-[#f87171] hover:opacity-80 disabled:opacity-40"
        >
          Forget everything
        </button>
      </div>
      {status && <p className="mt-2 text-[11px] text-[#f0c674]">{status}</p>}
    </section>
  );
}
