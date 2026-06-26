# Aiko UI Polish — Professional Audit & Fix Plan

## Why It Looks Like "AI Slop"

### 1. 🛑 Inline Styles EVERYWHERE (The #1 Tell)
**Problem:** `App.tsx` TitleBar has ~100 lines of inline `style={{...}}` objects with hardcoded hex values.
```tsx
style={{ width: 38, height: 48, background: 'transparent', border: 'none',
  cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
  color: 'rgba(255,255,255,0.35)', transition: 'background 100ms, color 100ms' }}
```
This is how AI generates code when it can't use a design system. Every pixel is micromanaged. No human writes CSS like this.

**Fix:** Replace with Tailwind classes or a dedicated `TitleBar` styled component.

---

### 2. 🎨 Color Chaos (5 Different Naming Conventions for the Same Color)
The warm accent color appears as:
- `rgba(212,149,106,0.4)` — inline hex with opacity
- `var(--acc)` — CSS custom property (pink)
- `var(--acc2)` — purple
- `pink-500` — Tailwind pink
- `text-[var(--t3)]` — text token
- `bg-[rgba(212,149,106,0.03)]` — arbitrary value
- `border-[var(--b1)]` — border token
- `shadow-[0_0_15px_rgba(212,149,106,0.1)]` — shadow
- `#ec4899` — hardcoded hex (Tailwind pink-500)

**The palette is:** dark brown + neon pink + warm tan + purple + green status + slate gray. That's 6 competing colors with no hierarchy.

**Fix:** Pick ONE accent color family. Warm gold/tan OR neon pink. Not both. Define 3 semantic tokens: `primary`, `secondary`, `muted`.

---

### 3. 🔬 Typography at Microscopic Sizes
**Current sizes:** 6.5px, 7px, 8px, 9px, 10px, 11px, 12px, 13px, 15px

6.5px is smaller than the minimum legal font size in most countries. It's unreadable on a 1080p screen. This is what happens when an AI tries to fit too many labels into a small UI.

**Fix:** Establish a type scale:
- `xs` = 11px (labels, badges)
- `sm` = 13px (body small, descriptions)
- `base` = 14px (body text)
- `lg` = 16px (chat messages)
- `xl` = 20px (headings)

---

### 4. ✨ Visual Effect Overload (Every Component Has 3+ Effects)
Every panel has: `backdrop-blur-md` + `border` + `shadow-[0_0_8px_...]` + `glow` + `animate-pulse` + `transition-all duration-500`

The eye has nowhere to rest. When everything glows, nothing glows.

**Fix:** Remove 80% of glows. Reserve effects for:
- Active/focused states only
- The primary accent element (the avatar ring)
- Status indicators (online dot)

---

### 5. 📊 Dashboard Sidebar Is a "Label Soup"
The right sidebar has 8+ tiny boxes with different border colors, all containing 8px uppercase text. It looks like a flight deck from a 1980s fighter jet, not a companion app.

**Fix:** Collapse into logical sections with breathing room. Use progressive disclosure (accordions) for advanced controls.

---

### 6. 🎛️ SettingsPanel Is a Generic Form
`SettingsPanel.tsx` looks like a Bootstrap form from 2014. No visual hierarchy, just stacked inputs with `text-[10px]` labels.

**Fix:** Group settings into cards with clear sections. Use proper form spacing (16px gaps, not 4px).

---

### 7. 🎭 Framer Motion Overuse
Every element has `motion.div` with `spring` physics. The sidebar bounces open, the chat bubbles fade in, the titlebar icons scale on hover. It's exhausting.

**Fix:** Use motion sparingly. Only animate:
- Sidebar collapse (smooth, not bouncy)
- Message appearance (subtle fade, not slide)
- Remove all `spring` physics — use `ease-out` transitions

---

### 8. 🪟 Custom Titlebar Looks Like a Cheap Winamp Skin
Manual SVG icons for window controls, inline hover handlers, hardcoded colors. It screams "I couldn't figure out native window controls."

**Fix:** If using a custom titlebar, make it look like **Windows 11** or **macOS Sonoma** — clean, minimal, dark. No more manual hover color transitions.

---

## Priority Fix List (Biggest Impact → Fastest)

| Priority | Fix | Files | Impact |
|----------|-----|-------|--------|
| 1 | **Kill inline styles in TitleBar** | `App.tsx` | 🔥 High — first thing users see |
| 2 | **Unify color palette** | `App.css`, all components | 🔥 High — fixes "cheap" look instantly |
| 3 | **Fix typography scale** | All components | 🔥 High — makes it readable |
| 4 | **Reduce glow/shadow noise** | Dashboard, ChatBubble | 🔥 High — gives it breathing room |
| 5 | **Polish SettingsPanel** | `SettingsPanel.tsx` | 🟡 Medium — users interact with this a lot |
| 6 | **Clean up NeuralControlPanel** | `NeuralControlPanel.tsx` | 🟡 Medium — dense label soup |
| 7 | **Fix framer-motion overuse** | `App.tsx`, `ChatBubble` | 🟡 Medium — less bouncy |
| 8 | **Mascot polish** | `MascotApp.tsx` | 🟢 Low — only used in overlay mode |

---

## Target Design System (What We Should Move Toward)

### Colors (3-color system)
```css
--surface-0: #0c0b0a;      /* Deepest background */
--surface-1: #141210;      /* Cards, panels */
--surface-2: #1c1916;      /* Elevated items */
--surface-3: #252220;      /* Hover states */
--text-primary: #f0ebe3;   /* Main text */
--text-secondary: #9a8f7e; /* Descriptions, labels */
--text-muted: #5a5248;     /* Placeholders, disabled */
--accent: #e8a87c;         /* Warm gold (replaces neon pink) */
--accent-dim: #e8a87c33;   /* Accent at 20% opacity */
--accent-glow: #e8a87c40;  /* Accent at 25% opacity */
--status-online: #4ade80;  /* Green */
--status-offline: #ef4444; /* Red */
--border: rgba(255,255,255,0.06);  /* All borders */
--border-focus: rgba(232,168,124,0.25); /* Focused borders */
```

### Typography
- **Font:** `Inter` (not Pixelify Sans + Orbitron + DM Sans + JetBrains Mono — that's 4 fonts for one app)
- **Scale:** 11px / 13px / 14px / 16px / 20px
- **No more `text-[9px]` or `text-[6.5px]`**

### Spacing
- **Base unit:** 4px
- **Section gap:** 16px (not 2px, 3px, 6px, 10px, 12px all mixed)
- **Card padding:** 12px–16px
- **Form gap:** 16px between fields, 8px between label and input

### Effects (Reduced by 80%)
- **Glow:** Only on avatar ring and active status dot
- **Shadow:** Subtle `0 2px 8px rgba(0,0,0,0.3)` for floating panels
- **Border:** Single `rgba(255,255,255,0.06)` for all cards
- **No more `animate-pulse` on everything**

---

*Generated for Aiko Desktop UI professionalization.*
