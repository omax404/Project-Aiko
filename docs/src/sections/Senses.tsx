import { useEffect, useRef, useCallback } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Eye, Mic, Volume2, User } from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

const SENSES = [
  {
    icon: Eye,
    title: 'She Sees You',
    subtitle: 'Gemma-4 Vision',
    description:
      'Multimodal image analysis \u2014 photos, screenshots, memes. She understands what she sees.',
    color: '#c8a4f4',
  },
  {
    icon: Mic,
    title: 'She Hears You',
    subtitle: 'Moonshine STT',
    description:
      'Discord voice message transcription with local speech recognition. She listens to every word.',
    color: '#f4a4c0',
  },
  {
    icon: Volume2,
    title: 'She Speaks to You',
    subtitle: 'Pocket-TTS',
    description:
      'Local voice synthesis with cloning from audio samples. Full-message chunked TTS with emotion-driven modulation.',
    color: '#ff6b35',
  },
  {
    icon: User,
    title: 'She Shows You How She Feels',
    subtitle: 'Live2D',
    description:
      'Smooth animations driven by her current emotional state. Every expression reflects her inner world.',
    color: '#a8d8ea',
  },
];

function SenseCard({
  sense,
  index,
}: {
  sense: (typeof SENSES)[0];
  index: number;
}) {
  const cardRef = useRef<HTMLDivElement>(null);

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      const card = cardRef.current;
      if (!card) return;

      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;

      const rotateX = ((y - centerY) / centerY) * -8;
      const rotateY = ((x - centerX) / centerX) * 8;

      card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
      card.style.boxShadow = `0 0 30px ${sense.color}40`;
    },
    [sense.color]
  );

  const handleMouseLeave = useCallback(() => {
    const card = cardRef.current;
    if (!card) return;
    card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg)';
    card.style.boxShadow = 'none';
  }, []);

  return (
    <div
      ref={cardRef}
      className="sense-card glass-card p-8 flex flex-col transition-all duration-300 ease-out"
      style={{
        transformStyle: 'preserve-3d',
        marginTop: index % 2 === 1 ? '40px' : '0',
      }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      <div
        className="w-14 h-14 rounded-xl flex items-center justify-center mb-6"
        style={{ backgroundColor: `${sense.color}15` }}
      >
        <sense.icon size={28} style={{ color: sense.color }} />
      </div>
      <h3 className="font-display text-xl text-moonlight mb-1">{sense.title}</h3>
      <code
        className="font-mono text-xs mb-4"
        style={{ color: sense.color }}
      >
        {sense.subtitle}
      </code>
      <p className="font-body text-moonlight/60 text-sm leading-relaxed">
        {sense.description}
      </p>
    </div>
  );
}

export default function Senses() {
  const sectionRef = useRef<HTMLElement>(null);
  const headerRef = useRef<HTMLDivElement>(null);

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
      const cards = sectionRef.current?.querySelectorAll('.sense-card');
      if (cards) {
        gsap.fromTo(
          cards,
          { opacity: 0, y: 50, rotateX: 10 },
          {
            opacity: 1,
            y: 0,
            rotateX: 0,
            duration: 0.8,
            stagger: 0.15,
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
      id="senses"
      className="relative section-padding"
      style={{
        background: 'linear-gradient(to bottom, #0a0a0f, rgba(45, 27, 78, 0.08), #0a0a0f)',
      }}
    >
      <div className="content-max mx-auto">
        {/* Header */}
        <div ref={headerRef} className="text-center mb-16">
          <p className="eyebrow mb-4">SENSES</p>
          <h2 className="display-heading text-[clamp(36px,5vw,72px)]">
            She Sees. She Hears. She Speaks.
          </h2>
        </div>

        {/* Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-[900px] mx-auto">
          {SENSES.map((sense, i) => (
            <SenseCard key={i} sense={sense} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}
