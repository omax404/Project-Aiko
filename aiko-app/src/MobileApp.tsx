import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Live2DAvatar } from './components/Live2DAvatar';
import { ChatBubble } from './components/ChatBubble';
import { useNeuralStore } from './store/useNeuralStore';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Send, Plus, ChevronDown, Settings, Zap, History } from 'lucide-react';

// OpenRouter direct call — no Python backend on mobile
async function callOpenRouter(messages: any[], apiKey: string, model: string): Promise<ReadableStream> {
  const resp = await fetch('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
      'HTTP-Referer': 'https://aiko-mobile.local',
      'X-Title': 'Aiko Mobile',
    },
    body: JSON.stringify({
      model,
      messages,
      stream: true,
    }),
  });
  if (!resp.ok) throw new Error(`OpenRouter error: ${resp.status}`);
  return resp.body!;
}

export default function MobileApp() {
  const { apiConfig } = useNeuralStore();
  const [text, setText] = useState('');
  const [localMessages, setLocalMessages] = useState<any[]>([]);
  const [streaming, setStreaming] = useState('');
  const [thinking, setThinking] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showSessions, setShowSessions] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const [emotion, setEmotion] = useState('neutral');

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [localMessages, streaming]);

  const handleSend = async () => {
    if (!text.trim() || thinking) return;
    const userText = text.trim();
    setText('');

    const userMsg = { role: 'user', content: userText, timestamp: new Date().toISOString() };
    setLocalMessages(prev => [...prev, userMsg]);
    setThinking(true);
    setStreaming('');

    // Build message history for API
    const history = localMessages.slice(-20).map(m => ({
      role: m.role === 'system' ? 'user' : m.role,
      content: m.content
    }));

    // Vivian's system prompt — matches desktop persona
    const systemPrompt = `You are Vivian (薇薇安), a warm, playful AI companion. You are helpful, creative, and have a sweet personality. You call the user "Master Omax". You can be playful and affectionate. Keep responses concise on mobile. Always respond in the same language as the user.`;

    const apiMessages = [
      { role: 'system', content: systemPrompt },
      ...history,
      { role: 'user', content: userText }
    ];

    try {
      const stream = await callOpenRouter(
        apiMessages,
        apiConfig.apiKey || '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',
        apiConfig.model || 'google/gemini-2.0-flash-exp:free'
      );

      const reader = stream.getReader();
      const decoder = new TextDecoder();
      let fullContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (!line.trim() || line === 'data: [DONE]') continue;
          if (line.startsWith('data: ')) {
            try {
              const parsed = JSON.parse(line.slice(6));
              const token = parsed.choices?.[0]?.delta?.content || '';
              if (token) {
                fullContent += token;
                setStreaming(fullContent);
              }
            } catch (_) {}
          }
        }
      }

      // Detect emotion from content
      const detectedEmotion = fullContent.includes('😊') || fullContent.includes('hehe') || fullContent.includes('love') ? 'happy'
        : fullContent.includes('😳') || fullContent.includes('blush') ? 'shy'
        : fullContent.includes('😢') || fullContent.includes('sorry') ? 'sad'
        : fullContent.includes('😤') || fullContent.includes('hmph') || fullContent.includes('baka') ? 'angry'
        : 'neutral';
      setEmotion(detectedEmotion);

      setLocalMessages(prev => [...prev, {
        role: 'assistant',
        content: fullContent,
        emotion: detectedEmotion,
        timestamp: new Date().toISOString()
      }]);
    } catch (err) {
      setLocalMessages(prev => [...prev, {
        role: 'system',
        content: `Neural connection failed: ${err}`,
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setStreaming('');
      setThinking(false);
    }
  };

  // Detect screen dimensions for Live2D sizing
  const screenW = window.innerWidth;
  const screenH = window.innerHeight;

  return (
    <div style={{
      width: '100vw', height: '100vh', overflow: 'hidden',
      background: '#0c0b0a', position: 'relative',
      fontFamily: "'DM Sans', system-ui, sans-serif"
    }}>
      {/* ── LAYER 0: Live2D full-screen background ─────── */}
      <div style={{
        position: 'absolute', inset: 0, zIndex: 0,
        pointerEvents: 'none', overflow: 'hidden',
        display: 'flex', alignItems: 'flex-end', justifyContent: 'flex-end',
      }}>
        {/* Gradient overlay — fades character into background on left */}
        <div style={{
          position: 'absolute', inset: 0, zIndex: 1,
          background: 'linear-gradient(to right, #0c0b0a 25%, transparent 70%)',
        }} />
        {/* Gradient overlay — fades bottom for chat area */}
        <div style={{
          position: 'absolute', bottom: 0, left: 0, right: 0, height: '60%', zIndex: 1,
          background: 'linear-gradient(to top, #0c0b0a 50%, transparent)',
        }} />
        <Live2DAvatar
          modelUrl="/live2d/vivian/薇薇安.model3.json"
          isThinking={thinking}
          emotion={emotion}
          width={screenW}
          height={screenH}
        />
      </div>

      {/* ── LAYER 1: Header bar ────────────────────────── */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, zIndex: 30,
        padding: 'env(safe-area-inset-top) 16px 0',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: 'linear-gradient(to bottom, rgba(12,11,10,0.8) 0%, transparent)',
        paddingTop: `calc(env(safe-area-inset-top, 0px) + 12px)`,
        paddingBottom: 12,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
           <button onClick={() => setShowSessions(true)} title="View Sessions" aria-label="View Sessions" style={{
                width: 36, height: 36, borderRadius: 10, background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.08)', display: 'flex',
                alignItems: 'center', justifyContent: 'center', color: 'rgba(255,255,255,0.4)'
            }}>
                <History size={16} />
            </button>
            <span style={{
                fontFamily: "'Pixelify Sans', cursive", fontSize: 16,
                color: 'rgba(212,149,106,0.9)', letterSpacing: 3
            }}>AIKO</span>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <div style={{
              display: 'flex', alignItems: 'center', gap: 6, padding: '4px 8px',
              borderRadius: 8, background: 'rgba(212,149,106,0.1)', border: '1px solid rgba(212,149,106,0.2)'
          }}>
              <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#ec4899' }} />
              <span style={{ fontSize: 9, color: '#ec4899', fontWeight: 'bold', textTransform: 'uppercase' }}>Neural Online</span>
          </div>
          <button onClick={() => setShowSettings(true)} title="Settings" aria-label="Settings" style={{
            width: 36, height: 36, borderRadius: 10, background: 'rgba(255,255,255,0.05)',
            border: '1px solid rgba(255,255,255,0.08)', display: 'flex',
            alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
            color: 'rgba(255,255,255,0.4)'
          }}>
            <Settings size={16} />
          </button>
        </div>
      </div>

      {/* ── LAYER 2: Chat messages ─────────────────────── */}
      <div style={{
        position: 'absolute', left: 0, right: 0, zIndex: 10,
        bottom: 110, // above input bar
        maxHeight: '60vh',
        overflowY: 'auto',
        padding: '16px 16px 0',
        WebkitOverflowScrolling: 'touch',
      }}>
        <AnimatePresence mode="popLayout" initial={false}>
          {localMessages.map((msg, i) => (
            <ChatBubble
              key={msg.timestamp + i}
              id={msg.timestamp}
              role={msg.role}
              content={msg.content}
              emotion={msg.emotion}
              timestamp={msg.timestamp}
            />
          ))}
        </AnimatePresence>

        {/* Streaming bubble */}
        {streaming && (
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
            style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
            <div style={{
              width: 32, height: 32, borderRadius: 10, flexShrink: 0, marginTop: 4,
              background: 'rgba(212,149,106,0.1)', border: '1px solid rgba(212,149,106,0.3)',
              display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <Zap size={14} style={{ color: '#ec4899' }} />
            </div>
            <div style={{ fontSize: 14, lineHeight: 1.7, color: 'rgba(237,232,223,0.9)' }}
              className="markdown-content selectable">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{streaming}</ReactMarkdown>
              <span style={{
                display: 'inline-block', width: 2, height: 14,
                background: '#ec4899', marginLeft: 2, verticalAlign: 'middle',
                animation: 'pulse 1s infinite'
              }} />
            </div>
          </motion.div>
        )}

        {/* Thinking indicator */}
        {thinking && !streaming && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            style={{ display: 'flex', gap: 8, padding: '8px 4px', alignItems: 'center' }}>
            {[0,1,2].map(i => (
              <div key={i} style={{
                width: 6, height: 6, borderRadius: '50%', background: 'rgba(212,149,106,0.5)',
                animation: `bounce 0.6s ${i * 0.15}s infinite`
              }} />
            ))}
          </motion.div>
        )}

        <div ref={chatEndRef} style={{ height: 20 }} />
      </div>

      {/* ── LAYER 3: Input bar ────────────────────────── */}
      <div style={{
        position: 'absolute', bottom: 0, left: 0, right: 0, zIndex: 20,
        padding: `12px 12px calc(env(safe-area-inset-bottom, 0px) + 12px)`,
        background: 'rgba(12,11,10,0.9)',
        backdropFilter: 'blur(20px)',
        borderTop: '1px solid rgba(255,255,255,0.06)',
      }}>
        <div style={{
          display: 'flex', alignItems: 'flex-end', gap: 10,
          background: 'rgba(255,255,255,0.04)',
          border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: 24, padding: '6px 6px 6px 16px',
        }}>
          {/* Attach */}
          <label style={{
            width: 40, height: 40, borderRadius: 14, flexShrink: 0, marginBottom: 0,
            background: 'rgba(255,255,255,0.05)', cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'rgba(255,255,255,0.4)', border: '1px solid rgba(255,255,255,0.05)'
          }}>
            <Plus size={20} />
            <input type="file" accept="image/*,.pdf,.txt" title="Attach file" aria-label="Attach file" style={{ display: 'none' }}
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) console.log('File selected:', file.name);
              }} />
          </label>

          {/* Text input */}
          <textarea
            ref={inputRef}
            value={text}
            onChange={e => setText(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Whisper to Aiko..."
            rows={1}
            style={{
              flex: 1, background: 'transparent', border: 'none', outline: 'none',
              boxShadow: 'none', resize: 'none', fontSize: 16, lineHeight: 1.5,
              color: 'rgba(237,232,223,0.9)', maxHeight: 120, overflowY: 'auto',
              padding: '10px 0', fontFamily: 'inherit',
              WebkitAppearance: 'none',
            }}
          />

          {/* Send */}
          <button onClick={handleSend} disabled={!text.trim() || thinking} title="Send Message" aria-label="Send Message"
            style={{
              width: 44, height: 44, borderRadius: 16, flexShrink: 0, marginBottom: 0,
              background: text.trim() && !thinking ? '#fff' : 'rgba(255,255,255,0.03)',
              border: 'none', cursor: text.trim() && !thinking ? 'pointer' : 'not-allowed',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: text.trim() && !thinking ? '#000' : 'rgba(255,255,255,0.1)',
              transition: 'all 200ms',
            }}>
            <Send size={18} />
          </button>
        </div>
      </div>

      {/* ── LAYER 4: Settings & Sessions Sheets ────────── */}
      <AnimatePresence>
        {(showSettings || showSessions) && (
          <>
             <motion.div 
               initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
               onClick={() => { setShowSettings(false); setShowSessions(false); }}
               style={{ position: 'absolute', inset: 0, zIndex: 40, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)' }} 
             />
             <motion.div
                initial={{ y: '100%' }} animate={{ y: 0 }} exit={{ y: '100%' }}
                transition={{ type: 'spring', damping: 28, stiffness: 300 }}
                style={{
                  position: 'absolute', bottom: 0, left: 0, right: 0, zIndex: 50,
                  background: '#141210', borderRadius: '24px 24px 0 0',
                  border: '1px solid rgba(255,255,255,0.08)',
                  padding: '24px 24px calc(env(safe-area-inset-bottom, 0px) + 24px)',
                  maxHeight: '80vh', overflowY: 'auto'
                }}>
                <div style={{ width: 40, height: 4, background: 'rgba(255,255,255,0.1)', borderRadius: 2, margin: '0 auto 20px' }} />
                
                {showSettings ? (
                    <div>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
                            <span style={{ fontSize: 18, fontWeight: 'bold', color: 'rgba(237,232,223,0.9)' }}>Neural Settings</span>
                            <button onClick={() => setShowSettings(false)} title="Close Settings" aria-label="Close Settings" style={{
                                width: 32, height: 32, borderRadius: 8, background: 'rgba(255,255,255,0.05)',
                                border: 'none', cursor: 'pointer', display: 'flex',
                                alignItems: 'center', justifyContent: 'center', color: 'rgba(255,255,255,0.5)'
                            }}>
                                <ChevronDown size={16} />
                            </button>
                        </div>
                        <div style={{ marginBottom: 16 }}>
                            <label style={{ fontSize: 11, color: 'rgba(212,149,106,0.7)', letterSpacing: 1, textTransform: 'uppercase', display: 'block', marginBottom: 12 }}>
                                Active Brain Model
                            </label>
                            {[
                                'google/gemini-2.0-flash-exp:free',
                                'meta-llama/llama-4-scout:free',
                                'deepseek/deepseek-chat-v3-0324:free',
                                'mistralai/mistral-7b-instruct:free'
                            ].map(m => (
                                <button key={m} onClick={() => { useNeuralStore.getState().updateApiConfig({ model: m }); setShowSettings(false); }}
                                style={{
                                    width: '100%', padding: '16px', borderRadius: 16, marginBottom: 10,
                                    background: apiConfig.model === m ? 'rgba(212,149,106,0.1)' : 'rgba(255,255,255,0.03)',
                                    border: `1px solid ${apiConfig.model === m ? 'rgba(212,149,106,0.4)' : 'rgba(255,255,255,0.07)'}`,
                                    cursor: 'pointer', textAlign: 'left', color: apiConfig.model === m ? '#ec4899' : 'rgba(255,255,255,0.5)',
                                    fontSize: 13, fontFamily: "'JetBrains Mono', monospace"
                                }}>
                                {m}
                                </button>
                            ))}
                        </div>
                    </div>
                ) : (
                    <div>
                         <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
                            <span style={{ fontSize: 18, fontWeight: 'bold', color: 'rgba(237,232,223,0.9)' }}>Neural History</span>
                            <button onClick={() => setShowSessions(false)} title="Close Sessions" aria-label="Close Sessions" style={{
                                width: 32, height: 32, borderRadius: 8, background: 'rgba(255,255,255,0.05)',
                                border: 'none', cursor: 'pointer', display: 'flex',
                                alignItems: 'center', justifyContent: 'center', color: 'rgba(255,255,255,0.5)'
                            }}>
                                <ChevronDown size={16} />
                            </button>
                        </div>
                        <p style={{ color: 'rgba(255,255,255,0.3)', fontSize: 13, textAlign: 'center', padding: '20px 0' }}>
                            Sessions are currently saved to local buffer.
                        </p>
                    </div>
                )}
            </motion.div>
          </>
        )}
      </AnimatePresence>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
        @keyframes bounce {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-4px); }
        }
        .markdown-content p { margin-bottom: 8px; }
        .markdown-content code { background: rgba(255,255,255,0.1); padding: 2px 4px; borderRadius: 4px; }
      `}</style>
    </div>
  );
}
