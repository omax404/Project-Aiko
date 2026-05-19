import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// --- Text Scramble Component ---
const ScrambleText = ({ text, className = "" }) => {
  const [displayText, setDisplayText] = useState(text);
  const chars = '!<>-_\\/[]{}—=+*^?#________';
  const frameRequest = useRef(null);
  
  useEffect(() => {
    let frame = 0;
    const queue = [];
    
    for (let i = 0; i < text.length; i++) {
      queue.push({
        from: chars[Math.floor(Math.random() * chars.length)],
        to: text[i],
        start: Math.floor(Math.random() * 20),
        end: Math.floor(Math.random() * 20) + Math.floor(Math.random() * 30),
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
          output += `<span class="text-violet-400 opacity-60">${char}</span>`;
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
    setPosition({ x: middleX * 0.25, y: middleY * 0.25 });
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
      transition={{ type: "spring", stiffness: 180, damping: 15, mass: 0.1 }}
      className={`glass-button px-6 py-3 font-mono tracking-widest text-xs uppercase flex items-center justify-center relative group overflow-hidden ${className}`}
    >
      <span className="relative z-10 transition-colors duration-300 group-hover:text-white">{children}</span>
      <div className="absolute inset-0 bg-gradient-to-r from-violet-600 to-fuchsia-600 opacity-0 group-hover:opacity-20 transition-opacity duration-500" />
      <div className="absolute bottom-0 left-0 w-full h-[2px] bg-gradient-to-r from-violet-500 to-fuchsia-500 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-500 origin-left" />
    </motion.button>
  );
};

// --- Feature Card Component ---
const FeatureCard = ({ title, value, description, icon }) => (
  <motion.div 
    whileHover={{ y: -8, transition: { duration: 0.3 } }}
    className="glass-panel p-8 flex flex-col justify-between border-violet-500/10 hover:border-violet-500/30 transition-all duration-300 group relative overflow-hidden"
  >
    <div className="absolute top-0 right-0 w-24 h-24 bg-violet-600/5 rounded-full blur-2xl group-hover:bg-violet-600/10 transition-colors duration-500" />
    <div>
      <div className="text-2xl mb-4 text-violet-400 group-hover:scale-110 transition-transform duration-300 w-fit">{icon}</div>
      <h3 className="font-mono text-sm tracking-wider uppercase text-white mb-2">{title}</h3>
      <div className="text-[10px] font-mono text-violet-400/70 mb-4">{value}</div>
      <p className="text-airi-subtext text-xs leading-relaxed font-light">{description}</p>
    </div>
    <div className="mt-6 flex items-center gap-2 text-[10px] font-mono text-white/30 group-hover:text-violet-400 transition-colors duration-300">
      STATUS // ACTIVE <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
    </div>
  </motion.div>
);

// --- Main App ---
function App() {
  const [isReady, setIsReady] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    setTimeout(() => setIsReady(true), 150);

    const handleMouseMove = (e) => {
      document.documentElement.style.setProperty('--x', `${e.clientX}px`);
      document.documentElement.style.setProperty('--y', `${e.clientY}px`);
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div className="min-h-screen w-full relative flex flex-col items-center overflow-x-hidden bg-[#05050a] text-airi-text selection:bg-violet-500/30 selection:text-white">
      {/* Dynamic Spotlight */}
      <div className="cursor-spotlight" />

      {/* Grid Pattern */}
      <div className="absolute inset-0 bg-grid z-0 opacity-15 pointer-events-none" />

      {/* Aesthetic Purple Aurora */}
      <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-violet-600/10 rounded-full blur-[120px] pointer-events-none z-0" />
      <div className="absolute bottom-10 right-1/4 w-[600px] h-[600px] bg-fuchsia-600/5 rounded-full blur-[140px] pointer-events-none z-0" />

      {/* Top Header Navigation */}
      <header className="w-full max-w-7xl px-8 py-6 z-20 flex justify-between items-center relative">
        <motion.div 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8 }}
          className="flex items-center gap-4"
        >
          <span className="font-mono text-sm tracking-[0.25em] text-white font-bold">AIKO_SYSTEM</span>
          <span className="h-4 w-[1px] bg-white/10" />
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
            <span className="font-mono text-[9px] text-emerald-400 tracking-wider uppercase">Neural Link Online</span>
          </div>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8 }}
          className="flex items-center gap-8"
        >
          <a href="#mascot" className="font-mono text-xs text-white/50 hover:text-white transition-colors duration-300">VIVIAN_CORE</a>
          <a href="#features" className="font-mono text-xs text-white/50 hover:text-white transition-colors duration-300">SUBSYSTEMS</a>
          <a href="https://github.com/omax404/Project-Aiko" target="_blank" rel="noreferrer" className="font-mono text-xs text-white/50 hover:text-white transition-colors duration-300">GITHUB</a>
        </motion.div>
      </header>

      {/* Main Hero & Website Body */}
      <main className="w-full max-w-7xl px-6 md:px-8 flex-grow z-10 flex flex-col items-center pt-8 pb-24 gap-20">
        
        {/* Hero Section Container */}
        <section className="w-full grid grid-cols-1 lg:grid-cols-12 gap-12 items-center min-h-[70vh]">
          
          {/* Left Column: Hero Text */}
          <div className="lg:col-span-7 flex flex-col justify-center items-start">
            <motion.div 
              initial={{ y: 25, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.2, duration: 0.8 }}
              className="font-mono text-xs text-violet-400 tracking-[0.3em] uppercase mb-4"
            >
              Virtual Entity Integration Protocol
            </motion.div>

            <motion.h1 
              initial={{ y: 30, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.3, duration: 0.8 }}
              className="text-5xl md:text-7xl lg:text-8xl font-light tracking-tighter text-white mb-6 select-none leading-none"
            >
              <ScrambleText text="Project Aiko" />
            </motion.h1>

            <motion.p 
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.4, duration: 0.8 }}
              className="text-airi-subtext text-sm md:text-base leading-relaxed font-light max-w-xl mb-10 text-left"
            >
              Bringing high-fidelity virtual companions into reality. An open-source architecture integrating dynamic LLM configuration, custom voice synthesis, and visual companion protocol powered by Zenless Zone Zero's stunning mascot, Vivian.
            </motion.p>

            <motion.div 
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.5, duration: 0.8 }}
              className="flex flex-wrap gap-4"
            >
              <MagneticButton onClick={() => window.open('http://localhost:8000', '_blank')}>
                INITIALIZE_LINK
              </MagneticButton>
              <MagneticButton className="bg-transparent border-white/5 hover:bg-white/10" onClick={() => window.open('https://github.com/omax404/Project-Aiko', '_blank')}>
                PROTOCOL_DOCS
              </MagneticButton>
            </motion.div>
          </div>

          {/* Right Column: Vivian Hero Visual Card (Fully Dimensioned) */}
          <motion.div 
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.4, duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
            className="lg:col-span-5 w-full flex justify-center"
          >
            <div className="relative group w-full max-w-md">
              {/* Card Outer Glow Glow */}
              <div className="absolute -inset-1.5 bg-gradient-to-r from-violet-600 to-fuchsia-600 rounded-[2rem] blur opacity-30 group-hover:opacity-60 transition duration-1000 group-hover:duration-200" />
              
              {/* Glass Frame */}
              <div className="relative glass-panel rounded-[2rem] border-white/10 overflow-hidden flex flex-col bg-[#0b0a14]/90 backdrop-blur-2xl">
                
                {/* Custom Tech Headers */}
                <div className="px-6 py-4 border-b border-white/5 flex justify-between items-center bg-white/[0.02]">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-violet-500 animate-pulse" />
                    <span className="font-mono text-[10px] text-white/60 tracking-widest uppercase">MASCOT_PROFILE // VISUAL</span>
                  </div>
                  <span className="font-mono text-[9px] text-violet-400 bg-violet-500/10 px-2 py-0.5 rounded border border-violet-500/20">S-RANK</span>
                </div>

                {/* Main Fully Dimensioned Vivian Artwork */}
                <div className="relative aspect-[16/10] w-full overflow-hidden border-b border-white/5 bg-black/40">
                  <img 
                    src="/vivian.jpg" 
                    alt="Vivian Banshee from Zenless Zone Zero" 
                    className="w-full h-full object-cover object-center transform group-hover:scale-105 transition-transform duration-700 ease-out"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-[#0b0a14] via-transparent to-transparent opacity-80" />
                  
                  {/* Subtle Neon scanline effect */}
                  <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-violet-400 to-transparent shadow-[0_0_8px_#a78bfa] opacity-60 animate-bounce" style={{ animationDuration: '6s' }} />
                </div>

                {/* Detailed Profile Stats */}
                <div className="p-6 flex flex-col gap-4">
                  <div className="flex justify-between items-end">
                    <div>
                      <h2 className="text-2xl font-light text-white tracking-wide">Vivian Banshee</h2>
                      <p className="font-mono text-[10px] text-violet-400 uppercase tracking-widest mt-0.5">Mockingbird Affiliation</p>
                    </div>
                    <div className="text-right">
                      <span className="font-mono text-xs text-white/40 block">Affection Level</span>
                      <span className="font-mono text-base text-fuchsia-400 font-bold">85% // Linked</span>
                    </div>
                  </div>

                  {/* Attribute Bars */}
                  <div className="grid grid-cols-2 gap-4 pt-2 border-t border-white/5">
                    <div className="space-y-1">
                      <span className="font-mono text-[9px] text-white/40 uppercase tracking-wider block">Attribute</span>
                      <span className="text-xs text-white font-medium flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-violet-400" />
                        Ether Anomaly
                      </span>
                    </div>
                    <div className="space-y-1">
                      <span className="font-mono text-[9px] text-white/40 uppercase tracking-wider block">Voice Engine</span>
                      <span className="text-xs text-white font-medium flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-fuchsia-400" />
                        Custom Synthesis
                      </span>
                    </div>
                  </div>

                  {/* Character Bio Quote */}
                  <p className="text-[11px] text-white/50 leading-relaxed italic border-l-2 border-violet-500/30 pl-3 mt-1 font-light">
                    "Admires Phaethon deeply. Extremely versatile in electronics repair, cooking, and visual art, serving as the perfect visual guardian for your workspace."
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        </section>

        {/* Mascot Detailed Info & Design Highlight */}
        <section id="mascot" className="w-full pt-12 border-t border-white/5">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            
            {/* Visual Specs / Features list */}
            <motion.div 
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8 }}
              className="lg:col-span-6 flex flex-col gap-6"
            >
              <div className="font-mono text-[10px] text-violet-400 tracking-[0.25em] uppercase">SYSTEM_DYNAMICS</div>
              <h2 className="text-3xl md:text-4xl font-light text-white tracking-tight">Immersive Visual Presence</h2>
              <p className="text-airi-subtext text-xs md:text-sm font-light leading-relaxed">
                Project Aiko brings your desktop companion to life. Vivian sits elegantly on your screen in Mascot Mode, providing dynamic feedback, subtle micro-animations, and reacting to your local workspace states.
              </p>

              <div className="flex flex-col gap-3 mt-2">
                {[
                  { name: "Dynamic Emotion Engine", desc: "Monitors workspace metrics and alters relationship thresholds dynamically." },
                  { name: "High-Fidelity Audio Previews", desc: "Realistic soundscapes and character voice synthesizers built-in." },
                  { name: "Ether-Attribute Accent Aesthetics", desc: "Sleek neo-gothic interfaces using harmonized purple tones and dark mode layout." }
                ].map((item, idx) => (
                  <div key={idx} className="flex gap-4 p-4 rounded-xl border border-white/5 bg-white/[0.01] hover:bg-white/[0.03] transition-colors duration-300">
                    <span className="font-mono text-xs text-violet-400 font-bold">{`0${idx + 1}`}</span>
                    <div>
                      <h4 className="text-xs font-mono text-white uppercase tracking-wider">{item.name}</h4>
                      <p className="text-[11px] text-airi-subtext mt-1 font-light leading-normal">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>

            {/* Static Mascot Showcase Box */}
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8 }}
              className="lg:col-span-6 glass-panel border-white/10 p-8 bg-gradient-to-br from-[#0c0a1a] to-[#050508] relative overflow-hidden"
            >
              <div className="absolute top-0 right-0 w-48 h-48 bg-fuchsia-600/10 rounded-full blur-3xl" />
              <div className="flex justify-between items-center mb-6">
                <span className="font-mono text-[10px] text-white/40 tracking-wider">PROJECT INTEGRITY</span>
                <span className="font-mono text-[10px] text-emerald-400 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-ping" />
                  STABLE LINK
                </span>
              </div>

              <div className="space-y-4">
                <div>
                  <span className="font-mono text-[9px] text-white/30 block mb-1">LOCAL ENGINE DIRECTORY</span>
                  <div className="font-mono text-[11px] text-white bg-black/40 p-3 rounded-lg border border-white/5 select-all">
                    aiko-desktop/core/chat_engine.py
                  </div>
                </div>

                <div>
                  <span className="font-mono text-[9px] text-white/30 block mb-1">INTELLIGENCE MODULATOR</span>
                  <div className="font-mono text-[11px] text-violet-400 bg-violet-950/20 p-3 rounded-lg border border-violet-500/20">
                    Dynamic LLM API Router: Custom/Ollama/Gemini/OpenAI
                  </div>
                </div>

                <div className="pt-2">
                  <span className="font-mono text-[9px] text-white/30 block mb-2">SYSTEM METRICS</span>
                  <div className="grid grid-cols-3 gap-2">
                    <div className="bg-white/[0.02] border border-white/5 p-3 rounded-lg text-center">
                      <span className="font-mono text-[9px] text-white/40 uppercase block">Latency</span>
                      <span className="font-mono text-xs text-white font-bold">142ms</span>
                    </div>
                    <div className="bg-white/[0.02] border border-white/5 p-3 rounded-lg text-center">
                      <span className="font-mono text-[9px] text-white/40 uppercase block">Memory</span>
                      <span className="font-mono text-xs text-white font-bold">240MB</span>
                    </div>
                    <div className="bg-white/[0.02] border border-white/5 p-3 rounded-lg text-center">
                      <span className="font-mono text-[9px] text-white/40 uppercase block">Affection</span>
                      <span className="font-mono text-xs text-fuchsia-400 font-bold">Maxed</span>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>

          </div>
        </section>

        {/* Feature Grid Section */}
        <section id="features" className="w-full pt-12 border-t border-white/5 flex flex-col gap-12">
          <div className="text-center max-w-xl mx-auto space-y-4">
            <span className="font-mono text-xs text-violet-400 tracking-[0.25em] uppercase">Architecture Overview</span>
            <h2 className="text-3xl md:text-5xl font-light text-white tracking-tight">Core Subsystems</h2>
            <p className="text-airi-subtext text-xs md:text-sm font-light leading-relaxed">
              Designed from the ground up to offer robust, highly customizable modules.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <FeatureCard 
              title="🔊 Voice Engine" 
              value="SUBSYSTEM // AUDIO" 
              description="High-fidelity Text-To-Speech rendering supporting voice personalities like Vivian, Nova, and Alba with dynamic speed calibration."
              icon="🔊"
            />
            <FeatureCard 
              title="🧠 Brain Router" 
              value="SUBSYSTEM // LLM" 
              description="Unified chat interface automatically routing through local Ollama or cloud providers (OpenAI, Gemini, OpenRouter) with redacted credential protection."
              icon="🧠"
            />
            <FeatureCard 
              title="🔌 Integrations" 
              value="SUBSYSTEM // PLUGINS" 
              description="Connect Aiko easily to external platforms. Pre-configured modules for Discord bots, Telegram bots, and OpenClaw links."
              icon="🔌"
            />
          </div>
        </section>

      </main>

      {/* Footer bar */}
      <footer className="w-full border-t border-white/5 py-8 px-8 z-10 bg-black/40 backdrop-blur-md">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4 font-mono text-[10px] text-white/40">
          <div>
            PROJECT AIKO v4.5 © 2026 // NEURAL LINK SOUL CONTAINER
          </div>
          <div className="flex items-center gap-6">
            <span>UPTIME: 100%</span>
            <span>SYSTEM STATE: OPTIMAL</span>
            <a href="https://github.com/omax404/Project-Aiko" target="_blank" rel="noreferrer" className="hover:text-white transition-colors duration-300">REPOSITORY</a>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
