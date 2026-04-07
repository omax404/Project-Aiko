import { useEffect, useState } from 'react';
import { getCurrentWindow } from '@tauri-apps/api/window';
import { motion, AnimatePresence } from 'framer-motion';
import { Live2DAvatar } from './components/Live2DAvatar';
import { useNeuralStore } from './store/useNeuralStore';
import { Home, X } from 'lucide-react';
import { Window } from '@tauri-apps/api/window';

/**
 * AIKO MASCOT SYSTEM v2.0
 * Renewed from scratch for 100% reliability and pure aesthetics.
 */
export default function MascotApp() {
  const {
    connect, isThinking, isTalking, currentEmotion, amplitude, fetchBridgeStatus
  } = useNeuralStore();

  const [isHovered, setIsHovered] = useState(false);

  useEffect(() => {
    try { connect('http://127.0.0.1:8000'); } catch (e) { }
    fetchBridgeStatus();
  }, []);

  const handleReturnToHub = async () => {
    try {
      const mainWindow = new Window('main');
      await mainWindow.show();
      await getCurrentWindow().hide();
    } catch (e) {
      console.error("Failed to swap windows", e);
    }
  };

  const handleDrag = () => {
    getCurrentWindow().startDragging().catch(console.error);
  };

  return (
    <div 
      className="mascot-container group"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* ── INTERACTION LAYER (Manual Drag + Native Region) ── */}
      <div 
        onMouseDown={handleDrag}
        data-tauri-drag-region
        className="absolute inset-0 z-20 cursor-move bg-white/[0.002]" 
        title="Drag Aiko anywhere"
      />

      {/* ── MODEL LAYER ── */}
      <div className="relative z-10 pointer-events-none transition-transform duration-500 hover:scale-105">
        <Live2DAvatar
          modelUrl="/live2d/vivian/vivian.model3.json"
          isThinking={isThinking}
          isTalking={isTalking}
          emotion={currentEmotion}
          width={400}
          height={550}
          scale={0.65}
          amplitude={amplitude}
        />
      </div>

      {/* ── HUD LAYER (Only on Hover) ── */}
      <AnimatePresence>
        {isHovered && (
          <div className="mascot-ui-layer">
            {/* Top Toolbar */}
            <motion.div 
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="absolute top-6 left-1/2 -translate-x-1/2 flex gap-3 pointer-events-auto"
            >
              <button 
                onClick={handleReturnToHub}
                className="p-2.5 rounded-full bg-black/60 border border-white/10 text-white/40 hover:text-white hover:bg-accent/40 transition-all backdrop-blur-lg shadow-2xl"
                title="Return to Main Hub"
              >
                <Home size={18} />
              </button>
              <button 
                onClick={() => getCurrentWindow().close()}
                className="p-2.5 rounded-full bg-black/60 border border-white/10 text-white/40 hover:text-red-400 hover:bg-red-400/20 transition-all backdrop-blur-lg shadow-2xl"
                title="Goodbye, Aiko"
              >
                <X size={18} />
              </button>
            </motion.div>

            {/* Drag Handle Indicator */}
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.5 }}
              exit={{ opacity: 0 }}
              className="absolute bottom-10 left-1/2 -translate-x-1/2 text-[9px] uppercase tracking-[0.2em] text-white/30 font-bold"
            >
              Locked & Loaded
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
