import React, { useEffect } from 'react';
import { listen } from '@tauri-apps/api/event';
import { Window } from '@tauri-apps/api/window';
import splashBg from './assets/ui/splash-bg.png';
import appIcon from './assets/ui/app-icon.png';

export default function SplashScreen() {
  useEffect(() => {
    let isTransitioning = false;

    const transitionToMain = async () => {
      if (isTransitioning) return;
      isTransitioning = true;
      try {
        const mainWindow = new Window('main');
        await mainWindow.show();
        const splashWindow = new Window('splashscreen');
        await splashWindow.close();
      } catch (err) {
        console.error("Error transitioning to main window:", err);
      }
    };

    const unlisten = listen('app-ready', () => {
      // Add a slight delay for smooth visual presentation
      setTimeout(transitionToMain, 1000);
    });

    // Fallback safety timer to ensure transition happens
    const timer = setTimeout(transitionToMain, 3000);

    return () => {
      clearTimeout(timer);
      unlisten.then(f => f());
    };
  }, []);

  return (
    <div 
      className="w-screen h-screen flex flex-col items-center justify-center relative overflow-hidden select-none"
      style={{
        backgroundImage: `url(${splashBg})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        backgroundColor: '#1C1320'
      }}
    >
      {/* Full-bleed overlay gradient for premium depth */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#2A1B30]/40 via-transparent to-[#1C1320]/80 pointer-events-none" />

      {/* Centered App Icon */}
      <div className="relative z-10 flex flex-col items-center gap-6">
        <img 
          src={appIcon} 
          alt="Aiko Icon" 
          className="w-32 h-32 object-contain drop-shadow-[0_0_25px_rgba(201,168,217,0.4)] animate-pulse" 
        />
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-[#C9A8D9] animate-ping" />
          <span className="text-[12px] font-bold uppercase tracking-[0.25em] text-[#C9A8D9]">
            Neural Hub Initializing...
          </span>
        </div>
      </div>
    </div>
  );
}
