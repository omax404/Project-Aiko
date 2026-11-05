import { motion } from 'framer-motion';
import { clsx } from 'clsx';
import { 
  Copy, 
  Trash, 
  Zap,
  RotateCcw,
  Volume2,
  Smile,
  Edit3,
  FileText
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import { useNeuralStore, getHubUrl } from '../store/useNeuralStore';
import { openUrl } from '@tauri-apps/plugin-opener';
import { useState, memo } from 'react';

interface ChatBubbleProps {
  id?: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  emotion?: string;
  timestamp?: string;
  isTyping?: boolean;
  attachments?: string[];
}

// Exported for unit tests — tests must exercise this implementation, not a copy.
export function sanitizeMarkdownContent(text: string): string {
  if (!text) return '';
  // Strip reasoning CONTENT first (tags alone would leak chain-of-thought),
  // then any stray emotion/reasoning tags that remain.
  let cleaned = text
    .replace(/<think>[\s\S]*?<\/think>/gi, '')
    .replace(/<thought>[\s\S]*?<\/thought>/gi, '')
    .replace(/<emotion>.*?<\/emotion>/gi, '')
    .replace(/<\/?(emotion|think|thought)>/gi, '');

  // 1. Convert [STICKER:xxx] or [mood:xxx] or [gesture:xxx] tags to markdown images
  cleaned = cleaned.replace(/\[(STICKER|mood|gesture)\s*:\s*([^\]]+)\]/gi, (_, _type, name) => {
    const cleanName = name.trim().replace(/\s+/g, '_');
    const withExt = cleanName.endsWith('.png') ? cleanName : `${cleanName}.png`;
    return `![sticker](/stickers/${withExt})`;
  });

  // 2. Fix missing exclamation mark in sticker links: [mood](/stickers/...) -> ![mood](/stickers/...)
  cleaned = cleaned.replace(/(?<!\!)\[(.*?)\]\s*\((\/?stickers\/.*?)\)/gi, '![$1]($2)');

  // 3. Fix whitespace/newlines between ![alt] and (url): ![mood] \n (/stickers/...) -> ![mood](/stickers/...)
  cleaned = cleaned.replace(/!\[(.*?)\]\s+\((.*?)\)/g, '![$1]($2)');

  // 4. Fix any spaces inside sticker URLs and normalize paths (e.g. "/stickers/05_Crying_Comical. png" -> "/stickers/05_Crying_Comical.png")
  cleaned = cleaned.replace(/!\[(.*?)\]\((\/?stickers\/[^\)]+)\)/gi, (_, alt, path) => {
    let cleanPath = path.trim();
    if (!cleanPath.startsWith('/')) cleanPath = '/' + cleanPath;
    cleanPath = cleanPath.replace(/\s+/g, '');
    if (!/\.(png|jpg|jpeg|gif|webp)$/i.test(cleanPath)) {
      cleanPath += '.png';
    }
    return `![${alt || 'sticker'}](${cleanPath})`;
  });

  // 5. Fix missing leading slash in ![alt](stickers/...)
  cleaned = cleaned.replace(/!\[(.*?)\]\(stickers\/(.*?)\)/gi, '![$1](/stickers/$2)');

  // 6. Fix [STICKER:xxx] inside image alt text
  cleaned = cleaned.replace(/!\[\[STICKER\s*:\s*([^\]]+)\]\]\((.*?)\)/gi, '![$1]($2)');

  // 7. Strip stray markdown escapes that break rendering
  cleaned = cleaned.replace(/\\([*_`~[\]()])/g, '$1');

  // 8. Fix malformed image extensions like ".png" with spaces before or after dot in any markdown image
  cleaned = cleaned.replace(/!\[(.*?)\]\((.*?)\s*\.\s*(png|jpg|jpeg|gif|webp)\)/gi, '![$1]($2.$3)');

  return cleaned.trim();
}

// Memoized to prevent re-render cascades across 50+ message bubbles when
// high-frequency store updates occur (e.g. 60Hz TTS speech amplitude updates).
export const ChatBubble = memo(function ChatBubble({ 
  id, 
  content, 
  role, 
  isTyping: _isTyping,
  timestamp, 
  attachments,
  emotion: _emotion = "neutral"
}: ChatBubbleProps) {
  // Use granular atomic selectors for stable store actions.
  // Destructuring `useNeuralStore()` directly causes every bubble to re-render on any store mutation.
  const deleteMessage = useNeuralStore((s) => s.deleteMessage);
  const retryMessage = useNeuralStore((s) => s.retryMessage);
  const branchChat = useNeuralStore((s) => s.branchChat);
  const playTTS = useNeuralStore((s) => s.playTTS);
  const editMessage = useNeuralStore((s) => s.editMessage);
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(content);
  const isUser = role === 'user';
  const isSystem = role === 'system';

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
  };

  const handleSaveEdit = () => {
    if (id || timestamp) {
      if (isUser) {
        branchChat(id || timestamp!, editValue);
      } else {
        editMessage(id || timestamp!, editValue);
      }
      setIsEditing(false);
    }
  };

  if (isSystem) {
    return (
      <motion.div 
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex justify-center w-full mb-8"
      >
        <div className="flex items-center gap-2.5 px-4 py-1.5 rounded-full bg-[var(--bg-hover)] border border-[var(--b1)] text-[11px] font-medium text-[var(--t4)]">
          <div className="w-1.5 h-1.5 rounded-full bg-[var(--p-accent)] opacity-60" />
          <span>{content}</span>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        type: "spring",
        stiffness: 160,
        damping: 18,
        mass: 0.8
      }}
      className={clsx(
        "flex w-full mb-8 group",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <div className={clsx(
        "flex max-w-[80%] gap-4",
        isUser ? "flex-row-reverse" : "flex-row"
      )}>

        {/* Avatar dot — taste-skill: ink-tinted, never neon */}
        <div className="flex flex-col items-center flex-shrink-0 mt-1">
          <div className={clsx(
            "w-7 h-7 rounded-[var(--p-radius-sm)] flex items-center justify-center border transition-all duration-300",
            isUser
              ? "bg-[var(--bg-elevated)] border-[var(--b1)]"
              : "bg-[var(--p-accent-soft)] border-[var(--b2)]"
          )}>
            {isUser ? (
               <div className="w-2.5 h-2.5 bg-[var(--t4)] rounded-sm" />
            ) : (
               <Zap size={13} strokeWidth={2} className="text-[var(--p-accent)]" />
            )}
          </div>
        </div>

        <div className={clsx(
          "flex flex-col gap-1.5",
          isUser ? "items-end" : "items-start"
        )}>
          {/* Meta row */}
          <div className="flex items-center gap-2 px-0.5">
             <span className={clsx(
               "text-[11px] font-semibold uppercase tracking-[0.1em]",
               isUser ? "text-[var(--t4)]" : "text-[var(--p-accent)]"
             )}>
               {isUser ? "You" : "Aiko"}
             </span>
             {timestamp && (
               <span className="text-[11px] text-[var(--t4)] font-medium tabular-nums">
                 {new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
               </span>
             )}
          </div>

          {/* Bubble body — taste-skill card system */}
          <div className={clsx(
            "relative transition-all duration-200",
            isUser
              ? "bg-[var(--p-accent)] text-[var(--p-accent-ink)] border border-[var(--p-accent)] rounded-[var(--p-radius)] rounded-tr-[6px] px-4 py-3 font-medium shadow-[0_2px_12px_rgba(180,155,240,0.2)]"
              : "bg-[var(--p-card)] text-[var(--t1)] border border-[var(--b1)] rounded-[var(--p-radius)] rounded-tl-[6px] px-4 py-3 shadow-[inset_0_1px_0_var(--p-inset-hi),0_4px_16px_-4px_rgba(0,0,0,0.5)]"
          )}>
            <div className={clsx(
              "text-[14px] leading-[1.75] font-normal antialiased selectable markdown-content",
              isUser && "text-[var(--p-accent-ink)]"
            )}>
              {isEditing ? (
                <div className="flex flex-col gap-3 min-w-[300px]">
                  <textarea
                    autoFocus
                    title="Edit message content"
                    aria-label="Edit message content"
                    placeholder="Edit your message..."
                    className="w-full bg-[var(--bg-elevated)] border border-[var(--b1)] rounded-[var(--p-radius-sm)] p-3 text-[13px] text-[var(--t1)] focus:outline-none focus:border-[var(--b3)] min-h-[100px] resize-none"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                  />
                  <div className="flex justify-end gap-2">
                    <button 
                      onClick={() => setIsEditing(false)}
                      className="px-3 py-1.5 text-[11px] font-medium text-[var(--t3)] hover:text-[var(--t1)] transition-colors"
                    >
                      Cancel
                    </button>
                    <button 
                      onClick={handleSaveEdit}
                      className="px-3 py-1.5 bg-[var(--p-accent-soft)] border border-[var(--b2)] rounded-[var(--p-radius-sm)] text-[11px] font-medium text-[var(--p-accent)] hover:bg-[var(--bg-active)] transition-colors"
                    >
                      Save Changes
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm, remarkMath]}
                    rehypePlugins={[rehypeKatex]}
                    components={{
                      a: ({ href, children, ...props }) => (
                        <a
                          {...props}
                          href={href}
                          target="_blank"
                          rel="noreferrer noopener"
                          onClick={(event) => {
                            event.preventDefault();
                            if (href && /^(https?:|mailto:)/i.test(href)) {
                              if ((window as any).__TAURI__) {
                                void openUrl(href).catch((error) => console.warn('[Aiko] Could not open link:', error));
                              } else {
                                window.open(href, '_blank', 'noopener,noreferrer');
                              }
                            }
                          }}
                          className="text-[var(--accent)] underline underline-offset-2 hover:opacity-80"
                        >
                          {children}
                        </a>
                      ),
                      img: ({ node, src, alt, ...props }) => {
                        if (!src) return null;
                        const hubUrl = getHubUrl();
                        const absoluteSrc = src.startsWith('http') || src.startsWith('data:') ? src : `${hubUrl}${src}`;
                        
                        const isSticker = src.includes('/stickers/') && !src.includes('selfie') && !src.includes('gen_');
                        if (isSticker) {
                          return (
                            <img 
                              src={absoluteSrc} 
                              alt={alt || "sticker"} 
                              className="w-28 h-28 object-contain my-2 inline-block transition-transform hover:scale-110 duration-200 cursor-pointer drop-shadow-[0_4px_12px_rgba(0,0,0,0.15)]"
                              {...props}
                            />
                          );
                        }
                        return <img src={absoluteSrc} alt={alt} className="max-w-[320px] max-h-[480px] rounded-xl my-2 object-cover shadow-lg border border-white/10" {...props} />;
                      }
                    }}
                  >
                    {sanitizeMarkdownContent(content)}
                  </ReactMarkdown>
                  
                  {attachments && attachments.length > 0 && (
                    <div className={clsx(
                      "flex flex-wrap gap-3 mt-4",
                      isUser ? "justify-end" : "justify-start"
                    )}>
                      {attachments.map((url, idx) => {
                        const isImg = url.match(/\.(jpg|jpeg|png|gif|webp|bmp|tiff|avif)(\?.*)?$/i) || url.startsWith('data:image/');
                        const filename = url.split('/').pop() || 'file';
                        return (
                          <div key={idx} className="relative group/att max-w-[200px]">
                            {isImg ? (
                              <motion.img 
                                whileHover={{ scale: 1.02 }}
                                src={url} 
                                alt="Attachment" 
                                className="rounded-2xl border border-white/10 shadow-lg cursor-pointer max-h-48 object-cover"
                                onClick={() => window.open(url, '_blank')}
                              />
                            ) : (
                              <a 
                                href={url} 
                                target="_blank" 
                                rel="noreferrer"
                                className="flex items-center gap-3 p-3 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors text-[12px] text-slate-300"
                              >
                                <div className="p-2 rounded-lg bg-white/5">
                                  <FileText size={14} className="text-[var(--acc)]" />
                                </div>
                                <span className="truncate font-medium">{filename}</span>
                              </a>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </>
              )}
            </div>
            
            {/* User glow — taste-skill: no neon, just a soft accent tint */}
            {isUser && (
              <div className="absolute inset-0 bg-[var(--p-accent)]/[0.04] blur-xl -z-10 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            )}
          </div>

          {/* Action Row */}
          <div className={clsx(
            "flex items-center gap-3 mt-1 px-0.5 opacity-0 translate-y-1 group-hover:opacity-100 group-hover:translate-y-0 transition-all duration-200",
            isUser ? "flex-row-reverse" : "flex-row"
          )}>
            <button
              onClick={handleCopy}
              aria-label="Copy message to clipboard"
              title="Copy" className="p-1 hover:text-[var(--t1)] transition-colors text-[var(--t4)]"
            >
               <Copy size={12} strokeWidth={1.8} />
            </button>
            <button aria-label="Add reaction" title="Reaction" className="p-1 hover:text-[var(--p-accent)] transition-colors text-[var(--t4)]">
               <Smile size={12} strokeWidth={1.8} />
            </button>
            {!isUser ? (
               <>
                 <button
                   onClick={() => retryMessage()}
                   aria-label="Retry generating response"
                   title="Retry" className="p-1 hover:text-[var(--p-accent)] transition-colors text-[var(--t4)]"
                 >
                    <RotateCcw size={12} strokeWidth={1.8} />
                 </button>
                 <button
                   onClick={() => playTTS(content)}
                   aria-label="Play text-to-speech"
                   title="Speech" className="p-1 hover:text-[var(--p-accent)] transition-colors text-[var(--t4)]"
                 >
                    <Volume2 size={12} strokeWidth={1.8} />
                 </button>
               </>
            ) : (
               <>
                 <button
                   onClick={() => setIsEditing(true)}
                   aria-label="Edit message"
                   title="Edit" className="p-1 hover:text-[var(--p-accent)] transition-colors text-[var(--t4)]"
                 >
                    <Edit3 size={12} strokeWidth={1.8} />
                 </button>
                 <button
                   onClick={() => (id || timestamp) && deleteMessage(id || timestamp!)}
                   aria-label="Delete message"
                   title="Delete" className="p-1 hover:text-[var(--red)] transition-colors text-[var(--t4)]"
                 >
                    <Trash size={12} strokeWidth={1.8} />
                 </button>
               </>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
});
