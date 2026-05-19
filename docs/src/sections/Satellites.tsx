import { useEffect, useRef, useCallback } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { MessageCircle, Send, Monitor, Check } from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

const SATELLITES = [
  {
    icon: MessageCircle,
    name: 'Discord Bot',
    description:
      'Mentions, DMs, voice messages, images, and slash commands. Full conversational context.',
    features: [
      'Voice message transcription',
      'Image analysis',
      'Proactive messaging',
      'Server-wide presence',
    ],
    color: '#5865F2',
  },
  {
    icon: Send,
    name: 'Telegram Bot',
    description:
      'Groups and DMs with full access to Aiko\'s capabilities. Lightweight and fast.',
    features: [
      'Group chat support',
      'Direct messages',
      'Media processing',
      'Inline queries',
    ],
    color: '#0088cc',
  },
  {
    icon: Monitor,
    name: 'Tauri Desktop',
    description:
      'Live2D overlay with global hotkey, mascot mode, and unified dashboard.',
    features: [
      'Ctrl+Alt+A global hotkey',
      'Click-through mascot mode',
      'Live2D avatar',
      'Unified dashboard',
    ],
    color: '#c8a4f4',
  },
];

function SatelliteCard({
  satellite,
  index,
}: {
  satellite: (typeof SATELLITES)[0];
  index: number;
}) {
  const cardRef = useRef<HTMLDivElement>(null);

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      const card = cardRef.current;
      if (!card) return;

      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left - rect.width / 2;
      const y = e.clientY - rect.top - rect.height / 2;

      const maxShift = 8;
      const shiftX = (x / rect.width) * maxShift;
      const shiftY = (y / rect.height) * maxShift;

      card.style.transform = `translate(${shiftX}px, ${shiftY}px)`;
    },
    []
  );

  const handleMouseLeave = useCallback(() => {
    const card = cardRef.current;
    if (!card) return;
    gsap.to(card, {
      x: 0,
      y: 0,
      duration: 0.6,
      ease: 'elastic.out(1, 0.5)',
    });
  }, []);

  return (
    <div
      ref={cardRef}
      className="satellite-card glass-card p-8 transition-shadow duration-300"
      style={{
        transitionDelay: `${index * 0.1}s`,
      }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      <div
        className="w-12 h-12 rounded-xl flex items-center justify-center mb-6"
        style={{ backgroundColor: `${satellite.color}15` }}
      >
        <satellite.icon size={24} style={{ color: satellite.color }} />
      </div>
      <h3 className="font-display text-xl text-moonlight mb-3">
        {satellite.name}
      </h3>
      <p className="font-body text-moonlight/60 text-sm leading-relaxed mb-6">
        {satellite.description}
      </p>
      <ul className="space-y-2">
        {satellite.features.map((feature, i) => (
          <li key={i} className="flex items-center gap-2 text-sm">
            <Check size={14} style={{ color: satellite.color }} />
            <span className="text-moonlight/50">{feature}</span>
          </li>
        ))}
      </ul>
      <button
        className="mt-6 w-full py-2.5 rounded-lg text-sm font-medium border transition-all duration-300 hover:bg-opacity-10"
        style={{
          borderColor: `${satellite.color}40`,
          color: satellite.color,
          backgroundColor: 'transparent',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = `${satellite.color}10`;
          e.currentTarget.style.borderColor = `${satellite.color}80`;
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = 'transparent';
          e.currentTarget.style.borderColor = `${satellite.color}40`;
        }}
      >
        Connect
      </button>
    </div>
  );
}

export default function Satellites() {
  const sectionRef = useRef<HTMLElement>(null);
  const headerRef = useRef<HTMLDivElement>(null);

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

      const cards = sectionRef.current?.querySelectorAll('.satellite-card');
      if (cards) {
        gsap.fromTo(
          cards,
          { opacity: 0, y: 60 },
          {
            opacity: 1,
            y: 0,
            duration: 0.8,
            stagger: 0.2,
            ease: 'power3.out',
            scrollTrigger: {
              trigger: cards[0],
              start: 'top 80%',
            },
          }
        );
      }
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section
      ref={sectionRef}
      id="satellites"
      className="relative section-padding overflow-hidden"
      style={{
        background: '#0a0a0f',
      }}
    >
      {/* Star dots background */}
      <div
        className="absolute inset-0 opacity-20"
        style={{
          backgroundImage: `radial-gradient(circle at 20% 30%, rgba(200, 164, 244, 0.3) 1px, transparent 1px),
                           radial-gradient(circle at 80% 70%, rgba(200, 164, 244, 0.2) 1px, transparent 1px),
                           radial-gradient(circle at 50% 50%, rgba(244, 164, 192, 0.2) 1px, transparent 1px),
                           radial-gradient(circle at 30% 80%, rgba(200, 164, 244, 0.15) 1px, transparent 1px),
                           radial-gradient(circle at 70% 20%, rgba(244, 164, 192, 0.15) 1px, transparent 1px)`,
          backgroundSize: '200px 200px, 300px 300px, 250px 250px, 350px 350px, 400px 400px',
        }}
      />

      {/* Constellation SVG */}
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none hidden lg:block"
        style={{ zIndex: 0 }}
      >
        <line
          x1="25%"
          y1="55%"
          x2="50%"
          y2="55%"
          stroke="rgba(200, 164, 244, 0.1)"
          strokeWidth="1"
          strokeDasharray="4 4"
          className="animate-dash-flow"
        />
        <line
          x1="50%"
          y1="55%"
          x2="75%"
          y2="55%"
          stroke="rgba(200, 164, 244, 0.1)"
          strokeWidth="1"
          strokeDasharray="4 4"
          className="animate-dash-flow"
        />
        <circle cx="25%" cy="55%" r="4" fill="#c8a4f4" className="animate-pulse-glow" />
        <circle cx="50%" cy="55%" r="5" fill="#c8a4f4" className="animate-pulse-glow" />
        <circle cx="75%" cy="55%" r="4" fill="#c8a4f4" className="animate-pulse-glow" />
      </svg>

      <div className="content-max mx-auto relative z-10">
        {/* Header */}
        <div ref={headerRef} className="text-center mb-16">
          <p className="eyebrow mb-4">SATELLITES</p>
          <h2 className="display-heading text-[clamp(36px,5vw,72px)]">
            Always Within Reach
          </h2>
        </div>

        {/* Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-[1000px] mx-auto">
          {SATELLITES.map((sat, i) => (
            <SatelliteCard key={i} satellite={sat} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}
