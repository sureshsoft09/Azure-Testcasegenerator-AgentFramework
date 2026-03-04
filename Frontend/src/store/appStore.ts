import { create } from 'zustand';
import { Project } from '../types';

interface AppState {
  // Projects
  projects: Project[];
  setProjects: (projects: Project[]) => void;

  // Active selections
  selectedProjectId: string | null;
  setSelectedProjectId: (id: string | null) => void;

  // Generate wizard
  generateStep: number;
  setGenerateStep: (step: number) => void;
  generateProjectId: string | null;
  setGenerateProjectId: (id: string | null) => void;
  generateSessionId: string | null;
  setGenerateSessionId: (id: string | null) => void;

  // Migrate wizard
  migrateStep: number;
  setMigrateStep: (step: number) => void;
  migrateSessionId: string | null;
  setMigrateSessionId: (id: string | null) => void;
  migrateProjectId: string | null;
  setMigrateProjectId: (id: string | null) => void;
  migrateColumns: string[];
  setMigrateColumns: (cols: string[]) => void;
}

export const useAppStore = create<AppState>((set) => ({
  projects: [],
  setProjects: (projects) => set({ projects }),

  selectedProjectId: null,
  setSelectedProjectId: (id) => set({ selectedProjectId: id }),

  generateStep: 1,
  setGenerateStep: (step) => set({ generateStep: step }),
  generateProjectId: null,
  setGenerateProjectId: (id) => set({ generateProjectId: id }),
  generateSessionId: null,
  setGenerateSessionId: (id) => set({ generateSessionId: id }),

  migrateStep: 1,
  setMigrateStep: (step) => set({ migrateStep: step }),
  migrateSessionId: null,
  setMigrateSessionId: (id) => set({ migrateSessionId: id }),
  migrateProjectId: null,
  setMigrateProjectId: (id) => set({ migrateProjectId: id }),
  migrateColumns: [],
  setMigrateColumns: (cols) => set({ migrateColumns: cols }),
}));
