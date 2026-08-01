import React from 'react';
import { Heart, MapPin, Building, Briefcase, ExternalLink } from 'lucide-react';
import useStore from '../store/useStore';

const JobCard = ({ job }) => {
  const { savedJobs, saveJob, removeJob } = useStore();
  const isSaved = (savedJobs || []).some(saved => saved.link === job.link || saved.id === job.id);

  const handleSaveToggle = () => isSaved ? removeJob(job.id || job.link) : saveJob(job);

  return (
    // Kart boyutunu daraltıp daha modern bir görünüm verdik
    <div className="bg-slate-900/40 backdrop-blur-md border border-white/10 rounded-2xl p-5 transition-all duration-300 hover:bg-slate-800/60 hover:border-emerald-500/30 flex flex-col justify-between h-full">
      <div>
        <div className="flex justify-between items-start mb-4 gap-3">
          <div className="flex-1">
            <h3 className="text-lg font-bold text-white line-clamp-2 leading-tight">{job.title || 'Unknown Title'}</h3>
            <div className="flex items-center gap-1.5 text-gray-400 mt-2 text-sm">
              <Building size={14} />
              <span className="truncate">{job.company || 'Unknown Company'}</span>
            </div>
          </div>
          
          {/* LOGO veya BİNA EMOJİSİ - Hata yakalayıcı (onError) eklendi */}
          <div className="w-10 h-10 shrink-0 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center text-xl overflow-hidden p-1">
            {job.logo && str(job.logo).length > 5 ? (
              <img 
                src={job.logo} 
                alt="Logo" 
                className="w-full h-full object-contain" 
                onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'block'; }} 
              />
            ) : null}
            <span style={{ display: (job.logo && str(job.logo).length > 5) ? 'none' : 'block' }}>🏢</span>
          </div>
        </div>

        <div className="flex flex-wrap gap-1.5 mb-5 mt-3">
          <span className="flex items-center gap-1 bg-white/5 border border-white/10 px-2.5 py-1 rounded-md text-xs text-gray-300"><MapPin size={12} />{job.location}</span>
          <span className="flex items-center gap-1 bg-white/5 border border-white/10 px-2.5 py-1 rounded-md text-xs text-gray-300"><Briefcase size={12} />{job.work_model !== 'Unknown' ? job.work_model : (job.job_type || 'Full-time')}</span>
          {job.experience && job.experience !== 'Unknown' && <span className="flex items-center gap-1 bg-white/5 border border-white/10 px-2.5 py-1 rounded-md text-xs text-gray-300">{job.experience}</span>}
        </div>
      </div>

      <div className="flex items-center justify-between mt-auto pt-3 border-t border-white/10">
        <a href={job.link} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 text-sm font-semibold text-emerald-400 hover:text-emerald-300">
          <span>Apply Now</span><ExternalLink size={14} />
        </a>
        <button onClick={handleSaveToggle} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${isSaved ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'bg-white/5 text-gray-400 border border-white/10 hover:text-white'}`}>
          <Heart size={14} className={isSaved ? "fill-current" : ""} /> {isSaved ? 'Saved' : 'Save'}
        </button>
      </div>
    </div>
  );
};
export default JobCard;