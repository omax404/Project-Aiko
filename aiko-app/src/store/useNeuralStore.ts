import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  attachments?: string[];
  emotion?: string;
  timestamp: string;
  id?: string;
}

export interface Session {
  id: string;
  title: string;
  preview: string;
  timestamp: string;
  pinned: boolean;
  lastActive: string;
}

interface NeuralState {
  // Chat State
  messages: Message[];
  sessions: Session[];
  activeSessionId: string | null;
  isThinking: boolean;
  isListening: boolean;
  streamingContent: string;
  streamingId: string | null;
  currentEmotion: string;
  isTalking: boolean;
  amplitude: number;
  projectStructure: any[];
  chemicals: {
    dopamine: number;
    serotonin: number;
    cortisol: number;
    adrenaline: number;
    oxytocin: number;
    melatonin: number;
  };
  isFlushing: boolean;
  manualOverrideEnabled: boolean;
  jitterIntensity: number;
  tearIntensity: number;
  leanIntensity: number;
  blushIntensity: number;
  poutIntensity: number;
  bobaIntensity: number;
  oxytocinIntensity: number;
  melatoninIntensity: number;
  visionStreamActive: boolean;
  
  apiConfig: {
    provider: string;
    model: string;
    endpoint: string;
    apiKey?: string;
    baseUrl?: string;
    ttsProvider: 'Pocket' | 'Gemini';
    ttsEnabled: boolean;
  };
  bridgeStatus: {
    status: 'connected' | 'disconnected';
    latency: number;
    lastSeen: string;
  };
  isSidebarOpen: boolean;
  themeColor: string;
  dynamicsIntensity: number;
  showAnimatedAssets: boolean;
  avatarScale: number;
  pendingToolRequest: null | { requestId: string, toolName: string, args: any };

  // Actions
  toggleSidebar: () => void;
  setThemeColor: (color: string) => void;
  updateSettings: (settings: Partial<NeuralState>) => void;
  connect: (url: string) => void;
  respondToToolRequest: (requestId: string, approved: boolean) => void;
  uploadFile: (file: File) => Promise<{url: string, filename: string, type: string}>;
  sendMessage: (content: string, attachments?: string[]) => void;
  loadSessions: () => Promise<void>;
  switchSession: (id: string) => Promise<void>;
  createNewSession: () => Promise<void>;
  deleteSession: (id: string) => Promise<void>;
  pinSession: (id: string) => Promise<void>;
  renameSession: (id: string, newName: string) => Promise<void>;
  triggerPurge: () => Promise<void>;
  fetchProjectStructure: () => Promise<void>;
  updateApiConfig: (config: Partial<NeuralState['apiConfig']>) => void;
  fetchBridgeStatus: () => Promise<void>;
  setEmotion: (emotion: string) => void;
  editMessage: (id: string, newContent: string) => void;
  deleteMessage: (id: string) => void;
  retryMessage: () => void;
  branchChat: (messageId: string, newContent: string) => void;
  startListening: () => void;
  playTTS: (text: string) => void;
  setDynamicsIntensity: (intensity: number) => void;
  setAvatarScale: (scale: number) => void;
  setShowAnimatedAssets: (show: boolean) => void;
  fetchSettings: () => Promise<void>;
  reloadConfig: () => void;
  updateChemicals: (chems: Partial<NeuralState['chemicals']>) => void;
  updateIntensityScalers: (scalers: Partial<{ jitterIntensity: number, tearIntensity: number, leanIntensity: number, blushIntensity: number, poutIntensity: number, bobaIntensity: number, oxytocinIntensity: number, melatoninIntensity: number }>) => void;
  setManualOverrideEnabled: (enabled: boolean) => void;
  toggleVisionStream: (active: boolean) => void;
}

let socket: WebSocket | null = null;
let reconnectTimer: any = null;
let reconnectAttempts = 0;
export const getHubUrl = (): string => {
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    if (!window.location.port || window.location.port !== '1422') {
      return window.location.origin;
    }
  }
  const envPort = (import.meta as any).env?.VITE_AIKO_PORT;
  if (envPort) {
    return `http://127.0.0.1:${envPort}`;
  }
  return 'http://127.0.0.1:8000';
};

let hubUrl = getHubUrl();
let isConnecting = false;
let globalAudioCtx: AudioContext | null = null;

function scheduleReconnect() {
  if (reconnectTimer) return;
  const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
  console.log(`[Aiko] Reconnecting in ${delay/1000}s... (Attempt ${reconnectAttempts + 1})`);
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    reconnectAttempts++;
    connectSocket();
  }, delay);
}

function connectSocket() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  const wsUrl = hubUrl.replace('http', 'ws') + '/ws';

  if (socket) {
    if (socket.url === wsUrl && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
      return;
    }
    if (socket.url !== wsUrl) {
      console.log(`[Aiko] Link URL changed from ${socket.url} to ${wsUrl}. Re-linking...`);
      try {
        socket.close();
      } catch (_) {}
      socket = null;
    }
  }

  if (isConnecting) return;
  isConnecting = true;
  try {
    socket = new WebSocket(wsUrl);
    
    let heartbeatInterval: ReturnType<typeof setInterval>;

    socket.onopen = () => {
      console.log('[Aiko] Neural Core Linked');
      isConnecting = false;
      reconnectAttempts = 0;
      useNeuralStore.setState({ bridgeStatus: { status: 'connected', latency: 0, lastSeen: new Date().toISOString() } });
      
      // Sync initial visionStreamActive state to backend
      const active = useNeuralStore.getState().visionStreamActive;
      console.log(`[Aiko] Syncing initial visionStreamActive state to backend: ${active}`);
      if (socket) {
        socket.send(JSON.stringify({
          type: 'system',
          action: 'proactive_toggle',
          state: active,
          interval: active ? 45 : 180
        }));
      }

      // Heartbeat to keep connection alive
      heartbeatInterval = setInterval(() => {
        if (socket?.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ type: 'ping' }));
        }
      }, 15000);
    };

    socket.onclose = () => {
      console.log('[Aiko] Neural Core Decoupled');
      isConnecting = false;
      clearInterval(heartbeatInterval);
      useNeuralStore.setState({ bridgeStatus: { status: 'disconnected', latency: 0, lastSeen: new Date().toISOString() } });
      scheduleReconnect();
    };

    socket.onerror = () => {
      socket?.close();
    };
    socket.onmessage = (event) => {
      try {
        const raw = JSON.parse(event.data);
        // Neural Hub wraps as {type, data} — unwrap both formats (including standard payload)
        const type = raw.type;
        const data = raw.payload !== undefined 
          ? raw.payload 
          : (raw.data !== undefined ? raw.data : raw);
        switch (type) {
          case 'chat_start':
            useNeuralStore.setState({ isThinking: true, streamingContent: '', streamingId: data.message_id || Date.now().toString() });
            break;
          // chat_chunk = explicit token stream (future)
          case 'chat_chunk':
            useNeuralStore.setState((s) => ({ streamingContent: s.streamingContent + (data.content || data.text || '') }));
            break;
          case 'chat_token':
            useNeuralStore.setState((s) => ({
              streamingContent: s.streamingContent + (data.token || data.text || '') + ' ',
              isThinking: false,
              currentEmotion: data.emotion || s.currentEmotion
            }));
            break;
          case 'tts_chunk':
            useNeuralStore.setState({ isThinking: false });
            break;
          case 'tts_audio': {
            const audioUrl = (data.url as string).startsWith('http')
              ? data.url
              : `http://127.0.0.1:8000${data.url}`;
            const audio = new Audio(audioUrl);
            audio.crossOrigin = "anonymous";
            
            try {
              if (!globalAudioCtx) {
                const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
                globalAudioCtx = new AudioContextClass();
              }
              const audioCtx = globalAudioCtx;
              if (audioCtx.state === 'suspended') {
                audioCtx.resume();
              }
              const source = audioCtx.createMediaElementSource(audio);
              const analyser = audioCtx.createAnalyser();
              analyser.fftSize = 256;
              source.connect(analyser);
              analyser.connect(audioCtx.destination);
              
              const dataArray = new Uint8Array(analyser.frequencyBinCount);
              let animationId: number;
              
              const updateAmplitude = () => {
                analyser.getByteTimeDomainData(dataArray);
                let sum = 0;
                for (let i = 0; i < dataArray.length; i++) {
                  const val = (dataArray[i] - 128) / 128;
                  sum += val * val;
                }
                const rms = Math.sqrt(sum / dataArray.length);
                const amp = Math.min(1.0, rms * 15.0); // Boost for better visuals
                useNeuralStore.setState({ amplitude: amp });
                animationId = requestAnimationFrame(updateAmplitude);
              };
              
              audio.play().then(() => {
                useNeuralStore.setState({ isTalking: true });
                updateAmplitude();
              }).catch(e => console.warn("[TTS] Blocked:", e));
              
              audio.onended = () => {
                if (animationId) cancelAnimationFrame(animationId);
                useNeuralStore.setState({ isTalking: false, amplitude: 0 });
                try {
                  source.disconnect();
                  analyser.disconnect();
                } catch (_) {}
              };
            } catch (e) {
              console.error("[TTS] WebAudio failed, using basic playback:", e);
              audio.play();
              useNeuralStore.setState({ isTalking: true });
              audio.onended = () => useNeuralStore.setState({ isTalking: false, amplitude: 0 });
            }
            break;
          }
          case 'chat_end': {
            const store2 = useNeuralStore.getState();
            const isProactive = data.proactive === true;
            // For proactive messages (no chat_start was sent), use the event's own text.
            // For streamed messages, prefer accumulated streamingContent.
            const finalContent = isProactive
              ? (data.text || data.content || '').trim()
              : (store2.streamingContent.trim() || data.text || data.content || '');
            const emotion = data.emotion || 'neutral';
            if (!finalContent) {
              // Clear streaming state even if content is empty
              useNeuralStore.setState({ streamingContent: '', streamingId: null, isThinking: false });
              break;
            }
            const newMessage: Message = {
              role: 'assistant',
              content: finalContent,
              emotion,
              timestamp: new Date().toISOString(),
              id: store2.streamingId || undefined
            };
            const cleanedContent = finalContent.replace(/<emotion>.*?<\/emotion>/gi, '').trim();
            const previewText = cleanedContent.substring(0, 60).replace(/\n/g, ' ') + (cleanedContent.length > 60 ? '...' : '');
            useNeuralStore.setState((s) => {
              const updatedSessions = s.sessions.map((sess) => {
                if (sess.id === s.activeSessionId) {
                  return {
                    ...sess,
                    preview: previewText || "Empty neural buffer...",
                    lastActive: new Date().toISOString()
                  };
                }
                return sess;
              });
              updatedSessions.sort((a, b) => {
                const timeA = new Date(a.lastActive || 0).getTime();
                const timeB = new Date(b.lastActive || 0).getTime();
                return timeB - timeA;
              });
              return {
                messages: [...s.messages, newMessage],
                sessions: updatedSessions,
                streamingContent: '',
                streamingId: null,
                isThinking: false,
                isTalking: false,
                currentEmotion: emotion
              };
            });
            break;
          }
          case 'pong':
            // Latency tracking could be added here
            break;
          case 'status':
            useNeuralStore.setState((s) => ({ 
              bridgeStatus: { 
                ...s.bridgeStatus, 
                status: (data.bridge_connected || data.status === 'connected' || data.status === 'online') ? 'connected' : 'disconnected' 
              } 
            }));
            break;
          case 'emotion':
            useNeuralStore.setState({ currentEmotion: data.emotion || data });
            break;
          case 'state':
            // The backend sends {listening: true/false} and {thinking: true/false}
            useNeuralStore.setState((s) => ({
              isThinking: data.thinking !== undefined ? data.thinking : s.isThinking,
              isListening: data.listening !== undefined ? data.listening : s.isListening
            }));
            break;
          case 'tts_amplitude':
            useNeuralStore.setState({ amplitude: data.amplitude || 0 });
            break;
          case 'biological_sync':
            if (!useNeuralStore.getState().manualOverrideEnabled) {
              useNeuralStore.setState({ 
                chemicals: data.chemicals,
                isFlushing: data.is_flushing || false
              });
            } else {
              useNeuralStore.setState({ 
                isFlushing: data.is_flushing || false
              });
            }
            break;
          case 'tool_request':
            useNeuralStore.setState({
              pendingToolRequest: {
                requestId: data.request_id,
                toolName: data.tool_name,
                args: data.args
              }
            });
            break;
          case 'stt_result':
            const sttText = data.text || '';
            if (sttText.trim()) {
               useNeuralStore.getState().sendMessage(sttText);
            }
            break;
        }
      } catch (_) {}
    };
  } catch (e) {
    console.warn('[Aiko] WebSocket init failed:', e);
    scheduleReconnect();
  }
}

export const useNeuralStore = create<NeuralState>()(
  persist(
    (set, get) => ({
      isConnected: false,
      messages: [],
      sessions: [],
      activeSessionId: null,
      isThinking: false,
      isListening: false,
      streamingContent: "",
      streamingId: null,
      currentEmotion: "neutral",
      isTalking: false,
      amplitude: 0,
      chemicals: {
        dopamine: 0.5,
        serotonin: 0.5,
        cortisol: 0.2,
        adrenaline: 0.1,
        oxytocin: 0.3,
        melatonin: 0.1
      },
      isFlushing: false,
      manualOverrideEnabled: false,
      jitterIntensity: 0.4, // subtler default
      tearIntensity: 1.0,
      leanIntensity: 1.0,
      blushIntensity: 1.0,
      poutIntensity: 1.0,
      bobaIntensity: 1.0,
      oxytocinIntensity: 1.0,
      melatoninIntensity: 1.0,
      visionStreamActive: false,
      projectStructure: [],
      fetchProjectStructure: async () => {
        try {
          const res = await fetch(`${hubUrl}/api/project/structure`);
          const data = await res.json();
          set({ projectStructure: data.structure || [] });
        } catch (e) {
          set({ projectStructure: [] });
        }
      },
      apiConfig: {
        provider: "OpenRouter",
        model: "qwen3.5:cloud",
        endpoint: "http://127.0.0.1:11434/api/chat",
        apiKey: "",
        baseUrl: "https://openrouter.ai/api/v1",
        ttsProvider: "Pocket",
        ttsEnabled: true
      },
      bridgeStatus: {
        status: 'disconnected',
        latency: 0,
        lastSeen: "",
      },
      isSidebarOpen: true,
      themeColor: '#C9A8D9',
      dynamicsIntensity: 80,
      showAnimatedAssets: true,
      avatarScale: 1.0,
      pendingToolRequest: null,

      toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
      
      setThemeColor: (color: string) => {
        set({ themeColor: color });
        document.documentElement.style.setProperty('--acc', color);
        document.documentElement.style.setProperty('--accent', color);
        document.documentElement.style.setProperty('--acc2', color);
        // Also update soft glow versions if needed
        document.documentElement.style.setProperty('--acc-soft', `${color}1f`);
        document.documentElement.style.setProperty('--acc-glow', `${color}40`);
      },

      updateSettings: (settings) => set((state) => ({ ...state, ...settings })),

      connect: (url) => {
        hubUrl = url;
        connectSocket();
      },

      respondToToolRequest: (requestId: string, approved: boolean) => {
        if (socket && socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({
            type: 'tool_response',
            request_id: requestId,
            approved: approved
          }));
        }
        set({ pendingToolRequest: null });
      },

      uploadFile: async (file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        const res = await fetch(`${hubUrl}/api/upload`, {
          method: 'POST',
          body: formData
        });
        if (!res.ok) throw new Error('Upload failed');
        return await res.json();
      },

      sendMessage: (content, attachments) => {
        const timestamp = new Date().toISOString();
        const userMsg: Message = { role: 'user', content, timestamp, attachments };
        const cleanedText = content.replace(/<emotion>.*?<\/emotion>/gi, '').trim();
        const shortPreview = cleanedText.substring(0, 60).replace(/\n/g, ' ') + (cleanedText.length > 60 ? '...' : '');

        set((state) => {
          const updatedMessages = [...state.messages, userMsg];
          const updatedSessions = state.sessions.map((sess) => {
            if (sess.id === state.activeSessionId) {
              return {
                ...sess,
                preview: shortPreview || "Empty neural buffer...",
                lastActive: new Date().toISOString()
              };
            }
            return sess;
          });
          updatedSessions.sort((a, b) => {
            const timeA = new Date(a.lastActive || 0).getTime();
            const timeB = new Date(b.lastActive || 0).getTime();
            return timeB - timeA;
          });
          return {
            messages: updatedMessages,
            sessions: updatedSessions,
            isThinking: true,
            streamingContent: ''
          };
        });

        // Rename session dynamically on first message
        const currentSession = get().sessions.find(s => s.id === get().activeSessionId);
        if (currentSession && (currentSession.title === "New Conversation" || get().messages.length <= 1)) {
          const newName = cleanedText.length > 25 ? cleanedText.substring(0, 22) + "..." : (cleanedText || "New Conversation");
          get().renameSession(get().activeSessionId!, newName);
        }

        const payload = JSON.stringify({
          type: 'chat',
          text: content,
          attachments,
          session_id: get().activeSessionId
        });

        // Try WebSocket first — fall back to HTTP POST if socket not ready
        if (socket && socket.readyState === WebSocket.OPEN) {
          socket.send(payload);
        } else {
          // HTTP fallback — works even when WebSocket hasn't connected yet
          fetch(`${hubUrl}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: content, user_id: 'master', attachments: attachments })
          })
          .then(r => r.json())
          .then(data => {
            const reply = data.response || data.text || '';
            const emotion = data.emotion || 'neutral';
            if (!reply) return;
            const aiMsg: Message = {
              role: 'assistant', content: reply, emotion,
              timestamp: new Date().toISOString()
            };
            const cleanedReply = reply.replace(/<emotion>.*?<\/emotion>/gi, '').trim();
            const replyPreview = cleanedReply.substring(0, 60).replace(/\n/g, ' ') + (cleanedReply.length > 60 ? '...' : '');
            useNeuralStore.setState((s) => {
              const updatedSessions = s.sessions.map((sess) => {
                if (sess.id === s.activeSessionId) {
                  return {
                    ...sess,
                    preview: replyPreview || "Empty neural buffer...",
                    lastActive: new Date().toISOString()
                  };
                }
                return sess;
              });
              updatedSessions.sort((a, b) => {
                const timeA = new Date(a.lastActive || 0).getTime();
                const timeB = new Date(b.lastActive || 0).getTime();
                return timeB - timeA;
              });
              return {
                messages: [...s.messages, aiMsg],
                sessions: updatedSessions,
                isThinking: false,
                currentEmotion: emotion
              };
            });
          })
          .catch(err => {
            console.error('[Aiko] Both WS and HTTP failed:', err);
            const errMsg: Message = {
              role: 'system',
              content: 'Neural Hub is offline. Start it with: python core/neural_hub.py',
              timestamp: new Date().toISOString()
            };
            useNeuralStore.setState((s) => ({
              messages: [...s.messages, errMsg],
              isThinking: false
            }));
          });
        }
      },

      loadSessions: async () => {
        try {
          const res = await fetch(`${hubUrl}/api/sessions`);
          const data = await res.json();
          set({ sessions: data.sessions });
          if (!get().activeSessionId && data.sessions.length > 0) {
            get().switchSession(data.sessions[0].id);
          }
        } catch (e) { console.error("Failed to load sessions", e); }
      },

      switchSession: async (id) => {
        try {
          const res = await fetch(`${hubUrl}/api/history?uid=${id}`);
          const data = await res.json();
          set({ 
            activeSessionId: id,
            messages: data.history || []
          });
        } catch (e) { console.error("Failed to switch session", e); }
      },

      createNewSession: async () => {
        const id = `session_${Date.now()}`;
        const newSession: Session = {
          id,
          title: "New Conversation",
          preview: "Empty neural buffer...",
          timestamp: "Just now",
          pinned: false,
          lastActive: new Date().toISOString()
        };
        set((state) => ({
          sessions: [newSession, ...state.sessions],
          activeSessionId: id,
          messages: [],
          streamingContent: ""
        }));
        // Persist new session to backend
        try {
          await fetch(`${hubUrl}/api/sessions/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id, title: "New Conversation" })
          });
        } catch (_) {}
      },

      deleteSession: async (id) => {
        try {
          await fetch(`${hubUrl}/api/sessions/delete?id=${id}`, { method: 'DELETE' });
          set((state) => ({
            sessions: state.sessions.filter(s => s.id !== id),
            activeSessionId: state.activeSessionId === id ? null : state.activeSessionId,
            messages: state.activeSessionId === id ? [] : state.messages
          }));
        } catch (e) { console.error("Delete failed", e); }
      },

      pinSession: async (id) => {
        try {
          await fetch(`${hubUrl}/api/sessions/pin`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id })
          });
          set((state) => ({
            sessions: state.sessions.map(s => s.id === id ? { ...s, pinned: !s.pinned } : s)
          }));
        } catch (e) { console.error("Pin failed", e); }
      },

      renameSession: async (id, newName) => {
        try {
          await fetch(`${hubUrl}/api/sessions/rename`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id, name: newName })
          });
          set((state) => ({
            sessions: state.sessions.map(s => s.id === id ? { ...s, title: newName } : s)
          }));
        } catch (e) { console.error("Rename failed", e); }
      },

      triggerPurge: async () => {
        set({ messages: [], streamingContent: "" });
      },

      updateApiConfig: (config) => set((state) => ({ apiConfig: { ...state.apiConfig, ...config } })),

      fetchBridgeStatus: async () => {
        try {
          const res = await fetch(`${hubUrl}/status`);
          const data = await res.json();
          set({ bridgeStatus: data.bridge || get().bridgeStatus });
        } catch (e) {}
      },

      setEmotion: (emotion) => set({ currentEmotion: emotion }),

      editMessage: (id, newContent) => {
        set((state) => ({
          messages: state.messages.map(m => (m.id === id || m.timestamp === id) ? { ...m, content: newContent } : m)
        }));
      },

      branchChat: (messageId, newContent) => {
        const state = get();
        const msgIdx = state.messages.findIndex(m => m.id === messageId || m.timestamp === messageId);
        if (msgIdx === -1) return;
        
        // Truncate locally up to the edited message, replace it, and set thinking state
        const newHistory = state.messages.slice(0, msgIdx);
        const timestamp = new Date().toISOString();
        const branchedUserMsg: Message = { role: 'user', content: newContent, timestamp, id: messageId };
        
        set({
          messages: [...newHistory, branchedUserMsg],
          isThinking: true,
          streamingContent: ''
        });

        // Send branch command to NeuralHub
        const payload = JSON.stringify({
          type: 'branch',
          message_id: messageId,
          text: newContent,
          session_id: state.activeSessionId
        });

        if (socket && socket.readyState === WebSocket.OPEN) {
          socket.send(payload);
        } else {
          console.error("[Aiko] WebSocket offline; branching only works via WS for now.");
        }
      },

      startListening: () => {
        if (socket && socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ type: 'listen' }));
        } else {
          console.error("[Aiko] WebSocket offline; STT only works via WS for now.");
        }
      },

      reloadConfig: () => {
        if (socket && socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ type: 'system', action: 'reload_config' }));
        }
      },

      playTTS: (text: string) => {
        if (socket && socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ type: 'speak', text }));
        }
      },

      deleteMessage: (id) => {
        set((state) => ({
          messages: state.messages.filter(m => m.id !== id && m.timestamp !== id)
        }));
      },

      retryMessage: () => {
        const lastUserMsg = [...get().messages].reverse().find((m: Message) => m.role === 'user');
        if (lastUserMsg) {
          get().sendMessage(lastUserMsg.content);
        }
      },

      setDynamicsIntensity: (intensity) => set({ dynamicsIntensity: intensity }),
      setAvatarScale: (scale: number) => set({ avatarScale: scale }),
      setShowAnimatedAssets: (show: boolean) => set({ showAnimatedAssets: show }),
      fetchSettings: async () => {
        try {
          const res = await fetch(`${hubUrl}/api/settings`);
          const data = await res.json();
          set((state) => ({
            apiConfig: {
              ...state.apiConfig,
              provider: data.PROVIDER || state.apiConfig.provider,
              apiKey: data.API_KEY || data.DEEPSEEK_API_KEY || data.GEMINI_API_KEY || state.apiConfig.apiKey,
              model: data.MODEL_NAME || state.apiConfig.model,
            },
            themeColor: data.appearance?.theme_color || data.theme_color || state.themeColor,
            avatarScale: data.appearance?.avatar_scale || data.avatar_scale || state.avatarScale,
            dynamicsIntensity: data.appearance?.dynamics_intensity || data.dynamics_intensity || state.dynamicsIntensity,
            showAnimatedAssets: data.appearance?.show_animated_assets !== undefined ? data.appearance.show_animated_assets : (data.show_animated_assets !== undefined ? data.show_animated_assets : state.showAnimatedAssets),
          }));
        } catch (e) {
          console.error("Failed to fetch settings", e);
        }
      },

      updateChemicals: (chems) => {
        set((state) => ({
          chemicals: {
            ...state.chemicals,
            ...chems
          }
        }));
      },

      updateIntensityScalers: (scalers) => {
        set((state) => ({
          ...state,
          ...scalers
        }));
      },

      setManualOverrideEnabled: (enabled) => {
        set({ manualOverrideEnabled: enabled });
      },

      toggleVisionStream: (active) => {
        set({ visionStreamActive: active });
        if (socket && socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({
            type: 'system',
            action: 'proactive_toggle',
            state: active,
            interval: active ? 45 : 180
          }));
        }
      }
    }),
    {
      name: 'neural-storage',
      partialize: (state) => ({ 
        apiConfig: state.apiConfig,
        themeColor: state.themeColor,
        isSidebarOpen: state.isSidebarOpen,
        dynamicsIntensity: state.dynamicsIntensity,
        showAnimatedAssets: state.showAnimatedAssets,
        avatarScale: state.avatarScale,
        jitterIntensity: state.jitterIntensity,
        tearIntensity: state.tearIntensity,
        leanIntensity: state.leanIntensity,
        blushIntensity: state.blushIntensity,
        poutIntensity: state.poutIntensity,
        bobaIntensity: state.bobaIntensity,
        oxytocinIntensity: state.oxytocinIntensity,
        melatoninIntensity: state.melatoninIntensity,
        manualOverrideEnabled: state.manualOverrideEnabled,
        visionStreamActive: state.visionStreamActive
      }),
    }
  )
);
