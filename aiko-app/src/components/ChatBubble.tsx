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
import { useNeuralStore } from '../store/useNeuralStore';
import { useState } from 'react';

interface ChatBubbleProps {
  id?: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  emotion?: string;
  timestamp?: string;
  isTyping?: boolean;
  attachments?: string[];
}

export function ChatBubble({ 
  id, 
  content, 
  role, 
  isTyping: _isTyping,
  timestamp, 
  attachments,
  emotion: _emotion = "neutral"
}: ChatBubbleProps) {
  const { deleteMessage, retryMessage, branchChat, playTTS, editMessage } = useNeuralStore();
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
        <div className="flex items-center gap-3 px-5 py-2 rounded-full bg-white/[0.02] border border-white/5 text-[9px] uppercase tracking-[0.3em] font-bold text-[var(--t3)]">
          <div className="w-1 h-1 rounded-full bg-amber-500/50 shadow-[0_0_8px_#d4956a]" />
          <span>{content}</span>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={clsx(
        "flex w-full mb-12 group",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <div className={clsx(
        "flex max-w-[85%] gap-6",
        isUser ? "flex-row-reverse" : "flex-row"
      )}>
        
        {/* Avatar Area */}
        <div className="flex flex-col items-center flex-shrink-0 mt-1">
          <div className={clsx(
            "w-9 h-9 rounded-xl flex items-center justify-center border transition-all duration-500",
            isUser 
              ? "bg-[var(--bg-card)] border-[var(--b2)]" 
              : "bg-amber-600/10 border-amber-500/30 shadow-[0_0_15px_rgba(212,149,106,0.1)]"
          )}>
            {isUser ? (
               <div className="w-3.5 h-3.5 bg-[var(--t3)] rounded-sm opacity-40" />
            ) : (
               <Zap size={16} className="text-amber-400 group-hover:scale-110 transition-transform" />
            )}
          </div>
        </div>

        <div className={clsx(
          "flex flex-col gap-2",
          isUser ? "items-end" : "items-start"
        )}>
          {/* Header */}
          <div className="flex items-center gap-3 px-1">
             <span className={clsx(
               "text-[10px] font-bold uppercase tracking-widest",
               isUser ? "text-[var(--t3)]" : "text-amber-500"
             )}>
               {isUser ? "Identity_Author" : "Aiko_Intelligence"}
             </span>
             {timestamp && (
               <span className="text-[9px] text-[var(--t4)] font-bold">
                 {new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
               </span>
             )}
          </div>

          {/* Chat Bubble Body */}
          <div className={clsx(
            "relative transition-all duration-500",
            isUser 
              ? "bg-[var(--bg-card)] border border-[var(--b2)] rounded-[24px] rounded-tr-none p-5 px-6 text-[var(--t1)]" 
              : "text-[var(--t1)] py-2"
          )}>
            <div className={clsx(
              "text-[15px] leading-[1.8] font-normal antialiased selectable markdown-content",
              !isUser && "text-[var(--t1)]/90"
            )}>
              {isEditing ? (
                <div className="flex flex-col gap-3 min-w-[300px]">
                  <textarea
                    autoFocus
                    title="Edit message content"
                    placeholder="Edit your message..."
                    className="w-full bg-white/5 border border-white/10 rounded-lg p-3 text-[14px] text-[var(--t1)] focus:outline-none focus:border-amber-500/50 min-h-[100px]"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                  />
                  <div className="flex justify-end gap-2">
                    <button 
                      onClick={() => setIsEditing(false)}
                      className="px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-[var(--t4)] hover:text-[var(--t2)]"
                    >
                      Cancel
                    </button>
                    <button 
                      onClick={handleSaveEdit}
                      className="px-3 py-1 bg-amber-500/20 border border-amber-500/30 rounded text-[10px] font-bold uppercase tracking-wider text-amber-500 hover:bg-amber-500/30"
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
                  >
                    {content}
                  </ReactMarkdown>
                  
                  {attachments && attachments.length > 0 && (
                    <div className={clsx(
                      "flex flex-wrap gap-3 mt-4",
                      isUser ? "justify-end" : "justify-start"
                    )}>
                      {attachments.map((url, idx) => {
                        const isImg = url.match(/\.(jpg|jpeg|png|gif|webp)$/i);
                        const filename = url.split('/').pop();
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
                                  <FileText size={14} className="text-amber-500" />
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
            
            {/* User Glow Effect */}
            {isUser && (
              <div className="absolute inset-0 bg-amber-500/5 blur-xl -z-10 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
            )}
          </div>

          {/* Action Row */}
          <div className={clsx(
            "flex items-center gap-4 mt-2 px-1 opacity-0 translate-y-1 group-hover:opacity-100 group-hover:translate-y-0 transition-all duration-300",
            isUser ? "flex-row-reverse" : "flex-row"
          )}>
            <button 
              onClick={handleCopy}
              title="Copy" className="p-1.5 hover:text-white transition-colors text-[var(--t4)]"
            >
               <Copy size={13} />
            </button>
            <button title="Reaction" className="p-1.5 hover:text-amber-500 transition-colors text-[var(--t4)]">
               <Smile size={13} />
            </button>
            {!isUser ? (
               <>
                 <button 
                   onClick={() => retryMessage()}
                   title="Retry" className="p-1.5 hover:text-amber-400 transition-colors text-[var(--t4)]"
                 >
                    <RotateCcw size={13} />
                 </button>
                 <button 
                   onClick={() => playTTS(content)}
                   title="Speech" className="p-1.5 hover:text-amber-400 transition-colors text-[var(--t4)]"
                 >
                    <Volume2 size={13} />
                 </button>
               </>
            ) : (
               <>
                 <button 
                   onClick={() => setIsEditing(true)}
                   title="Edit" className="p-1.5 hover:text-amber-400 transition-colors text-[var(--t4)]"
                 >
                    <Edit3 size={13} />
                 </button>
                 <button 
                   onClick={() => (id || timestamp) && deleteMessage(id || timestamp!)}
                   title="Delete" className="p-1.5 hover:text-red-400 transition-colors text-[var(--t4)]"
                 >
                    <Trash size={13} />
                 </button>
               </>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
