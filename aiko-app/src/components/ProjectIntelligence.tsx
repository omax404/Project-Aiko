import { motion, AnimatePresence } from 'framer-motion';
import { Folder, File, Search, RefreshCw, X, Box } from 'lucide-react';
import { useNeuralStore } from '../store/useNeuralStore';
import { useEffect, useState } from 'react';

interface ProjectIntelligenceProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ProjectIntelligence({ isOpen, onClose }: ProjectIntelligenceProps) {
  const { projectStructure, fetchProjectStructure } = useNeuralStore();
  const [searchQuery, setSearchQuery] = useState('');

  // Fallback if prop not present in store
  const structure = projectStructure || [];

  useEffect(() => {
    if (isOpen && typeof fetchProjectStructure === 'function') {
      fetchProjectStructure();
    }
  }, [isOpen]);

  const filteredStructure = structure.filter(item => 
    item.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] flex items-center justify-center p-8 bg-black/80 backdrop-blur-md"
        >
          <motion.div 
            initial={{ scale: 0.95, y: 30 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.95, y: 30 }}
            className="w-full max-w-4xl h-[75vh] bg-[var(--bg-elevated)] border border-[var(--b2)] rounded-[40px] flex flex-col overflow-hidden shadow-[0_0_50px_rgba(0,0,0,0.5)] relative"
          >
            {/* Header */}
            <div className="h-28 px-10 border-b border-[var(--b1)] flex items-center justify-between bg-gradient-to-br from-amber-600/5 to-transparent">
              <div className="flex flex-col gap-1.5">
                <h2 className="text-[10px] font-bold text-[var(--t3)] uppercase tracking-[0.25em]">Neural Module Workspace</h2>
                <div className="flex items-center gap-4">
                   <h1 className="text-2xl font-bold text-[var(--t1)] tracking-widest uppercase brand-text">Workspace Intelligence</h1>
                   <div className="px-2.5 py-1 rounded-full bg-amber-600/10 border border-amber-500/20 text-[9px] font-bold text-amber-500 uppercase tracking-tight">Active_Indexing</div>
                </div>
              </div>
              
              <div className="flex items-center gap-4">
                <button 
                  title="Refresh Workspace"
                  onClick={() => fetchProjectStructure?.()}
                  className="w-11 h-11 rounded-2xl bg-white/[0.02] border border-white/10 flex items-center justify-center hover:bg-white/5 transition-all group shadow-inner"
                >
                  <RefreshCw size={18} className="text-[var(--t3)] group-hover:text-amber-500 transition-all" />
                </button>
                <button 
                  title="Close Workspace"
                  onClick={onClose}
                  className="w-11 h-11 rounded-2xl bg-white/[0.02] border border-white/10 flex items-center justify-center hover:bg-white/5 transition-all group shadow-inner"
                >
                  <X size={18} className="text-[var(--t3)] group-hover:text-red-400 transition-all" />
                </button>
              </div>
            </div>

            {/* Search Bar */}
            <div className="p-6 px-10 border-b border-[var(--b1)] bg-black/10">
              <div className="relative group">
                 <Search size={14} className="absolute left-6 top-1/2 -translate-y-1/2 text-[var(--t4)] group-focus-within:text-amber-500 transition-colors" />
                 <input 
                   type="text" 
                   placeholder="SCAN NEURAL NODES & FILES..."
                   value={searchQuery}
                   onChange={(e) => setSearchQuery(e.target.value)}
                   className="w-full h-14 bg-[var(--bg-input)] border border-[var(--b1)] rounded-2xl pl-14 pr-6 text-[12px] font-bold text-[var(--t1)] uppercase tracking-wider focus:outline-none focus:border-amber-500/30 transition-all placeholder:text-[var(--t4)]"
                 />
              </div>
            </div>

            {/* File explorer */}
            <div className="flex-1 overflow-y-auto p-10 custom-scrollbar bg-black/5">
              <div className="grid grid-cols-4 gap-6">
                {filteredStructure.map((item, i) => (
                  <motion.div 
                    key={i}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.02 }}
                    className="group relative flex flex-col items-center justify-center p-6 rounded-[32px] bg-[var(--bg-input)] border border-[var(--b1)] hover:bg-amber-600/5 hover:border-amber-500/20 transition-all cursor-pointer overflow-hidden shadow-lg hover:shadow-amber-900/10"
                  >
                     <div className="absolute top-0 right-0 w-16 h-16 bg-amber-600/5 blur-2xl group-hover:bg-amber-600/10 transition-colors" />
                     
                     <div className="w-14 h-14 rounded-2xl bg-black/40 flex items-center justify-center mb-4 border border-white/5 group-hover:scale-105 group-hover:border-amber-500/30 transition-all shadow-inner">
                       {item.type === 'folder' ? (
                         <Folder size={22} className="text-amber-500/80 group-hover:text-amber-400" />
                       ) : (
                         <File size={22} className="text-amber-400/60 group-hover:text-amber-300" />
                       )}
                     </div>
                     
                     <span className="text-[10px] font-bold text-[var(--t2)] uppercase tracking-widest text-center truncate w-full group-hover:text-white transition-colors">
                       {item.name}
                     </span>
                     
                     <div className="mt-2 flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <span className="text-[8px] text-amber-500 font-bold uppercase tracking-widest">Linked_Entity</span>
                     </div>
                  </motion.div>
                ))}
              </div>
              
              {filteredStructure.length === 0 && (
                <div className="h-full flex flex-col items-center justify-center gap-4 text-[var(--t4)]">
                   <div className="w-20 h-20 rounded-full border-2 border-dashed border-[var(--b1)] flex items-center justify-center opacity-50">
                      <Box size={32} />
                   </div>
                   <span className="text-[11px] font-bold uppercase tracking-[0.2em] px-4 text-center">No neural clusters mapped to workspace criteria</span>
                </div>
              )}
            </div>

            {/* Footer Workspace Info */}
            <div className="h-16 px-10 bg-[var(--bg-sidebar)] border-t border-[var(--b1)] flex items-center justify-between">
               <div className="flex items-center gap-6">
                  <div className="flex items-center gap-2">
                     <div className="w-1.5 h-1.5 rounded-full bg-green-500 shadow-[0_0_8px_#22c55e]" />
                     <span className="text-[9px] font-bold text-[var(--t3)] uppercase tracking-widest">Core_Locked</span>
                  </div>
                  <div className="w-px h-3 bg-white/10" />
                  <span className="text-[9px] font-bold text-[var(--t4)] uppercase tracking-widest">{structure.length} Entities Subscribed</span>
               </div>
               
               <span className="text-[9px] font-bold text-amber-500/60 uppercase tracking-widest italic brand-text">Aiko Neural Link // v3.0 stable</span>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
