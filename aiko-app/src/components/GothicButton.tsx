import React from 'react';
import { motion } from 'framer-motion';
import { clsx } from 'clsx';
import { Heart, Settings, Mic, ArrowUp, X, MessageCircle, Volume2 } from 'lucide-react';

export type GothicIconType = 'rose' | 'settings' | 'mic' | 'send' | 'close' | 'discord' | 'volume';

interface GothicButtonProps {
  icon: GothicIconType;
  onClick?: () => void;
  title?: string;
  active?: boolean;
  disabled?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const iconMap = {
  rose: Heart,
  settings: Settings,
  mic: Mic,
  send: ArrowUp,
  close: X,
  discord: MessageCircle,
  volume: Volume2,
};

export const GothicButton: React.FC<GothicButtonProps> = ({
  icon,
  onClick,
  title,
  active,
  disabled,
  size = 'md',
  className
}) => {
  const Icon = iconMap[icon];
  const sizeConfig = {
    sm: { btn: 'w-8 h-8', icon: 14 },
    md: { btn: 'w-10 h-10', icon: 18 },
    lg: { btn: 'w-14 h-14', icon: 24 },
  }[size];

  return (
    <motion.button
      whileHover={disabled ? {} : { scale: 1.05 }}
      whileTap={disabled ? {} : { scale: 0.95 }}
      onClick={onClick}
      title={title}
      disabled={disabled}
      className={clsx(
        'relative rounded-full border cursor-pointer flex items-center justify-center transition-all duration-150 shrink-0 select-none',
        sizeConfig.btn,
        active
          ? 'bg-[var(--p-accent)] border-[var(--p-accent)] text-[var(--p-accent-ink)] font-medium shadow-[0_2px_12px_rgba(180,155,240,0.25)]'
          : 'bg-[var(--p-surface)] border-[var(--b1)] text-[var(--t2)] hover:text-[var(--t1)] hover:bg-[var(--bg-hover)] hover:border-[var(--b2)] shadow-[inset_0_1px_0_var(--p-inset-hi)]',
        disabled && 'opacity-30 cursor-not-allowed pointer-events-none',
        className
      )}
    >
      <Icon size={sizeConfig.icon} strokeWidth={1.8} />
    </motion.button>
  );
};
