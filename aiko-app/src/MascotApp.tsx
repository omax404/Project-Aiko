import { useEffect, useState, useRef, useCallback } from 'react';
import { getCurrentWindow, Window, LogicalSize } from '@tauri-apps/api/window';
import { invoke } from '@tauri-apps/api/core';
import { motion, AnimatePresence } from 'framer-motion';
import { Live2DAvatar } from './components/Live2DAvatar';
import { useNeuralStore, getHubUrl } from './store/useNeuralStore';
import { useShallow } from 'zustand/react/shallow';
import { Home, X, MessageCircle, Send, Volume2, VolumeX, Pin, ZoomIn } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

/**
 * AIKO MASCOT v3.0 — "Ghost Pet"
 * ────────────────────────────────
 * Professional desktop companion with:
 * - Pixel-perfect click-through (no ghost hitboxes)
 * - Compact drag zone on model only
 * - Expandable quick-chat bubble
 * - Sleek mini-toolbar on hover
 * - Real-time emotion & lip-sync from Neural Hub
 */

const MASCOT_W = 300;
const MASCOT_H = 420;

export default function MascotApp() {
  // Field selectors: a whole-store subscription here re-rendered the mascot
  // (and its Live2D canvas wrapper) on every unrelated store mutation.
  const {
    connect, isThinking, isTalking, currentEmotion, amplitude,
    sendMessage, streamingContent, messages, fetchBridgeStatus,
    apiConfig, updateApiConfig,
  } = useNeuralStore(useShallow((s) => ({
    connect: s.connect,
    isThinking: s.isThinking,
    isTalking: s.isTalking,
    currentEmotion: s.currentEmotion,
    amplitude: s.amplitude,
    sendMessage: s.sendMessage,
    streamingContent: s.streamingContent,
    messages: s.messages,
    fetchBridgeStatus: s.fetchBridgeStatus,
    apiConfig: s.apiConfig,
    updateApiConfig: s.updateApiConfig,
  })));
  const ttsEnabled = apiConfig?.ttsEnabled ?? true;

  const isTauri = typeof window !== 'undefined' && !!(window as any).__TAURI__;
  const [chatOpen, setChatOpen] = useState(false);
  const [chatInput, setChatInput] = useState('');
  const [toolbarVisible, setToolbarVisible] = useState(!isTauri);
  const [pinned, setPinned] = useState(true);
  const [petScale, setPetScale] = useState<number>(0.72);
  const toolbarTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Tauri Click-Through Helper
  const setIgnoreCursor = useCallback((ignore: boolean) => {
    if (isTauri) {
      getCurrentWindow().setIgnoreCursorEvents(ignore).catch(() => {});
    }
  }, [isTauri]);

  // Connect to Neural Hub and set default click-through
  useEffect(() => {
    try { connect(getHubUrl()); } catch (_) {}
    fetchBridgeStatus();
    if (isTauri) {
      setIgnoreCursor(true); // Clicks on transparent areas fall through by default
    }
  }, [isTauri, setIgnoreCursor]);

  // Auto-focus input when chat opens
  useEffect(() => {
    if (chatOpen && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [chatOpen]);

  // Show toolbar on hover, auto-hide after delay
  const showToolbar = useCallback(() => {
    setToolbarVisible(true);
    if (toolbarTimeout.current) clearTimeout(toolbarTimeout.current);
    toolbarTimeout.current = setTimeout(() => {
      if (isTauri) setToolbarVisible(false);
    }, 3500);
  }, [isTauri]);

  const handleDrag = useCallback(() => {
    if (isTauri) {
      getCurrentWindow().startDragging().catch(() => {});
    }
  }, [isTauri]);

  const handleTogglePin = useCallback(async () => {
    const next = !pinned;
    setPinned(next);
    if (isTauri) {
      try {
        await getCurrentWindow().setAlwaysOnTop(next);
      } catch (_) {}
    }
  }, [pinned, isTauri]);

  const handleCycleScale = useCallback(() => {
    setPetScale((prev) => (prev < 0.65 ? 0.72 : prev < 0.8 ? 0.85 : 0.58));
  }, []);

  const handleReturnToHub = useCallback(async () => {
    if (isTauri) {
      try {
        await invoke('restore_from_mascot');
        return;
      } catch (_) {
        try {
          const cur = getCurrentWindow();
          if (cur.label === 'main') {
            await cur.setAlwaysOnTop(false);
            await cur.setSize(new LogicalSize(1400, 900));
            window.location.href = '/';
            return;
          }
          const mainWindow = new Window('main');
          await mainWindow.show();
          await mainWindow.setFocus();
          await cur.hide();
          return;
        } catch (e) {
          console.error('Failed to swap windows:', e);
        }
      }
    }
    if (window.opener && !window.opener.closed) {
      window.opener.focus();
      window.close();
      return;
    }
    window.location.href = '/';
  }, [isTauri]);

  const handleCloseMascot = useCallback(() => {
    if (isTauri) {
      getCurrentWindow().hide().catch(() => {
        void handleReturnToHub();
      });
      return;
    }
    if (window.opener && !window.opener.closed) {
      window.close();
    } else {
      window.location.href = '/';
    }
  }, [isTauri, handleReturnToHub]);

  const handleSend = useCallback(() => {
    const text = chatInput.trim();
    if (!text) return;
    sendMessage(text);
    setChatInput('');
  }, [chatInput, sendMessage]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
    if (e.key === 'Escape') {
      setChatOpen(false);
    }
  }, [handleSend]);

  // Get last assistant message for the speech bubble
  const lastReplyRaw = streamingContent.trim() ||
    [...messages].reverse().find(m => m.role === 'assistant')?.content || '';

  // Clean the speech bubble: strip sticker/image markdown, tool tags, and debug junk
  const cleanForBubble = (text: string): string => {
    let cleaned = text;
    // Strip markdown images — extract alt text if present
    cleaned = cleaned.replace(/!\[([^\]]*)\]\([^)]*\)/g, '$1');
    // Strip tool tags like [SCAN], [MCP:...], [MUSIC:...] etc.
    cleaned = cleaned.replace(/\[(SCAN|MCP|TASK|BIO_REGISTER|GAME|OPEN|TYPE|CLICK|PRESS|WAIT|WALLPAPER|WEATHER|MUSIC|LETTER|VTS_BG|IMAGE|RECALL|LATEX|GIF)[^\]]*\]/gi, '');
    // Strip markdown emphasis wrappers for speech bubble readability
    cleaned = cleaned.replace(/\*([^*]+)\*/g, '$1');
    // Strip stray dashes and excessive whitespace
    cleaned = cleaned.replace(/^\s*--\s*$/gm, '').replace(/\n{2,}/g, ' ').trim();
    // If what remains is just numbers, dots, or empty — discard
    if (!cleaned || /^[\d.\s-]+$/.test(cleaned)) return '';
    return cleaned;
  };

  const bubbleText = (() => {
    const cleaned = cleanForBubble(lastReplyRaw);
    if (!cleaned) return '';
    return cleaned.length > 120 ? cleaned.slice(0, 117) + '...' : cleaned;
  })();

  return (
    <div className="mascot-root">
      {/* ══════════════════════════════════════════════════
          MODEL LAYER — draggable, hover triggers toolbar
         ══════════════════════════════════════════════════ */}
      <div
        className="mascot-model-zone"
        onMouseDown={handleDrag}
        onMouseEnter={() => { showToolbar(); setIgnoreCursor(false); }}
        onMouseLeave={() => setIgnoreCursor(true)}
        onMouseMove={showToolbar}
        data-tauri-drag-region
      >
        <Live2DAvatar
          modelUrl="/live2d/vivian/vivian.model3.json"
          isThinking={isThinking}
          isTalking={isTalking}
          emotion={currentEmotion}
          width={MASCOT_W}
          height={MASCOT_H}
          scale={petScale}
          amplitude={amplitude}
          offsetX={35}
          offsetY={45}
        />

        {/* Thinking indicator — orbiting dots */}
        <AnimatePresence>
          {isThinking && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              className="mascot-thinking"
            >
              <span /><span /><span />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ══════════════════════════════════════════════════
          SPEECH BUBBLE — shows last reply, click to expand
         ══════════════════════════════════════════════════ */}
      <AnimatePresence>
        {bubbleText && !chatOpen && !isThinking && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.9 }}
            transition={{ type: 'spring', stiffness: 400, damping: 25 }}
            className="mascot-speech-bubble"
            onClick={() => setChatOpen(true)}
            onMouseEnter={() => setIgnoreCursor(false)}
            onMouseLeave={() => setIgnoreCursor(true)}
          >
            <p>{bubbleText}</p>
            <div className="mascot-speech-tail" />
          </motion.div>
        )}
      </AnimatePresence>

      {/* ══════════════════════════════════════════════════
          MINI TOOLBAR — slides up on hover over model
         ══════════════════════════════════════════════════ */}
      <AnimatePresence>
        {toolbarVisible && !chatOpen && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            transition={{ duration: 0.2 }}
            className="mascot-toolbar"
            onMouseEnter={() => setIgnoreCursor(false)}
            onMouseLeave={() => setIgnoreCursor(true)}
          >
            <button
              onClick={() => setChatOpen(true)}
              className="mascot-btn mascot-btn-primary"
              title="Quick Chat"
            >
              <MessageCircle size={15} />
            </button>
            <button
              onClick={() => updateApiConfig({ ttsEnabled: !ttsEnabled })}
              className="mascot-btn"
              title={ttsEnabled ? "Mute Voice" : "Unmute Voice"}
            >
              {!ttsEnabled ? <VolumeX size={15} /> : <Volume2 size={15} />}
            </button>
            <button
              onClick={handleCycleScale}
              className="mascot-btn"
              title={`Resize Pet (${Math.round(petScale * 100)}%)`}
            >
              <ZoomIn size={15} />
            </button>
            {isTauri && (
              <button
                onClick={handleTogglePin}
                className={`mascot-btn ${pinned ? 'mascot-btn-primary' : ''}`}
                title={pinned ? "Pinned Always-On-Top (Click to Unpin)" : "Pin Always-On-Top"}
              >
                <Pin size={15} />
              </button>
            )}
            <button
              onClick={handleReturnToHub}
              className="mascot-btn"
              title="Return to Full Aiko Studio"
            >
              <Home size={15} />
            </button>
            <button
              onClick={handleCloseMascot}
              className="mascot-btn mascot-btn-danger"
              title="Hide Mascot"
            >
              <X size={15} />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ══════════════════════════════════════════════════
          QUICK CHAT PANEL — compact glassmorphism panel
         ══════════════════════════════════════════════════ */}
      <AnimatePresence>
        {chatOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.92 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.92 }}
            transition={{ type: 'spring', stiffness: 380, damping: 28 }}
            className="mascot-chat-panel"
            onMouseEnter={() => setIgnoreCursor(false)}
            onMouseLeave={() => setIgnoreCursor(true)}
          >
            <div className="mascot-chat-header">
              <div className="mascot-chat-status">
                <div className={`mascot-dot ${isThinking ? 'thinking' : 'online'}`} />
                <span>Aiko</span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleReturnToHub}
                  className="mascot-chat-action"
                  title="Return to Main Hub"
                  style={{ background: 'transparent', border: 'none', color: 'var(--t4)', cursor: 'pointer', padding: '4px' }}
                >
                  <Home size={14} />
                </button>
                <button
                  onClick={() => setChatOpen(false)}
                  className="mascot-chat-close"
                  title="Close chat"
                >
                  <X size={14} />
                </button>
              </div>
            </div>

            {/* Messages area */}
            <div className="mascot-chat-messages custom-scrollbar">
              {messages.slice(-10).map((msg, i) => {
                const displayContent = msg.content.replace(/<emotion>.*?<\/emotion>/gi, '').trim();
                return (
                  <div key={i} className={`mascot-msg ${msg.role}`}>
                    {msg.role === 'assistant' ? (
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          img: ({ src, alt, ...props }) => {
                            if (!src) return null;
                            const isSticker = src.includes('/stickers/');
                            if (isSticker) {
                              const hubUrl = getHubUrl();
                              const absoluteSrc = src.startsWith('http') ? src : `${hubUrl}${src}`;
                              return (
                                <img
                                  src={absoluteSrc}
                                  alt={alt || 'sticker'}
                                  style={{ width: 64, height: 64, objectFit: 'contain', display: 'inline-block', margin: '4px 0', filter: 'drop-shadow(0 2px 6px rgba(0,0,0,0.2))' }}
                                  {...props}
                                />
                              );
                            }
                            return <img src={src} alt={alt} style={{ maxWidth: '100%', borderRadius: 8, margin: '4px 0' }} {...props} />;
                          },
                          p: ({ children }) => <span>{children}</span>,
                        }}
                      >
                        {displayContent}
                      </ReactMarkdown>
                    ) : (
                      displayContent
                    )}
                  </div>
                );
              })}
              {streamingContent && (
                <div className="mascot-msg assistant streaming">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      img: ({ src, alt, ...props }) => {
                        if (!src) return null;
                        const isSticker = src.includes('/stickers/');
                        if (isSticker) {
                          const hubUrl = getHubUrl();
                          const absoluteSrc = src.startsWith('http') ? src : `${hubUrl}${src}`;
                          return (
                            <img
                              src={absoluteSrc}
                              alt={alt || 'sticker'}
                              style={{ width: 64, height: 64, objectFit: 'contain', display: 'inline-block' }}
                              {...props}
                            />
                          );
                        }
                        return <img src={src} alt={alt} style={{ maxWidth: '100%', borderRadius: 8 }} {...props} />;
                      },
                      p: ({ children }) => <span>{children}</span>,
                    }}
                  >
                    {streamingContent}
                  </ReactMarkdown>
                  <span className="mascot-cursor" />
                </div>
              )}
              {isThinking && !streamingContent && (
                <div className="mascot-msg assistant thinking-msg">
                  <span className="mascot-thinking-dots">
                    <span /><span /><span />
                  </span>
                </div>
              )}
            </div>

            {/* Input bar */}
            <div className="mascot-chat-input-bar">
              <input
                ref={inputRef}
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Talk to Aiko..."
                className="mascot-chat-input"
              />
              <button
                onClick={handleSend}
                disabled={!chatInput.trim()}
                className="mascot-send-btn"
                title="Send message"
              >
                <Send size={14} />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
