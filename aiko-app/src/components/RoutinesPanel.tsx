import { useCallback, useEffect, useState } from 'react';
import { Plus, Save, Trash2 } from 'lucide-react';
import { getHubUrl, getAuthHeaders } from '../store/hubClient';

type Kind = 'greeting' | 'study' | 'deadline' | 'reminder';

interface Routine {
  id: string;
  type: Kind;
  time: string;
  days: number[];
  date: string;
  text: string;
  enabled: boolean;
}

const KINDS: { id: Kind; label: string }[] = [
  { id: 'greeting', label: 'Greeting' },
  { id: 'study', label: 'Study' },
  { id: 'deadline', label: 'Deadline' },
  { id: 'reminder', label: 'Reminder' },
];
const DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const ALL_DAYS = [0, 1, 2, 3, 4, 5, 6];

const PRESETS: Omit<Routine, 'id'>[] = [
  { type: 'greeting', time: '08:00', days: ALL_DAYS, date: '', text: 'Good morning, Master! Ready for a great day?', enabled: true },
  { type: 'study', time: '18:00', days: [0, 1, 2, 3, 4], date: '', text: 'Study time! Open your notes and do one focused hour.', enabled: true },
];

let counter = 0;
const newId = () => `local-${Date.now()}-${counter++}`;

/** Settings > Memory: Aiko speaks up on a schedule (greeting, study, deadlines). */
export function RoutinesPanel() {
  const [items, setItems] = useState<Routine[]>([]);
  const [status, setStatus] = useState('');
  const [busy, setBusy] = useState(false);
  const [dirty, setDirty] = useState(false);

  const load = useCallback(async () => {
    setBusy(true);
    try {
      const headers = await getAuthHeaders();
      const res = await fetch(`${getHubUrl()}/api/routines`, { headers });
      if (!res.ok) throw new Error(res.status === 403 ? 'Administrator access required' : `HTTP ${res.status}`);
      const data = await res.json();
      setItems(data.routines || []);
      setDirty(false);
      setStatus('');
    } catch (e: any) {
      setStatus(`Could not load routines: ${e?.message || e}`);
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const update = (id: string, patch: Partial<Routine>) => {
    setItems((prev) => prev.map((r) => (r.id === id ? { ...r, ...patch } : r)));
    setDirty(true);
  };
  const remove = (id: string) => {
    setItems((prev) => prev.filter((r) => r.id !== id));
    setDirty(true);
  };
  const addBlank = () => {
    setItems((prev) => [
      ...prev,
      { id: newId(), type: 'reminder', time: '09:00', days: ALL_DAYS, date: '', text: '', enabled: true },
    ]);
    setDirty(true);
  };
  const addPreset = (p: Omit<Routine, 'id'>) => {
    setItems((prev) => [...prev, { ...p, id: newId() }]);
    setDirty(true);
  };
  const toggleDay = (r: Routine, day: number) => {
    const has = r.days.includes(day);
    const days = has ? r.days.filter((d) => d !== day) : [...r.days, day].sort();
    update(r.id, { days: days.length ? days : r.days });
  };

  const save = async () => {
    const empty = items.find((r) => !r.text.trim());
    if (empty) {
      setStatus('Every routine needs a message.');
      return;
    }
    setBusy(true);
    try {
      const headers = await getAuthHeaders({ 'Content-Type': 'application/json' });
      const res = await fetch(`${getHubUrl()}/api/routines`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ routines: items }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setItems(data.routines || []);
      setDirty(false);
      setStatus('Saved. Aiko will speak up at those times while she is running.');
    } catch (e: any) {
      setStatus(`Could not save: ${e?.message || e}`);
    } finally {
      setBusy(false);
    }
  };

  const field =
    'bg-[#181612] border border-white/[0.06] rounded-lg px-2 py-1.5 text-[12px] text-[#f0ebe3] focus:border-[var(--accent)]/50 focus:outline-none';

  return (
    <section className="p-4 rounded-xl bg-[var(--bg-base)] border border-white/[0.06]">
      <span className="block text-[13px] font-medium text-[#f0ebe3]">Daily routines</span>
      <p className="text-[12px] text-[#9a8f7e] mt-1 mb-3">
        Aiko messages you on a schedule: a morning greeting, study reminders, deadlines. Pick a date for a one-time
        deadline. She only speaks up while the app is running.
      </p>

      <div className="flex flex-col gap-3">
        {items.length === 0 && !busy && <p className="text-[12px] text-[#5a5248]">No routines yet. Add one below.</p>}
        {items.map((r) => (
          <div key={r.id} className="p-3 rounded-lg border border-white/[0.06] bg-[#14110e] flex flex-col gap-2">
            <div className="flex flex-wrap items-center gap-2">
              <input
                type="checkbox"
                checked={r.enabled}
                onChange={(e) => update(r.id, { enabled: e.target.checked })}
                className="w-4 h-4 accent-[var(--accent)]"
                aria-label="Enabled"
              />
              <select
                value={r.type}
                onChange={(e) => update(r.id, { type: e.target.value as Kind })}
                className={field}
                aria-label="Type"
              >
                {KINDS.map((k) => (
                  <option key={k.id} value={k.id}>
                    {k.label}
                  </option>
                ))}
              </select>
              <input
                type="time"
                value={r.time}
                onChange={(e) => update(r.id, { time: e.target.value })}
                className={field}
                aria-label="Time"
              />
              <input
                type="date"
                value={r.date}
                onChange={(e) => update(r.id, { date: e.target.value })}
                className={field}
                aria-label="Date (leave empty to repeat)"
                title="Leave empty to repeat on the chosen days"
              />
              <button
                type="button"
                onClick={() => remove(r.id)}
                className="ml-auto p-1.5 text-[#9a8f7e] hover:text-[#f87171]"
                aria-label="Delete routine"
              >
                <Trash2 size={14} />
              </button>
            </div>
            {!r.date && (
              <div className="flex flex-wrap gap-1.5">
                {DAY_LABELS.map((label, day) => (
                  <button
                    key={label}
                    type="button"
                    onClick={() => toggleDay(r, day)}
                    className={`px-2 py-0.5 rounded-md text-[11px] border ${
                      r.days.includes(day)
                        ? 'border-[var(--accent)]/60 text-[var(--accent)] bg-white/[0.05]'
                        : 'border-white/[0.08] text-[#5a5248]'
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            )}
            <textarea
              value={r.text}
              onChange={(e) => update(r.id, { text: e.target.value })}
              rows={2}
              maxLength={500}
              placeholder="What should Aiko say?"
              aria-label="Message"
              className={`${field} resize-y`}
            />
          </div>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-3 mt-4 pt-3 border-t border-white/[0.08]">
        <button type="button" onClick={addBlank} className="flex items-center gap-1.5 text-[12px] text-[var(--accent)] hover:opacity-80">
          <Plus size={14} /> Add routine
        </button>
        <button type="button" onClick={() => addPreset(PRESETS[0]!)} className="text-[12px] text-[#9a8f7e] hover:text-[var(--accent)]">
          + Morning greeting
        </button>
        <button type="button" onClick={() => addPreset(PRESETS[1]!)} className="text-[12px] text-[#9a8f7e] hover:text-[var(--accent)]">
          + Study reminder
        </button>
        <button
          type="button"
          onClick={save}
          disabled={busy || !dirty}
          className="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[var(--accent)]/15 border border-[var(--accent)]/40 text-[12px] text-[var(--accent)] disabled:opacity-40"
        >
          <Save size={13} /> Save routines
        </button>
      </div>
      {status && <p className="mt-2 text-[11px] text-[#f0c674]">{status}</p>}
    </section>
  );
}
