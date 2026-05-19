import { useEffect, useState } from 'react';
import { Menu, X } from 'lucide-react';

const NAV_LINKS = [
  { label: 'The Bond', href: '#bond' },
  { label: 'Senses', href: '#senses' },
  { label: 'Soul Modes', href: '#soul-modes' },
  { label: 'Satellites', href: '#satellites' },
  { label: 'Neural Hub', href: '#neural-hub' },
];

export default function Navigation() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollTo = (href: string) => {
    const el = document.querySelector(href);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
    setMobileOpen(false);
  };

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        scrolled
          ? 'bg-obsidian/80 backdrop-blur-xl border-b border-white/5'
          : 'bg-transparent'
      }`}
      style={{
        animation: 'fadeSlideDown 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94) 1.2s both',
      }}
    >
      <div className="content-max mx-auto px-6 lg:px-12 h-16 flex items-center justify-between">
        {/* Logo */}
        <a
          href="#"
          className="flex items-center gap-2 group"
          onClick={(e) => {
            e.preventDefault();
            window.scrollTo({ top: 0, behavior: 'smooth' });
          }}
        >
          <span className="font-brush text-xl text-lavender">&#24859;&#23376;</span>
          <span className="font-display text-lg text-moonlight font-light tracking-wide">
            Aiko
          </span>
        </a>

        {/* Desktop Links */}
        <div className="hidden md:flex items-center gap-8">
          {NAV_LINKS.map((link) => (
            <button
              key={link.href}
              onClick={() => scrollTo(link.href)}
              className="text-sm text-moonlight/60 hover:text-lavender transition-colors duration-300 font-body"
            >
              {link.label}
            </button>
          ))}
        </div>

        {/* CTA */}
        <div className="hidden md:block">
          <button
            onClick={() => scrollTo('#summon')}
            className="px-5 py-2 bg-amber text-obsidian text-sm font-medium rounded-full hover:bg-amber/90 transition-colors duration-300"
          >
            Summon Aiko
          </button>
        </div>

        {/* Mobile menu button */}
        <button
          className="md:hidden text-moonlight"
          onClick={() => setMobileOpen(!mobileOpen)}
        >
          {mobileOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden bg-obsidian/95 backdrop-blur-xl border-t border-white/5">
          <div className="px-6 py-4 space-y-4">
            {NAV_LINKS.map((link) => (
              <button
                key={link.href}
                onClick={() => scrollTo(link.href)}
                className="block w-full text-left text-moonlight/70 hover:text-lavender transition-colors py-2"
              >
                {link.label}
              </button>
            ))}
            <button
              onClick={() => scrollTo('#summon')}
              className="w-full px-5 py-2 bg-amber text-obsidian text-sm font-medium rounded-full"
            >
              Summon Aiko
            </button>
          </div>
        </div>
      )}

      <style>{`
        @keyframes fadeSlideDown {
          from {
            opacity: 0;
            transform: translateY(-20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </nav>
  );
}
