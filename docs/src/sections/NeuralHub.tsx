import { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Cpu, Eye, Satellite, Plug, ChevronDown } from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

const NODES = [
  {
    id: 'neural',
    icon: Cpu,
    label: 'Neural Hub',
    sublabel: 'Port 8000',
    color: '#e94560',
    size: 'large',
    position: 'center',
    details: [
      { name: 'Chat Engine', desc: 'ReAct Agent + LLM' },
      { name: 'Emotion Engine', desc: 'Neuromodulator system' },
      { name: 'Unified Memory', desc: 'RAG + MemPalace' },
      { name: 'Persona Layer', desc: 'Character + Mood' },
    ],
  },
  {
    id: 'senses',
    icon: Eye,
    label: 'Senses',
    sublabel: 'Vision \u00b7 Hearing \u00b7 Voice',
    color: '#0f3460',
    size: 'normal',
    position: 'left',
    details: [
      { name: 'Vision', desc: 'Gemma-4 Multimodal' },
      { name: 'Hearing', desc: 'Moonshine STT' },
      { name: 'Voice', desc: 'Pocket-TTS' },
    ],
  },
  {
    id: 'satellites',
    icon: Satellite,
    label: 'Satellites',
    sublabel: 'Discord \u00b7 Telegram \u00b7 Desktop',
    color: '#533483',
    size: 'normal',
    position: 'right',
    details: [
      { name: 'Discord Bot', desc: 'messages + images' },
      { name: 'Telegram Bot', desc: 'messages' },
      { name: 'Desktop', desc: 'WebSocket connection' },
    ],
  },
  {
    id: 'plugins',
    icon: Plug,
    label: 'Plugins',
    sublabel: 'MCP \u00b7 Games \u00b7 Spotify',
    color: '#e94560',
    size: 'normal',
    position: 'bottom',
    details: [
      { name: 'Plugin Manager', desc: 'Dynamic discovery' },
      { name: 'Game Plugin', desc: 'Minecraft/Factorio' },
      { name: 'Spotify Plugin', desc: 'Music awareness' },
      { name: 'MCP Plugin', desc: 'File system tools' },
    ],
  },
];

export default function NeuralHub() {
  const sectionRef = useRef<HTMLElement>(null);
  const headerRef = useRef<HTMLDivElement>(null);
  const diagramRef = useRef<HTMLDivElement>(null);
  const [expandedNode, setExpandedNode] = useState<string | null>(null);

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

      // Nodes entrance
      const nodes = diagramRef.current?.querySelectorAll('.hub-node');
      if (nodes) {
        // Central node first
        gsap.fromTo(
          nodes[0],
          { opacity: 0, scale: 0.8 },
          {
            opacity: 1,
            scale: 1,
            duration: 0.6,
            ease: 'power3.out',
            scrollTrigger: {
              trigger: diagramRef.current,
              start: 'top 75%',
            },
          }
        );

        // Surrounding nodes
        gsap.fromTo(
          Array.from(nodes).slice(1),
          { opacity: 0, scale: 0.8 },
          {
            opacity: 1,
            scale: 1,
            duration: 0.6,
            stagger: 0.15,
            ease: 'power3.out',
            scrollTrigger: {
              trigger: diagramRef.current,
              start: 'top 70%',
            },
          }
        );
      }

      // Connection lines
      const lines = diagramRef.current?.querySelectorAll('.connection-line');
      if (lines) {
        lines.forEach((line) => {
          gsap.fromTo(
            line,
            { strokeDashoffset: 200 },
            {
              strokeDashoffset: 0,
              duration: 1,
              ease: 'power2.out',
              scrollTrigger: {
                trigger: diagramRef.current,
                start: 'top 65%',
              },
            }
          );
        });
      }
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  const toggleNode = (id: string) => {
    setExpandedNode(expandedNode === id ? null : id);
  };

  const node = NODES.find((n) => n.id === expandedNode);

  return (
    <section
      ref={sectionRef}
      id="neural-hub"
      className="relative section-padding"
      style={{
        background: `
          linear-gradient(to bottom, #0a0a0f, rgba(45, 27, 78, 0.05)),
          url('/images/portrait-guardian.png')`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundBlendMode: 'overlay',
      }}
    >
      {/* Overlay to dim the background */}
      <div className="absolute inset-0 bg-obsidian/95" />

      <div className="content-max mx-auto relative z-10">
        {/* Header */}
        <div ref={headerRef} className="text-center mb-16">
          <p className="eyebrow mb-4">NEURAL HUB</p>
          <h2 className="display-heading text-[clamp(36px,5vw,72px)]">
            The Architecture of Her Mind
          </h2>
        </div>

        {/* Architecture Diagram */}
        <div ref={diagramRef} className="relative max-w-[700px] mx-auto">
          {/* Connection Lines SVG */}
          <svg
            className="absolute inset-0 w-full h-full pointer-events-none"
            style={{ zIndex: 0 }}
            viewBox="0 0 700 500"
            preserveAspectRatio="xMidYMid meet"
          >
            {/* Neural Hub to Senses */}
            <line
              x1="350"
              y1="180"
              x2="150"
              y2="250"
              stroke="rgba(233, 69, 96, 0.3)"
              strokeWidth="2"
              strokeDasharray="200"
              className="connection-line"
            />
            {/* Neural Hub to Satellites */}
            <line
              x1="350"
              y1="180"
              x2="550"
              y2="250"
              stroke="rgba(233, 69, 96, 0.3)"
              strokeWidth="2"
              strokeDasharray="200"
              className="connection-line"
            />
            {/* Neural Hub to Plugins */}
            <line
              x1="350"
              y1="220"
              x2="350"
              y2="380"
              stroke="rgba(233, 69, 96, 0.3)"
              strokeWidth="2"
              strokeDasharray="200"
              className="connection-line"
            />

            {/* Data packet animations */}
            <circle r="4" fill="#e94560">
              <animateMotion
                dur="2s"
                repeatCount="indefinite"
                path="M350,180 L150,250"
              />
            </circle>
            <circle r="4" fill="#e94560">
              <animateMotion
                dur="2.5s"
                repeatCount="indefinite"
                path="M350,180 L550,250"
              />
            </circle>
            <circle r="4" fill="#e94560">
              <animateMotion
                dur="3s"
                repeatCount="indefinite"
                path="M350,220 L350,380"
              />
            </circle>
          </svg>

          {/* Nodes Grid */}
          <div className="relative grid grid-cols-3 gap-4" style={{ minHeight: '400px' }}>
            {/* Senses - left */}
            <div className="flex items-center justify-center" style={{ paddingTop: '60px' }}>
              <NodeCard node={NODES[1]} onClick={() => toggleNode('senses')} />
            </div>

            {/* Neural Hub - center top */}
            <div className="flex items-start justify-center">
              <NodeCard node={NODES[0]} onClick={() => toggleNode('neural')} />
            </div>

            {/* Satellites - right */}
            <div className="flex items-center justify-center" style={{ paddingTop: '60px' }}>
              <NodeCard node={NODES[2]} onClick={() => toggleNode('satellites')} />
            </div>

            {/* Plugins - center bottom */}
            <div className="col-start-2 flex items-end justify-center">
              <NodeCard node={NODES[3]} onClick={() => toggleNode('plugins')} />
            </div>
          </div>
        </div>

        {/* Detail Panel */}
        {node && (
          <div
            className="mt-8 glass-card p-6 max-w-[600px] mx-auto overflow-hidden"
            style={{
              animation: 'expandPanel 0.5s ease forwards',
            }}
          >
            <div className="flex items-center gap-3 mb-4">
              <node.icon size={24} style={{ color: node.color }} />
              <h4 className="font-display text-xl text-moonlight">{node.label} Modules</h4>
            </div>
            <div className="space-y-3">
              {node.details.map((detail, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between py-2 border-b border-white/5 last:border-0"
                  style={{
                    animation: `fadeSlideUp 0.3s ease ${i * 0.1 + 0.2}s both`,
                  }}
                >
                  <span className="font-mono text-sm text-moonlight">{detail.name}</span>
                  <span className="text-sm text-moonlight/50">{detail.desc}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <style>{`
        @keyframes expandPanel {
          from {
            opacity: 0;
            max-height: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            max-height: 400px;
            transform: translateY(0);
          }
        }
        @keyframes fadeSlideUp {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </section>
  );
}

function NodeCard({
  node,
  onClick,
}: {
  node: (typeof NODES)[0];
  onClick: () => void;
}) {
  return (
    <button
      className="hub-node glass-card p-5 flex flex-col items-center text-center gap-2 hover:scale-105 transition-transform duration-300"
      style={{
        width: node.size === 'large' ? '200px' : '160px',
        borderColor: `${node.color}30`,
      }}
      onClick={onClick}
    >
      <div
        className="w-10 h-10 rounded-lg flex items-center justify-center"
        style={{ backgroundColor: `${node.color}15` }}
      >
        <node.icon size={20} style={{ color: node.color }} />
      </div>
      <span className="font-display text-sm text-moonlight">{node.label}</span>
      <span className="font-mono text-[10px] text-moonlight/40">{node.sublabel}</span>
      <ChevronDown size={14} className="text-moonlight/30 mt-1" />
    </button>
  );
}
