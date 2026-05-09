import { motion, AnimatePresence } from 'framer-motion';
import { 
  Folder, File, Search, RefreshCw, X, Box, 
  Activity, Cpu, HardDrive, Brain, GitPullRequest, 
  GitCommit, AlertCircle, Clock, Zap, Network
} from 'lucide-react';
import { useNeuralStore } from '../store/useNeuralStore';
import { useEffect, useState } from 'react';

interface ProjectIntelligenceProps {
  isOpen: boolean;
  onClose: () => void;
}

type Tab = 'overview' | 'filesystem' | 'resources';

export function ProjectIntelligence({ isOpen, onClose }: ProjectIntelligenceProps) {
  const { projectStructure, fetchProjectStructure, systemStats, fetchSystemStats, chemicals } = useNeuralStore();
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    if (isOpen) {
      fetchProjectStructure?.();
      fetchSystemStats?.();
      const interval = setInterval(() => fetchSystemStats?.(), 5000);
      return () => clearInterval(interval);
    }
  }, [isOpen]);

  const structure = projectStructure || [];
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
          className="fixed inset-0 z-[100] flex items-center justify-center p-8 bg-black/85 backdrop-blur-xl"
        >
          <motion.div 
            initial={{ scale: 0.9, y: 40 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.9, y: 40 }}
            className="w-full max-w-6xl h-[85vh] bg-[#0c0c0c] border border-white/5 rounded-[48px] flex flex-col overflow-hidden shadow-[0_0_100px_rgba(0,0,0,0.8)] relative"
          >
            {/* Header Area */}
            <div className="h-32 px-12 border-b border-white/5 flex items-center justify-between bg-gradient-to-br from-pink-600/[0.03] to-transparent relative">
              <div className="flex flex-col gap-2">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-pink-500 animate-pulse shadow-[0_0_10px_rgba(236,72,153,0.8)]" />
                  <h2 className="text-[10px] font-black text-pink-500/50 uppercase tracking-[0.4em]">Neural Intelligence Nexus</h2>
                </div>
                <h1 className="text-3xl font-black text-white tracking-tighter uppercase italic leading-none">Aiko Intelligence Dashboard</h1>
              </div>

              {/* Tab Switcher */}
              <div className="flex bg-white/[0.02] border border-white/5 p-1.5 rounded-3xl backdrop-blur-md">
                {(['overview', 'filesystem', 'resources'] as Tab[]).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`px-8 py-3 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all ${
                      activeTab === tab 
                        ? 'bg-pink-600 text-white shadow-[0_0_20px_rgba(219,39,119,0.4)]' 
                        : 'text-white/30 hover:text-white/60'
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>

              <div className="flex items-center gap-4">
                <button 
                  onClick={onClose}
                  className="w-12 h-12 rounded-full bg-white/[0.02] border border-white/10 flex items-center justify-center hover:bg-white/10 transition-all group"
                >
                  <X size={20} className="text-white/40 group-hover:text-white transition-all" />
                </button>
              </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-hidden flex flex-col">
              <AnimatePresence mode="wait">
                {activeTab === 'overview' && (
                  <motion.div 
                    key="overview"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    className="flex-1 overflow-y-auto p-12 custom-scrollbar"
                  >
                    <div className="grid grid-cols-12 gap-8">
                      {/* Top Row: Repobeats Style Dashboard */}
                      <div className="col-span-8 bg-white/[0.02] border border-white/5 rounded-[40px] p-8 relative overflow-hidden group">
                        <div className="absolute top-0 right-0 w-64 h-64 bg-pink-600/5 blur-[100px] pointer-events-none" />
                        <div className="flex items-center justify-between mb-10">
                          <div className="flex items-center gap-4">
                            <div className="w-12 h-12 rounded-2xl bg-pink-600/10 border border-pink-500/20 flex items-center justify-center">
                              <GitCommit className="text-pink-500" />
                            </div>
                            <div>
                              <h3 className="text-white font-black uppercase tracking-widest text-sm">Neural Activity (30D)</h3>
                              <p className="text-white/40 text-[10px] uppercase font-bold tracking-tight">Syncing with omax404/Project-Aiko</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <span className="text-3xl font-black text-white italic tracking-tighter">{systemStats?.activity?.commits || 0}</span>
                            <p className="text-pink-500/60 text-[9px] font-black uppercase tracking-widest">Total Synapses</p>
                          </div>
                        </div>

                        {/* Activity Graph (SVG Mock) */}
                        <div className="h-48 w-full flex items-end gap-1.5 px-4 mb-4">
                          {Array.from({ length: 48 }).map((_, i) => {
                            const h = 20 + Math.random() * 80;
                            return (
                              <motion.div 
                                key={i}
                                initial={{ height: 0 }}
                                animate={{ height: `${h}%` }}
                                transition={{ delay: i * 0.01, duration: 1 }}
                                className="flex-1 bg-gradient-to-t from-pink-600/40 to-pink-500 rounded-full group-hover:from-pink-500 group-hover:to-white transition-all shadow-[0_0_15px_rgba(236,72,153,0.1)]"
                              />
                            );
                          })}
                        </div>
                        <div className="flex justify-between text-[8px] font-black text-white/20 uppercase tracking-[0.3em] px-4">
                          <span>April 01</span>
                          <span>May 09</span>
                        </div>
                      </div>

                      {/* Summary Stats */}
                      <div className="col-span-4 flex flex-col gap-6">
                        <StatCard icon={<GitPullRequest size={20}/>} label="Neural Merges" value={systemStats?.activity?.prs || 0} color="text-indigo-400" />
                        <StatCard icon={<AlertCircle size={20}/>} label="Critical Anomalies" value={systemStats?.activity?.issues || 0} color="text-amber-400" />
                        <StatCard icon={<Zap size={20}/>} label="Last Evolution" value={systemStats?.activity?.last_push || 'N/A'} color="text-green-400" />
                      </div>

                      {/* Biological Pulse */}
                      <div className="col-span-4 bg-white/[0.02] border border-white/5 rounded-[40px] p-8 flex flex-col gap-6">
                         <h3 className="text-[10px] font-black text-white/40 uppercase tracking-[0.4em] mb-2 flex items-center gap-2">
                           <Zap size={14} className="text-pink-500" /> Biological Pulse
                         </h3>
                         <ChemicalRow label="Dopamine" value={chemicals?.dopamine || 0.5} color="bg-pink-500" />
                         <ChemicalRow label="Serotonin" value={chemicals?.serotonin || 0.5} color="bg-blue-400" />
                         <ChemicalRow label="Adrenaline" value={chemicals?.adrenaline || 0.1} color="bg-orange-500" />
                         <ChemicalRow label="Cortisol" value={chemicals?.cortisol || 0.2} color="bg-purple-500" />
                      </div>

                      {/* Neural Uptime */}
                      <div className="col-span-8 bg-white/[0.02] border border-white/5 rounded-[40px] p-8 flex items-center justify-between relative overflow-hidden">
                        <div className="absolute inset-0 bg-gradient-to-r from-pink-600/[0.02] to-transparent pointer-events-none" />
                        <div className="flex gap-10 items-center">
                          <div className="w-20 h-20 rounded-full border-4 border-pink-500/20 flex items-center justify-center p-2 relative">
                            <div className="absolute inset-0 rounded-full border-4 border-pink-500 border-t-transparent animate-spin-slow" />
                            <Clock size={32} className="text-pink-500" />
                          </div>
                          <div>
                            <h3 className="text-2xl font-black text-white italic uppercase tracking-tighter leading-none mb-2">Neural Linkage Stable</h3>
                            <div className="flex gap-6">
                              <div className="flex flex-col">
                                <span className="text-xs font-bold text-white/40 uppercase tracking-widest">Uptime</span>
                                <span className="text-xl font-black text-pink-500 font-mono">
                                  {formatUptime(systemStats?.neural?.uptime || 0)}
                                </span>
                              </div>
                              <div className="flex flex-col">
                                <span className="text-xs font-bold text-white/40 uppercase tracking-widest">Synapses</span>
                                <span className="text-xl font-black text-pink-500 font-mono">
                                  {systemStats?.neural?.synapses || 0}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                        <div className="flex flex-col items-end">
                           <span className="text-[10px] font-black text-green-500 uppercase tracking-widest bg-green-500/10 px-3 py-1 rounded-full border border-green-500/20">System Online</span>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}

                {activeTab === 'filesystem' && (
                  <motion.div 
                    key="filesystem"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    className="flex-1 flex flex-col"
                  >
                    <div className="p-10 px-12 border-b border-white/5 bg-white/[0.01]">
                      <div className="relative group max-w-2xl">
                         <Search size={18} className="absolute left-6 top-1/2 -translate-y-1/2 text-white/20 group-focus-within:text-pink-500 transition-colors" />
                         <input 
                           type="text" 
                           placeholder="SCAN NEURAL NODES & FILES..."
                           value={searchQuery}
                           onChange={(e) => setSearchQuery(e.target.value)}
                           className="w-full h-16 bg-white/[0.02] border border-white/5 rounded-3xl pl-16 pr-8 text-sm font-bold text-white uppercase tracking-widest focus:outline-none focus:border-pink-500/30 transition-all placeholder:text-white/10"
                         />
                      </div>
                    </div>

                    <div className="flex-1 overflow-y-auto p-12 custom-scrollbar">
                      <div className="grid grid-cols-4 gap-8">
                        {filteredStructure.map((item, i) => (
                          <motion.div 
                            key={i}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.01 }}
                            className="group relative flex flex-col items-center justify-center p-8 rounded-[40px] bg-white/[0.02] border border-white/5 hover:bg-pink-600/[0.04] hover:border-pink-500/20 transition-all cursor-pointer overflow-hidden"
                          >
                             <div className="absolute top-0 right-0 w-24 h-24 bg-pink-600/[0.03] blur-3xl group-hover:bg-pink-600/[0.06]" />
                             
                             <div className="w-16 h-16 rounded-[24px] bg-black/40 flex items-center justify-center mb-6 border border-white/5 group-hover:scale-110 group-hover:border-pink-500/40 transition-all">
                               {item.type === 'folder' ? (
                                 <Folder size={28} className="text-pink-500" />
                               ) : (
                                 <File size={28} className="text-white/40 group-hover:text-white/80" />
                               )}
                             </div>
                             
                             <span className="text-[11px] font-black text-white/50 uppercase tracking-[0.2em] text-center truncate w-full group-hover:text-white">
                               {item.name}
                             </span>
                          </motion.div>
                        ))}
                      </div>
                    </div>
                  </motion.div>
                )}

                {activeTab === 'resources' && (
                  <motion.div 
                    key="resources"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    className="flex-1 p-12 overflow-y-auto custom-scrollbar"
                  >
                    <div className="grid grid-cols-3 gap-10">
                      <ResourceCard 
                        icon={<Cpu size={32} className="text-indigo-400" />}
                        label="Processing Core"
                        subLabel={`${systemStats?.hardware?.cpu?.cores || 0} THREADS`}
                        usage={systemStats?.hardware?.cpu?.usage || 0}
                        color="bg-indigo-500"
                        details={`${(systemStats?.hardware?.cpu?.usage || 0).toFixed(1)}% LOAD`}
                      />
                      <ResourceCard 
                        icon={<Network size={32} className="text-pink-400" />}
                        label="Neural Synapses"
                        subLabel={`${systemStats?.neural?.memories || 0} MEMORIES`}
                        usage={systemStats?.hardware?.ram?.percent || 0}
                        color="bg-pink-500"
                        details={`${((systemStats?.hardware?.ram?.used || 0) / 1024 / 1024 / 1024).toFixed(1)}GB / ${((systemStats?.hardware?.ram?.total || 0) / 1024 / 1024 / 1024).toFixed(1)}GB`}
                      />
                      <ResourceCard 
                        icon={<HardDrive size={32} className="text-amber-400" />}
                        label="Memory Matrix"
                        subLabel="SYSTEM VOLUME"
                        usage={systemStats?.hardware?.disk?.percent || 0}
                        color="bg-amber-500"
                        details={`${(systemStats?.hardware?.disk?.percent || 0).toFixed(1)}% CAPACITY`}
                      />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Footer */}
            <div className="h-20 px-12 bg-white/[0.01] border-t border-white/5 flex items-center justify-between">
               <div className="flex items-center gap-10">
                  <div className="flex items-center gap-3">
                     <div className="w-2 h-2 rounded-full bg-green-500" />
                     <span className="text-[10px] font-black text-white/30 uppercase tracking-[0.3em]">Neural Protocol: v3.1_PRO</span>
                  </div>
                  <div className="h-4 w-px bg-white/5" />
                  <span className="text-[10px] font-black text-white/20 uppercase tracking-[0.3em]">{structure.length} Active Nodes Monitored</span>
               </div>
               
               <div className="flex items-center gap-2">
                 <span className="text-[10px] font-black text-pink-500 uppercase tracking-widest">Aiko Neural Interface</span>
                 <Zap size={12} className="text-pink-500" />
               </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function StatCard({ icon, label, value, color }: { icon: any, label: string, value: any, color: string }) {
  return (
    <div className="bg-white/[0.02] border border-white/5 rounded-[32px] p-6 flex items-center gap-6 group hover:bg-white/[0.04] transition-all">
      <div className={`w-14 h-14 rounded-2xl bg-white/[0.03] border border-white/10 flex items-center justify-center ${color}`}>
        {icon}
      </div>
      <div>
        <h4 className="text-[10px] font-black text-white/30 uppercase tracking-[0.2em] mb-1">{label}</h4>
        <span className="text-2xl font-black text-white italic tracking-tighter">{value}</span>
      </div>
    </div>
  );
}

function ResourceCard({ icon, label, subLabel, usage, color, details }: { 
  icon: any, label: string, subLabel: string, usage: number, color: string, details: string 
}) {
  return (
    <div className="bg-white/[0.02] border border-white/5 rounded-[48px] p-10 flex flex-col gap-8 relative overflow-hidden group">
      <div className="absolute top-0 right-0 w-32 h-32 bg-white/[0.01] rounded-full -mr-16 -mt-16 group-hover:scale-150 transition-transform duration-1000" />
      <div className="flex items-start justify-between">
        <div className="w-16 h-16 rounded-[24px] bg-white/[0.03] border border-white/10 flex items-center justify-center">
          {icon}
        </div>
        <div className="text-right">
          <h4 className="text-[11px] font-black text-white/20 uppercase tracking-[0.4em] mb-1">{subLabel}</h4>
          <span className="text-xl font-black text-white uppercase italic tracking-widest">{label}</span>
        </div>
      </div>

      <div className="flex-1 flex flex-col justify-end gap-6">
        <div className="flex justify-between items-end">
           <span className="text-4xl font-black text-white tracking-tighter">{Math.round(usage)}%</span>
           <span className="text-[10px] font-black text-white/40 uppercase tracking-widest mb-2">{details}</span>
        </div>
        <div className="h-3 w-full bg-white/5 rounded-full overflow-hidden border border-white/5 p-0.5">
           <motion.div 
             initial={{ width: 0 }}
             animate={{ width: `${usage}%` }}
             className={`h-full rounded-full ${color} shadow-[0_0_15px_rgba(255,255,255,0.1)]`}
           />
        </div>
      </div>
    </div>
  );
}

function ChemicalRow({ label, value, color }: { label: string, value: number, color: string }) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex justify-between text-[9px] font-black uppercase tracking-[0.2em]">
        <span className="text-white/40">{label}</span>
        <span className="text-white">{Math.round(value * 100)}%</span>
      </div>
      <div className="h-1.5 w-full bg-white/[0.03] rounded-full overflow-hidden">
        <motion.div 
          animate={{ width: `${value * 100}%` }}
          className={`h-full ${color}`}
        />
      </div>
    </div>
  );
}

function formatUptime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}
