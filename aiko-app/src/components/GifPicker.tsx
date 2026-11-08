import { motion } from 'framer-motion';
import { Upload } from 'lucide-react';

const AIKO_ASSETS = [
  { id: '1', url: '/stickers/01_Happy_Cheer.png', label: 'Happy Cheer' },
  { id: '2', url: '/stickers/02_Blushing_Shy.png', label: 'Blushing Shy' },
  { id: '3', url: '/stickers/09_Heart_Eyes_Rose.png', label: 'Heart Eyes' },
  { id: '4', url: '/stickers/10_Annoyed_Pout.png', label: 'Annoyed Pout' },
  { id: '5', url: '/stickers/13_Excited_Jump.png', label: 'Excited Jump' },
  { id: '6', url: '/stickers/14_Winking_Peace.png', label: 'Winking Peace' },
];

export function GifPicker({
  onSelect,
  onClose,
  onUploadClick,
}: {
  onSelect: (url: string) => void;
  onClose: () => void;
  onUploadClick?: () => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95, y: 10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95, y: 10 }}
      className="absolute bottom-full left-0 mb-4 w-72 h-84 glass-pane rounded-[24px] border border-white/10 shadow-2xl p-4 flex flex-col gap-3 z-50 overflow-hidden bg-[#13111c]/95 backdrop-blur-xl"
    >
      <div className="flex justify-between items-center px-1">
        <span className="text-[12px] font-semibold text-[var(--accent)]">Images & Stickers</span>
        <button onClick={onClose} className="text-[11px] text-[#8a8298] hover:text-[#f0ebe3] font-medium">
          Close
        </button>
      </div>

      {onUploadClick && (
        <button
          onClick={onUploadClick}
          className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-xl bg-[var(--p-accent-soft)] border border-[var(--p-accent)]/40 text-[12px] font-medium text-[var(--p-accent)] hover:bg-[var(--p-accent)]/20 transition-all"
        >
          <Upload size={14} />
          Upload Image from PC
        </button>
      )}

      <div className="flex-1 overflow-y-auto custom-scrollbar pr-1">
        <div className="grid grid-cols-2 gap-2">
          {AIKO_ASSETS.map((asset) => (
            <motion.button
              key={asset.id}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => onSelect(asset.url)}
              className="relative group rounded-xl overflow-hidden aspect-square border border-white/5 hover:border-[var(--accent)]/30 bg-white/[0.02] p-2 transition-all"
            >
              <img
                src={asset.url}
                alt={asset.label}
                className="w-full h-full object-contain opacity-85 group-hover:opacity-100 transition-opacity"
              />
              <div className="absolute inset-x-0 bottom-0 bg-black/70 flex items-center justify-center py-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <span className="text-[10px] font-medium text-[#f0ebe3]">{asset.label}</span>
              </div>
            </motion.button>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
