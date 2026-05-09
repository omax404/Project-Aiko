import { motion } from 'framer-motion';

export const NeuralPulse = () => (
  <div className="relative w-6 h-6 flex items-center justify-center">
    {[0, 1, 2].map((i) => (
      <motion.div
        key={i}
        initial={{ scale: 0.8, opacity: 0.5 }}
        animate={{ 
          scale: [0.8, 1.5, 0.8],
          opacity: [0.5, 0, 0.5]
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          delay: i * 0.6,
          ease: "easeInOut"
        }}
        className="absolute inset-0 rounded-full border border-pink-500/30"
      />
    ))}
    <div className="w-1.5 h-1.5 rounded-full bg-pink-500 shadow-[0_0_8px_#ec4899]" />
  </div>
);

export const DataStream = () => (
  <div className="flex gap-1 items-end h-4 px-2">
    {[0, 1, 2, 3].map((i) => (
      <motion.div
        key={i}
        animate={{ 
          height: ["20%", "100%", "20%"],
          opacity: [0.3, 1, 0.3]
        }}
        transition={{
          duration: 1.5,
          repeat: Infinity,
          delay: i * 0.2,
          ease: "linear"
        }}
        className="w-1 bg-pink-500/40 rounded-full"
      />
    ))}
  </div>
);

export const RotatingOrbital = () => (
  <div className="relative w-10 h-10 flex items-center justify-center">
    <motion.div
      animate={{ rotate: 360 }}
      transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
      className="absolute inset-0 border border-dashed border-pink-500/20 rounded-full"
    />
    <motion.div
      animate={{ rotate: -360 }}
      transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
      className="absolute inset-2 border border-dotted border-pink-500/10 rounded-full"
    />
    <div className="w-2 h-2 rounded-full bg-pink-500/20 blur-[2px]" />
  </div>
);

export const ThinkingDots = () => (
  <div className="flex gap-1.5 items-center px-1">
    {[0, 1, 2].map((i) => (
      <motion.div
        key={i}
        animate={{ 
          scale: [1, 1.3, 1],
          opacity: [0.3, 1, 0.3]
        }}
        transition={{
          duration: 1.2,
          repeat: Infinity,
          delay: i * 0.2,
          ease: "easeInOut"
        }}
        className="w-1.5 h-1.5 rounded-full bg-pink-500/60"
      />
    ))}
  </div>
);

export const NeuralNode = () => (
  <div className="relative w-8 h-8 flex items-center justify-center">
     <motion.div 
       animate={{ 
         scale: [1, 1.1, 1],
         opacity: [0.4, 0.8, 0.4],
         rotate: [0, 90, 0]
       }}
       transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
       className="absolute inset-0 border border-pink-500/20 rounded-lg rotate-45"
     />
     <div className="w-1.5 h-1.5 rounded-full bg-pink-500 shadow-[0_0_10px_#ec4899]" />
  </div>
);
