import { create } from 'zustand';

interface PlayerState {
  seekToTime: number | null;
  setSeekToTime: (time: number) => void;
  clearSeekToTime: () => void;
}

export const usePlayerStore = create<PlayerState>((set) => ({
  seekToTime: null,
  setSeekToTime: (time) => set({ seekToTime: time }),
  clearSeekToTime: () => set({ seekToTime: null }),
}));
