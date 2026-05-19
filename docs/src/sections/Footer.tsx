import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { ExternalLink } from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

const LINKS = [
  { label: 'Discord', href: '#' },
  { label: 'Wiki', href: '#' },
  { label: "Master's Profile", href: '#' },
];

export default function Footer() {
  const footerRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.fromTo(
        footerRef.current,
        { opacity: 0 },
        {
          opacity: 1,
          duration: 0.6,
          scrollTrigger: {
            trigger: footerRef.current,
            start: 'top 90%',
          },
        }
      );
    }, footerRef);

    return () => ctx.revert();
  }, []);

  return (
    <footer
      ref={footerRef}
      className="relative py-12 px-6"
      style={{
        background: 'linear-gradient(to bottom, #0a0a0f, #000000)',
      }}
    >
      <div className="content-max mx-auto text-center">
        {/* Star CTA */}
        <p className="font-display text-lg italic text-moonlight/40 mb-8">
          <span className="mr-2">
            <svg
              className="inline-block w-4 h-4 text-amber fill-current"
              viewBox="0 0 24 24"
            >
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
            </svg>
          </span>
          Star this repo if Aiko made you smile.
        </p>

        {/* Links */}
        <div className="flex justify-center gap-8 mb-8">
          {LINKS.map((link) => (
            <a
              key={link.label}
              href={link.href}
              className="flex items-center gap-1.5 text-sm text-lavender/70 hover:text-lavender transition-colors duration-300 hover:underline underline-offset-4"
            >
              {link.label}
              <ExternalLink size={12} />
            </a>
          ))}
        </div>

        {/* Copyright */}
        <p className="text-sm text-moonlight/20">
          Made with love by the Aiko Team &middot; MIT License
        </p>

        {/* Decorative bottom fade */}
        <div
          className="absolute bottom-0 left-0 right-0 h-px"
          style={{
            background: 'linear-gradient(to right, transparent, rgba(200, 164, 244, 0.3), transparent)',
          }}
        />
      </div>
    </footer>
  );
}
