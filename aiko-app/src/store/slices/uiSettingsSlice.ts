import { StateCreator } from 'zustand';
import { NeuralState, ApiConfig } from '../types';
import { getHubUrl, getAuthHeaders } from '../hubClient';

export interface UiSettingsSlice {
  isSidebarOpen: boolean;
  themeColor: string;
  customBackground: string | null;
  dynamicsIntensity: number;
  showAnimatedAssets: boolean;
  layoutMode: 'cinematic' | 'classic';
  projectStructure: any[];
  apiConfig: ApiConfig;
  toggleSidebar: () => void;
  setLayoutMode: (mode: 'cinematic' | 'classic') => void;
  setCustomBackground: (bg: string | null) => void;
  setThemeColor: (color: string) => void;
  setDynamicsIntensity: (intensity: number) => void;
  setShowAnimatedAssets: (show: boolean) => void;
  updateSettings: (settings: Partial<NeuralState>) => void;
  updateApiConfig: (config: Partial<ApiConfig>) => void;
  fetchProjectStructure: () => Promise<void>;
  fetchSettings: () => Promise<void>;
}

export const createUiSettingsSlice: StateCreator<NeuralState, [], [], UiSettingsSlice> = (set) => ({
  isSidebarOpen: true,
  themeColor: '#C9A8D9',
  customBackground: null,
  dynamicsIntensity: 80,
  showAnimatedAssets: true,
  layoutMode: 'cinematic',
  projectStructure: [],
  apiConfig: {
    provider: 'OpenRouter',
    model: 'qwen3.5:cloud',
    endpoint: 'http://127.0.0.1:11434/api/chat',
    apiKey: '',
    baseUrl: 'https://openrouter.ai/api/v1',
    ttsProvider: 'Pocket',
    ttsEnabled: true,
  },

  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  setLayoutMode: (mode) => set({ layoutMode: mode }),
  setCustomBackground: (bg) => set({ customBackground: bg }),
  setThemeColor: (color) => {
    set({ themeColor: color });
    if (typeof document !== 'undefined') {
      document.documentElement.style.setProperty('--acc', color);
      document.documentElement.style.setProperty('--accent', color);
      document.documentElement.style.setProperty('--acc2', color);
      document.documentElement.style.setProperty('--acc-soft', `${color}1f`);
      document.documentElement.style.setProperty('--acc-glow', `${color}40`);
    }
  },
  setDynamicsIntensity: (intensity) => set({ dynamicsIntensity: intensity }),
  setShowAnimatedAssets: (show) => set({ showAnimatedAssets: show }),
  updateSettings: (settings) => set((state) => ({ ...state, ...settings })),
  updateApiConfig: (config) =>
    set((state) => ({ apiConfig: { ...state.apiConfig, ...config } })),

  fetchProjectStructure: async () => {
    try {
      const headers = await getAuthHeaders();
      const res = await fetch(`${getHubUrl()}/api/project/structure`, { headers });
      const data = await res.json();
      set({ projectStructure: data.structure || [] });
    } catch (_) {
      set({ projectStructure: [] });
    }
  },

  fetchSettings: async () => {
    try {
      const headers = await getAuthHeaders();
      const res = await fetch(`${getHubUrl()}/api/settings`, { headers });
      const data = await res.json();
      set((state) => ({
        apiConfig: {
          ...state.apiConfig,
          provider: data.PROVIDER || state.apiConfig.provider,
          apiKey:
            data.API_KEY ||
            data.DEEPSEEK_API_KEY ||
            data.GEMINI_API_KEY ||
            state.apiConfig.apiKey,
          model: data.MODEL_NAME || state.apiConfig.model,
        },
        themeColor: data.appearance?.theme_color || data.theme_color || state.themeColor,
        avatarScale: data.appearance?.avatar_scale || data.avatar_scale || state.avatarScale,
        dynamicsIntensity:
          data.appearance?.dynamics_intensity ||
          data.dynamics_intensity ||
          state.dynamicsIntensity,
        showAnimatedAssets:
          data.appearance?.show_animated_assets !== undefined
            ? data.appearance.show_animated_assets
            : data.show_animated_assets !== undefined
              ? data.show_animated_assets
              : state.showAnimatedAssets,
      }));
    } catch (e) {
      console.error('Failed to fetch settings', e);
    }
  },
});
