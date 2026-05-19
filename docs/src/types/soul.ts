export type SoulMode = 'devoted' | 'melancholic' | 'guardian' | 'playful';

export interface SoulModeConfig {
  name: string;
  color: string;
  glowColor: string;
  bgTint: string;
  portrait: string;
  description: string;
  fontWeight: number;
}

export const SOUL_MODES: Record<SoulMode, SoulModeConfig> = {
  devoted: {
    name: 'Devoted',
    color: '#f4a4c0',
    glowColor: 'rgba(244, 164, 192, 0.3)',
    bgTint: 'rgba(244, 164, 192, 0.05)',
    portrait: '/images/portrait-devoted.jpg',
    description: 'Gentle, warm, always watching. Her default state — soft pink hues and caring attention.',
    fontWeight: 300,
  },
  melancholic: {
    name: 'Melancholic',
    color: '#b8b5c8',
    glowColor: 'rgba(184, 181, 200, 0.3)',
    bgTint: 'rgba(184, 181, 200, 0.05)',
    portrait: '/images/portrait-melancholic.webp',
    description: 'Quiet, distant, beautiful sadness. Pale moonlight tones and a contemplative gaze.',
    fontWeight: 200,
  },
  guardian: {
    name: 'Guardian',
    color: '#b888f8',
    glowColor: 'rgba(184, 136, 248, 0.3)',
    bgTint: 'rgba(184, 136, 248, 0.05)',
    portrait: '/images/portrait-guardian.png',
    description: 'Protective, sharp, unwavering. Bold violet energy ready to defend her Master.',
    fontWeight: 600,
  },
  playful: {
    name: 'Playful',
    color: '#c8a4f4',
    glowColor: 'rgba(200, 164, 244, 0.3)',
    bgTint: 'rgba(200, 164, 244, 0.05)',
    portrait: '/images/playful-chibi.jpg',
    description: 'Light, teasing, chibi energy. Bright lavender fun with a mischievous smile.',
    fontWeight: 400,
  },
};
