"use client";

import { useEffect } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useReducedMotion } from "@/hooks/useReducedMotion";

/**
 * Orchestrated GSAP ScrollTrigger reveals for [data-reveal] elements.
 * Complements Framer Motion section components with timeline-driven polish.
 */
export function ScrollOrchestrator() {
  const reduced = useReducedMotion();

  useEffect(() => {
    if (reduced) return;
    gsap.registerPlugin(ScrollTrigger);

    const lenis = (window as unknown as { __lenis?: { on: Function; off: Function; raf: Function } }).__lenis;
    if (lenis) {
      lenis.on("scroll", ScrollTrigger.update);
    }

    const ctx = gsap.context(() => {
      gsap.utils.toArray<HTMLElement>("[data-reveal]").forEach((el) => {
        const delay = Number(el.dataset.revealDelay ?? 0);
        gsap.fromTo(
          el,
          { autoAlpha: 0, y: 40, filter: "blur(6px)" },
          {
            autoAlpha: 1,
            y: 0,
            filter: "blur(0px)",
            duration: 1.05,
            delay,
            ease: "power3.out",
            scrollTrigger: {
              trigger: el,
              start: "top 88%",
              toggleActions: "play none none none",
            },
          },
        );
      });

      gsap.utils.toArray<HTMLElement>("[data-parallax]").forEach((el) => {
        const speed = Number(el.dataset.parallax ?? 0.15);
        gsap.to(el, {
          y: () => speed * 120,
          ease: "none",
          scrollTrigger: {
            trigger: el,
            start: "top bottom",
            end: "bottom top",
            scrub: true,
          },
        });
      });
    });

    return () => {
      if (lenis) lenis.off("scroll", ScrollTrigger.update);
      ctx.revert();
    };
  }, [reduced]);

  return null;
}
