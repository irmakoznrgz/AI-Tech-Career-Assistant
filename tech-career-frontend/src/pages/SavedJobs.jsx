import React, { useState, useEffect } from 'react';
import useStore from '../store/useStore';
import JobCard from '../components/JobCard';
import { checkExpiredJobs } from '../services/api';
import { AlertTriangle } from 'lucide-react';

const SavedJobs = () => {
  const savedJobs = useStore((state) => state.savedJobs);
  const [expiredIds, setExpiredIds] = useState([]);

  useEffect(() => {
    const verifyJobs = async () => {
      if (savedJobs.length === 0) {
        setExpiredIds([]);
        return;
      }
      const idsToCheck = savedJobs.map(job => job.id);
      const expired = await checkExpiredJobs(idsToCheck);
      setExpiredIds(expired);
    };
    
    verifyJobs();
  }, [savedJobs]);

  return (
    <div className="pb-12">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-white drop-shadow-md mb-2">
          Saved Jobs <span className="text-emerald-400">({savedJobs.length})</span>
        </h2>
        <p className="text-gray-400">Manage your favorite opportunities.</p>
      </div>

      {savedJobs.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-gray-400 bg-slate-900/60 backdrop-blur-md border border-white/10 rounded-2xl">
          <p className="text-lg">You haven't saved any jobs yet.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {savedJobs.map((job, index) => {
            const isExpired = expiredIds.includes(job.id);
            
            return (
              <div key={job.id || index} className="relative group">
                
                {isExpired && (
                  <div className="absolute top-4 right-[65px] z-30 bg-rose-500/90 backdrop-blur-sm text-white text-[11px] uppercase tracking-wider font-bold px-3 py-1.5 rounded-lg flex items-center gap-1.5 shadow-xl border border-rose-400/50 pointer-events-none">
                    <AlertTriangle size={14} />
                    EXPIRED
                  </div>
                )}
                
                <div className={`h-full relative z-10 transition-all duration-300 ${isExpired ? 'opacity-60 grayscale' : ''}`}>
                  <JobCard job={job} />
                </div>

              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default SavedJobs;