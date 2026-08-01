import React from 'react';
import useStore from '../store/useStore';
import JobCard from '../components/JobCard';

const SavedJobs = () => {
  const savedJobs = useStore((state) => state.savedJobs);

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
          {savedJobs.map((job, index) => (
            <JobCard key={job.id || index} job={job} />
          ))}
        </div>
      )}
    </div>
  );
};

export default SavedJobs;