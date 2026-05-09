import { motion } from 'framer-motion';

const AIKO_ASSETS = [
  { id: '1', url: 'https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJ6enh6eHh6eHh6eHh6eHh6eHh6eHh6eHh6eHh6eHh6JmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1n/3o7TKMGpxu5w1sZ1iU/giphy.gif', label: 'Neural Wave' },
  { id: '2', url: 'https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJ6enh6eHh6eHh6eHh6eHh6eHh6eHh6eHh6eHh6eHh6eHh6JmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1n/l41lTf0bB1h4b1Jzy/giphy.gif', label: 'Data Sync' },
  { id: '3', url: 'https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJ6enh6eHh6eHh6eHh6eHh6eHh6eHh6eHh6eHh6eHh6eHh6JmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1n/3o7TKVUn7iM8FMEU24/giphy.gif', label: 'System Boot' },
];

export function GifPicker({ onSelect, onClose }: { onSelect: (url: string) => void, onClose: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95, y: 10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95, y: 10 }}
      className="absolute bottom-full left-0 mb-4 w-72 h-80 glass-pane rounded-[24px] border border-white/10 shadow-2xl p-4 flex flex-col gap-3 z-50 overflow-hidden"
    >
      <div className="flex justify-between items-center px-1">
        <span className="text-[10px] uppercase tracking-widest font-bold text-pink-500">Animated Assets</span>
        <button onClick={onClose} className="text-[9px] text-slate-500 hover:text-white uppercase font-bold">Close</button>
      </div>
      
      <div className="flex-1 overflow-y-auto custom-scrollbar pr-1">
        <div className="grid grid-cols-2 gap-2">
          {AIKO_ASSETS.map((asset) => (
            <motion.button
              key={asset.id}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => onSelect(asset.url)}
              className="relative group rounded-xl overflow-hidden aspect-video border border-white/5 hover:border-pink-500/30 transition-all"
            >
              <img src={asset.url} alt={asset.label} className="w-full h-full object-cover opacity-60 group-hover:opacity-100 transition-opacity" />
              <div className="absolute inset-0 bg-black/60 flex items-end p-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <span className="text-[8px] font-bold text-white uppercase tracking-tighter">{asset.label}</span>
              </div>
            </motion.button>
          ))}
        </div>
      </div>
      
      <div className="text-[8px] text-slate-600 font-bold uppercase tracking-widest text-center py-1">
        Neural Hub Library v1.0
      </div>
    </motion.div>
  );
}
