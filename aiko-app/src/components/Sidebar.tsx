import { 
  Plus, 
  Settings, 
  Trash2,
  Search,
  MoreVertical,
  Pin,
  Edit2,
  BrainCircuit,
  Bot
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { clsx } from 'clsx';
import { useNeuralStore } from '../store/useNeuralStore';
import { motion, AnimatePresence } from 'framer-motion';
import { NeuralPulse } from './AnimatedIcons';

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
        "group relative px-4 py-3 rounded-xl transition-all duration-200 cursor-pointer border-l-2",
        active 
          ? "bg-[var(--bg-active)] border-amber-500/50" 
          : "hover:bg-[var(--bg-hover)] border-transparent"
      )}
    >
      <div className="flex flex-col gap-0.5 pr-6">
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
              className="flex-1 bg-transparent border-b border-amber-500/50 text-[12px] text-[var(--t1)] outline-none mr-2"
            />
          ) : (
            <h3 className={clsx(
              "text-[12px] font-medium truncate",
              active ? "text-[var(--t1)]" : "text-[var(--t2)] group-hover:text-[var(--t1)]"
            )}>
              {title}
            </h3>
          )}
          <span className="text-[9px] text-[var(--t3)] font-mono shrink-0 ml-2">{timestamp}</span>
        </div>
        <p className="text-[10px] text-[var(--t3)] truncate leading-relaxed">{preview}</p>
      </div>

      <div className="absolute top-3 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
        <button 
          onClick={(e) => { e.stopPropagation(); setShowMenu(!showMenu); }}
          className="p-1 hover:text-white text-[var(--t3)]"
          title="Session Actions"
        >
          <MoreVertical size={12} />
        </button>
      </div>

      <AnimatePresence>
        {showMenu && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setShowMenu(false)} />
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: -10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -10 }}
              className="absolute right-2 top-8 z-50 w-32 bg-[var(--bg-card)] border border-[var(--b2)] rounded-lg shadow-xl py-1 overflow-hidden"
            >
              <button 
                onClick={(e) => { e.stopPropagation(); onPin(id); setShowMenu(false); }}
                className="w-full flex items-center gap-2 px-3 py-1.5 text-[10px] text-[var(--t2)] hover:bg-[var(--bg-hover)] hover:text-white"
              >
                <Pin size={10} className={pinned ? "fill-amber-500 text-amber-500" : ""} />
                {pinned ? "Unpin" : "Pin"}
              </button>
              <button 
                onClick={(e) => { e.stopPropagation(); setIsRenaming(true); setShowMenu(false); }}
                className="w-full flex items-center gap-2 px-3 py-1.5 text-[10px] text-[var(--t2)] hover:bg-[var(--bg-hover)] hover:text-white"
              >
                <Edit2 size={10} />
                Rename
              </button>
              <div className="h-px bg-[var(--b1)] my-1" />
              <button 
                onClick={(e) => { e.stopPropagation(); onDelete(id); setShowMenu(false); }}
                className="w-full flex items-center gap-2 px-3 py-1.5 text-[10px] text-red-400 hover:bg-red-500/10"
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

export function Sidebar({ onOpenSettings, onOpenProject }: { onOpenSettings: () => void, onOpenProject: () => void }) {
  const { 
    sessions, 
    activeSessionId,
    loadSessions,
    switchSession,
    createNewSession,
    deleteSession,
    pinSession,
    renameSession,
    relationship,
    fetchRelationship,
    setEmotion: _setEmotion,
    showAnimatedAssets
  } = useNeuralStore();
  const [search, setSearch] = useState("");

  const filteredSessions = sessions.filter(s => s.title.toLowerCase().includes(search.toLowerCase()) || (s.preview || "").toLowerCase().includes(search.toLowerCase()));
  const pinnedSessions = filteredSessions.filter(s => s.pinned);
  const unpinnedSessions = filteredSessions.filter(s => !s.pinned);

  useEffect(() => {
    fetchRelationship();
    loadSessions();
  }, []);

  return (
    <div className="w-[var(--sidebar-w)] h-full flex flex-col bg-[var(--bg-sidebar)] border-r border-[var(--b1)] p-4 gap-4">
      
      {/* Profile & Affection */}
      <div className="flex flex-col gap-4 px-1 py-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-600/10 border border-amber-500/20 flex items-center justify-center shadow-lg shadow-amber-900/10 overflow-hidden">
             {/* Small Live2D avatar would go here or a placeholder */}
             <Bot size={22} className="text-amber-500" />
          </div>
          <div className="flex flex-col">
            <h1 className="text-sm font-bold text-[var(--t1)] brand-text uppercase tracking-wider">Aiko Core</h1>
            <div className="flex items-center gap-1.5">
              {showAnimatedAssets ? <NeuralPulse /> : <div className="w-1.5 h-1.5 rounded-full bg-amber-500/50" />}
              <p className="text-[9px] text-amber-500/80 font-mono font-bold">Synchronized</p>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-1.5">
          <div className="flex justify-between items-center px-0.5">
             <span className="text-[9px] font-bold text-[var(--t3)] uppercase tracking-wider">Affection Level</span>
             <span className="text-[9px] font-mono font-bold text-amber-500">{relationship.affection}%</span>
          </div>
          <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
            <motion.div 
              initial={{ width: 0 }}
              animate={{ width: `${relationship.affection}%` }}
              className="h-full bg-amber-500" 
            />
          </div>
        </div>
      </div>

      <button 
        onClick={createNewSession}
        className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-amber-600/10 border border-amber-500/20 text-[11px] font-bold text-amber-500 uppercase tracking-widest hover:bg-amber-600/20 transition-all"
      >
        <Plus size={14} />
        New Neural Link
      </button>

      {/* Search */}
      <div className="relative group">
        <Search size={12} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--t3)] group-focus-within:text-amber-500 transition-colors" />
        <input 
          type="text" 
          placeholder="Search sessions..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-[var(--bg-input)] border border-[var(--b1)] rounded-xl py-2 pl-9 pr-4 text-[11px] text-[var(--t1)] placeholder-[var(--t3)] focus:outline-none focus:border-amber-500/30 transition-all"
        />
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto custom-scrollbar pr-1 flex flex-col gap-6">
        
        {pinnedSessions.length > 0 && (
          <div className="flex flex-col gap-2">
            <span className="text-[9px] font-bold text-[var(--t4)] uppercase tracking-[0.2em] px-3">Pinned Linkage</span>
            <div className="flex flex-col gap-1">
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

        <div className="flex flex-col gap-2">
          <span className="text-[9px] font-bold text-[var(--t4)] uppercase tracking-[0.2em] px-3">Recent Memory Nodes</span>
          <div className="flex flex-col gap-1">
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
      <div className="flex flex-col gap-1 pt-4 border-t border-[var(--b1)]">
        <button 
          onClick={onOpenSettings}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-[var(--t2)] hover:text-white hover:bg-[var(--bg-hover)] transition-all"
        >
          <Settings size={14} />
          <span className="text-[11px] font-medium">Neural Config</span>
        </button>
        <button 
          onClick={onOpenProject}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-[var(--t2)] hover:text-white hover:bg-[var(--bg-hover)] transition-all"
        >
          <BrainCircuit size={14} />
          <span className="text-[11px] font-medium">Core Intelligence</span>
        </button>
      </div>
    </div>
  );
}
