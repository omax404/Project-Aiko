import { useEffect, useState } from 'react';
import { getAuthHeaders, getHubUrl, resolveHubUrl } from './store/useNeuralStore';

/**
 * Custom background for Aiko's cinematic stage (the area behind the avatar).
 * Supports Scene Presets, Solid Colors, Gradients, Pictures, Animated GIFs, and Videos (.mp4/.webm/.mov),
 * plus Mood-Reactive ambient lighting.
 */
export type StageBgMode = 'default' | 'preset' | 'color' | 'gradient' | 'image' | 'video';

export interface StageScenePreset {
  id: string;
  name: string;
  subtitle: string;
  css: string;
  accentGlow: string;
}

export const STAGE_SCENE_PRESETS: StageScenePreset[] = [
  {
    id: 'cosmic-starfield',
    name: 'Cosmic Starfield',
    subtitle: 'Deep violet nebula & stardust',
    css: 'radial-gradient(ellipse at 50% 28%, #352056 0%, #171124 52%, #0b0812 100%)',
    accentGlow: 'rgba(168, 85, 247, 0.28)',
  },
  {
    id: 'sakura-twilight',
    name: 'Sakura Twilight',
    subtitle: 'Warm blossom pink & dusk indigo',
    css: 'radial-gradient(ellipse at 50% 25%, #5c244c 0%, #241332 55%, #0e0918 100%)',
    accentGlow: 'rgba(244, 114, 182, 0.30)',
  },
  {
    id: 'cyberpunk-neon',
    name: 'Cyberpunk Rain',
    subtitle: 'Neon cyan & magenta night city',
    css: 'radial-gradient(circle at 25% 25%, rgba(6, 182, 212, 0.28) 0%, transparent 45%), radial-gradient(circle at 78% 35%, rgba(217, 70, 239, 0.26) 0%, transparent 50%), linear-gradient(180deg, #090d1e 0%, #0f081d 60%, #06050c 100%)',
    accentGlow: 'rgba(34, 211, 238, 0.28)',
  },
  {
    id: 'cozy-lofi',
    name: 'Cozy Lo-Fi Study',
    subtitle: 'Warm amber lamp & espresso',
    css: 'radial-gradient(ellipse at 55% 30%, #4a2c1d 0%, #231612 55%, #0f0a09 100%)',
    accentGlow: 'rgba(251, 191, 36, 0.25)',
  },
  {
    id: 'emerald-sanctuary',
    name: 'Emerald Shrine',
    subtitle: 'Mystic forest jade & fireflies',
    css: 'radial-gradient(ellipse at 50% 25%, #134e4a 0%, #0b2228 55%, #060f14 100%)',
    accentGlow: 'rgba(52, 211, 153, 0.25)',
  },
  {
    id: 'midnight-ocean',
    name: 'Midnight Abyss',
    subtitle: 'Bioluminescent deep sea',
    css: 'radial-gradient(ellipse at 50% 30%, #1e3a8a 0%, #0f172a 55%, #050811 100%)',
    accentGlow: 'rgba(59, 130, 246, 0.28)',
  },
];

export interface UploadedStageMedia {
  filename: string;
  url: string;
  kind: 'image' | 'gif' | 'video';
  size: number;
  modified?: number;
}

export interface StageBg {
  mode: StageBgMode;
  presetId: string;
  color: string;       // solid colour / gradient end
  color2: string;      // gradient start
  image: string;       // URL or data URL of chosen picture / animated GIF
  video: string;       // URL of chosen video (.mp4 / .webm / .mov)
  mediaKind: 'image' | 'gif' | 'video';
  dim: number;         // 0-90, darkens the picture/video so Aiko stays readable
  blur: number;        // 0-30 px
  moodReactive: boolean; // shifts ambient stage glow with Aiko's current emotion
}

export const DEFAULT_STAGE_BG: StageBg = {
  mode: 'default',
  presetId: 'cosmic-starfield',
  color: '#171124',
  color2: '#301f4a',
  image: '',
  video: '',
  mediaKind: 'image',
  dim: 25,
  blur: 0,
  moodReactive: true,
};

const KEY = 'aiko.stageBackground.v1';
const EVENT = 'aiko-stage-bg-change';

function load(): StageBg {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) return { ...DEFAULT_STAGE_BG, ...JSON.parse(raw) };
  } catch (_) {
    /* ignore corrupt / unavailable storage */
  }
  return { ...DEFAULT_STAGE_BG };
}

let current: StageBg = load();

export function getStageBg(): StageBg {
  return current;
}

/** Resolves a relative `/backgrounds/...` URL to the active Hub origin. */
export function resolveStageMediaUrl(src: string): string {
  if (!src) return '';
  if (src.startsWith('http://') || src.startsWith('https://') || src.startsWith('data:') || src.startsWith('blob:')) {
    return src;
  }
  const base = getHubUrl().replace(/\/+$/, '');
  return `${base}${src.startsWith('/') ? '' : '/'}${src}`;
}

/** Applies the background immediately. Returns false if it could not be saved for next launch. */
export function setStageBg(next: StageBg): boolean {
  current = next;
  window.dispatchEvent(new Event(EVENT));
  try {
    localStorage.setItem(KEY, JSON.stringify(next));
    return true;
  } catch (_) {
    return false;
  }
}

export function useStageBackground(): StageBg {
  const [bg, setBg] = useState<StageBg>(current);
  useEffect(() => {
    const onChange = () => setBg({ ...current });
    window.addEventListener(EVENT, onChange);
    return () => window.removeEventListener(EVENT, onChange);
  }, []);
  return bg;
}

/** CSS `background` for the stage container itself (pictures & videos are drawn as separate layers). */
export function stageBgCss(bg: StageBg): string {
  switch (bg.mode) {
    case 'preset': {
      const preset = STAGE_SCENE_PRESETS.find((p) => p.id === bg.presetId) || STAGE_SCENE_PRESETS[0]!;
      return preset.css;
    }
    case 'color':
      return bg.color;
    case 'gradient':
      return `linear-gradient(160deg, ${bg.color2} 0%, ${bg.color} 100%)`;
    case 'image':
    case 'video':
      return '#0d0a14';
    default:
      return 'radial-gradient(ellipse at 50% 30%, #301f4a 0%, #171124 50%, #0d0a14 100%)';
  }
}

/** Returns a subtle mood-reactive radial glow CSS string based on Aiko's current emotion. */
export function moodAmbientCss(emotion: string | undefined, enabled = true): string | null {
  if (!enabled) return null;
  const e = (emotion || 'neutral').toLowerCase();
  const map: Record<string, string> = {
    happy: 'radial-gradient(circle at 50% 42%, rgba(244, 114, 182, 0.18) 0%, transparent 65%)',
    excited: 'radial-gradient(circle at 50% 42%, rgba(251, 191, 36, 0.22) 0%, transparent 65%)',
    love: 'radial-gradient(circle at 50% 42%, rgba(244, 63, 94, 0.24) 0%, transparent 65%)',
    affectionate: 'radial-gradient(circle at 50% 42%, rgba(236, 72, 153, 0.22) 0%, transparent 65%)',
    sad: 'radial-gradient(circle at 50% 42%, rgba(59, 130, 246, 0.18) 0%, transparent 65%)',
    angry: 'radial-gradient(circle at 50% 42%, rgba(239, 68, 68, 0.20) 0%, transparent 65%)',
    annoyed: 'radial-gradient(circle at 50% 42%, rgba(249, 115, 22, 0.18) 0%, transparent 65%)',
    calm: 'radial-gradient(circle at 50% 42%, rgba(52, 211, 153, 0.16) 0%, transparent 65%)',
    thinking: 'radial-gradient(circle at 50% 42%, rgba(168, 85, 247, 0.20) 0%, transparent 65%)',
  };
  return map[e] || null;
}

/** Uploads an image, animated GIF, or video (.mp4/.webm/.mov) to the Neural Hub so it persists without localStorage limits. */
export async function uploadStageMedia(file: File): Promise<{ url: string; kind: 'image' | 'gif' | 'video'; filename?: string }> {
  const isVideo = file.type.startsWith('video/') || /\.(mp4|webm|mov)$/i.test(file.name);
  const isGif = file.type === 'image/gif' || /\.gif$/i.test(file.name);
  const isImage = file.type.startsWith('image/') || /\.(png|jpe?g|webp|avif)$/i.test(file.name);

  if (!isVideo && !isGif && !isImage) {
    throw new Error('Please choose an image (PNG, JPG, WEBP), animated GIF, or video (MP4, WEBM).');
  }

  // First try uploading to the Neural Hub's persistent `data/backgrounds/` storage
  try {
    const hubUrl = await resolveHubUrl();
    const headers = await getAuthHeaders();
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${hubUrl}/api/background/upload`, {
      method: 'POST',
      headers,
      body: form,
    });
    if (res.ok) {
      const data = await res.json();
      if (data?.url) {
        return {
          url: data.url,
          kind: data.kind || (isVideo ? 'video' : isGif ? 'gif' : 'image'),
          filename: data.filename,
        };
      }
    }
  } catch (_) {
    // Fall back to client-side reading if hub upload is unreachable
  }

  if (isVideo) {
    // Create an object URL for immediate session playback if backend is offline
    return { url: URL.createObjectURL(file), kind: 'video' };
  }

  if (isGif) {
    // Read GIF as raw data URL so animation frames are preserved
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve({ url: String(reader.result || ''), kind: 'gif' });
      reader.onerror = () => reject(new Error('Could not read that GIF file.'));
      reader.readAsDataURL(file);
    });
  }

  const dataUrl = await fileToStageImage(file);
  return { url: dataUrl, kind: 'image' };
}

export async function listUploadedBackgrounds(): Promise<UploadedStageMedia[]> {
  try {
    const hubUrl = await resolveHubUrl();
    const headers = await getAuthHeaders();
    const res = await fetch(`${hubUrl}/api/background/list`, { headers });
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data?.backgrounds) ? data.backgrounds : [];
  } catch (_) {
    return [];
  }
}

export async function deleteUploadedBackground(filename: string): Promise<boolean> {
  try {
    const hubUrl = await resolveHubUrl();
    const headers = await getAuthHeaders();
    const res = await fetch(`${hubUrl}/api/background/${encodeURIComponent(filename)}`, {
      method: 'DELETE',
      headers,
    });
    return res.ok;
  } catch (_) {
    return false;
  }
}

/** Reads a static picture file and shrinks it so it fits comfortably in local storage as fallback. */
export function fileToStageImage(file: File, maxSide = 1920, quality = 0.85): Promise<string> {
  return new Promise((resolve, reject) => {
    if (!file.type.startsWith('image/')) {
      reject(new Error('Please choose an image file.'));
      return;
    }
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      try {
        const ratio = Math.min(1, maxSide / Math.max(img.naturalWidth, img.naturalHeight));
        const w = Math.max(1, Math.round(img.naturalWidth * ratio));
        const h = Math.max(1, Math.round(img.naturalHeight * ratio));
        const canvas = document.createElement('canvas');
        canvas.width = w;
        canvas.height = h;
        const ctx = canvas.getContext('2d');
        if (!ctx) throw new Error('Canvas unavailable');
        ctx.drawImage(img, 0, 0, w, h);
        resolve(canvas.toDataURL('image/jpeg', quality));
      } catch (e) {
        reject(e);
      } finally {
        URL.revokeObjectURL(url);
      }
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error('Could not read that image.'));
    };
    img.src = url;
  });
}
