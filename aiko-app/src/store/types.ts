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

export interface ChemicalsState {
  dopamine: number;
  serotonin: number;
  cortisol: number;
  adrenaline: number;
  oxytocin: number;
  melatonin: number;
}

export interface IntensityScalers {
  jitterIntensity: number;
  tearIntensity: number;
  leanIntensity: number;
  blushIntensity: number;
  poutIntensity: number;
  bobaIntensity: number;
  oxytocinIntensity: number;
  melatoninIntensity: number;
}

export interface ApiConfig {
  provider: string;
  model: string;
  endpoint: string;
  apiKey?: string;
  baseUrl?: string;
  ttsProvider: 'Pocket' | 'Gemini';
  ttsEnabled: boolean;
}

export interface BridgeStatus {
  status: 'connected' | 'disconnected';
  latency: number;
  lastSeen: string;
}

export interface NeuralState extends IntensityScalers {
  // Chat & Session State
  messages: Message[];
  sessions: Session[];
  activeSessionId: string | null;
  isThinking: boolean;
  isListening: boolean;
  streamingContent: string;
  streamingId: string | null;
  streamingSessionId: string | null;

  // Avatar & Biological State
  currentEmotion: string;
  isTalking: boolean;
  amplitude: number;
  chemicals: ChemicalsState;
  isFlushing: boolean;
  manualOverrideEnabled: boolean;
  avatarScale: number;

  // Project & System State
  projectStructure: any[];
  visionStreamActive: boolean;
  apiConfig: ApiConfig;
  bridgeStatus: BridgeStatus;
  pendingToolRequest: null | { requestId: string; toolName: string; args: any };

  // UI & Theme State
  isSidebarOpen: boolean;
  themeColor: string;
  customBackground: string | null;
  dynamicsIntensity: number;
  showAnimatedAssets: boolean;
  layoutMode: 'cinematic' | 'classic';

  // Actions
  toggleSidebar: () => void;
  setLayoutMode: (mode: 'cinematic' | 'classic') => void;
  setThemeColor: (color: string) => void;
  setCustomBackground: (bg: string | null) => void;
  updateSettings: (settings: Partial<NeuralState>) => void;
  connect: (url: string) => void;
  respondToToolRequest: (requestId: string, approved: boolean) => void;
  uploadFile: (file: File) => Promise<{ url: string; filename: string; type: string }>;
  sendMessage: (content: string, attachments?: string[]) => void;
  loadSessions: () => Promise<void>;
  switchSession: (id: string) => Promise<void>;
  createNewSession: () => Promise<void>;
  deleteSession: (id: string) => Promise<void>;
  pinSession: (id: string) => Promise<void>;
  renameSession: (id: string, newName: string) => Promise<void>;
  triggerPurge: () => Promise<void>;
  fetchProjectStructure: () => Promise<void>;
  updateApiConfig: (config: Partial<ApiConfig>) => void;
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
  updateChemicals: (chems: Partial<ChemicalsState>) => void;
  updateIntensityScalers: (scalers: Partial<IntensityScalers>) => void;
  setManualOverrideEnabled: (enabled: boolean) => void;
  toggleVisionStream: (active: boolean) => void;
}
