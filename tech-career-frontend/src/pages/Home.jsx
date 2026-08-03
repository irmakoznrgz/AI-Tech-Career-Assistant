import React, { useState, useEffect } from 'react';
import FilterBar from '../components/FilterBar';
import JobCard from '../components/JobCard';
import { searchJobs, uploadCv, generateGalaxyMap } from '../services/api';
import { Loader2, Sparkles, ChevronLeft, ChevronRight, X } from 'lucide-react';
import { ScatterChart, Scatter, XAxis, YAxis, ZAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import useStore from '../store/useStore';

const CustomScatterShape = (props) => {
  const { cx, cy, payload } = props;
  if (payload.category === 'MY CV') {
    return (
      <g transform={`translate(${cx},${cy}) scale(1.5)`}>
        <path d="M0,-10 L2.245,-3.09 L9.51,-3.09 L3.632,1.18 L5.877,8.09 L0,3.82 L-5.877,8.09 L-3.632,1.18 L-9.51,-3.09 L-2.245,-3.09 Z" fill="#f43f5e" className="cursor-pointer hover:opacity-80 transition-opacity" />
      </g>
    );
  }
  return <circle cx={cx} cy={cy} r={7} fill="#10b981" fillOpacity={0.8} className="cursor-pointer hover:opacity-100 transition-opacity duration-300" />;
};

const JobCardSkeleton = () => (
  <div className="bg-slate-900/60 border border-white/5 rounded-2xl p-6 shadow-xl animate-pulse">
    <div className="flex items-start justify-between gap-4 mb-3">
      <div className="w-2/3">
        <div className="h-6 bg-slate-700/50 rounded-lg w-full mb-3"></div>
        <div className="h-4 bg-slate-700/50 rounded-lg w-2/3"></div>
      </div>
      <div className="h-6 bg-slate-700/50 rounded-full w-20 shrink-0"></div>
    </div>
    <div className="flex gap-2 mb-4 mt-4">
      <div className="h-6 bg-slate-700/50 rounded-lg w-20"></div>
      <div className="h-6 bg-slate-700/50 rounded-lg w-24"></div>
      <div className="h-6 bg-slate-700/50 rounded-lg w-24"></div>
    </div>
    <div className="space-y-2 mb-4 mt-6">
      <div className="h-4 bg-slate-700/50 rounded-lg w-full"></div>
      <div className="h-4 bg-slate-700/50 rounded-lg w-4/5"></div>
    </div>
  </div>
);

const Home = () => {
  const [jobs, setJobs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSearching, setIsSearching] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const jobsPerPage = 10;

  const [sortBy, setSortBy] = useState('match');

  const [mapData, setMapData] = useState([]);
  const [isGeneratingMap, setIsGeneratingMap] = useState(false);
  const [showMap, setShowMap] = useState(false);

  const { cvText, setCvText } = useStore();

  useEffect(() => { fetchInitialJobs(); }, []);

  const fetchInitialJobs = async () => {
    setIsLoading(true);
    try {
      const data = await searchJobs("yazılım bilişim teknoloji veri", null, 50);
      setJobs(Array.isArray(data) ? data : []);
    } catch (err) { setJobs([]); } finally { setIsLoading(false); }
  };

  const handleSearch = async (filters, limit, customQuery = null) => {
    setIsSearching(true); setShowMap(false); setCurrentPage(1);
    try {
      const query = customQuery || "yazılım bilişim teknoloji veri";
      const data = await searchJobs(query, filters, limit);
      setJobs(Array.isArray(data) ? data : []);
    } catch (err) { setJobs([]); } finally { setIsSearching(false); }
  };

  const handleUploadCv = async (file) => {
    try {
      const result = await uploadCv(file);
      setCvText(result.cv_text);
      const skillsQuery = result.found_skills.length > 0 ? result.found_skills.join(" ") : "yazılım geliştirici";
      handleSearch(null, 10000, skillsQuery);
    } catch (err) { console.error(err); }
  };

  const handleGenerateMap = async () => {
    if ((jobs || []).length < 3) return;
    setIsGeneratingMap(true); setShowMap(true);
    try {
      const data = await generateGalaxyMap(jobs, cvText);
      setMapData(data || []);
    } catch (err) { setShowMap(false); } finally { setIsGeneratingMap(false); }
  };

  const handlePointClick = (data) => {
    const link = data?.link || data?.payload?.link;
    if (link && link !== "N/A" && link !== "#") window.open(link, '_blank', 'noopener,noreferrer');
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-slate-900/95 backdrop-blur-md border border-white/10 p-4 rounded-xl shadow-2xl max-w-[260px] z-50">
          <p className="text-emerald-400 font-bold mb-1 leading-tight">{data.title}</p>
          <p className="text-gray-300 text-sm">{data.company}</p>
          {data.category === 'MY CV' && <p className="text-rose-400 text-xs mt-2 font-bold uppercase tracking-wider">Your Profile</p>}
        </div>
      );
    } return null;
  };

  let sortedJobs = [...(Array.isArray(jobs) ? jobs : [])];
  
  if (sortBy === 'newest') {
    sortedJobs.sort((a, b) => (b.last_seen_int || 0) - (a.last_seen_int || 0));
  } else if (sortBy === 'oldest') {
    sortedJobs.sort((a, b) => (a.last_seen_int || 0) - (b.last_seen_int || 0));
  } else {
    sortedJobs.sort((a, b) => (b.match_score || 0) - (a.match_score || 0));
  }

  const currentJobs = sortedJobs.slice((currentPage - 1) * jobsPerPage, currentPage * jobsPerPage);
  const totalPages = Math.ceil(sortedJobs.length / jobsPerPage);

  const renderPageNumbers = () => {
    const pages = [];
    for (let i = 1; i <= totalPages; i++) {
      pages.push(
        <button key={i} onClick={() => setCurrentPage(i)} className={`w-9 h-9 mx-1 flex items-center justify-center rounded-lg text-sm font-bold transition-all ${currentPage === i ? 'bg-emerald-500 text-slate-950 shadow-md scale-105' : 'text-gray-400 hover:bg-white/10 hover:text-white'}`}>
          {i}
        </button>
      );
    } return pages;
  };

  return (
    <div className="pb-12">
      <FilterBar onSearch={handleSearch} onUploadCv={handleUploadCv} isSearching={isSearching} />

      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <h2 className="text-2xl font-bold text-white drop-shadow-md">
            Found Jobs <span className="text-emerald-400">({sortedJobs.length})</span>
          </h2>
          
          {!isLoading && sortedJobs.length > 0 && (
            <select 
              value={sortBy} 
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-slate-800/80 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-gray-300 focus:outline-none focus:ring-1 focus:ring-emerald-500 cursor-pointer"
            >
              <option value="match">Recommended</option>
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
            </select>
          )}
        </div>

        <button onClick={handleGenerateMap} disabled={sortedJobs.length < 3 || isGeneratingMap} className="flex items-center gap-2 bg-slate-800 border border-emerald-500/30 hover:border-emerald-400 text-emerald-400 px-4 py-2.5 rounded-xl transition-all text-sm font-medium disabled:opacity-50">
          <Sparkles size={16} /> {isGeneratingMap ? 'Calculating...' : 'Generate Map'}
        </button>
      </div>

      {showMap && (
        <div className="relative mb-10 bg-slate-900/80 backdrop-blur-lg border border-white/10 rounded-3xl p-6 shadow-2xl pt-10">
          <button onClick={() => setShowMap(false)} className="absolute top-5 right-5 text-gray-400 hover:text-rose-400 transition-colors z-20 bg-white/5 hover:bg-white/10 p-1.5 rounded-xl"><X size={20} /></button>
          <div className="flex items-center gap-3 mb-4">
            <h3 className="text-lg font-bold text-emerald-400">AI Similarity Map</h3>
            <span className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400/80 text-[11px] uppercase tracking-wider font-semibold px-2.5 py-1 rounded-md">Interactive</span>
          </div>
          {isGeneratingMap ? (
            <div className="h-[350px] flex justify-center items-center"><Loader2 size={32} className="animate-spin text-emerald-400" /></div>
          ) : (
            <div className="h-[450px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                  <XAxis type="number" dataKey="x" name="PCA-1" stroke="#94a3b8" tick={{ fill: '#64748b', fontSize: 12 }} /> 
                  <YAxis type="number" dataKey="y" name="PCA-2" stroke="#94a3b8" tick={{ fill: '#64748b', fontSize: 12 }} />
                  <ZAxis type="number" range={[100, 100]} />
                  <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3', stroke: '#475569' }} />
                  <Legend verticalAlign="top" align="right" iconType="circle" wrapperStyle={{ paddingBottom: '20px' }} payload={[{ value: 'Available Jobs', type: 'circle', color: '#10b981' }, { value: 'Your Profile (CV)', type: 'star', color: '#f43f5e' }]} />
                  <Scatter name="Jobs" data={mapData} onClick={handlePointClick} shape={<CustomScatterShape />} />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {isLoading || isSearching ? (
        <div className="flex gap-8 relative">
          <div className="w-full lg:w-[calc(100%-480px)] max-w-3xl flex flex-col gap-5">
            <JobCardSkeleton />
            <JobCardSkeleton />
            <JobCardSkeleton />
          </div>
          <div className="hidden lg:block lg:w-[450px]"></div>
        </div>
      ) : sortedJobs.length === 0 ? (
        <div className="flex justify-center py-20 text-gray-400">
          <div className="text-center">
            <p className="text-lg mb-2">No jobs found matching your criteria.</p>
            <p className="text-sm text-gray-500 italic">Try selecting fewer filters or resetting them.</p>
          </div>
        </div>
      ) : (
        <div className="flex gap-8 relative">
          <div className="w-full lg:w-[calc(100%-480px)] max-w-3xl flex flex-col gap-5">
            {currentJobs.map((job, index) => <JobCard key={job.id || index} job={job} />)}
            {totalPages > 1 && (
              <div className="flex flex-wrap items-center justify-center gap-1 mt-8 bg-slate-900/40 p-2.5 rounded-xl border border-white/10 w-fit mx-auto">
                <button onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))} disabled={currentPage === 1} className="p-1.5 text-emerald-400 disabled:text-gray-600 hover:bg-white/5 rounded-lg"><ChevronLeft size={20}/></button>
                <div className="flex flex-wrap items-center mx-2 gap-1">{renderPageNumbers()}</div>
                <button onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))} disabled={currentPage === totalPages} className="p-1.5 text-emerald-400 disabled:text-gray-600 hover:bg-white/5 rounded-lg"><ChevronRight size={20}/></button>
              </div>
            )}
          </div>
          <div className="hidden lg:block lg:w-[450px]"></div>
        </div>
      )}
    </div>
  );
};

export default Home;