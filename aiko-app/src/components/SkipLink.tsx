import { useState } from 'react';

/**
 * SkipLink
 * Allows keyboard users to skip navigation and jump to main content.
 * Visible only when focused via keyboard.
 */
export function SkipLink({ targetId = "main-content", label = "Skip to main content" }: {
  targetId?: string;
  label?: string;
}) {
  const [visible, setVisible] = useState(false);

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    const target = document.getElementById(targetId);
    if (target) {
      target.focus();
      target.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <a
      href={`#${targetId}`}
      onClick={handleClick}
      onFocus={() => setVisible(true)}
      onBlur={() => setVisible(false)}
      className={`
        fixed top-3 left-3 z-[9999] px-4 py-2 rounded-lg text-[13px] font-medium
        bg-[var(--accent)] text-[var(--bg-base)] transition-all duration-200
        ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-4 pointer-events-none'}
      `}
    >
      {label}
    </a>
  );
}
