import { create } from 'zustand';
import type { Project, FilterRound, FilterAgent } from '@/types';

interface ProjectStore {
  // Data
  projects: Project[];
  currentProject: Project | null;
  loading: boolean;
  error: string | null;

  // Filters
  filterRound: FilterRound;
  filterAgent: FilterAgent;

  // Actions
  setProjects: (projects: Project[]) => void;
  setCurrentProject: (project: Project | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setFilterRound: (round: FilterRound) => void;
  setFilterAgent: (agent: FilterAgent) => void;
  resetFilters: () => void;
}

export const useProjectStore = create<ProjectStore>((set) => ({
  projects: [],
  currentProject: null,
  loading: false,
  error: null,
  filterRound: 'all',
  filterAgent: 'all',

  setProjects: (projects) => set({ projects }),
  setCurrentProject: (currentProject) => set({ currentProject }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  setFilterRound: (filterRound) => set({ filterRound }),
  setFilterAgent: (filterAgent) => set({ filterAgent }),
  resetFilters: () => set({ filterRound: 'all', filterAgent: 'all' }),
}));
