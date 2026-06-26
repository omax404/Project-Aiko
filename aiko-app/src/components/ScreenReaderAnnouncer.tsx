import { useEffect, useRef } from 'react';

/**
 * ScreenReaderAnnouncer
 * Hidden aria-live region that announces dynamic content to screen readers.
 * Use announce() to notify users of state changes ("Aiko is typing", "Message sent", etc.).
 */
let _announce: (message: string, priority?: 'polite' | 'assertive') => void = () => {};

export function announce(message: string, priority: 'polite' | 'assertive' = 'polite') {
  _announce(message, priority);
}

export function ScreenReaderAnnouncer() {
  const politeRef = useRef<HTMLDivElement>(null);
  const assertiveRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    _announce = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
      const ref = priority === 'assertive' ? assertiveRef : politeRef;
      if (ref.current) {
        // Clear then set to force announcement even if same message
        ref.current.textContent = '';
        requestAnimationFrame(() => {
          if (ref.current) ref.current.textContent = message;
        });
      }
    };
  }, []);

  return (
    <div className="sr-only" aria-hidden="false">
      <div
        ref={politeRef}
        aria-live="polite"
        aria-atomic="true"
        className="absolute -z-10 w-px h-px overflow-hidden"
      />
      <div
        ref={assertiveRef}
        aria-live="assertive"
        aria-atomic="true"
        className="absolute -z-10 w-px h-px overflow-hidden"
      />
    </div>
  );
}
