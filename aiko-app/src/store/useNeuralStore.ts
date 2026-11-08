import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { resolveReplyEmotion } from '../animation/emotionProfile';
import { Message, Session, NeuralState } from './types';
import {
  getHubUrl,
  setHubUrl,
  getCachedToken,
  setCachedToken,
  fetchLocalToken,
  findActiveHubUrl,

  getAuthHeaders,
} from './hubClient';
import { createAvatarSlice } from './slices/avatarSlice';
import { createUiSettingsSlice } from './slices/uiSettingsSlice';

export type { Message, Session, NeuralState } from './types';
export { getHubUrl, resolveHubUrl, getAuthHeaders } from './hubClient';

let socket: WebSocket | null = null;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
let reconnectAttempts = 0;
let thinkingWatchdog: ReturnType<typeof setTimeout> | null = null;
let isConnecting = false;
let globalAudioCtx: AudioContext | null = null;

function startThinkingWatchdog() {
  if (thinkingWatchdog) clearTimeout(thinkingWatchdog);
  thinkingWatchdog = setTimeout(() => {
    if (useNeuralStore.getState().isThinking) {
      console.warn('[Aiko] Still waiting for the active response; keeping its request state intact.');
    }
    thinkingWatchdog = null;
  }, 45000);
}

function stopThinkingWatchdog() {
  if (thinkingWatchdog) {
    clearTimeout(thinkingWatchdog);
    thinkingWatchdog = null;
  }
}

function scheduleReconnect() {
  if (reconnectTimer) return;
  const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
  console.log(`[Aiko] Reconnecting in ${delay / 1000}s (attempt ${reconnectAttempts + 1})`);
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    reconnectAttempts++;
    connectSocket();
  }, delay);
}

async function connectSocket() {
  if (isConnecting) return;
  isConnecting = true;

  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }

  let activeUrl = getHubUrl();
  try {
    activeUrl = await findActiveHubUrl();
    setHubUrl(activeUrl);
  } catch (e) {
    console.warn('[Aiko] Port discovery failed, using default:', e);
  }

  let token = getCachedToken();
  if (!token) {
    token = await fetchLocalToken();
    setCachedToken(token);
  }
  if (!token) {
    isConnecting = false;
    return;
  }
  const wsUrl = activeUrl.replace('http', 'ws') + '/ws';

  if (socket) {
    const baseUrl = socket.url;
    if (
      baseUrl === wsUrl &&
      (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)
    ) {
      isConnecting = false;
      return;
    }
    if (baseUrl !== wsUrl) {
      try {
        socket.close();
      } catch (_) {}
      socket = null;
    }
  }

  try {
    socket = new WebSocket(wsUrl);
    let heartbeatInterval: ReturnType<typeof setInterval>;

    socket.onopen = () => {
      console.log('[Aiko] Neural Core Linked');
      isConnecting = false;
      reconnectAttempts = 0;
      useNeuralStore.setState({
        bridgeStatus: { status: 'connected', latency: 0, lastSeen: new Date().toISOString() },
      });

      const currentToken = getCachedToken();
      if (socket && currentToken) {
        socket.send(JSON.stringify({ type: 'auth', token: currentToken }));
      }
      if (socket) {
        socket.send(
          JSON.stringify({
            type: 'system',
            action: 'proactive_toggle',
            state: false,
            interval: 180,
          })
        );
      }

      heartbeatInterval = setInterval(() => {
        if (socket?.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ type: 'ping' }));
        }
      }, 15000);
    };

    socket.onclose = (event) => {
      console.log('[Aiko] Neural Core Decoupled', event.code);
      isConnecting = false;
      clearInterval(heartbeatInterval);
      stopThinkingWatchdog();
      if (event.code === 1008 || event.code === 4001) {
        setCachedToken(null);
      }
      useNeuralStore.setState({
        bridgeStatus: { status: 'disconnected', latency: 0, lastSeen: new Date().toISOString() },
        isThinking: false,
        streamingContent: '',
        streamingId: null,
        streamingSessionId: null,
      });
      scheduleReconnect();
    };

    socket.onerror = () => {
      stopThinkingWatchdog();
      useNeuralStore.setState({ isThinking: false });
      socket?.close();
    };

    socket.onmessage = (event) => {
      try {
        const raw = JSON.parse(event.data);
        const type = raw.type;
        const nestedData =
          typeof raw.payload === 'object' && raw.payload !== null
            ? raw.payload
            : typeof raw.data === 'object' && raw.data !== null
              ? raw.data
              : {};
        const data = { ...raw, ...nestedData };

        switch (type) {
          case 'chat_start':
            startThinkingWatchdog();
            useNeuralStore.setState({
              isThinking: true,
              streamingContent: '',
              streamingId: data.message_id || Date.now().toString(),
              streamingSessionId: data.session_id || null,
            });
            break;

          case 'chat_chunk':
            if (data.session_id && data.session_id !== useNeuralStore.getState().activeSessionId) break;
            useNeuralStore.setState((s) => ({
              streamingContent: s.streamingContent + (data.content || data.text || ''),
            }));
            break;

          case 'chat_token': {
            if (data.session_id && data.session_id !== useNeuralStore.getState().activeSessionId) break;
            startThinkingWatchdog();
            const tokenText = data.token || data.text || '';
            useNeuralStore.setState((s) => {
              const newContent = s.streamingContent + tokenText;
              let detectedEmotion = data.emotion || s.currentEmotion;
              const moodMatch = newContent.match(/<emotion>(.*?)<\/emotion>|\[mood:(.*?)\]/i);
              if (moodMatch) {
                const rawTag = (moodMatch[1] || moodMatch[2] || '').trim();
                if (rawTag) detectedEmotion = rawTag.toLowerCase();
              }
              return {
                streamingContent: newContent,
                currentEmotion: detectedEmotion,
              };
            });
            break;
          }

          case 'tts_chunk':
            break;

          case 'tts_audio': {
            if (typeof window !== 'undefined' && window.location.search.includes('mascot')) break;
            const audioUrl = (data.url as string).startsWith('http')
              ? data.url
              : `${getHubUrl()}${data.url}`;
            const audio = new Audio(audioUrl);
            audio.crossOrigin = 'anonymous';

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
                  const byte = dataArray[i];
                  if (byte !== undefined) {
                    const val = (byte - 128) / 128;
                    sum += val * val;
                  }
                }
                const rms = Math.sqrt(sum / dataArray.length);
                const amp = Math.min(1.0, rms * 15.0);
                useNeuralStore.setState({ amplitude: amp });
                animationId = requestAnimationFrame(updateAmplitude);
              };

              audio
                .play()
                .then(() => {
                  useNeuralStore.setState({ isTalking: true });
                  updateAmplitude();
                })
                .catch((e) => console.warn('[TTS] Blocked:', e));

              audio.onended = () => {
                if (animationId) cancelAnimationFrame(animationId);
                useNeuralStore.setState({ isTalking: false, amplitude: 0 });
                try {
                  source.disconnect();
                  analyser.disconnect();
                } catch (_) {}
              };
            } catch (e) {
              console.error('[TTS] WebAudio failed, using basic playback:', e);
              audio.play();
              useNeuralStore.setState({ isTalking: true });
              audio.onended = () => useNeuralStore.setState({ isTalking: false, amplitude: 0 });
            }
            break;
          }

          case 'chat_end': {
            stopThinkingWatchdog();
            const store2 = useNeuralStore.getState();
            const isProactive = data.proactive === true;
            const responseSessionId = data.session_id || store2.streamingSessionId;
            if (
              !isProactive &&
              responseSessionId &&
              store2.activeSessionId &&
              responseSessionId !== store2.activeSessionId
            ) {
              const preview = String(data.text || data.content || '').trim().slice(0, 60);
              useNeuralStore.setState((state) => ({
                sessions: state.sessions.map((session) =>
                  session.id === responseSessionId
                    ? { ...session, preview, lastActive: new Date().toISOString() }
                    : session
                ),
                streamingContent: '',
                streamingId: null,
                streamingSessionId: null,
                isThinking: false,
              }));
              break;
            }

            const serverContent =
              (typeof data.text === 'string' ? data.text : '') ||
              (typeof data.content === 'string' ? data.content : '');
            const finalContent = serverContent.trim()
              ? serverContent.trim()
              : isProactive
                ? ''
                : store2.streamingContent.trim();
            const emotion = resolveReplyEmotion(finalContent, data.emotion);
            if (!finalContent) {
              useNeuralStore.setState({
                streamingContent: '',
                streamingId: null,
                streamingSessionId: null,
                isThinking: false,
              });
              break;
            }
            const cleanedContent = finalContent
              .replace(/<think>[\s\S]*?<\/think>/gi, '')
              .replace(/<thought>[\s\S]*?<\/thought>/gi, '')
              .replace(/<emotion>.*?<\/emotion>/gi, '')
              .replace(/<\/?(emotion|think|thought)>/gi, '')
              .trim();
            const newMessage: Message = {
              role: 'assistant',
              content: cleanedContent,
              emotion,
              timestamp: new Date().toISOString(),
              id: store2.streamingId || undefined,
            };
            const previewText =
              cleanedContent.substring(0, 60).replace(/\n/g, ' ') +
              (cleanedContent.length > 60 ? '...' : '');
            useNeuralStore.setState((s) => {
              const updatedSessions = s.sessions.map((sess) => {
                if (sess.id === s.activeSessionId) {
                  return {
                    ...sess,
                    preview: previewText || 'Empty neural buffer...',
                    lastActive: new Date().toISOString(),
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
                streamingSessionId: null,
                isThinking: false,
                isTalking: false,
                currentEmotion: emotion,
              };
            });
            break;
          }

          case 'pong':
            break;

          case 'status':
            useNeuralStore.setState((s) => ({
              bridgeStatus: {
                ...s.bridgeStatus,
                status:
                  data.bridge_connected || data.status === 'connected' || data.status === 'online'
                    ? 'connected'
                    : 'disconnected',
              },
            }));
            break;

          case 'emotion':
            useNeuralStore.setState({ currentEmotion: data.emotion || data });
            break;

          case 'state':
            useNeuralStore.setState((s) => ({
              isThinking: data.thinking !== undefined ? data.thinking : s.isThinking,
              isListening: data.listening !== undefined ? data.listening : s.isListening,
            }));
            break;

          case 'tts_amplitude':
            useNeuralStore.setState({ amplitude: data.amplitude || 0 });
            break;

          case 'biological_sync':
            if (!useNeuralStore.getState().manualOverrideEnabled) {
              useNeuralStore.setState({
                chemicals: data.chemicals,
                isFlushing: data.is_flushing || false,
              });
            } else {
              useNeuralStore.setState({
                isFlushing: data.is_flushing || false,
              });
            }
            break;

          case 'tool_request':
            useNeuralStore.setState({
              pendingToolRequest: {
                requestId: data.request_id,
                toolName: data.tool_name,
                args: data.args,
              },
            });
            break;

          case 'stt_result': {
            const sttText = data.text || '';
            if (sttText.trim()) {
              useNeuralStore.getState().sendMessage(sttText);
            }
            break;
          }

          case 'error': {
            stopThinkingWatchdog();
            const errDetail = data.message || data.detail || 'An error occurred during processing.';
            console.warn('[Aiko] Server error event received:', errDetail);
            useNeuralStore.setState((s) => ({
              streamingContent: '',
              streamingId: null,
              isThinking: false,
              messages: [
                ...s.messages,
                {
                  role: 'system',
                  content: `⚠️ ${errDetail}`,
                  timestamp: new Date().toISOString(),
                },
              ],
            }));
            break;
          }
        }
      } catch (err) {
        console.error('[Aiko] Error parsing WebSocket message:', err);
      }
    };
  } catch (e) {
    isConnecting = false;
    console.warn('[Aiko] WebSocket init failed:', e);
    scheduleReconnect();
  }
}

export const useNeuralStore = create<NeuralState>()(
  persist(
    (set, get, api) => ({
      ...createAvatarSlice(set, get, api),
      ...createUiSettingsSlice(set, get, api),

      messages: [],
      sessions: [],
      activeSessionId: null,
      isThinking: false,
      isListening: false,
      streamingContent: '',
      streamingId: null,
      streamingSessionId: null,
      visionStreamActive: false,
      bridgeStatus: {
        status: 'disconnected',
        latency: 0,
        lastSeen: '',
      },
      pendingToolRequest: null,

      connect: (url) => {
        setHubUrl(url);
        connectSocket();
      },

      respondToToolRequest: (requestId, approved) => {
        if (socket && socket.readyState === WebSocket.OPEN) {
          socket.send(
            JSON.stringify({
              type: 'tool_response',
              request_id: requestId,
              approved,
            })
          );
        }
        set({ pendingToolRequest: null });
      },

      uploadFile: async (file) => {
        const formData = new FormData();
        formData.append('file', file);
        const headers = await getAuthHeaders();
        const res = await fetch(`${getHubUrl()}/api/upload`, {
          method: 'POST',
          headers,
          body: formData,
        });
        if (!res.ok) throw new Error('Upload failed');
        return await res.json();
      },

      sendMessage: (content, attachments) => {
        if (get().isThinking) return;
        const requestSessionId = get().activeSessionId;
        startThinkingWatchdog();
        const timestamp = new Date().toISOString();
        const userMsg: Message = { role: 'user', content, timestamp, attachments };
        const cleanedText = content.replace(/<emotion>.*?<\/emotion>/gi, '').trim();
        const shortPreview =
          cleanedText.substring(0, 60).replace(/\n/g, ' ') +
          (cleanedText.length > 60 ? '...' : '');

        set((state) => {
          const updatedMessages = [...state.messages, userMsg];
          const updatedSessions = state.sessions.map((sess) => {
            if (sess.id === state.activeSessionId) {
              return {
                ...sess,
                preview: shortPreview || 'Empty neural buffer...',
                lastActive: new Date().toISOString(),
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
            streamingContent: '',
            streamingSessionId: requestSessionId,
          };
        });

        const currentSession = get().sessions.find((s) => s.id === get().activeSessionId);
        if (
          currentSession &&
          (currentSession.title === 'New Conversation' || get().messages.length <= 1)
        ) {
          const newName =
            cleanedText.length > 25
              ? cleanedText.substring(0, 22) + '...'
              : cleanedText || 'New Conversation';
          get().renameSession(get().activeSessionId!, newName);
        }

        const payload = JSON.stringify({
          type: 'chat',
          text: content,
          attachments,
          session_id: requestSessionId,
        });

        if (socket && socket.readyState === WebSocket.OPEN) {
          socket.send(payload);
        } else {
          getAuthHeaders({ 'Content-Type': 'application/json' }).then((headers) => {
            fetch(`${getHubUrl()}/api/chat`, {
              method: 'POST',
              headers,
              body: JSON.stringify({
                message: content,
                user_id: 'master',
                session_id: requestSessionId,
                attachments,
              }),
            })
              .then((r) => r.json())
              .then((data) => {
                stopThinkingWatchdog();
                const reply = data.response || data.text || '';
                const emotion = resolveReplyEmotion(reply, data.emotion);
                if (requestSessionId !== get().activeSessionId) {
                  set((state) => ({
                    sessions: state.sessions.map((session) =>
                      session.id === requestSessionId
                        ? {
                            ...session,
                            preview: reply.slice(0, 60),
                            lastActive: new Date().toISOString(),
                          }
                        : session
                    ),
                    isThinking: false,
                    streamingContent: '',
                    streamingSessionId: null,
                  }));
                  return;
                }
                if (!reply) {
                  useNeuralStore.setState({ isThinking: false });
                  return;
                }
                const cleanedReply = reply
                  .replace(/<think>[\s\S]*?<\/think>/gi, '')
                  .replace(/<thought>[\s\S]*?<\/thought>/gi, '')
                  .replace(/<emotion>.*?<\/emotion>/gi, '')
                  .replace(/<\/?(emotion|think|thought)>/gi, '')
                  .trim();
                const aiMsg: Message = {
                  role: 'assistant',
                  content: cleanedReply,
                  emotion,
                  timestamp: new Date().toISOString(),
                };
                const replyPreview =
                  cleanedReply.substring(0, 60).replace(/\n/g, ' ') +
                  (cleanedReply.length > 60 ? '...' : '');
                useNeuralStore.setState((s) => {
                  const updatedSessions = s.sessions.map((sess) => {
                    if (sess.id === s.activeSessionId) {
                      return {
                        ...sess,
                        preview: replyPreview || 'Empty neural buffer...',
                        lastActive: new Date().toISOString(),
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
                    currentEmotion: emotion,
                  };
                });
              })
              .catch((err) => {
                stopThinkingWatchdog();
                console.error('[Aiko] Both WS and HTTP failed:', err);
                const errMsg: Message = {
                  role: 'system',
                  content: 'Neural Hub is offline. Start it with: python core/neural_hub.py',
                  timestamp: new Date().toISOString(),
                };
                useNeuralStore.setState((s) => ({
                  messages: [...s.messages, errMsg],
                  isThinking: false,
                }));
              });
          });
        }
      },

      loadSessions: async () => {
        try {
          const headers = await getAuthHeaders();
          const res = await fetch(`${getHubUrl()}/api/sessions`, { headers });
          const data = await res.json();
          const loadedSessions = Array.isArray(data.sessions) ? data.sessions : [];
          set({ sessions: loadedSessions });
          if (!get().activeSessionId && loadedSessions.length > 0) {
            get().switchSession(loadedSessions[0].id);
          }
        } catch (e) {
          console.error('Failed to load sessions', e);
          set({ sessions: [] });
        }
      },

      switchSession: async (id) => {
        try {
          const headers = await getAuthHeaders();
          const res = await fetch(`${getHubUrl()}/api/history?uid=${id}`, { headers });
          const data = await res.json();
          set({
            activeSessionId: id,
            messages: Array.isArray(data.history) ? data.history : [],
          });
        } catch (e) {
          console.error('Failed to switch session', e);
        }
      },

      createNewSession: async () => {
        const id = `session_${Date.now()}`;
        const newSession: Session = {
          id,
          title: 'New Conversation',
          preview: 'Empty neural buffer...',
          timestamp: 'Just now',
          pinned: false,
          lastActive: new Date().toISOString(),
        };
        set((state) => ({
          sessions: [newSession, ...(state.sessions || [])],
          activeSessionId: id,
          messages: [],
          streamingContent: '',
        }));
        try {
          const headers = await getAuthHeaders({ 'Content-Type': 'application/json' });
          await fetch(`${getHubUrl()}/api/sessions/create`, {
            method: 'POST',
            headers,
            body: JSON.stringify({ id, title: 'New Conversation' }),
          });
        } catch (_) {}
      },

      deleteSession: async (id) => {
        try {
          const headers = await getAuthHeaders();
          await fetch(`${getHubUrl()}/api/sessions/delete?id=${id}`, {
            method: 'DELETE',
            headers,
          });
          set((state) => ({
            sessions: (state.sessions || []).filter((s) => s.id !== id),
            activeSessionId: state.activeSessionId === id ? null : state.activeSessionId,
            messages: state.activeSessionId === id ? [] : state.messages,
          }));
        } catch (e) {
          console.error('Delete failed', e);
        }
      },

      pinSession: async (id) => {
        try {
          const headers = await getAuthHeaders({ 'Content-Type': 'application/json' });
          await fetch(`${getHubUrl()}/api/sessions/pin`, {
            method: 'POST',
            headers,
            body: JSON.stringify({ id }),
          });
          set((state) => ({
            sessions: (state.sessions || []).map((s) =>
              s.id === id ? { ...s, pinned: !s.pinned } : s
            ),
          }));
        } catch (e) {
          console.error('Pin failed', e);
        }
      },

      renameSession: async (id, newName) => {
        try {
          const headers = await getAuthHeaders({ 'Content-Type': 'application/json' });
          await fetch(`${getHubUrl()}/api/sessions/rename`, {
            method: 'POST',
            headers,
            body: JSON.stringify({ id, name: newName }),
          });
          set((state) => ({
            sessions: (state.sessions || []).map((s) =>
              s.id === id ? { ...s, title: newName } : s
            ),
          }));
        } catch (e) {
          console.error('Rename failed', e);
        }
      },

      triggerPurge: async () => {
        set({ messages: [], streamingContent: '' });
      },

      fetchBridgeStatus: async () => {
        try {
          const res = await fetch(`${getHubUrl()}/status`);
          const data = await res.json();
          set({ bridgeStatus: data.bridge || get().bridgeStatus });
        } catch (_) {}
      },

      editMessage: (id, newContent) => {
        set((state) => ({
          messages: state.messages.map((m) =>
            m.id === id || m.timestamp === id ? { ...m, content: newContent } : m
          ),
        }));
      },

      branchChat: (messageId, newContent) => {
        const state = get();
        const msgIdx = state.messages.findIndex(
          (m) => m.id === messageId || m.timestamp === messageId
        );
        if (msgIdx === -1) return;

        const newHistory = state.messages.slice(0, msgIdx);
        const timestamp = new Date().toISOString();
        const branchedUserMsg: Message = {
          role: 'user',
          content: newContent,
          timestamp,
          id: messageId,
        };

        set({
          messages: [...newHistory, branchedUserMsg],
          isThinking: true,
          streamingContent: '',
        });

        const payload = JSON.stringify({
          type: 'branch',
          message_id: messageId,
          text: newContent,
          session_id: state.activeSessionId,
        });

        const failBranch = (reason: string) => {
          stopThinkingWatchdog();
          console.error(reason);
          useNeuralStore.setState((s) => ({
            isThinking: false,
            streamingContent: '',
            streamingId: null,
            messages: [
              ...s.messages,
              {
                role: 'system',
                content: 'Neural Hub is offline. Start it with: python core/neural_hub.py',
                timestamp: new Date().toISOString(),
              },
            ],
          }));
        };

        if (socket && socket.readyState === WebSocket.OPEN) {
          startThinkingWatchdog();
          try {
            socket.send(payload);
          } catch (err) {
            failBranch(`[Aiko] Branch send failed: ${String(err)}`);
          }
        } else {
          failBranch('[Aiko] WebSocket offline; branching only works via WS for now.');
        }
      },

      startListening: () => {
        if (socket && socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ type: 'listen' }));
        } else {
          console.error('[Aiko] WebSocket offline; STT only works via WS for now.');
        }
      },

      reloadConfig: () => {
        if (socket && socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ type: 'system', action: 'reload_config' }));
        }
      },

      playTTS: (text) => {
        if (socket && socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ type: 'speak', text }));
        }
      },

      deleteMessage: (id) => {
        set((state) => ({
          messages: state.messages.filter((m) => m.id !== id && m.timestamp !== id),
        }));
      },

      retryMessage: () => {
        const lastUserMsg = [...get().messages].reverse().find((m: Message) => m.role === 'user');
        if (lastUserMsg) {
          get().sendMessage(lastUserMsg.content);
        }
      },

      toggleVisionStream: (active) => {
        set({ visionStreamActive: active });
        if (socket && socket.readyState === WebSocket.OPEN) {
          socket.send(
            JSON.stringify({
              type: 'system',
              action: 'proactive_toggle',
              state: active,
              interval: active ? 12 : 180,
            })
          );
        }
      },
    }),
    {
      name: 'neural-storage',
      version: 2,
      migrate: (persistedState: any) => {
        if (!persistedState || typeof persistedState !== 'object') return persistedState;
        const { apiConfig: _discardedCredentials, ...safeState } = persistedState;
        return safeState as NeuralState;
      },
      partialize: (state) => ({
        themeColor: state.themeColor,
        customBackground: state.customBackground,
        layoutMode: state.layoutMode,
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
        visionStreamActive: state.visionStreamActive,
      }),
    }
  )
);
