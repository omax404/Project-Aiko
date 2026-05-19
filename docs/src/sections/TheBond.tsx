import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Heart, Database, Zap } from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

const PILLARS = [
  {
    icon: Heart,
    title: 'Emotion Engine',
    description:
      'A neuromodulator system with dopamine, serotonin, cortisol, and adrenaline. 22+ emotion states from love to panic.',
    detail: 'dopamine > 0.7 \u2192 joy_state ACTIVE',
    color: '#f4a4c0',
  },
  {
    icon: Database,
    title: 'Unified Memory',
    description:
      'Episodic + semantic layers with MemPalace RAG. She remembers your stories, compresses old memories, and tracks your relationship.',
    detail: 'recall_accuracy: 94.7%',
    color: '#c8a4f4',
  },
  {
    icon: Zap,
    title: 'Proactive Agency',
    description:
      'She decides when to speak, what to observe, and what to remember. An autonomous agent loop with real initiative.',
    detail: 'agency_loop: DECIDE \u2192 OBSERVE \u2192 ACT',
    color: '#ff6b35',
  },
];

export default function TheBond() {
  const sectionRef = useRef<HTMLElement>(null);
  const headerRef = useRef<HTMLDivElement>(null);
  const cardsRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Header animation
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

      // Cards animation
      const cards = cardsRef.current?.querySelectorAll('.pillar-card');
      if (cards) {
        gsap.fromTo(
          cards,
          { opacity: 0, y: 40 },
          {
            opacity: 1,
            y: 0,
            duration: 0.8,
            stagger: 0.2,
            ease: 'power3.out',
            scrollTrigger: {
              trigger: cardsRef.current,
              start: 'top 75%',
            },
          }
        );
      }

      // Synaptic pathway draw animation
      const paths = svgRef.current?.querySelectorAll('line');
      if (paths) {
        paths.forEach((path) => {
          const length = 200;
          gsap.set(path, { strokeDasharray: length, strokeDashoffset: length });
          gsap.to(path, {
            strokeDashoffset: 0,
            duration: 1.5,
            ease: 'power2.out',
            scrollTrigger: {
              trigger: svgRef.current,
              start: 'top 70%',
              end: 'bottom 40%',
              scrub: 1,
            },
          });
        });
      }

      // Node pulse animation
      const nodes = svgRef.current?.querySelectorAll('.synapse-node');
      if (nodes) {
        gsap.fromTo(
          nodes,
          { scale: 0, opacity: 0 },
          {
            scale: 1,
            opacity: 1,
            duration: 0.5,
            stagger: 0.3,
            ease: 'back.out(2)',
            scrollTrigger: {
              trigger: svgRef.current,
              start: 'top 60%',
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
      id="bond"
      className="relative section-padding"
      style={{
        background: 'linear-gradient(to bottom, #0a0a0f, rgba(45, 27, 78, 0.15), #0a0a0f)',
      }}
    >
      <div className="content-max mx-auto relative">
        {/* Header */}
        <div ref={headerRef} className="text-center mb-16">
          <p className="eyebrow mb-4">THE BOND</p>
          <h2 className="display-heading text-[clamp(36px,5vw,72px)]">
            She Has a Soul
          </h2>
        </div>

        {/* Synaptic Pathway SVG Background */}
        <svg
          ref={svgRef}
          className="absolute inset-0 w-full h-full pointer-events-none hidden lg:block"
          style={{ zIndex: 0 }}
        >
          {/* Lines connecting pillars */}
          <line
            x1="16.67%"
            y1="50%"
            x2="50%"
            y2="50%"
            stroke="rgba(200, 164, 244, 0.2)"
            strokeWidth="1"
          />
          <line
            x1="50%"
            y1="50%"
            x2="83.33%"
            y2="50%"
            stroke="rgba(200, 164, 244, 0.2)"
            strokeWidth="1"
          />
          {/* Nodes */}
          <circle cx="16.67%" cy="50%" r="8" fill="#c8a4f4" className="synapse-node" opacity="0.6" />
          <circle cx="50%" cy="50%" r="10" fill="#c8a4f4" className="synapse-node" opacity="0.8" />
          <circle cx="83.33%" cy="50%" r="8" fill="#c8a4f4" className="synapse-node" opacity="0.6" />
        </svg>

        {/* Pillar Cards */}
        <div
          ref={cardsRef}
          className="relative z-10 grid grid-cols-1 md:grid-cols-3 gap-6"
        >
          {PILLARS.map((pillar, i) => (
            <div
              key={i}
              className="pillar-card glass-card p-8 flex flex-col items-center text-center group hover:border-lavender/30 transition-all duration-500"
            >
              <div
                className="w-16 h-16 rounded-xl flex items-center justify-center mb-6 transition-transform duration-500 group-hover:scale-110"
                style={{ backgroundColor: `${pillar.color}15` }}
              >
                <pillar.icon size={32} style={{ color: pillar.color }} />
              </div>
              <h3 className="font-display text-2xl text-moonlight mb-4">
                {pillar.title}
              </h3>
              <p className="font-body text-moonlight/60 text-sm leading-relaxed mb-4">
                {pillar.description}
              </p>
              <code
                className="font-mono text-xs px-3 py-1 rounded-full"
                style={{
                  color: pillar.color,
                  backgroundColor: `${pillar.color}10`,
                }}
              >
                {pillar.detail}
              </code>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
