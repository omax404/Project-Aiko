---
name: Project Aiko
description: Devoted Neural Companion — Warm Cyber-Sakura & Tactile Minimalist UI
colors:
  primary: "#b49bf0"
  primary-hover: "#c8b4f8"
  primary-deep: "#8e6ed6"
  neutral-bg: "#0b0a10"
  neutral-surface: "#14121b"
  neutral-elevated: "#1b1825"
  neutral-card: "#181521"
  neutral-border: "rgba(247, 244, 252, 0.08)"
  neutral-border-subtle: "rgba(247, 244, 252, 0.04)"
  text-high: "#f7f4fc"
  text-medium: "#c5bdd4"
  text-muted: "#948aab"
  text-subtle: "#73688b"
  status-online: "#34d399"
  status-warn: "#fbbf24"
  status-err: "#f87171"
typography:
  display:
    fontFamily: "'Sora', system-ui, -apple-system, sans-serif"
    fontSize: "2.75rem"
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "-0.03em"
  headline:
    fontFamily: "'Sora', system-ui, -apple-system, sans-serif"
    fontSize: "1.75rem"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "-0.02em"
  title-lg:
    fontFamily: "'Sora', system-ui, -apple-system, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "-0.01em"
  title:
    fontFamily: "'DM Sans', system-ui, -apple-system, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 600
    lineHeight: 1.35
    letterSpacing: "-0.01em"
  body-lg:
    fontFamily: "'DM Sans', system-ui, -apple-system, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "0em"
  body:
    fontFamily: "'DM Sans', system-ui, -apple-system, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "0em"
  body-sm:
    fontFamily: "'DM Sans', system-ui, -apple-system, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "0em"
  label:
    fontFamily: "'DM Sans', system-ui, -apple-system, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: "0.02em"
  code:
    fontFamily: "'JetBrains Mono', ui-monospace, monospace"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "0em"
rounded:
  sm: "6px"
  md: "10px"
  lg: "16px"
  xl: "24px"
  full: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  2xl: "48px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.neutral-bg}"
    rounded: "{rounded.md}"
    padding: "10px 20px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-secondary:
    backgroundColor: "{colors.neutral-elevated}"
    textColor: "{colors.text-high}"
    rounded: "{rounded.md}"
    padding: "10px 18px"
  card-base:
    backgroundColor: "{colors.neutral-card}"
    rounded: "{rounded.lg}"
    padding: "20px"
---

## Overview

Project Aiko's visual language is **Warm Cyber-Sakura & Tactile Minimalist**. It rejects common AI tropes—such as neon purple chromatic halos, fake gridlines, gradient-masked headings, and unreadable 8px micro-labels. Instead, it balances high-clarity typography with physical tactile depth, subtle organic warmth, and accessible contrast.

## Colors

- **Primary Accent (`#b49bf0`)**: An intentional, warm wisteria/sakura violet. Used sparingly for interactive affordances, active tabs, and primary action buttons.
- **Deep Slate Backgrounds (`#0b0a10` → `#14121b` → `#1b1825`)**: Neutral deep carbon and dark obsidian surfaces that create natural depth without high-saturation purple backwashes.
- **Text & Contrast Contracts**:
  - `text-high` (`#f7f4fc`): High-contrast primary reading text (14:1 contrast ratio against base backgrounds).
  - `text-medium` (`#c5bdd4`): Secondary descriptions and content paragraphs (8:1 contrast ratio).
  - `text-muted` (`#948aab`): Metadata, timestamps, and active status labels (5:1 contrast ratio, strictly exceeding WCAG AA 4.5:1).
  - Minimum functional text size: **11px**; minimum body/chat text size: **14px**.

## Typography

- **Headings & Display**: Space Grotesk. Distinctive geometric character with editorial proportion, rendered in solid high-contrast ink (no gradient clipping).
- **Body & Controls**: Inter. Crisp readability, natural line height (1.5–1.6), and clear optical tracking.
- **Technical & Metrics**: JetBrains Mono. Tabular figures and telemetry in diagnostics and code blocks.

## Layout

- Desktop App operates in two responsive modes:
  1. **Full Workspace**: Balanced 3-column layout (Collapsible Nav, Live2D Character Stage, Neural Chat / Diagnostic Dock).
  2. **Floating Companion (Pet Mode)**: Compact borderless viewport with transparent backing, floating Live2D model, and minimal HUD.
- The documentation / landing page uses single-column editorial sections with comfortable max-widths (`1120px`), generous breathing room (`48px–96px` vertical rhythm), and clear visual hierarchy.

## Elevation & Depth

- **Tactile Borders**: 1px crisp hairlines (`rgba(247, 244, 252, 0.08)`) define boundaries rather than heavy neon drop-shadows.
- **Directional Shadows**: Neutral vertical drop-shadows (`box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45)`) that simulate a physical overhead light source.
- Zero-offset chromatic halos (e.g. `box-shadow: 0 0 20px #9b6bff`) are banned.

## Shapes

- Smooth squircle-like radius curves:
  - Small tags/badges: `6px`
  - Action buttons and inputs: `10px`
  - Component cards and dialogs: `16px`–`24px`
- Consistent inner vs outer border-radius nesting: outer radius equals inner radius plus padding.

## Components

- **Action Buttons**: Solid, tactile backgrounds with clear hover transitions (`140ms cubic-bezier(0.16, 1, 0.3, 1)`).
- **Status Pills**: Pill indicators feature clean, steady green/amber/red indicators with real semantic text (no decorative fake infinite pulsing dots).
- **Diagnostics Cards**: High-contrast tables with monospace telemetry and 1-click remediation triggers.

## Do's and Don'ts

### Do
- Use solid, crisp white/cream colors on headings for maximum punch and legibility.
- Keep all interactive labels and meta tags at 11px or higher.
- Structure layouts with clear spacing rhythms (multiples of 8px).
- Provide immediate visual feedback for all hover, active, and focus states.

### Don't
- Don't use `background-clip: text` gradient fills on headings.
- Don't use decorative tiled grid backgrounds (`linear-gradient` lattices).
- Don't use zero-offset neon glow halos on buttons or cards.
- Don't saturate body copy with robotic em-dashes (`—`). Use crisp, concise sentence structure.
