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
import { ModelPicker } from "./ModelPicker";
import { AnimatePresence } from "framer-motion";
import { GothicButton } from "./GothicButton";


export function InputDock() {
  const [text, setText] = useState("");
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [showGifPicker, setShowGifPicker] = useState(false);
  const [pendingFiles, setPendingFiles] = useState<{url: string, filename: string, type: string}[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const sendMessage = useNeuralStore((s) => s.sendMessage);
  const isThinking = useNeuralStore((s) => s.isThinking);
  const isListening = useNeuralStore((s) => s.isListening);
  const startListening = useNeuralStore((s) => s.startListening);
  const apiConfig = useNeuralStore((s) => s.apiConfig);
  const uploadFile = useNeuralStore((s) => s.uploadFile);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [text]);

  const isSendingRef = useRef(false);

  const handleSend = () => {
    if ((!text.trim() && pendingFiles.length === 0) || isThinking || isSendingRef.current) return;
    isSendingRef.current = true;
    const sendContent = text.trim() || (pendingFiles.length > 0 ? "Look at what I attached for you, Aiko!" : "");
    const sendFiles = pendingFiles.map(f => f.url);
    setText("");
    setPendingFiles([]);
    sendMessage(sendContent, sendFiles);
    setTimeout(() => {
      isSendingRef.current = false;
    }, 400);
  };

  const handleAttach = () => {
    fileInputRef.current?.click();
  };

  const handleImageAttach = () => {
    imageInputRef.current?.click();
  };

  const handlePaste = async (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
    const items = e.clipboardData?.items;
    if (!items) return;
    const imageFiles: File[] = [];
    for (const item of Array.from(items)) {
      if (item.kind === 'file' && item.type.startsWith('image/')) {
        const file = item.getAsFile();
        if (file) imageFiles.push(file);
      }
    }
    if (imageFiles.length === 0) return;
    e.preventDefault();
    setIsUploading(true);
    try {
      const newFiles: {url: string, filename: string, type: string}[] = [];
      for (const file of imageFiles) {
        const res = await uploadFile(file);
        newFiles.push(res);
      }
      setPendingFiles(prev => [...prev, ...newFiles]);
    } catch (err) {
      console.error("Clipboard image upload failed", err);
    } finally {
      setIsUploading(false);
    }
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
    <div className="w-full max-w-4xl mx-auto px-4 pb-3 pt-1">
      {/* Absolute glow bloom — invisible until focus */}
      <div className="relative group">
        <div className="absolute -inset-1 bg-[var(--p-accent)] blur-2xl rounded-3xl opacity-0 group-focus-within:opacity-[0.04] transition-opacity duration-300 pointer-events-none" />

        {/* Main dock shell — taste-skill: inset-hi top highlight, crisp 1px border */}
        <div className="relative flex flex-col gap-0 bg-[var(--bg-surface)] border border-[var(--b1)] rounded-[var(--p-radius)] shadow-[inset_0_1px_0_var(--p-inset-hi),0_8px_24px_-6px_rgba(0,0,0,0.5)] focus-within:border-[var(--b2)] transition-colors duration-150">

          {/* Top toolbar row */}
          <div className="flex items-center justify-between px-3 py-2 border-b border-[var(--b1)]">
            {/* Model pill */}
            <div className="flex items-center gap-1.5">
              <ModelPicker
                fallbackLabel={apiConfig.model}
                icon={<Sparkles size={10} className="text-[var(--p-accent)] shrink-0" />}
              />
            </div>

            {/* Controls */}
            <div className="flex items-center gap-1.5">
              <GothicButton
                icon="volume"
                size="sm"
                title={ttsEnabled ? "TTS Active" : "TTS Muted"}
                onClick={() => setTtsEnabled(!ttsEnabled)}
                active={ttsEnabled}
                className={!ttsEnabled ? "opacity-40 grayscale" : ""}
              />
              <div className="w-px h-3.5 bg-[var(--b1)] mx-0.5" />
              <GothicButton
                icon="mic"
                size="sm"
                onClick={() => { if (!isListening) startListening(); }}
                title={isListening ? "Listening..." : "Voice Input"}
                active={isListening}
                className={isListening ? "animate-pulse ring-1 ring-[var(--p-accent)] ring-offset-1 ring-offset-[var(--bg-surface)]" : ""}
              />
            </div>
          </div>

          {/* File attachment strip */}
          {(pendingFiles.length > 0 || isUploading) && (
            <div className="flex flex-wrap gap-2 px-3 py-2 border-b border-[var(--b1)]">
              {pendingFiles.map((file, idx) => (
                <div key={idx} className="relative group/file">
                  {file.type.startsWith('image/') ? (
                    <div className="w-14 h-14 rounded-[var(--p-radius-sm)] overflow-hidden border border-[var(--b1)] bg-[var(--bg-hover)]">
                      <img src={file.url} alt="preview" className="w-full h-full object-cover" />
                    </div>
                  ) : (
                    <div className="h-9 px-2.5 flex items-center gap-1.5 rounded-[var(--p-radius-sm)] bg-[var(--bg-hover)] border border-[var(--b1)] text-[11px] text-[var(--t3)]">
                      <Paperclip size={11} />
                      <span className="max-w-[80px] truncate">{file.filename}</span>
                    </div>
                  )}
                  <button
                    onClick={() => removeFile(idx)}
                    aria-label={`Remove file ${file.filename}`}
                    title="Remove file"
                    className="absolute -top-1.5 -right-1.5 w-4.5 h-4.5 rounded-full bg-[var(--red)]/90 text-white flex items-center justify-center opacity-0 group-hover/file:opacity-100 transition-opacity"
                  >
                    <X size={9} />
                  </button>
                </div>
              ))}
              {isUploading && (
                <div className="w-9 h-9 flex items-center justify-center animate-spin text-[var(--p-accent)]">
                  <Sparkles size={14} />
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
          <input
            type="file"
            ref={imageInputRef}
            onChange={onFileChange}
            multiple
            title="Image Upload"
            className="hidden"
            accept="image/png,image/jpeg,image/webp,image/gif,image/bmp"
          />

          {/* Textarea + action row */}
          <div className="flex items-end gap-2 px-2 pb-2 pt-1">
            <button
              onClick={handleAttach}
              aria-label="Attach file"
              title="Attach File or Document (+)"
              className="p-2 rounded-[var(--p-radius-sm)] text-[var(--t3)] hover:text-[var(--t1)] hover:bg-[var(--bg-hover)] transition-all duration-150 mb-1 shrink-0"
            >
              <Plus size={17} strokeWidth={2} />
            </button>

            <div className="relative mb-1 shrink-0">
              <button
                onClick={handleImageAttach}
                onContextMenu={(e) => {
                  e.preventDefault();
                  setShowGifPicker(!showGifPicker);
                }}
                aria-label="Upload image to chat"
                title="Send Image (Right-click for Stickers)"
                className={clsx(
                  "p-2 rounded-[var(--p-radius-sm)] transition-all duration-150",
                  showGifPicker || pendingFiles.length > 0
                    ? "text-[var(--p-accent)] bg-[var(--p-accent-soft)]"
                    : "text-[var(--t3)] hover:text-[var(--p-accent)] hover:bg-[var(--p-accent-soft)]"
                )}
              >
                <ImageIcon size={17} strokeWidth={2} className={clsx((showGifPicker || isUploading) && "animate-pulse")} />
              </button>

              <AnimatePresence>
                {showGifPicker && (
                  <GifPicker
                    onClose={() => setShowGifPicker(false)}
                    onUploadClick={() => {
                      setShowGifPicker(false);
                      handleImageAttach();
                    }}
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
              onPaste={handlePaste}
              onKeyDown={(e) => {
                if (e.nativeEvent.isComposing) return;
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              title="Message input"
              aria-label="Message input. Press Enter to send, Shift+Enter for new line."
              placeholder="Ask Aiko anything…"
              className="flex-1 text-[14px] text-[var(--t1)] placeholder:text-[var(--t4)] max-h-48 custom-scrollbar leading-[1.65] py-2.5 font-normal focus:outline-none bg-transparent border-none resize-none select-text"
              rows={1}
            />

            <GothicButton
              icon="send"
              size="md"
              onClick={handleSend}
              title="Send Message (Enter)"
              disabled={(!text.trim() && pendingFiles.length === 0) || isThinking || isUploading}
              className={clsx("mb-1 shrink-0", isThinking && "animate-pulse")}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
