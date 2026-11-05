import { 
  Plus, 
  Trash2,
  Search,
  MoreVertical,
  Pin,
  Edit2,
  Settings,
  MessageCircle
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { clsx } from 'clsx';
import { useNeuralStore } from '../store/useNeuralStore';
import { useShallow } from 'zustand/react/shallow';
import { motion, AnimatePresence, useMotionValue, useSpring, useTransform } from 'framer-motion';


interface SidebarItemProps {
  id: string;
  title: string;
  preview: string;
  timestamp: string;
  active?: boolean;
  pinned?: boolean;
  onSelect: (id: string) => void;
  onRename: (id: string, name: string) => void;
  onDelete: (id: string) => void;
  onPin: (id: string) => void;
}

const SessionItem = ({ id, title, preview, timestamp, active, pinned, onSelect, onRename, onDelete, onPin }: SidebarItemProps) => {
  const [showMenu, setShowMenu] = useState(false);
  const [isRenaming, setIsRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState(title);

  const handleRenameSubmit = () => {
    if (renameValue.trim() && renameValue !== title) {
      onRename(id, renameValue.trim());
    }
    setIsRenaming(false);
  };

  return (
    <div
      onClick={() => !isRenaming && onSelect(id)}
      className={clsx(
        "group relative px-3 py-2.5 rounded-[var(--p-radius-sm)] transition-all duration-150 cursor-pointer border-l-[1.5px]",
        active
          ? "bg-[var(--bg-active)] border-[var(--p-accent)]"
          : "hover:bg-[var(--bg-hover)] border-transparent hover:border-[var(--b2)]"
      )}
    >
      <div className="flex flex-col gap-0.5 pr-5">
        <div className="flex items-center justify-between">
          {isRenaming ? (
            <input
              autoFocus
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              onBlur={handleRenameSubmit}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleRenameSubmit();
                if (e.key === 'Escape') { setRenameValue(title); setIsRenaming(false); }
                e.stopPropagation();
              }}
              onClick={(e) => e.stopPropagation()}
              className="flex-1 bg-transparent border-b border-[var(--b3)] text-[12px] text-[var(--t1)] outline-none mr-2"
            />
          ) : (
            <h3 className={clsx(
              "text-[12px] font-medium truncate",
              active ? "text-[var(--t1)]" : "text-[var(--t2)] group-hover:text-[var(--t1)]"
            )}>
              {title}
            </h3>
          )}
          <span className="text-[10px] text-[var(--t4)] font-mono shrink-0 ml-2 tabular-nums">{timestamp}</span>
        </div>
        <p className="text-[11px] text-[var(--t4)] truncate leading-relaxed">{preview}</p>
      </div>

      <div className="absolute top-2.5 right-1.5 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-0.5">
        <button
          onClick={(e) => { e.stopPropagation(); setShowMenu(!showMenu); }}
          className="p-1 rounded-md hover:text-[var(--t1)] hover:bg-[var(--bg-hover)] text-[var(--t3)] transition-all"
          title="Session Actions"
        >
          <MoreVertical size={11} />
        </button>
      </div>

      <AnimatePresence>
        {showMenu && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setShowMenu(false)} />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: -6 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -6 }}
              transition={{ duration: 0.1 }}
              className="absolute right-2 top-8 z-50 w-32 bg-[var(--p-card)] border border-[var(--b1)] rounded-[var(--p-radius-sm)] shadow-[0_8px_24px_-6px_rgba(0,0,0,0.6),inset_0_1px_0_var(--p-inset-hi)] py-1 overflow-hidden"
            >
              <button
                onClick={(e) => { e.stopPropagation(); onPin(id); setShowMenu(false); }}
                className="w-full flex items-center gap-2 px-3 py-1.5 text-[11px] text-[var(--t2)] hover:bg-[var(--bg-hover)] hover:text-[var(--t1)] transition-colors"
              >
                <Pin size={10} className={pinned ? "fill-[var(--p-accent)] text-[var(--p-accent)]" : ""} />
                {pinned ? "Unpin" : "Pin"}
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); setIsRenaming(true); setShowMenu(false); }}
                className="w-full flex items-center gap-2 px-3 py-1.5 text-[11px] text-[var(--t2)] hover:bg-[var(--bg-hover)] hover:text-[var(--t1)] transition-colors"
              >
                <Edit2 size={10} />
                Rename
              </button>
              <div className="h-px bg-[var(--b1)] my-1" />
              <button
                onClick={(e) => { e.stopPropagation(); onDelete(id); setShowMenu(false); }}
                className="w-full flex items-center gap-2 px-3 py-1.5 text-[11px] text-[var(--red)] hover:bg-[var(--red)]/10 transition-colors"
              >
                <Trash2 size={10} />
                Delete
              </button>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};

export function Sidebar({ onOpenSettings }: { onOpenSettings: () => void }) {
  const { 
    sessions, 
    activeSessionId,
    loadSessions,
    switchSession,
    createNewSession,
    deleteSession,
    pinSession,
    renameSession
  } = useNeuralStore(useShallow((state) => ({
    sessions: state.sessions,
    activeSessionId: state.activeSessionId,
    loadSessions: state.loadSessions,
    switchSession: state.switchSession,
    createNewSession: state.createNewSession,
    deleteSession: state.deleteSession,
    pinSession: state.pinSession,
    renameSession: state.renameSession
  })));
  const [search, setSearch] = useState("");

  const filteredSessions = sessions.filter(s => s.title.toLowerCase().includes(search.toLowerCase()) || (s.preview || "").toLowerCase().includes(search.toLowerCase()));
  const pinnedSessions = filteredSessions.filter(s => s.pinned);
  const unpinnedSessions = filteredSessions.filter(s => !s.pinned);

  useEffect(() => {
    loadSessions();
  }, []);

  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  const springConfig = { stiffness: 120, damping: 20 };
  const glowX = useSpring(mouseX, springConfig);
  const glowY = useSpring(mouseY, springConfig);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    mouseX.set(e.clientX - rect.left);
    mouseY.set(e.clientY - rect.top);
  };

  return (
    <nav
      onMouseMove={handleMouseMove}
      aria-label="Conversations"
      className="w-[var(--sidebar-w)] h-full flex flex-col bg-[var(--bg-sidebar)] border-r border-[var(--b1)] p-3 gap-3 relative overflow-hidden group/sidebar"
    >
      {/* Subtle mouse-follow bloom */}
      <motion.div
        className="absolute pointer-events-none rounded-full w-36 h-36 bg-[var(--p-accent)] blur-3xl opacity-0 group-hover/sidebar:opacity-[0.04] transition-opacity"
        style={{
          x: useTransform(glowX, (v: number) => v - 72),
          y: useTransform(glowY, (v: number) => v - 72),
        }}
      />

      {/* Identity header */}
      <div className="flex items-center gap-2.5 px-1 py-3">
        <img src="/assets/illustrations/aiko-mark.svg" alt="" width="32" height="32" className="h-8 w-8 shrink-0 opacity-80" />
        <div className="flex flex-col min-w-0">
          <h1 className="text-[13px] font-semibold text-[var(--t1)] tracking-tight leading-none">Aiko</h1>
          <div className="flex items-center gap-1 mt-0.5">
            <div className="h-1.5 w-1.5 rounded-full bg-[var(--p-accent)] opacity-70" />
            <p className="text-[10px] text-[var(--t4)]">Your companion</p>
          </div>
        </div>
      </div>

      {/* Divider */}
      <div className="h-px bg-[var(--b1)] mx-1" />

      {/* New chat — taste-skill: filled button, single accent touch */}
      <button
        onClick={createNewSession}
        className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-[var(--p-radius-sm)] bg-[var(--p-accent-soft)] border border-[var(--b1)] text-[11px] font-semibold text-[var(--p-accent)] tracking-wide hover:bg-[var(--bg-active)] hover:border-[var(--b2)] transition-all duration-150 shadow-[inset_0_1px_0_var(--p-inset-hi)]"
      >
        <Plus size={13} strokeWidth={2} />
        New chat
      </button>

      {/* Search */}
      <div className="relative group">
        <Search size={11} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--t4)] group-focus-within:text-[var(--p-accent)] transition-colors" />
        <input
          type="text"
          placeholder="Search conversations…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-[var(--bg-elevated)] border border-[var(--b1)] rounded-[var(--p-radius-sm)] py-1.5 pl-7 pr-3 text-[11px] text-[var(--t1)] placeholder-[var(--t4)] focus:outline-none focus:border-[var(--b2)] transition-all shadow-[inset_0_1px_0_var(--p-inset-hi)]"
        />
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto custom-scrollbar -mx-1 px-1 flex flex-col gap-5">

        {pinnedSessions.length > 0 && (
          <div className="flex flex-col gap-1">
            <span className="text-[9px] font-semibold text-[var(--t4)] px-2 uppercase tracking-[0.12em]">Pinned</span>
            <div className="flex flex-col gap-0.5">
              {pinnedSessions.map(session => (
                <SessionItem
                  key={session.id}
                  {...session}
                  active={activeSessionId === session.id}
                  onSelect={switchSession}
                  onRename={renameSession}
                  onDelete={deleteSession}
                  onPin={pinSession}
                />
              ))}
            </div>
          </div>
        )}

        <div className="flex flex-col gap-1">
          <span className="text-[9px] font-semibold text-[var(--t4)] px-2 uppercase tracking-[0.12em]">Recent</span>
          <div className="flex flex-col gap-0.5">
            {unpinnedSessions.map(session => (
              <SessionItem
                key={session.id}
                {...session}
                active={activeSessionId === session.id}
                onSelect={switchSession}
                onRename={renameSession}
                onDelete={deleteSession}
                onPin={pinSession}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Actions */}
      <div className="flex flex-col gap-0.5 pt-3 border-t border-[var(--b1)]">
        <button
          onClick={onOpenSettings}
          className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-[var(--p-radius-sm)] text-[var(--t2)] hover:text-[var(--t1)] hover:bg-[var(--bg-hover)] transition-all duration-150 group cursor-pointer"
        >
          <div className="w-7 h-7 rounded-[var(--p-radius-sm)] border border-[var(--b1)] bg-[var(--bg-elevated)] flex items-center justify-center text-[var(--t3)] group-hover:border-[var(--b2)] group-hover:text-[var(--t1)] transition-all shrink-0 shadow-[inset_0_1px_0_var(--p-inset-hi)]">
            <Settings size={13} strokeWidth={1.8} />
          </div>
          <span className="text-[11px] font-medium">Settings</span>
        </button>

        <button
          onClick={() => window.open('https://discord.com', '_blank')}
          className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-[var(--p-radius-sm)] text-[var(--t2)] hover:text-[var(--t1)] hover:bg-[var(--bg-hover)] transition-all duration-150 group cursor-pointer"
        >
          <div className="w-7 h-7 rounded-[var(--p-radius-sm)] border border-[var(--b1)] bg-[var(--bg-elevated)] flex items-center justify-center text-[var(--t3)] group-hover:border-[var(--b2)] group-hover:text-[var(--t1)] transition-all shrink-0 shadow-[inset_0_1px_0_var(--p-inset-hi)]">
            <MessageCircle size={13} strokeWidth={1.8} />
          </div>
          <span className="text-[11px] font-medium">Discord Community</span>
        </button>
      </div>
    </nav>
  );
}
