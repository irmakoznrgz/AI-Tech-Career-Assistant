import React, { useState, useEffect } from 'react';
import { Search, UploadCloud, ChevronDown, CheckCircle2, X } from 'lucide-react';
import { getFilters } from '../services/api';
import useStore from '../store/useStore';

const FilterBar = ({ onSearch, onUploadCv, isSearching }) => {
  const { cvText, clearCvText } = useStore();
  const [filters, setFilters] = useState({ location: '', work_model: '', job_type: '', experience: '', domain: '' });

  const [options, setOptions] = useState({ 
    locations: [], 
    work_models: [], 
    job_types: [], 
    experiences: [], 
    domains: [] 
  });

  useEffect(() => {
    getFilters().then(data => { 
      if (data) {
        setOptions({
          locations: data.locations || [],
          work_models: data.work_models || [],
          job_types: data.job_types || [],
          experiences: data.experiences || [],
          domains: data.domains || []
        });
      } 
    });
  }, []);

  const handleFilterChange = (e) => {
    setFilters(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSearchClick = () => {
    const cleanFilters = {};
    Object.keys(filters).forEach(key => {
      if (filters[key]) cleanFilters[key] = filters[key];
    });
    onSearch(Object.keys(cleanFilters).length > 0 ? cleanFilters : null, 10000); 
  };

  const handleFileChange = (e) => {
    if (e.target.files[0]) onUploadCv(e.target.files[0]);
  };

  const handleClearCv = (e) => {
    e.preventDefault();
    clearCvText();
  };

  return (
    <div className="w-full bg-slate-900/60 backdrop-blur-lg border border-white/10 rounded-2xl p-6 shadow-2xl mb-8">
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
        
        <div className="flex flex-col gap-1.5 relative">
          <label className="text-xs font-medium text-gray-400 uppercase tracking-wider px-1">Location</label>
          <select name="location" value={filters.location} onChange={handleFilterChange} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-sm text-white appearance-none cursor-pointer focus:outline-none focus:ring-1 focus:ring-emerald-500/50">
            <option value="" className="bg-slate-800 text-gray-400">All Locations</option>
            {options.locations.map((loc, i) => <option key={`loc-${i}`} value={loc} className="bg-slate-800 text-white">{loc}</option>)}
          </select>
          <ChevronDown size={16} className="absolute right-4 top-9 text-gray-500 pointer-events-none" />
        </div>

        <div className="flex flex-col gap-1.5 relative">
          <label className="text-xs font-medium text-gray-400 uppercase tracking-wider px-1">Work Model</label>
          <select name="work_model" value={filters.work_model} onChange={handleFilterChange} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-sm text-white appearance-none cursor-pointer focus:outline-none focus:ring-1 focus:ring-emerald-500/50">
            <option value="" className="bg-slate-800 text-gray-400">All Models</option>
            {options.work_models.map((type, i) => <option key={`wm-${i}`} value={type} className="bg-slate-800 text-white">{type}</option>)}
          </select>
          <ChevronDown size={16} className="absolute right-4 top-9 text-gray-500 pointer-events-none" />
        </div>

        <div className="flex flex-col gap-1.5 relative">
          <label className="text-xs font-medium text-gray-400 uppercase tracking-wider px-1">Job Type</label>
          <select name="job_type" value={filters.job_type} onChange={handleFilterChange} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-sm text-white appearance-none cursor-pointer focus:outline-none focus:ring-1 focus:ring-emerald-500/50">
            <option value="" className="bg-slate-800 text-gray-400">All Types</option>
            {options.job_types.map((type, i) => <option key={`jt-${i}`} value={type} className="bg-slate-800 text-white">{type}</option>)}
          </select>
          <ChevronDown size={16} className="absolute right-4 top-9 text-gray-500 pointer-events-none" />
        </div>

        <div className="flex flex-col gap-1.5 relative">
          <label className="text-xs font-medium text-gray-400 uppercase tracking-wider px-1">Experience</label>
          <select name="experience" value={filters.experience} onChange={handleFilterChange} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-sm text-white appearance-none cursor-pointer focus:outline-none focus:ring-1 focus:ring-emerald-500/50">
            <option value="" className="bg-slate-800 text-gray-400">All Levels</option>
            {options.experiences.map((exp, i) => <option key={`exp-${i}`} value={exp} className="bg-slate-800 text-white">{exp}</option>)}
          </select>
          <ChevronDown size={16} className="absolute right-4 top-9 text-gray-500 pointer-events-none" />
        </div>

        <div className="flex flex-col gap-1.5 relative">
          <label className="text-xs font-medium text-gray-400 uppercase tracking-wider px-1">Domain</label>
          <select name="domain" value={filters.domain} onChange={handleFilterChange} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-sm text-white appearance-none cursor-pointer focus:outline-none focus:ring-1 focus:ring-emerald-500/50">
            <option value="" className="bg-slate-800 text-gray-400">All Domains</option>
            {options.domains.map((dom, i) => <option key={`dom-${i}`} value={dom} className="bg-slate-800 text-white">{dom}</option>)}
          </select>
          <ChevronDown size={16} className="absolute right-4 top-9 text-gray-500 pointer-events-none" />
        </div>

      </div>

      <div className="flex flex-col sm:flex-row gap-4 items-center">
        <button onClick={handleSearchClick} disabled={isSearching} className="w-full sm:w-auto min-w-[160px] flex items-center justify-center gap-2 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold px-8 py-3.5 rounded-xl transition-all disabled:opacity-50">
          <Search size={18} strokeWidth={2.5} />
          {isSearching ? 'Searching...' : 'Search'}
        </button>

        <div className="flex items-center w-full sm:w-auto">
          {cvText ? (
            <div className="flex items-center gap-3 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-6 py-2.5 rounded-xl text-sm font-medium">
              <CheckCircle2 size={18} />
              <span>CV Active</span>
              <button onClick={handleClearCv} className="hover:text-rose-400 ml-2 transition-colors" title="Remove CV"><X size={18} /></button>
            </div>
          ) : (
            <label className="flex items-center gap-2 bg-white/5 hover:bg-white/10 border border-white/10 text-white px-6 py-2.5 rounded-xl cursor-pointer transition-all text-sm font-medium">
              <UploadCloud size={18} />
              <span>Upload CV (PDF)</span>
              <input type="file" accept=".pdf" className="hidden" onChange={handleFileChange} />
            </label>
          )}
        </div>
      </div>
    </div>
  );
};

export default FilterBar;