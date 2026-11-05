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
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: Math.min(0.4, (100 - dynamicsIntensity) / 300 + 0.16), ease: [0.16, 1, 0.3, 1] }}
      className="mx-auto flex min-h-full w-full max-w-[640px] flex-col justify-center px-6 py-14 sm:px-10"
    >
      {/* Mark — small, quiet, anchors the page */}
      <img
        src="/assets/illustrations/aiko-mark.svg"
        alt=""
        className="mb-9 h-10 w-10 opacity-70"
        width="40"
        height="40"
      />

      {/* Eyebrow — taste-skill: one accent touch, uppercase, tracked */}
      <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[var(--p-accent)] opacity-80">
        Your space with Aiko
      </p>

      {/* Headline — Major Third scale (~1.25), tight negative tracking */}
      <h1 className="mt-3 max-w-md text-[2rem] font-semibold leading-[1.18] tracking-[-0.038em] text-[var(--t1)] sm:text-[2.25rem]">
        What would you<br />like help with?
      </h1>

      <p className="mt-3.5 max-w-sm text-[13px] leading-[1.7] text-[var(--t3)]">
        Start with a question, share something you are working on, or bring in a file.
      </p>

      {/* Starter cards — taste-skill card system */}
      <div className="mt-9 grid gap-2 sm:grid-cols-3">
        {starters.map(({ label, artwork, prompt }) => (
          <button
            key={label}
            type="button"
            onClick={() => onStartPrompt(prompt)}
            className="group taste-card flex min-h-[88px] flex-col items-start justify-between p-4 text-left hover:-translate-y-[2px] hover:border-[var(--b2)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--p-accent)]/40 transition-all duration-150"
          >
            <span className="flex w-full items-start justify-between">
              <img src={artwork} alt="" className="h-10 w-auto object-contain object-left" width="66" height="40" />
              <ArrowUpRight
                size={13}
                strokeWidth={2}
                className="text-[var(--t4)] opacity-0 transition-all duration-150 group-hover:text-[var(--p-accent)] group-hover:opacity-100"
              />
            </span>
            <span className="mt-3.5 text-[12px] leading-[1.55] text-[var(--t2)] font-medium">{label}</span>
          </button>
        ))}
      </div>

      {/* Recall CTA — quiet, text-only */}
      <button
        type="button"
        onClick={onRecall}
        className="mt-8 inline-flex w-fit items-center gap-1.5 text-[12px] text-[var(--t4)] transition hover:text-[var(--t2)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--p-accent)]/40"
      >
        <Clock3 size={13} strokeWidth={1.8} />
        Pick up a recent conversation
      </button>
    </motion.div>
  );
}
