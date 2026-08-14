import { useEffect, useState } from 'react';
import appIcon from './assets/ui/app-icon.png';
import splashVideo from './assets/ui/splash-video.mp4';

export default function SplashScreen() {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    // Smooth progress simulation (0% to 100% over 2.4s)
    const startTime = Date.now();
    const duration = 2400;

    const isTauri = !!(window as any).__TAURI__;
    let isTransitioning = false;

    const transitionToMain = async () => {
      if (isTransitioning) return;
      isTransitioning = true;
      try {
        const { Window } = await import('@tauri-apps/api/window');
        const mainWindow = new Window('main');
        await mainWindow.show();
        const splashWindow = new Window('splashscreen');
        await splashWindow.close();
      } catch (err) {
        console.error("Error transitioning to main window:", err);
      }
    };

    const interval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const pct = Math.min(100, Math.floor((elapsed / duration) * 100));
      setProgress(pct);
      if (pct >= 100) {
        clearInterval(interval);
        // Auto transition to main once loading bar reaches 100%
        setTimeout(transitionToMain, 300);
      }
    }, 30);

    if (!isTauri) return () => clearInterval(interval);

    let unlisten: (() => void) | null = null;

    import('@tauri-apps/api/event').then(({ listen }) => {
      listen('app-ready', () => {
        // App is ready - if progress is close to finished, transition shortly
        setTimeout(transitionToMain, 500);
      }).then(fn => { unlisten = fn; });
    });

    const timer = setTimeout(transitionToMain, 4000);

    return () => {
      clearInterval(interval);
      clearTimeout(timer);
      unlisten?.();
    };
  }, []);

  return (
    <div className="w-screen h-screen bg-transparent flex items-center justify-center p-2 select-none overflow-hidden">
      {/* Floating Glassmorphic Card Container with Pure Transparent PNG Outer Edges */}
      <div className="w-full h-full flex flex-col items-center justify-center relative overflow-hidden bg-[#0B060F]/95 backdrop-blur-2xl rounded-[24px] border border-white/[0.12] shadow-[0_20px_50px_rgba(0,0,0,0.75)]">
        {/* Background Video */}
        <video
          autoPlay
          loop
          muted
          playsInline
          className="absolute inset-0 w-full h-full object-cover z-0 pointer-events-none rounded-[24px]"
          src={splashVideo}
        />
        {/* Dynamic Overlay for high-end backdrop depth */}
        <div className="absolute inset-0 bg-gradient-to-b from-[#1C0F24]/60 via-transparent to-[#0B060F]/95 z-5 pointer-events-none rounded-[24px]" />
        
        <div className="relative z-10 w-[88%] h-[82%] flex flex-col items-center justify-center gap-6 p-6 rounded-2xl bg-white/[0.015] border border-white/[0.05] backdrop-blur-md shadow-2xl">
        <style>{`
          @keyframes sweep {
            0% { transform: translateX(-150%); }
            50% { transform: translateX(150%); }
            100% { transform: translateX(150%); }
          }
          .shimmer-sweep {
            animation: sweep 2.5s infinite ease-in-out;
          }
        `}</style>

        {/* Scaled Transparent Logo Image (No Border Container, Expanded Size) */}
        <img 
          src={appIcon} 
          alt="Aiko Icon" 
          className="w-[320px] h-32 object-contain drop-shadow-[0_0_35px_rgba(201,168,217,0.55)] transition-all duration-300 animate-pulse" 
        />

        {/* Loading text with high contrast and text glow */}
        <div className="flex flex-col items-center gap-3">
          <span 
            className="text-[12px] font-semibold uppercase tracking-[0.35em] text-[#EBE3FF]"
            style={{
              textShadow: '0 0 10px rgba(235, 227, 255, 0.4)'
            }}
          >
            Neural Hub Initializing...
          </span>

          {/* Premium Glowing Progress Bar with Shimmer */}
          <div className="relative w-60 h-1.5 bg-[#251630]/75 rounded-full overflow-hidden border border-white/[0.06] shadow-inner">
            <div 
              className="h-full bg-gradient-to-r from-[#B192CD] via-[#D1A7E2] to-[#B192CD] rounded-full shadow-[0_0_8px_#D1A7E2] transition-all duration-100 ease-out relative overflow-hidden"
              style={{ width: `${progress}%` }}
            >
              {/* Shimmer sweep effect */}
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent shimmer-sweep w-[150%] h-full z-10 pointer-events-none" />
            </div>
          </div>

          {/* Loading Percentage with aristocratic Cormorant Garamond */}
          <span 
            className="text-[14px] tracking-wider text-[#C9A8D9] opacity-90 font-light italic"
            style={{
              fontFamily: "'Cormorant Garamond', serif"
            }}
          >
            {progress}% Loaded
          </span>
        </div>
      </div>
    </div>
  </div>
  );
}
