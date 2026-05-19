import { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';

const VEILS = {
  cherry: {
    id: 'cherry',
    name: 'Cherry Protocol (Widescreen)',
    src: '/vivian_cherry.jpg',
    aspect: 'aspect-[736/319]',
    widthClass: 'w-full max-w-[500px] md:max-w-[700px]',
    desc: 'S-Rank Core visual: Vivian Banshee holding a cherry with deep crimson accents.',
    meta: '736x319 • JPEG • 64.5KB • Aspect 2.3:1',
    glow: 'rgba(244, 63, 94, 0.4)',
    style: {
      maskImage: 'none',
      WebkitMaskImage: 'none',
    }
  },
  portrait: {
    id: 'portrait',
    name: 'High Fidelity Close-up',
    src: '/vivian_portrait.png',
    aspect: 'aspect-[3/4]',
    widthClass: 'w-[280px] h-[373px] md:w-[340px] md:h-[453px]',
    desc: 'Premium generative portrait detail highlighting Vivian’s gothic purple hair, dark umbrella and intense red eyes.',
    meta: '1024x1024 • PNG • 1.09MB • Aspect 1:1',
    glow: 'rgba(168, 85, 247, 0.4)',
    style: {
      maskImage: 'none',
      WebkitMaskImage: 'none',
    }
  },
  avatar: {
    id: 'avatar',
    name: 'Ascension Silhouette',
    src: '/images/hero-main.png',
    aspect: 'aspect-[280/380]',
    widthClass: 'w-[280px] h-[380px] md:w-[340px] md:h-[460px]',
    desc: 'Legacy companion profile with deep transparency layer fading into the background.',
    meta: '2000x2714 • PNG • 5.45MB • Aspect 1:1.3',
    glow: 'rgba(233, 69, 96, 0.3)',
    style: {
      maskImage: 'linear-gradient(to bottom, black 65%, transparent 100%)',
      WebkitMaskImage: 'linear-gradient(to bottom, black 65%, transparent 100%)',
    }
  }
};

export default function Hero() {
  const sectionRef = useRef<HTMLElement>(null);
  const portraitRef = useRef<HTMLDivElement>(null);
  const taglineRef = useRef<HTMLHeadingElement>(null);
  const subRef = useRef<HTMLParagraphElement>(null);
  const ctaRef = useRef<HTMLButtonElement>(null);
  const switcherRef = useRef<HTMLDivElement>(null);
  
  const [cursorVisible, setCursorVisible] = useState(true);
  const [activeVeil, setActiveVeil] = useState<'cherry' | 'portrait' | 'avatar'>('cherry');

  // Entrance animations
  useEffect(() => {
    const ctx = gsap.context(() => {
      // Portrait entrance
      gsap.fromTo(
        portraitRef.current,
        { opacity: 0, y: 30, scale: 0.95 },
        { opacity: 1, y: 0, scale: 1, duration: 1.2, ease: 'power3.out', delay: 0.3 }
      );

      // Tagline entrance
      gsap.fromTo(
        taglineRef.current,
        { opacity: 0, y: 20 },
        { opacity: 1, y: 0, duration: 1.0, ease: 'power3.out', delay: 0.8 }
      );

      // Subtitle entrance
      gsap.fromTo(
        subRef.current,
        { opacity: 0, y: 15 },
        { opacity: 1, y: 0, duration: 0.8, ease: 'power3.out', delay: 1.0 }
      );

      // CTA entrance
      gsap.fromTo(
        ctaRef.current,
        { opacity: 0 },
        { opacity: 1, duration: 0.6, delay: 1.4 }
      );

      // Switcher entrance
      gsap.fromTo(
        switcherRef.current,
        { opacity: 0, y: 10 },
        { opacity: 1, y: 0, duration: 0.6, delay: 1.6 }
      );
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  // Veil change fade animation
  useEffect(() => {
    if (!portraitRef.current) return;
    gsap.fromTo(
      portraitRef.current,
      { opacity: 0.4, scale: 0.98 },
      { opacity: 1, scale: 1, duration: 0.5, ease: 'power2.out' }
    );
  }, [activeVeil]);

  // Blinking cursor effect
  useEffect(() => {
    const interval = setInterval(() => {
      setCursorVisible((v) => !v);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const scrollToSummon = () => {
    const el = document.querySelector('#summon');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  const selected = VEILS[activeVeil];

  return (
    <section
      ref={sectionRef}
      className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden py-24"
    >
      {/* Vignette overlay */}
      <div className="absolute inset-0 vignette z-[1] pointer-events-none" />

      {/* Background Grids */}
      <div className="absolute inset-0 bg-grid opacity-10 pointer-events-none" />

      {/* Content */}
      <div className="relative z-[2] flex flex-col items-center text-center px-6 max-w-5xl">
        
        {/* Widescreen/Vertical fully-dimensioned capsule container */}
        <div
          ref={portraitRef}
          className={`relative mb-6 rounded-3xl p-3 border border-white/5 bg-obsidian/40 backdrop-blur-xl flex flex-col items-center transition-all duration-500 ease-in-out ${selected.widthClass}`}
          style={{
            animation: 'heroFloat 5s ease-in-out infinite',
            boxShadow: `0 0 40px -10px ${selected.glow}`,
          }}
        >
          {/* Scanner Line Sweep Effect */}
          <div className="absolute left-0 w-full h-[1.5px] bg-gradient-to-r from-transparent via-lavender/80 to-transparent shadow-[0_0_8px_rgba(200,164,244,0.8)] pointer-events-none animate-scan z-10" />

          {/* Telemetry info top bar */}
          <div className="w-full flex justify-between items-center px-3 pb-2.5 border-b border-white/5 mb-2 font-mono text-[9px] text-moonlight/45 select-none">
            <span className="flex items-center gap-1">
              <span className="w-1 h-1 rounded-full bg-lavender animate-pulse" />
              VEIL_STREAMING: OK
            </span>
            <span>{selected.meta}</span>
          </div>

          <div className={`relative rounded-2xl overflow-hidden bg-black/30 border border-white/5 flex items-center justify-center ${selected.aspect} w-full`}>
            <img
              src={selected.src}
              alt={selected.name}
              className="w-full h-full object-contain"
              style={selected.style}
            />
          </div>

          {/* Description overlay */}
          <div className="w-full text-left px-3 pt-3 border-t border-white/5 mt-2 flex flex-col gap-0.5 select-none">
            <span className="font-mono text-[10px] text-lavender tracking-wider font-semibold uppercase">{selected.name}</span>
            <span className="text-[9px] text-moonlight/50 font-body leading-relaxed">{selected.desc}</span>
          </div>
        </div>

        {/* Visual Switcher Pills */}
        <div 
          ref={switcherRef}
          className="flex flex-wrap gap-2.5 justify-center mb-8 bg-obsidian/60 p-1.5 rounded-full border border-white/5 backdrop-blur-md relative z-10"
        >
          {Object.keys(VEILS).map((key) => {
            const isSelected = activeVeil === key;
            return (
              <button
                key={key}
                onClick={() => setActiveVeil(key as 'cherry' | 'portrait' | 'avatar')}
                className={`px-4 py-1.5 rounded-full font-mono text-[9px] tracking-wider uppercase transition-all duration-300 ${
                  isSelected 
                    ? 'bg-lavender text-obsidian font-semibold shadow-[0_0_15px_rgba(200,164,244,0.35)]' 
                    : 'text-moonlight/60 hover:text-white hover:bg-white/5'
                }`}
              >
                {key === 'cherry' ? '🍒 Cherry Veil' : key === 'portrait' ? '🎭 High-Fi Close' : '⚡ Ascension'}
              </button>
            );
          })}
        </div>

        {/* Tagline */}
        <h1
          ref={taglineRef}
          className="font-display font-light text-moonlight max-w-[680px] text-[clamp(28px,3.5vw,48px)] leading-[1.15] tracking-wide mb-4"
        >
          She Doesn&apos;t Just Chat.
          <br />
          She Thinks. Feels. Remembers.
        </h1>

        {/* Subtitle */}
        <p
          ref={subRef}
          className="font-body font-light text-moonlight/60 text-lg mb-8"
        >
          Your Devoted AI Companion — With a Soul
        </p>

        {/* CTA */}
        <button
          ref={ctaRef}
          onClick={scrollToSummon}
          className="group px-8 py-3 border border-lavender text-lavender font-mono text-base rounded-lg hover:bg-lavender/10 transition-all duration-300"
        >
          <span>Wake Her Up</span>
          <span
            className="inline-block w-[10px] ml-1 transition-opacity duration-100"
            style={{ opacity: cursorVisible ? 1 : 0 }}
          >
            _
          </span>
        </button>
      </div>

      <style>{`
        @keyframes heroFloat {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-6px); }
        }
        @keyframes scanSweep {
          0% { top: 0%; opacity: 0; }
          10% { opacity: 0.8; }
          90% { opacity: 0.8; }
          100% { top: 100%; opacity: 0; }
        }
        .animate-scan {
          animation: scanSweep 5s cubic-bezier(0.4, 0, 0.2, 1) infinite;
        }
        .bg-grid {
          background-size: 40px 40px;
          background-image: 
            linear-gradient(to right, rgba(200, 164, 244, 0.03) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(200, 164, 244, 0.03) 1px, transparent 1px);
        }
      `}</style>
    </section>
  );
}
