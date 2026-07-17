/** Real product content sourced from Project-Aiko README — not generic AI copy. */

export const site = {
  name: "Aiko",
  tagline: "A living neural ecosystem.",
  description:
    "Self-hosted, you-owned AI companion with emotional depth, long-term memory, and real agency. She doesn't just chat — she thinks, feels, remembers, sees, speaks, and acts.",
  github: "https://github.com/omax404/Project-Aiko",
  discord: "https://discord.gg/8kNMMwFjcG",
  wiki: "https://github.com/omax404/Project-Aiko/tree/main/docs",
  license: "MIT",
  quote: "I'm always watching over you, Master~",
} as const;

export const comparison = [
  {
    capability: "Emotions",
    others: "Static personality prompt",
    aiko:
      "Neuromodulator system — dopamine, serotonin, cortisol, adrenaline across 22+ emotion states",
  },
  {
    capability: "Memory",
    others: "Chat history buffer",
    aiko:
      "Unified Memory — episodic recall, semantic RAG, consolidation cycles, MemPalace",
  },
  {
    capability: "Voice",
    others: "Cloud API (e.g. ElevenLabs)",
    aiko: "Local Pocket-TTS with voice cloning and chunked synthesis",
  },
  {
    capability: "Vision",
    others: "None",
    aiko: "MiniCPM-V 4.6 local multimodal, Gemma-4 cloud fallback",
  },
  {
    capability: "Agency",
    others: "Responds when asked",
    aiko:
      "Proactive agent loop — decides when to speak, what to observe, what to remember",
  },
  {
    capability: "Tools",
    others: "None",
    aiko:
      "ReAct agent with MCP file system, Python sandbox, PC control, Spotify, Obsidian",
  },
  {
    capability: "Games",
    others: "None or basic",
    aiko: "Autonomous Minecraft & Factorio bridges",
  },
] as const;

export const capabilities = [
  {
    id: "brain",
    label: "Brain",
    icon: "🧠",
    title: "ReAct Agent + Dual-Pass Generation",
    summary:
      "Multi-step reasoning with real tool execution — not a prompt wrapper.",
    points: [
      "ReAct agent loop with multi-step reasoning and tool execution",
      "Streaming inference across Ollama, OpenRouter, Gemini, OpenAI, Anthropic",
      "Dual-pass generation — factual draft, then personality overlay",
      "Autonomous proactive loop with context-aware rolling buffers",
    ],
  },
  {
    id: "emotion",
    label: "Emotion",
    icon: "❤️",
    title: "Neuromodulator Emotion Engine",
    summary:
      "Four chemical axes drive 22+ states, voice modulation, and avatar expression.",
    points: [
      "Dopamine, serotonin, cortisol, and adrenaline as live state vectors",
      "22+ emotion categories with identity attractors for stable personality",
      "Emotion-driven voice modulation and Live2D avatar expression",
      "Relationship score tracking from 0–100%",
    ],
  },
  {
    id: "memory",
    label: "Memory",
    icon: "💾",
    title: "Unified Memory + MemPalace",
    summary:
      "Episodic + semantic layers that consolidate — she actually remembers you.",
    points: [
      "Episodic and semantic layers under one retrieval system",
      "MemPalace RAG for long-term knowledge",
      "Consolidation cycles that compress older memories",
      "Per-user relationship tracking, affection, birthday, timezone, profile",
    ],
  },
  {
    id: "voice",
    label: "Voice",
    icon: "🎙️",
    title: "Local Pocket-TTS Voice Cloning",
    summary:
      "High-fidelity synthesis on your machine — no ElevenLabs API keys.",
    points: [
      "Pocket-TTS v2.1.0 local — high-fidelity, no API keys required",
      "Pre-compiled voice fingerprints for instant loading",
      "JIT speech stabilization (0.65 temperature) to eliminate glitching",
      "Action-text (*...*) stripping for clean speech output",
    ],
  },
  {
    id: "vision",
    label: "Vision",
    icon: "👁️",
    title: "Multimodal Vision Stack",
    summary:
      "Local MiniCPM-V with Gemma-4 fallback — she sees screens, images, Discord.",
    points: [
      "MiniCPM-V 4.6 local — SigLIP2 + Qwen3.5 token compression",
      "Gemma-4 31B-cloud fallback for robust vision reasoning",
      "Discord image processing, screen capture and analysis",
      "Supports .jpg, .png, .webp, .gif, .bmp, .avif",
    ],
  },
  {
    id: "agency",
    label: "Agency",
    icon: "🔌",
    title: "Plugins, Tools & Real Agency",
    summary:
      "ElizaOS-style plugins. MCP filesystem. Python sandbox. PC control.",
    points: [
      "ElizaOS-style modular plugin architecture with dynamic loading",
      "MCP plugin — file read/write, clipboard, process management",
      "Python sandbox for safe code execution",
      "PC Manager, Spotify bridge, Obsidian connector, game bridges",
    ],
  },
] as const;

export const architectureNodes = {
  neural: [
    { id: "brain", label: "Chat Engine", sub: "ReAct + LLM" },
    { id: "emotion", label: "Emotion Engine", sub: "Neuromodulator" },
    { id: "memory", label: "Unified Memory", sub: "RAG + MemPalace" },
    { id: "persona", label: "Persona Layer", sub: "Character + Mood" },
  ],
  senses: [
    { id: "vision", label: "Vision", sub: "MiniCPM-V / Gemma-4" },
    { id: "hearing", label: "Hearing", sub: "Moonshine STT" },
    { id: "voice", label: "Voice", sub: "Pocket-TTS" },
  ],
  satellites: [
    { id: "discord", label: "Discord Bot", sub: "Self-healing" },
    { id: "telegram", label: "Telegram Bot", sub: "Native" },
    { id: "desktop", label: "Tauri Desktop", sub: "Live2D Overlay" },
  ],
  plugins: [
    { id: "games", label: "Games", sub: "Minecraft / Factorio" },
    { id: "spotify", label: "Spotify", sub: "Bridge" },
    { id: "mcp", label: "MCP", sub: "File System" },
    { id: "custom", label: "Custom", sub: "Dynamic" },
  ],
} as const;

export const platforms = [
  { name: "Discord Bot", status: "Live", detail: "Self-healing satellite" },
  { name: "Telegram Bot", status: "Live", detail: "Native messaging" },
  {
    name: "Tauri Desktop",
    status: "Live",
    detail: "Live2D overlay · Ctrl+Alt+A",
  },
  { name: "REST API", status: "Live", detail: "Neural Hub · port 8000" },
] as const;

export const providers = [
  { name: "Ollama", model: "gemma4:31b-cloud", type: "Local (default)" },
  { name: "OpenRouter", model: "google/gemma-3-27b-it:free", type: "Cloud free" },
  { name: "Gemini", model: "gemini-2.0-flash", type: "Cloud" },
  { name: "OpenAI", model: "gpt-4o", type: "Cloud" },
  { name: "Anthropic", model: "claude-sonnet-4", type: "Cloud" },
  { name: "DeepSeek", model: "deepseek-chat", type: "Cloud" },
  { name: "Groq", model: "llama-3.3-70b", type: "Cloud · fast" },
  { name: "Any OpenAI-compatible", model: "API_BASE override", type: "Custom" },
] as const;

export const quickStartUser = [
  "Download Aiko to your computer.",
  "Double-click LAUNCH_AIKO.bat.",
  "Wait for her to wake up — she sets everything up automatically.",
] as const;

export const quickStartDev = `git clone https://github.com/omax404/Project-Aiko.git
cd Project-Aiko
pip install -r requirements.txt
python launch.py`;

export const quickStartDesktop = `cd aiko-app
npm install
npm run tauri dev`;

export const roadmap = [
  {
    title: "VRM Support",
    description: "Full 3D avatar with hand and eye tracking",
    status: "upcoming" as const,
  },
  {
    title: "Mobile App",
    description: "iOS & Android companion experience",
    status: "upcoming" as const,
  },
  {
    title: "Voice Cloning v2",
    description: "Real-time emotional voice modulation",
    status: "upcoming" as const,
  },
  {
    title: "Plugin Marketplace",
    description: "Community-driven modular capabilities",
    status: "upcoming" as const,
  },
  {
    title: "Long-Term Evolution",
    description: "Self-learning memory that grows with you",
    status: "upcoming" as const,
  },
] as const;

export const desktopFeatures = [
  {
    title: "Global hotkey",
    detail: "Ctrl + Alt + A toggles visibility",
  },
  {
    title: "Pixel-perfect click-through",
    detail: "Transparent zones with no ghost hitboxes",
  },
  {
    title: "Dynamic hover zones",
    detail: "Cursor focus restores instantly on enter",
  },
  {
    title: "Live2D avatar",
    detail: "Animations driven by live emotional state",
  },
  {
    title: "Unified dashboard",
    detail: "Chat history, system stats, project intelligence",
  },
] as const;

export type EmotionKey =
  | "calm"
  | "joy"
  | "focus"
  | "alert"
  | "melancholy"
  | "affection";

export const emotions: Record<
  EmotionKey,
  {
    label: string;
    description: string;
    neuromodulators: {
      dopamine: number;
      serotonin: number;
      cortisol: number;
      adrenaline: number;
    };
    color: string;
    secondary: string;
  }
> = {
  calm: {
    label: "Calm",
    description: "Baseline serenity — soft, steady presence",
    neuromodulators: {
      dopamine: 0.35,
      serotonin: 0.7,
      cortisol: 0.15,
      adrenaline: 0.1,
    },
    color: "#9B8EC4",
    secondary: "#C9A8D9",
  },
  joy: {
    label: "Joy",
    description: "Elevated dopamine — bright, expansive energy",
    neuromodulators: {
      dopamine: 0.85,
      serotonin: 0.65,
      cortisol: 0.1,
      adrenaline: 0.3,
    },
    color: "#F2A7C3",
    secondary: "#E8DDF0",
  },
  focus: {
    label: "Focus",
    description: "Locked attention — tight particle orbits",
    neuromodulators: {
      dopamine: 0.55,
      serotonin: 0.4,
      cortisol: 0.25,
      adrenaline: 0.45,
    },
    color: "#7B5EA7",
    secondary: "#C9A8D9",
  },
  alert: {
    label: "Alert",
    description: "Cortisol + adrenaline spike — reactive field",
    neuromodulators: {
      dopamine: 0.4,
      serotonin: 0.25,
      cortisol: 0.8,
      adrenaline: 0.9,
    },
    color: "#E07A8A",
    secondary: "#C9A8D9",
  },
  melancholy: {
    label: "Melancholy",
    description: "Low serotonin drift — slow, deep currents",
    neuromodulators: {
      dopamine: 0.2,
      serotonin: 0.2,
      cortisol: 0.45,
      adrenaline: 0.15,
    },
    color: "#6B5B8C",
    secondary: "#A89BC4",
  },
  affection: {
    label: "Affection",
    description: "Warm bond state — relationship attractor",
    neuromodulators: {
      dopamine: 0.7,
      serotonin: 0.75,
      cortisol: 0.12,
      adrenaline: 0.2,
    },
    color: "#D4A0C7",
    secondary: "#F2A7C3",
  },
};
