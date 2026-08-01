import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const useStore = create(
  persist(
    (set) => ({
      savedJobs: [],
      isChatOpen: false,
      cvText: "", 
      
      setChatOpen: (isOpen) => set({ isChatOpen: isOpen }),
      setCvText: (text) => set({ cvText: text }),
      clearCvText: () => set({ cvText: "" }), // YENİ: CV silme fonksiyonu

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