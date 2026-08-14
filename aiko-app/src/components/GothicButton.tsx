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
      whileHover={disabled ? {} : { scale: 1.08 }}
      whileTap={disabled ? {} : { scale: 0.95 }}
      onClick={onClick}
      title={title}
      disabled={disabled}
      className={clsx(
        'relative rounded-full border cursor-pointer flex items-center justify-center transition-all duration-200 shrink-0 select-none shadow-md',
        sizeConfig.btn,
        active
          ? 'bg-[#B8A1D9] border-[#B8A1D9] text-[#1A0F24] font-semibold shadow-[0_0_18px_rgba(184,161,217,0.45)]'
          : 'bg-[#3B2249]/60 border-[#B8A1D9]/30 text-[#F3EAF9] hover:bg-[#B8A1D9]/20 hover:border-[#B8A1D9]/50 hover:shadow-[0_0_15px_rgba(184,161,217,0.3)]',
        disabled && 'opacity-30 cursor-not-allowed',
        className
      )}
    >
      <Icon size={sizeConfig.icon} strokeWidth={1.8} />
    </motion.button>
  );
};
