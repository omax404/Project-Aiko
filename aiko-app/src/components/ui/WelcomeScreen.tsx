import { motion } from 'framer-motion';
import { ArrowUpRight, Clock3 } from 'lucide-react';
import { useNeuralStore } from '../../store/useNeuralStore';

interface WelcomeScreenProps {
  onRecall: () => void;
  onStartPrompt: (prompt: string) => void;
}

const starters = [
  { label: 'Help me think something through', artwork: '/assets/illustrations/think.svg', prompt: 'Help me think something through.' },
  { label: 'Make a plan for today', artwork: '/assets/illustrations/plan.svg', prompt: 'Help me make a realistic plan for today.' },
  { label: 'Understand a file or image', artwork: '/assets/illustrations/file.svg', prompt: 'I have a file or image I would like help understanding.' },
];

export function WelcomeScreen({ onRecall, onStartPrompt }: WelcomeScreenProps) {
  const dynamicsIntensity = useNeuralStore(state => state.dynamicsIntensity);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: Math.min(0.45, (100 - dynamicsIntensity) / 300 + 0.18) }}
      className="mx-auto flex min-h-full w-full max-w-2xl flex-col justify-center px-5 py-12 sm:px-10"
    >
      <img src="/assets/illustrations/aiko-mark.svg" alt="" className="mb-8 h-12 w-12" width="48" height="48" />
      <p className="text-xs font-medium uppercase tracking-[0.16em] text-[var(--accent)]/75">Your space with Aiko</p>
      <h1 className="mt-3 max-w-xl text-3xl font-semibold leading-tight tracking-[-0.04em] text-white sm:text-4xl">
        What would you like help with?
      </h1>
      <p className="mt-3 max-w-lg text-sm leading-6 text-white/50">
        Start with a question, share something you are working on, or bring in a file. Aiko will meet you there.
      </p>

      <div className="mt-8 grid gap-2 sm:grid-cols-3">
        {starters.map(({ label, artwork, prompt }) => (
          <button
            key={label}
            type="button"
            onClick={() => onStartPrompt(prompt)}
            className="group flex min-h-[92px] flex-col items-start justify-between rounded-2xl border border-white/[0.07] bg-white/[0.025] p-4 text-left transition hover:-translate-y-0.5 hover:border-[var(--accent)]/30 hover:bg-white/[0.045] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)]/45"
          >
            <span className="flex w-full items-center justify-between">
              <img src={artwork} alt="" className="h-12 w-[66px] object-contain object-left" width="88" height="64" />
              <ArrowUpRight size={14} className="text-white/30 opacity-0 transition group-hover:text-[var(--accent)] group-hover:opacity-100" />
            </span>
            <span className="mt-4 text-xs leading-5 text-white/70">{label}</span>
          </button>
        ))}
      </div>

      <button
        type="button"
        onClick={onRecall}
        className="mt-7 inline-flex w-fit items-center gap-2 text-xs text-white/40 transition hover:text-white/75 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)]/45"
      >
        <Clock3 size={14} /> Pick up a recent conversation
      </button>
    </motion.div>
  );
}
