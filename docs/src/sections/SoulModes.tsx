import { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { useSoul } from '@/context/SoulContext';
import { SOUL_MODES } from '@/types/soul';
import type { SoulMode } from '@/types/soul';

gsap.registerPlugin(ScrollTrigger);

export default function SoulModes() {
  const sectionRef = useRef<HTMLElement>(null);
  const headerRef = useRef<HTMLDivElement>(null);
  const portraitRef = useRef<HTMLDivElement>(null);
  const descRef = useRef<HTMLDivElement>(null);
  const { activeMode, setMode, config } = useSoul();
  const [isTransitioning, setIsTransitioning] = useState(false);

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.fromTo(
        headerRef.current?.children || [],
        { opacity: 0, y: 30 },
        {
          opacity: 1,
          y: 0,
          duration: 0.8,
          stagger: 0.15,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: headerRef.current,
            start: 'top 80%',
          },
        }
      );

      gsap.fromTo(
        portraitRef.current,
        { opacity: 0, scale: 0.9 },
        {
          opacity: 1,
          scale: 1,
          duration: 1,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: portraitRef.current,
            start: 'top 75%',
          },
        }
      );
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  const handleModeChange = (mode: SoulMode) => {
    if (mode === activeMode || isTransitioning) return;
    setIsTransitioning(true);

    // Fade out portrait
    gsap.to(portraitRef.current, {
      opacity: 0,
      scale: 0.98,
      duration: 0.4,
      ease: 'power2.in',
      onComplete: () => {
        setMode(mode);
        // Fade in new portrait
        gsap.to(portraitRef.current, {
          opacity: 1,
          scale: 1,
          duration: 0.6,
          ease: 'power3.out',
          onComplete: () => setIsTransitioning(false),
        });
      },
    });

    // Fade out/in description
    gsap.to(descRef.current, {
      opacity: 0,
      y: 10,
      duration: 0.3,
      onComplete: () => {
        gsap.to(descRef.current, {
          opacity: 1,
          y: 0,
          duration: 0.5,
          delay: 0.3,
        });
      },
    });
  };

  const modes = Object.keys(SOUL_MODES) as SoulMode[];

  return (
    <section
      ref={sectionRef}
      id="soul-modes"
      className="relative section-padding soul-transition"
      style={{
        backgroundColor: config.bgTint.replace('0.05', '0.08'),
      }}
    >
      <div className="content-max mx-auto">
        {/* Header */}
        <div ref={headerRef} className="text-center mb-12">
          <p className="eyebrow mb-4">SOUL MODES</p>
          <h2 className="display-heading text-[clamp(36px,5vw,72px)]">
            Her Heart Shifts
          </h2>
        </div>

        {/* Toggle Bar */}
        <div className="flex justify-center gap-3 mb-16 flex-wrap">
          {modes.map((mode) => {
            const modeConfig = SOUL_MODES[mode];
            const isActive = activeMode === mode;
            return (
              <button
                key={mode}
                onClick={() => handleModeChange(mode)}
                className="px-6 py-2.5 rounded-full text-sm font-medium transition-all duration-400"
                style={{
                  backgroundColor: isActive ? modeConfig.color : 'transparent',
                  color: isActive ? '#0a0a0f' : modeConfig.color,
                  border: `1px solid ${isActive ? modeConfig.color : `${modeConfig.color}4D`}`,
                  opacity: isTransitioning && !isActive ? 0.5 : 1,
                }}
              >
                {modeConfig.name}
              </button>
            );
          })}
        </div>

        {/* Portrait */}
        <div
          ref={portraitRef}
          className="relative mx-auto mb-10"
          style={{ maxWidth: '400px', aspectRatio: '3/4' }}
        >
          <div className="relative w-full h-full rounded-2xl overflow-hidden">
            <img
              src={config.portrait}
              alt={`Vivian - ${config.name} mode`}
              className="w-full h-full object-cover transition-all duration-800"
            />
            {/* Border glow */}
            <div
              className="absolute inset-0 rounded-2xl pointer-events-none transition-all duration-800"
              style={{
                boxShadow: `inset 0 0 0 1px ${config.color}40, 0 0 60px ${config.glowColor}`,
              }}
            />
          </div>
        </div>

        {/* Description */}
        <div ref={descRef} className="text-center max-w-md mx-auto">
          <h3
            className="font-display text-2xl mb-3 soul-transition"
            style={{
              color: config.color,
              fontWeight: config.fontWeight,
            }}
          >
            {config.name}
          </h3>
          <p className="font-body text-moonlight/70 text-base leading-relaxed soul-transition">
            {config.description}
          </p>
        </div>
      </div>
    </section>
  );
}
