import { StateCreator } from 'zustand';
import { NeuralState, ChemicalsState, IntensityScalers } from '../types';

export interface AvatarSlice {
  currentEmotion: string;
  isTalking: boolean;
  amplitude: number;
  chemicals: ChemicalsState;
  isFlushing: boolean;
  manualOverrideEnabled: boolean;
  avatarScale: number;
  jitterIntensity: number;
  tearIntensity: number;
  leanIntensity: number;
  blushIntensity: number;
  poutIntensity: number;
  bobaIntensity: number;
  oxytocinIntensity: number;
  melatoninIntensity: number;
  setEmotion: (emotion: string) => void;
  setAvatarScale: (scale: number) => void;
  updateChemicals: (chems: Partial<ChemicalsState>) => void;
  updateIntensityScalers: (scalers: Partial<IntensityScalers>) => void;
  setManualOverrideEnabled: (enabled: boolean) => void;
}

export const createAvatarSlice: StateCreator<NeuralState, [], [], AvatarSlice> = (set) => ({
  currentEmotion: 'neutral',
  isTalking: false,
  amplitude: 0,
  chemicals: {
    dopamine: 0.5,
    serotonin: 0.5,
    cortisol: 0.2,
    adrenaline: 0.1,
    oxytocin: 0.3,
    melatonin: 0.1,
  },
  isFlushing: false,
  manualOverrideEnabled: false,
  avatarScale: 1.0,
  jitterIntensity: 0.4,
  tearIntensity: 1.0,
  leanIntensity: 1.0,
  blushIntensity: 1.0,
  poutIntensity: 1.0,
  bobaIntensity: 1.0,
  oxytocinIntensity: 1.0,
  melatoninIntensity: 1.0,

  setEmotion: (emotion) => set({ currentEmotion: emotion }),
  setAvatarScale: (scale) => set({ avatarScale: scale }),
  updateChemicals: (chems) =>
    set((state) => ({
      chemicals: {
        ...state.chemicals,
        ...chems,
      },
    })),
  updateIntensityScalers: (scalers) =>
    set((state) => ({
      ...state,
      ...scalers,
    })),
  setManualOverrideEnabled: (enabled) => set({ manualOverrideEnabled: enabled }),
});
