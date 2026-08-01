import React, { useState, useEffect } from 'react';
import FilterBar from '../components/FilterBar';
import JobCard from '../components/JobCard';
import { searchJobs, uploadCv, generateGalaxyMap } from '../services/api';
import { Loader2, AlertCircle, Sparkles, ChevronLeft, ChevronRight, MessageSquare } from 'lucide-react';
import { ScatterChart, Scatter, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, Legend } from 'recharts';
import useStore from '../store/useStore';

const Home = () => {
  const [jobs, setJobs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSearching, setIsSearching] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const jobsPerPage = 10;
  
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

  // query opsiyonel parametresi eklendi (CV araması için)
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
      // CV yüklendiğinde Chatbotu zıplatma, doğrudan CV'deki yeteneklerle "Sessiz Arama" yap.
      const skillsQuery = result.found_skills.length > 0 ? result.found_skills.join(" ") : "yazılım geliştirici";
      handleSearch(null, 50, skillsQuery);
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

  const safeJobs = Array.isArray(jobs) ? jobs : [];
  const currentJobs = safeJobs.slice((currentPage - 1) * jobsPerPage, currentPage * jobsPerPage);
  const totalPages = Math.ceil(safeJobs.length / jobsPerPage);

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-slate-900 border border-white/10 p-3 rounded-xl shadow-xl max-w-[250px]">
          <p className="text-emerald-400 font-bold mb-1 leading-tight">{data.title}</p>
          <p className="text-gray-300 text-xs">{data.company}</p>
        </div>
      );
    } return null;
  };

  return (
    <div className="pb-12">
      <FilterBar onSearch={handleSearch} onUploadCv={handleUploadCv} isSearching={isSearching} />

      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white drop-shadow-md">
          Found Jobs <span className="text-emerald-400">({safeJobs.length})</span>
        </h2>
        <button onClick={handleGenerateMap} disabled={safeJobs.length < 3 || isGeneratingMap} className="flex items-center gap-2 bg-slate-800 border border-emerald-500/30 hover:border-emerald-400 text-emerald-400 px-4 py-2.5 rounded-xl transition-all text-sm font-medium disabled:opacity-50">
          <Sparkles size={16} /> {isGeneratingMap ? 'Calculating...' : 'Generate Map'}
        </button>
      </div>

      {showMap && (
        <div className="mb-8 bg-slate-900/80 border border-white/10 rounded-2xl p-6 shadow-xl">
          {isGeneratingMap ? (
            <div className="h-[250px] flex justify-center items-center"><Loader2 size={32} className="animate-spin text-emerald-400" /></div>
          ) : (
            <div className="h-[350px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                  <XAxis type="number" dataKey="x" name="PCA-1" tick={false} stroke="#475569" /> 
                  <YAxis type="number" dataKey="y" name="PCA-2" tick={false} stroke="#475569" />
                  <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
                  {/* RENK AÇIKLAMALARI (LEJANT) EKLENDİ */}
                  <Legend verticalAlign="top" height={36} payload={[ { value: 'Available Jobs', type: 'circle', color: '#10b981' }, { value: 'Your Profile (CV)', type: 'circle', color: '#f43f5e' } ]} />
                  <Scatter name="Jobs" data={mapData}>
                    {(mapData || []).map((entry, index) => <Cell key={`cell-${index}`} fill={entry.category === 'MY CV' ? '#f43f5e' : '#10b981'} className="cursor-pointer hover:opacity-80" />)}
                  </Scatter>
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {isLoading ? (
        <div className="flex justify-center py-20 text-emerald-400"><Loader2 size={48} className="animate-spin" /></div>
      ) : safeJobs.length === 0 ? (
        <div className="flex justify-center py-20 text-gray-400"><p className="text-lg">No jobs found.</p></div>
      ) : (
        <div className="flex gap-8 relative">
          
          <div className="w-full lg:w-[calc(100%-380px)] flex flex-col gap-5">
            {currentJobs.map((job, index) => (
              <JobCard key={job.id || index} job={job} />
            ))}

            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-4 mt-6 bg-slate-900/40 p-3 rounded-xl border border-white/10 w-fit mx-auto">
                <button onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))} disabled={currentPage === 1} className="p-1.5 text-emerald-400 disabled:text-gray-600 hover:bg-white/5 rounded-lg"><ChevronLeft size={20}/></button>
                <span className="text-gray-300 font-medium text-sm">Page {currentPage} of {totalPages}</span>
                <button onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))} disabled={currentPage === totalPages} className="p-1.5 text-emerald-400 disabled:text-gray-600 hover:bg-white/5 rounded-lg"><ChevronRight size={20}/></button>
              </div>
            )}
          </div>

          {/* SAĞ TARAF: Chatbot için boşluk */}
          <div className="hidden lg:block lg:w-[350px]">
             {/* Burası boş kalacak ki chatbot kartların üstünü kapatmasın */}
          </div>

        </div>
      )}
    </div>
  );
};
export default Home;