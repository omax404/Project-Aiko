import React, { useEffect, useRef, useState } from 'react';
import { ImagePlus, RotateCcw, Film, Sparkles, Trash2, Check } from 'lucide-react';
import {
  DEFAULT_STAGE_BG,
  STAGE_SCENE_PRESETS,
  StageBg,
  StageBgMode,
  UploadedStageMedia,
  deleteUploadedBackground,
  listUploadedBackgrounds,
  resolveStageMediaUrl,
  setStageBg,
  uploadStageMedia,
  useStageBackground,
} from '../stageBackground';

const MODES: { id: StageBgMode; label: string }[] = [
  { id: 'preset', label: 'Scenes' },
  { id: 'image', label: 'GIF / Pic' },
  { id: 'video', label: 'Video' },
  { id: 'gradient', label: 'Gradient' },
  { id: 'color', label: 'Solid' },
];

/** Appearance-tab section: choose scenes, animated GIFs, videos (.mp4/.webm), or pictures behind Aiko. */
export const StageBackgroundSettings: React.FC = () => {
  const bg = useStageBackground();
  const fileRef = useRef<HTMLInputElement>(null);
  const [note, setNote] = useState('');
  const [uploading, setUploading] = useState(false);
  const [gallery, setGallery] = useState<UploadedStageMedia[]>([]);

  const refreshGallery = async () => {
    const items = await listUploadedBackgrounds();
    setGallery(items);
  };

  useEffect(() => {
    void refreshGallery();
  }, []);

  const update = (patch: Partial<StageBg>) => {
    const saved = setStageBg({ ...bg, ...patch });
    setNote(saved ? '' : 'Applied for this session. Tip: keep Hub running so large media saves to disk.');
  };

  const handleFileUpload = async (file: File) => {
    setUploading(true);
    setNote('');
    try {
      const result = await uploadStageMedia(file);
      if (result.kind === 'video') {
        update({
          mode: 'video',
          video: result.url,
          mediaKind: 'video',
        });
      } else {
        update({
          mode: 'image',
          image: result.url,
          mediaKind: result.kind,
        });
      }
      await refreshGallery();
    } catch (err: any) {
      setNote(err?.message || 'Could not load that background file.');
    } finally {
      setUploading(false);
    }
  };

  const onPick = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    await handleFileUpload(file);
  };

  const handleSelectGalleryItem = (item: UploadedStageMedia) => {
    if (item.kind === 'video') {
      update({ mode: 'video', video: item.url, mediaKind: 'video' });
    } else {
      update({ mode: 'image', image: item.url, mediaKind: item.kind });
    }
  };

  const handleDeleteGalleryItem = async (e: React.MouseEvent, item: UploadedStageMedia) => {
    e.stopPropagation();
    const ok = await deleteUploadedBackground(item.filename);
    if (ok) {
      if (bg.image === item.url || bg.video === item.url) {
        setStageBg({ ...DEFAULT_STAGE_BG });
      }
      await refreshGallery();
    }
  };

  const colorInput = (label: string, value: string, onChange: (v: string) => void) => (
    <label className="flex items-center justify-between gap-3 text-[12px] text-[#9a8f7e]">
      {label}
      <input
        type="color"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-8 w-14 cursor-pointer rounded border border-white/[0.1] bg-transparent"
        aria-label={label}
      />
    </label>
  );

  const activeMediaUrl = bg.mode === 'video' ? bg.video : bg.mode === 'image' ? bg.image : '';

  return (
    <div className="flex flex-col gap-3.5 p-3.5 rounded-xl bg-[var(--bg-base)] border border-white/[0.06]">
      <div className="flex items-center justify-between">
        <div>
          <label className="text-[13px] font-semibold text-[#f0ebe3] block">
            Stage Background & Scenes
          </label>
          <span className="text-[11px] text-[#9a8f7e]">
            Upload animated GIFs, MP4/WebM videos, pictures, or switch 1-click atmospheric scenes.
          </span>
        </div>
        <button
          type="button"
          onClick={() => {
            setStageBg({ ...DEFAULT_STAGE_BG });
            setNote('');
          }}
          className="flex items-center gap-1 text-[11px] text-[#9a8f7e] hover:text-[var(--accent)] shrink-0"
          title="Reset background"
        >
          <RotateCcw size={12} /> Reset
        </button>
      </div>

      {/* Mode Selector Tabs */}
      <div className="grid grid-cols-5 gap-1.5">
        {MODES.map((m) => {
          const isActive = bg.mode === m.id || (bg.mode === 'default' && m.id === 'preset');
          return (
            <button
              key={m.id}
              type="button"
              onClick={() => update({ mode: m.id })}
              className={`px-2 py-2 rounded-lg border text-[11px] font-medium transition-all ${
                isActive
                  ? 'border-[var(--accent)]/60 bg-[var(--accent)]/15 text-[var(--accent)]'
                  : 'border-white/[0.06] text-[#f0ebe3] hover:bg-white/[0.04]'
              }`}
            >
              {m.label}
            </button>
          );
        })}
      </div>

      {/* 1. SCENE PRESETS */}
      {(bg.mode === 'preset' || bg.mode === 'default') && (
        <div className="grid grid-cols-2 gap-2">
          {STAGE_SCENE_PRESETS.map((scene) => {
            const selected = (bg.mode === 'preset' || bg.mode === 'default') && bg.presetId === scene.id;
            return (
              <button
                key={scene.id}
                type="button"
                onClick={() => update({ mode: 'preset', presetId: scene.id })}
                className={`relative flex flex-col justify-end h-16 p-2.5 rounded-lg border text-left overflow-hidden transition-all ${
                  selected
                    ? 'border-[var(--accent)] ring-1 ring-[var(--accent)]/50'
                    : 'border-white/[0.08] hover:border-white/25'
                }`}
                style={{ background: scene.css }}
              >
                <div className="relative z-10 flex items-center justify-between">
                  <span className="text-[11px] font-semibold text-white drop-shadow">{scene.name}</span>
                  {selected && <Check size={12} className="text-[var(--accent)]" />}
                </div>
                <span className="relative z-10 text-[9.5px] text-white/65 truncate">{scene.subtitle}</span>
              </button>
            );
          })}
        </div>
      )}

      {/* 2. SOLID COLOR */}
      {bg.mode === 'color' && colorInput('Stage Color', bg.color, (v) => update({ color: v }))}

      {/* 3. GRADIENT */}
      {bg.mode === 'gradient' && (
        <div className="flex flex-col gap-2">
          {colorInput('Top color', bg.color2, (v) => update({ color2: v }))}
          {colorInput('Bottom color', bg.color, (v) => update({ color: v }))}
        </div>
      )}

      {/* 4. IMAGE / GIF / VIDEO UPLOADER + GALLERY */}
      {(bg.mode === 'image' || bg.mode === 'video') && (
        <div className="flex flex-col gap-3">
          <input
            ref={fileRef}
            type="file"
            accept="image/png,image/jpeg,image/webp,image/gif,image/avif,video/mp4,video/webm,video/quicktime,.gif,.mp4,.webm,.mov"
            className="hidden"
            onChange={onPick}
          />
          <button
            type="button"
            disabled={uploading}
            onClick={() => fileRef.current?.click()}
            className="flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg border border-dashed border-white/[0.18] text-[12px] font-medium text-[#f0ebe3] hover:border-[var(--accent)]/60 hover:bg-white/[0.04] transition-all cursor-pointer"
          >
            {bg.mode === 'video' ? <Film size={15} className="text-[var(--accent)]" /> : <ImagePlus size={15} className="text-[var(--accent)]" />}
            {uploading
              ? 'Uploading media...'
              : 'Upload Custom GIF, Video (.mp4 / .webm), or Wallpaper'}
          </button>

          {/* Active Preview */}
          {activeMediaUrl && (
            <div className="relative h-28 w-full rounded-lg border border-white/[0.1] overflow-hidden bg-black/50">
              {bg.mode === 'video' ? (
                <video
                  src={resolveStageMediaUrl(activeMediaUrl)}
                  autoPlay
                  loop
                  muted
                  playsInline
                  className="w-full h-full object-cover"
                />
              ) : (
                <img
                  src={resolveStageMediaUrl(activeMediaUrl)}
                  alt="Active stage background"
                  className="w-full h-full object-cover"
                />
              )}
              <span className="absolute bottom-1.5 right-2 px-2 py-0.5 rounded bg-black/70 text-[10px] font-mono uppercase text-white/80">
                Active {bg.mode === 'video' ? 'Video' : bg.mediaKind === 'gif' ? 'Animated GIF' : 'Wallpaper'}
              </span>
            </div>
          )}

          {/* Uploaded Gallery */}
          {gallery.length > 0 && (
            <div className="flex flex-col gap-1.5">
              <span className="text-[11px] font-medium text-[#9a8f7e]">
                Your Uploaded Backgrounds ({gallery.length})
              </span>
              <div className="grid grid-cols-4 gap-2 max-h-36 overflow-y-auto pr-1 custom-scrollbar">
                {gallery.map((item) => {
                  const isSelected = activeMediaUrl === item.url;
                  const fullUrl = resolveStageMediaUrl(item.url);
                  return (
                    <div
                      key={item.filename}
                      onClick={() => handleSelectGalleryItem(item)}
                      className={`group relative h-16 rounded-lg border overflow-hidden cursor-pointer bg-black/40 transition-all ${
                        isSelected ? 'border-[var(--accent)] ring-1 ring-[var(--accent)]' : 'border-white/10 hover:border-white/30'
                      }`}
                      title={item.filename}
                    >
                      {item.kind === 'video' ? (
                        <video src={fullUrl} muted loop playsInline className="w-full h-full object-cover" />
                      ) : (
                        <img src={fullUrl} alt={item.filename} className="w-full h-full object-cover" />
                      )}
                      <span className="absolute left-1 bottom-1 px-1 py-0.2 rounded bg-black/70 text-[8px] font-mono uppercase text-white/80">
                        {item.kind}
                      </span>
                      <button
                        type="button"
                        onClick={(e) => handleDeleteGalleryItem(e, item)}
                        className="opacity-0 group-hover:opacity-100 absolute top-1 right-1 p-1 rounded bg-black/80 text-white/70 hover:text-[#f87171] transition-opacity"
                        title="Delete background"
                        aria-label={`Delete ${item.filename}`}
                      >
                        <Trash2 size={10} />
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Dim & Blur Sliders */}
          <div className="grid grid-cols-2 gap-3 pt-1">
            <div className="flex flex-col gap-1">
              <div className="flex justify-between text-[11px] text-[#9a8f7e]">
                <span>Darken Overlay</span>
                <span className="font-mono text-[var(--accent)]">{bg.dim}%</span>
              </div>
              <input
                type="range"
                min={0}
                max={90}
                step={5}
                value={bg.dim}
                onChange={(e) => update({ dim: parseInt(e.target.value, 10) })}
                className="w-full accent-[var(--accent)]"
                aria-label="Darken background"
              />
            </div>
            <div className="flex flex-col gap-1">
              <div className="flex justify-between text-[11px] text-[#9a8f7e]">
                <span>Backdrop Blur</span>
                <span className="font-mono text-[var(--accent)]">{bg.blur}px</span>
              </div>
              <input
                type="range"
                min={0}
                max={30}
                step={1}
                value={bg.blur}
                onChange={(e) => update({ blur: parseInt(e.target.value, 10) })}
                className="w-full accent-[var(--accent)]"
                aria-label="Blur background"
              />
            </div>
          </div>
        </div>
      )}

      {/* Mood-Reactive Ambient Aura Toggle */}
      <label className="flex items-center justify-between gap-3 pt-2 border-t border-white/[0.06] cursor-pointer">
        <span className="flex items-center gap-2 text-[12px] text-[#f0ebe3]">
          <Sparkles size={13} className="text-[var(--accent)]" />
          <span>Mood-Reactive Lighting (stage aura shifts with Aiko's emotion)</span>
        </span>
        <input
          type="checkbox"
          className="w-4 h-4 accent-[var(--accent)]"
          checked={bg.moodReactive ?? true}
          onChange={(e) => update({ moodReactive: e.target.checked })}
          aria-label="Enable Mood-Reactive Lighting"
        />
      </label>

      {note && <p className="text-[11px] text-[#f0c674]">{note}</p>}
    </div>
  );
};
