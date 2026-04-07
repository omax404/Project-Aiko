import { motion } from 'framer-motion';

export function SkeletonLoader() {
  const bars = [
    { width: '85%', delay: 0 },
    { width: '45%', delay: 0.15 },
    { width: '95%', delay: 0.3 },
    { width: '65%', delay: 0.45 },
  ];

  return (
    <div className="flex flex-col gap-4 ml-2 w-full max-w-[450px]">
      {bars.map((bar, i) => (
        <div key={i} className="relative overflow-hidden h-3 rounded-full bg-amber-500/5 border border-amber-500/5" style={{ width: bar.width }}>
          <motion.div
            animate={{ 
              opacity: [0.2, 0.4, 0.2],
            }}
            transition={{ 
              duration: 3, 
              repeat: Infinity, 
              delay: bar.delay,
              ease: "easeInOut"
            }}
            className="absolute inset-0 bg-amber-500/10 w-full h-full"
          />
        </div>
      ))}
    </div>
  );
}
