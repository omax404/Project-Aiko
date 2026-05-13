import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

// --- Text Scramble Component ---
const ScrambleText = ({ text, className = "" }) => {
  const [displayText, setDisplayText] = useState(text);
  const chars = '!<>-_\\\\/[]{}—=+*^?#________';
  const frameRequest = useRef(null);
  
  useEffect(() => {
    let frame = 0;
    const queue = [];
    
    for (let i = 0; i < text.length; i++) {
      queue.push({
        from: chars[Math.floor(Math.random() * chars.length)],
        to: text[i],
        start: Math.floor(Math.random() * 40),
        end: Math.floor(Math.random() * 40) + Math.floor(Math.random() * 40),
        char: ''
      });
    }

    const update = () => {
      let output = '';
      let complete = 0;
      for (let i = 0, n = queue.length; i < n; i++) {
        let { from, to, start, end, char } = queue[i];
        if (frame >= end) {
          complete++;
          output += to;
        } else if (frame >= start) {
          if (!char || Math.random() < 0.28) {
            char = chars[Math.floor(Math.random() * chars.length)];
            queue[i].char = char;
          }
          output += `<span class="opacity-50">${char}</span>`;
        } else {
          output += from;
        }
      }
      setDisplayText(output);
      if (complete === queue.length) {
        setDisplayText(text);
        cancelAnimationFrame(frameRequest.current);
      } else {
        frameRequest.current = requestAnimationFrame(update);
        frame++;
      }
    };
    
    update();
    return () => cancelAnimationFrame(frameRequest.current);
  }, [text]);

  return <span className={`scramble-text ${className}`} dangerouslySetInnerHTML={{ __html: displayText }} />;
};

// --- Magnetic Button Component ---
const MagneticButton = ({ children, className = "", onClick }) => {
  const ref = useRef(null);
  const [position, setPosition] = useState({ x: 0, y: 0 });

  const handleMouse = (e) => {
    const { clientX, clientY } = e;
    const { height, width, left, top } = ref.current.getBoundingClientRect();
    const middleX = clientX - (left + width / 2);
    const middleY = clientY - (top + height / 2);
    setPosition({ x: middleX * 0.3, y: middleY * 0.3 });
  };

  const reset = () => {
    setPosition({ x: 0, y: 0 });
  };

  return (
    <motion.button
      ref={ref}
      onMouseMove={handleMouse}
      onMouseLeave={reset}
      onClick={onClick}
      animate={{ x: position.x, y: position.y }}
      transition={{ type: "spring", stiffness: 150, damping: 15, mass: 0.1 }}
      className={`glass-button px-8 py-3 font-medium tracking-wider text-sm flex items-center justify-center relative group ${className}`}
    >
      <span className="relative z-10">{children}</span>
      <div className="absolute inset-0 rounded-full bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
    </motion.button>
  );
};

// --- Main App ---
function App() {
  const [isReady, setIsReady] = useState(false);
  const spotlightRef = useRef(null);

  useEffect(() => {
    // Reveal animation
    setTimeout(() => setIsReady(true), 100);

    const handleMouseMove = (e) => {
      document.documentElement.style.setProperty('--x', `${e.clientX}px`);
      document.documentElement.style.setProperty('--y', `${e.clientY}px`);
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div className="min-h-screen w-full relative flex flex-col items-center justify-center overflow-hidden">
      {/* Dynamic Cursor Spotlight */}
      <div className="cursor-spotlight" />

      {/* Background Ghost Grid */}
      <div className="absolute inset-0 bg-grid z-0 opacity-20 pointer-events-none" />
      
      {/* Main Glass Container (Crystal) */}
      <motion.div 
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: isReady ? 1 : 0, y: isReady ? 0 : 30 }}
        transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
        className="z-10 flex flex-col items-center justify-center glass-crystal p-12 md:p-20 rounded-[3rem] max-w-[90vw]"
      >
        {/* Tagline */}
        <motion.div 
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.5, duration: 0.8 }}
          className="text-white/40 text-[0.6rem] tracking-[0.4em] uppercase font-mono mb-8"
        >
          Neural Hub — Soul Container Protocol
        </motion.div>

        {/* Title */}
        <h1 className="text-6xl md:text-8xl font-light tracking-tighter text-transparent bg-clip-text bg-gradient-to-b from-white to-white/30 mb-6 select-none mix-blend-plus-lighter">
          <ScrambleText text="Project Aiko" />
        </h1>

        {/* Subtitle */}
        <motion.p 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1, duration: 1 }}
          className="text-airi-subtext text-center max-w-lg mb-12 text-sm md:text-base leading-relaxed font-light"
        >
          Bringing high-fidelity virtual entities into our reality. An open-source architecture for local AI orchestration and visual presence.
        </motion.p>

        {/* Action Buttons */}
        <motion.div 
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 1.2, duration: 0.8 }}
          className="flex flex-wrap gap-8 justify-center"
        >
          <MagneticButton onClick={() => window.open('http://localhost:8000', '_blank')}>
            INITIALIZE_LINK
          </MagneticButton>
          <MagneticButton className="bg-transparent border-white/10 hover:bg-white/20" onClick={() => window.open('https://github.com/omax404/Project-Aiko', '_blank')}>
            PROTOCOL_DOCS
          </MagneticButton>
        </motion.div>
      </motion.div>

      {/* Mascot Silhouette */}
      <motion.div 
        initial={{ y: "100%", opacity: 0 }}
        animate={{ y: 0, opacity: 0.4 }}
        transition={{ delay: 1.5, duration: 2, ease: [0.16, 1, 0.3, 1] }}
        className="fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-5xl h-[70vh] pointer-events-none z-0 mix-blend-lighten opacity-40"
        style={{
          backgroundImage: 'url(/aiko.png)',
          backgroundSize: 'contain',
          backgroundPosition: 'bottom center',
          backgroundRepeat: 'no-repeat',
          filter: 'drop-shadow(0 0 50px rgba(255, 255, 255, 0.1)) grayscale(100%) brightness(1.5)'
        }}
      />
    </div>
  );
}

export default App;
