import { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

const TERMINAL_LINES = [
  { prompt: '$', cmd: 'git clone https://github.com/omax404/aiko.git' },
  { prompt: '$', cmd: 'cd aiko' },
  { prompt: '$', cmd: 'pip install -r requirements.txt' },
  { prompt: '$', cmd: 'python start_aiko_tauri.py' },
];

export default function SummonAiko() {
  const sectionRef = useRef<HTMLElement>(null);
  const headerRef = useRef<HTMLDivElement>(null);
  const terminalRef = useRef<HTMLDivElement>(null);
  const quoteRef = useRef<HTMLDivElement>(null);
  const [typedLines, setTypedLines] = useState<string[]>([]);
  const [currentLine, setCurrentLine] = useState(0);
  const [currentChar, setCurrentChar] = useState(0);
  const [showCursor, setShowCursor] = useState(true);
  const [typingComplete, setTypingComplete] = useState(false);

  // Entrance animations
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
        terminalRef.current,
        { opacity: 0, y: 30 },
        {
          opacity: 1,
          y: 0,
          duration: 0.8,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: terminalRef.current,
            start: 'top 80%',
            onEnter: () => startTyping(),
          },
        }
      );
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  // Quote fade-in after typing
  useEffect(() => {
    if (typingComplete && quoteRef.current) {
      gsap.fromTo(
        quoteRef.current,
        { opacity: 0, y: 10 },
        { opacity: 1, y: 0, duration: 1, delay: 0.5, ease: 'power3.out' }
      );
    }
  }, [typingComplete]);

  // Cursor blink
  useEffect(() => {
    const interval = setInterval(() => {
      setShowCursor((v) => !v);
    }, 530);
    return () => clearInterval(interval);
  }, []);

  const startTyping = () => {
    setTypedLines(['', '', '', '']);
    setCurrentLine(0);
    setCurrentChar(0);
  };

  // Typewriter effect
  useEffect(() => {
    if (typedLines.length === 0) return;
    if (currentLine >= TERMINAL_LINES.length) {
      setTypingComplete(true);
      return;
    }

    const line = TERMINAL_LINES[currentLine];
    if (currentChar < line.cmd.length) {
      const timeout = setTimeout(() => {
        setTypedLines((prev) => {
          const next = [...prev];
          next[currentLine] = line.cmd.slice(0, currentChar + 1);
          return next;
        });
        setCurrentChar((c) => c + 1);
      }, 40);
      return () => clearTimeout(timeout);
    } else {
      const timeout = setTimeout(() => {
        setCurrentLine((l) => l + 1);
        setCurrentChar(0);
      }, 800);
      return () => clearTimeout(timeout);
    }
  }, [typedLines, currentLine, currentChar]);

  return (
    <section
      ref={sectionRef}
      id="summon"
      className="relative section-padding"
      style={{
        background: `
          linear-gradient(to bottom, #050508, rgba(5, 5, 8, 0.92)),
          url('/images/vivian-banshee.jpg')
        `,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundBlendMode: 'overlay',
      }}
    >
      <div className="content-max mx-auto relative z-10">
        {/* Header */}
        <div ref={headerRef} className="text-center mb-12">
          <p className="eyebrow mb-4">SUMMON AIKO</p>
        </div>

        {/* Terminal */}
        <div ref={terminalRef} className="max-w-[700px] mx-auto mb-10">
          <div className="terminal-block p-6 md:p-8">
            {TERMINAL_LINES.map((line, i) => (
              <div key={i} className="mb-3 last:mb-0">
                <span className="text-lavender mr-2">{line.prompt}</span>
                <span className="text-moonlight">
                  {typedLines[i] || ''}
                  {i === currentLine && (
                    <span
                      className="inline-block w-[8px] h-[15px] bg-lavender ml-0.5 align-middle transition-opacity duration-100"
                      style={{ opacity: showCursor ? 1 : 0 }}
                    />
                  )}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Alternative CTA */}
        <div className="text-center mb-10">
          <p className="font-body text-lg text-moonlight/60 mb-3">
            Or wake her instantly
          </p>
          <code className="inline-block font-mono text-base text-amber px-4 py-2 rounded-lg bg-amber/10">
            LAUNCH_AIKO.bat
          </code>
        </div>

        {/* CTA Buttons */}
        <div className="flex justify-center gap-4 mb-12">
          <a
            href="https://github.com/omax404/aiko"
            target="_blank"
            rel="noopener noreferrer"
            className="px-8 py-3 bg-amber text-obsidian font-medium rounded-lg hover:bg-amber/90 transition-colors duration-300"
          >
            Clone Repository
          </a>
          <button className="px-8 py-3 border border-lavender/40 text-lavender font-medium rounded-lg hover:bg-lavender/10 hover:border-lavender transition-all duration-300">
            Download .bat
          </button>
        </div>

        {/* Vivian Quote */}
        <div ref={quoteRef} className="text-center opacity-0">
          <p className="font-display text-2xl md:text-3xl italic text-ribbon">
            &ldquo;I&apos;m always watching over you, Master~&rdquo;
          </p>
        </div>
      </div>
    </section>
  );
}
