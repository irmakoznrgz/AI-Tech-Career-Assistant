import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const useStore = create(
  persist(
    (set) => ({
      savedJobs: [],
      isChatOpen: false,
      cvText: "", 
      
      searchQuery: "",
      filters: {
        location: "",
        experience: "",
        domain: "",
        workModel: "",
        jobType: ""
      },

      setChatOpen: (isOpen) => set({ isChatOpen: isOpen }),
      setCvText: (text) => set({ cvText: text }),
      clearCvText: () => set({ cvText: "" }),

      setSearchQuery: (query) => set({ searchQuery: query }),
      setFilters: (newFilters) => set((state) => ({ 
        filters: { ...state.filters, ...newFilters } 
      })),
      resetFilters: () => set({
        searchQuery: "",
        filters: { location: "", experience: "", domain: "", workModel: "", jobType: "" }
      }),

      saveJob: (job) => set((state) => {
        const isAlreadySaved = state.savedJobs.find((j) => j.id === job.id || j.link === job.link);
        if (isAlreadySaved) return state;
        return { savedJobs: [...state.savedJobs, job] };
      }),
      
      removeJob: (jobId) => set((state) => ({
        savedJobs: state.savedJobs.filter((j) => j.id !== jobId && j.link !== jobId)
      })),
    }),
    { name: 'tech-career-storage' }
  )
);

export default useStore;