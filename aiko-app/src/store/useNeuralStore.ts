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

export interface Relationship {
  affection: number;
  level: string;
  points: number;
}

export interface SystemStats {
  hardware: {
    cpu: { usage: number; cores: number; temp: number };
    ram: { total: number; used: number; percent: number };
    disk: { total: number; used: number; percent: number };
  };
  neural: {
    memories: number;
    thoughts: number;
    uptime: number;
    synapses: number;
  };
  activity: {
    commits: number;
    prs: number;
    issues: number;
    last_push: string;
  };
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
  };
  isFlushing: boolean;
  
  
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
  relationship: Relationship;
  isSidebarOpen: boolean;
  themeColor: string;
  dynamicsIntensity: number;
  showAnimatedAssets: boolean;
  avatarScale: number;
  systemStats: SystemStats | null;

  // Actions
  toggleSidebar: () => void;
  setThemeColor: (color: string) => void;
  updateSettings: (settings: Partial<NeuralState>) => void;
  connect: (url: string) => void;
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
  fetchRelationship: () => Promise<void>;
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
  fetchSystemStats: () => Promise<void>;
}

let socket: WebSocket | null = null;
let reconnectTimer: any = null;
let reconnectAttempts = 0;
const isTauri = typeof window !== 'undefined' && !!(window as any).__TAURI__;
let hubUrl = isTauri ? 'http://127.0.0.1:8000' : (typeof window !== 'undefined' ? window.location.origin : 'http://127.0.0.1:8000');
let isConnecting = false;

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
  if (isConnecting) return;
  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) return;
  
  isConnecting = true;
  try {
    const wsUrl = hubUrl.replace('http', 'ws') + '/ws';
    socket = new WebSocket(wsUrl);
    
    let heartbeatInterval: ReturnType<typeof setInterval>;

    socket.onopen = () => {
      console.log('[Aiko] Neural Core Linked');
      isConnecting = false;
      reconnectAttempts = 0;
      useNeuralStore.setState({ bridgeStatus: { status: 'connected', latency: 0, lastSeen: new Date().toISOString() } });
      
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
        // Neural Hub wraps as {type, data} — unwrap both formats
        const type = raw.type;
        const data = raw.data !== undefined ? raw.data : raw;
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
            // Consolidated high-performance TTS audio & lip-sync handler
            const audioUrl = (data.url as string).startsWith('http')
              ? data.url
              : `http://127.0.0.1:8000${data.url}`;
            const audio = new Audio(audioUrl);
            audio.crossOrigin = "anonymous";
            
            // Mute the mascot window to prevent double playback echo,
            // while still allowing WebAudio Analyser to capture lip-sync data.
            const isMascot = typeof window !== 'undefined' && window.location.search.includes('mascot');
            if (isMascot) {
               audio.muted = true;
            }
            
            try {
              const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
              const audioCtx = new AudioContext();
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
                audioCtx.close(); // Clean up context
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
            const finalContent = store2.streamingContent.trim() || data.text || data.content || '';
            const emotion = data.emotion || 'neutral';
            if (!finalContent) break;
            const newMessage: Message = {
              role: 'assistant',
              content: finalContent,
              emotion,
              timestamp: new Date().toISOString(),
              id: store2.streamingId || undefined
            };
            useNeuralStore.setState((s) => ({
              messages: [...s.messages, newMessage],
              streamingContent: '',
              streamingId: null,
              isThinking: false,
              isTalking: false,
              currentEmotion: emotion
            }));
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
            useNeuralStore.setState({ 
              chemicals: data.chemicals,
              isFlushing: data.is_flushing || false
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
        adrenaline: 0.1
      },
      isFlushing: false,
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
      relationship: {
        affection: 85,
        level: "Devoted",
        points: 1250
      },
      isSidebarOpen: true,
      themeColor: '#ec4899',
      dynamicsIntensity: 80,
      showAnimatedAssets: true,
      avatarScale: 1.0,
      systemStats: null,

      toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
      
      setThemeColor: (color: string) => {
        set({ themeColor: color });
        document.documentElement.style.setProperty('--acc', color);
        // Also update soft glow versions if needed
        document.documentElement.style.setProperty('--acc-soft', `${color}1f`);
        document.documentElement.style.setProperty('--acc-glow', `${color}40`);
      },

      updateSettings: (settings) => set((state) => ({ ...state, ...settings })),

      connect: (url) => {
        hubUrl = url;
        connectSocket();
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

        set((state) => ({
          messages: [...state.messages, userMsg],
          isThinking: true,
          streamingContent: ''
        }));

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
            body: JSON.stringify({ message: content, user_id: 'omax' })
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
            useNeuralStore.setState((s) => ({
              messages: [...s.messages, aiMsg],
              isThinking: false,
              currentEmotion: emotion
            }));
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

      fetchSystemStats: async () => {
        try {
          const res = await fetch(`${hubUrl}/api/system/stats`);
          const data = await res.json();
          set({ systemStats: data });
        } catch (e) {
          console.error("Failed to fetch system stats", e);
        }
      },

      fetchRelationship: async () => {
        try {
          const res = await fetch(`${hubUrl}/api/relationship`);
          const data = await res.json();
          set({ relationship: data || get().relationship });
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
      setAvatarScale: (scale) => set({ avatarScale: scale }),
      setShowAnimatedAssets: (show) => set({ showAnimatedAssets: show }),
    }),
    {
      name: 'neural-storage',
      partialize: (state) => ({ 
        apiConfig: state.apiConfig,
        relationship: state.relationship,
        themeColor: state.themeColor,
        isSidebarOpen: state.isSidebarOpen,
        dynamicsIntensity: state.dynamicsIntensity,
        showAnimatedAssets: state.showAnimatedAssets,
        avatarScale: state.avatarScale,
        // sessions intentionally excluded — always loaded fresh from backend
      }),
    }
  )
);
