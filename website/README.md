# Aiko Marketing Site

Premium marketing website for [Project-Aiko](https://github.com/omax404/Project-Aiko) — a self-hosted, emotionally-intelligent local AI companion.

## Stack

- **Next.js 16** (App Router) + TypeScript
- **Tailwind CSS v4**
- **Framer Motion** — section reveals, magnetic UI, cursor
- **Three.js / React Three Fiber** — signature neuromodulator particle field
- **Lenis** — smooth scrolling

## Design system

| Token | Hex | Role |
|-------|-----|------|
| `void` | `#0B0810` | Page background |
| `plum` | `#1C1320` | Elevated surfaces |
| `midnight` | `#2A1B30` | Cards / panels |
| `lavender` | `#C9A8D9` | Primary brand |
| `mist` | `#E8DDF0` | Soft light text |
| `bloom` | `#F2A7C3` | Emotional accent |

**Type:** Fraunces (display) + Outfit (body) + JetBrains Mono (code)

## Signature moment

The hero **Emotion Field** is a WebGL particle system driven by live neuromodulator values (dopamine / serotonin / cortisol / adrenaline). Switching emotional states in the hero recolors, expands, jitter, and pulses the field — the same conceptual model as Aiko’s emotion engine.

## Develop

```bash
cd website
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Build & deploy

```bash
npm run build
npm start
```

Deploy the `website` folder to Vercel (root directory: `website`). No env vars required.

## Structure

```
src/
  app/                 # layout, page, globals
  components/
    three/             # EmotionField (R3F)
    sections/          # Hero → Footer
    ui/                # cursor, magnetic btn, glass cards
    providers/         # Lenis, emotion state
  lib/content.ts       # Real product copy from Project-Aiko README
```
