import { useState, useRef, useEffect } from "react";
import { 
  Plus,
  Sparkles,
  Image as ImageIcon,
  X,
  Paperclip
} from "lucide-react";
import { clsx } from 'clsx';
import { useNeuralStore } from "../store/useNeuralStore";
import { GifPicker } from "./GifPicker";
import { AnimatePresence } from "framer-motion";
import { GothicButton } from "./GothicButton";


export function InputDock() {
  const [text, setText] = useState("");
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [showGifPicker, setShowGifPicker] = useState(false);
  const [pendingFiles, setPendingFiles] = useState<{url: string, filename: string, type: string}[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  
  const { sendMessage, isThinking, isListening, startListening, apiConfig, uploadFile } = useNeuralStore();
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [text]);

  const handleSend = () => {
    if ((!text.trim() && pendingFiles.length === 0) || isThinking) return;
    sendMessage(text.trim(), pendingFiles.map(f => f.url));
    setText("");
    setPendingFiles([]);
  };

  const handleAttach = () => {
    fileInputRef.current?.click();
  };

  const onFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);
    try {
      const newFiles: {url: string, filename: string, type: string}[] = [];
      for (const file of Array.from(files)) {
        const res = await uploadFile(file);
        newFiles.push(res);
      }
      setPendingFiles(prev => [...prev, ...newFiles]);
    } catch (err) {
      console.error("Upload failed", err);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const removeFile = (index: number) => {
    setPendingFiles(prev => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 pb-2">
      <div className="relative">
        <div className="w-full mb-2">
          <div className="flex items-center gap-3 w-full opacity-30 select-none pointer-events-none">
            <div className="flex-1 h-px bg-gradient-to-r from-transparent via-[var(--acc)]/30 to-transparent" />
            <div className="w-1 h-1 rotate-45 border border-[var(--acc)]/20" />
            <div className="flex-1 h-px bg-gradient-to-r from-transparent via-[var(--acc)]/30 to-transparent" />
          </div>
        </div>
        <div className="absolute -inset-2 bg-[var(--accent)]/5 blur-2xl rounded-3xl opacity-0 group-focus-within:opacity-100 transition-opacity" />
        
        <div className="relative flex flex-col gap-2 p-1.5 glass-pane rounded-3xl shadow-2xl focus-within:border-accent/30 transition-all duration-500">
          
          <div className="flex items-center justify-between px-4 py-2 border-b border-white/5 mb-1">
             <div className="flex items-center gap-2.5">
                <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-accent/10 border border-accent/20">
                   <Sparkles size={11} className="text-accent" />
                   <span className="text-[11px] font-bold text-[var(--accent)] uppercase tracking-widest">{apiConfig.model}</span>
                </div>

             </div>

             <div className="flex items-center gap-2 text-slate-500">
                <GothicButton 
                  icon="volume"
                  size="sm"
                  title={ttsEnabled ? "TTS Active" : "TTS Muted"}
                  aria-label={ttsEnabled ? "Text-to-speech is active" : "Text-to-speech is muted"}
                  onClick={() => setTtsEnabled(!ttsEnabled)}
                  active={ttsEnabled}
                  className={!ttsEnabled ? "opacity-40 grayscale" : ""}
                />
                <div className="w-px h-3 bg-white/5 mx-1" />
                <GothicButton 
                  icon="mic"
                  size="sm"
                  onClick={() => {
                    if (!isListening) {
                      startListening();
                    }
                  }}
                  title={isListening ? "Listening..." : "Voice Input"}
                  aria-label={isListening ? "Microphone is listening" : "Start voice input"}
                  active={isListening}
                  className={isListening ? "animate-pulse ring-2 ring-red-500 shadow-[0_0_20px_rgba(239,68,68,0.5)]" : ""}
                />
             </div>
           </div>
           
           {/* Attachment Preview Area */}
           {(pendingFiles.length > 0 || isUploading) && (
             <div className="flex flex-wrap gap-2 px-4 py-2 border-b border-white/5">
                {pendingFiles.map((file, idx) => (
                  <div key={idx} className="relative group/file">
                    {file.type.startsWith('image/') ? (
                      <div className="w-16 h-16 rounded-xl overflow-hidden border border-white/10 bg-white/5">
                        <img src={file.url} alt="preview" className="w-full h-full object-cover" />
                      </div>
                    ) : (
                      <div className="h-10 px-3 flex items-center gap-2 rounded-xl bg-white/5 border border-white/10 text-[11px] text-slate-300">
                        <Paperclip size={12} />
                        <span className="max-w-[80px] truncate">{file.filename}</span>
                      </div>
                    )}
                    <button 
                      onClick={() => removeFile(idx)}
                      aria-label={`Remove file ${file.filename}`}
                      title="Remove file"
                      className="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full bg-red-500 text-white flex items-center justify-center opacity-0 group-hover/file:opacity-100 transition-opacity"
                    >
                      <X size={10} />
                    </button>
                  </div>
                ))}
                {isUploading && (
                  <div className="w-10 h-10 flex items-center justify-center animate-spin text-accent">
                    <Sparkles size={16} />
                  </div>
                )}
             </div>
           )}
           
           <input 
             type="file" 
             ref={fileInputRef} 
             onChange={onFileChange} 
             multiple 
             title="File Upload"
             className="hidden" 
             accept="image/*,application/pdf,text/*,.py,.js,.json"
           />

          <div className="flex items-end gap-3 px-3 pb-2 pt-1">
            <button 
              onClick={handleAttach}
              aria-label="Attach file"
              title="Attach File" className="p-3 rounded-2xl text-slate-500 hover:text-white hover:bg-white/5 transition-all mb-1"
            >
              <Plus size={18} strokeWidth={2.5} />
            </button>

            <div className="relative mb-1">
               <button 
                 onClick={() => setShowGifPicker(!showGifPicker)}
                 aria-label="Open animated assets picker"
                 title="Animated Assets" 
                 className={clsx(
                   "p-3 rounded-2xl transition-all",
                   showGifPicker ? "text-accent bg-accent/5" : "text-slate-500 hover:text-[var(--acc)] hover:bg-[var(--acc)]/5"
                 )}
               >
                 <ImageIcon size={18} strokeWidth={2.5} className={clsx(showGifPicker && "animate-pulse")} />
               </button>

               <AnimatePresence>
                 {showGifPicker && (
                   <GifPicker 
                     onClose={() => setShowGifPicker(false)} 
                     onSelect={(url) => {
                       sendMessage(`![Neural_Asset](${url})`);
                       setShowGifPicker(false);
                     }} 
                   />
                 )}
               </AnimatePresence>
            </div>
            
            <textarea
              ref={textareaRef}
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
                if (e.key === 'Enter' && e.ctrlKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              title="Message input"
              aria-label="Message input. Press Enter to send, Shift+Enter for new line."
              placeholder="Ask Aiko anything..."
              className="flex-1 text-[15px] text-gray-100 placeholder:text-slate-600 max-h-48 custom-scrollbar leading-[1.6] py-3 font-normal focus:outline-none focus:ring-0 focus:border-0 bg-transparent outline-none shadow-none border-none resize-none"
              rows={1}
            />

            <GothicButton
              icon="send"
              size="md"
              onClick={handleSend}
              title="Send Message"
              disabled={(!text.trim() && pendingFiles.length === 0) || isThinking || isUploading}
              className={clsx(
                "mb-1 shadow-[0_0_15px_rgba(212,149,106,0.3)] hover:shadow-[0_0_25px_rgba(212,149,106,0.6)]",
                isThinking && "animate-pulse"
              )}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
