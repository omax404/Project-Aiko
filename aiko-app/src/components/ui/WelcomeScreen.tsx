import { motion } from 'framer-motion';
import { GothicButton } from '../GothicButton';
import { useNeuralStore } from '../../store/useNeuralStore';

interface WelcomeScreenProps {
  onRecall: () => void;
}

export function WelcomeScreen({ onRecall }: WelcomeScreenProps) {
  const dynamicsIntensity = useNeuralStore(state => state.dynamicsIntensity);
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: (100 - dynamicsIntensity) / 100 + 0.2 }}
      className="flex-1 flex flex-col items-center justify-center text-center p-12 gap-8"
    >
      <div className="max-w-md">
        <div className="w-full mb-6">
          <div className="flex items-center gap-3 w-full opacity-60 select-none pointer-events-none">
            <div className="flex-1 h-px bg-gradient-to-r from-transparent via-[var(--acc)]/30 to-transparent" />
            <div className="w-1.5 h-1.5 rotate-45 border border-[var(--acc)]/40" />
            <div className="w-1 h-1 rotate-45 bg-[var(--acc)]/20" />
            <div className="w-1.5 h-1.5 rotate-45 border border-[var(--acc)]/40" />
            <div className="flex-1 h-px bg-gradient-to-r from-transparent via-[var(--acc)]/30 to-transparent" />
          </div>
        </div>
        <GothicButton icon="rose" size="lg" active className="mx-auto mb-6 pointer-events-none shadow-purple-glow" />
        <h1 className="text-3xl font-bold text-white uppercase brand-text tracking-widest">Aiko</h1>
        <p className="text-[13px] text-slate-500 mt-3 leading-relaxed font-light px-4">
          Your neural companion is ready.
        </p>
      </div>
      <button onClick={onRecall}
        className="px-8 py-3 rounded-xl bg-white/[0.03] border border-white/10 text-[12px] font-bold text-slate-400 uppercase tracking-widest hover:bg-white/5 hover:text-white transition-all">
        View History
      </button>
    </motion.div>
  );
}
