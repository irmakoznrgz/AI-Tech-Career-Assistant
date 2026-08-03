import React from 'react';
import { MapPin, Briefcase, Clock, Building2, ExternalLink, Heart, Layers } from 'lucide-react';
import useStore from '../store/useStore';

const JobCard = ({ job }) => {
  const { savedJobs, saveJob, removeJob, cvText } = useStore();
  
  const isSaved = savedJobs.some(s => s.id === job.id);

  const handleSaveToggle = () => {
    if (isSaved) {
      removeJob(job.id); 
    } else {
      saveJob(job);
    }
  };

  return (
    <div className="bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-2xl p-6 shadow-xl hover:border-emerald-500/30 transition-all flex flex-col justify-between group">
      <div>
        <div className="flex items-start justify-between gap-4 mb-3">
          <div>
            <h3 className="text-lg font-bold text-white group-hover:text-emerald-400 transition-colors leading-snug">
              {job.title}
            </h3>
            <div className="flex items-center gap-1.5 text-gray-400 text-sm mt-1">
              <Building2 size={14} className="text-emerald-400 shrink-0" />
              <span>{job.company}</span>
            </div>
          </div>
          
          {cvText && job.match_score && (
            <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold px-2.5 py-1 rounded-full shrink-0">
              %{job.match_score} Match
            </div>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2 mb-4">
       
          {job.location && job.location !== 'Unknown' && (
            <div className="flex items-center gap-1 bg-white/5 border border-white/10 text-gray-300 text-xs px-2.5 py-1 rounded-lg">
              <MapPin size={12} className="text-emerald-400" />
              <span>{job.location}</span>
            </div>
          )}

          {job.work_model && job.work_model !== 'Unknown' && (
            <div className="flex items-center gap-1 bg-white/5 border border-white/10 text-gray-300 text-xs px-2.5 py-1 rounded-lg">
              <Briefcase size={12} className="text-emerald-400" />
              <span>{job.work_model}</span>
            </div>
          )}

          {job.job_type && job.job_type !== 'Unknown' && (
            <div className="flex items-center gap-1 bg-white/5 border border-white/10 text-gray-300 text-xs px-2.5 py-1 rounded-lg">
              <Clock size={12} className="text-emerald-400" />
              <span>{job.job_type}</span>
            </div>
          )}

          {job.experience && job.experience !== 'Unknown' && (
            <div className="flex items-center gap-1 bg-white/5 border border-white/10 text-gray-300 text-xs px-2.5 py-1 rounded-lg">
              <Layers size={12} className="text-emerald-400" />
              <span>{job.experience}</span>
            </div>
          )}
          
        </div>
      </div>

      <div className="flex items-center justify-between pt-4 border-t border-white/5 mt-2">
        <a 
          href={job.link} 
          target="_blank" 
          rel="noopener noreferrer" 
          className="flex items-center gap-1.5 text-emerald-400 hover:text-emerald-300 text-sm font-semibold transition-colors"
        >
          <span>View Details</span>
          <ExternalLink size={14} />
        </a>

        <button 
          onClick={handleSaveToggle}
          className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-medium transition-all ${
            isSaved 
              ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' 
              : 'bg-white/5 hover:bg-white/10 text-gray-300 border border-white/10'
          }`}
        >
          <Heart size={14} className={isSaved ? 'fill-rose-400 text-rose-400' : ''} />
          <span>{isSaved ? 'Saved' : 'Save'}</span>
        </button>
      </div>
    </div>
  );
};

export default JobCard;