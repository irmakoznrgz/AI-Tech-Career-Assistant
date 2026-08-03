import React, { useState, useEffect } from 'react';
import { getDashboardStats, getChartInsight } from '../services/api';
import { 
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer, 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  LineChart, Line
} from 'recharts';
import { Activity, Lightbulb, Loader2 } from 'lucide-react';

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#8b5cf6', '#ec4899', '#14b8a6', '#f43f5e', '#6366f1'];
const RADIAN = Math.PI / 180;

const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
  if (percent < 0.05) return null; 
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);
  return (
    <text x={x} y={y} fill="white" textAnchor={x > cx ? 'start' : 'end'} dominantBaseline="central" className="text-xs font-bold font-sans">
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

const ChartCard = ({ title, data, children, kpiLabel, hideAI = false }) => {
  const [insight, setInsight] = useState("");
  const [loadingInsight, setLoadingInsight] = useState(false);

  const getTopKpi = () => {
    if (!data || data.length === 0) return "N/A";
    const topItem = [...data].sort((a, b) => b.value - a.value)[0];
    return `${topItem.name} (${topItem.value})`;
  };

  const handleGetInsight = async () => {
    if (insight) {
      setInsight(""); 
      return;
    }
    setLoadingInsight(true);
    const result = await getChartInsight(title, data);
    setInsight(result);
    setLoadingInsight(false);
  };

  return (
    <div className="bg-slate-900/60 backdrop-blur-md border border-white/10 rounded-2xl p-6 shadow-xl flex flex-col relative overflow-hidden group">
      
      <div className="flex items-start justify-between mb-4 z-10">
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-semibold text-white">{title}</h3>
          
          {!hideAI && (
            <button 
              onClick={handleGetInsight} 
              disabled={loadingInsight}
              className={`p-1.5 border rounded-lg transition-colors cursor-pointer ${loadingInsight ? 'bg-emerald-500/20 border-emerald-500/50' : 'bg-yellow-500/10 hover:bg-yellow-500/20 border-yellow-500/30'}`}
              title="Analyze with AI"
            >
              {loadingInsight ? (
                <Loader2 size={16} className="text-emerald-400 animate-spin" />
              ) : (
                <Lightbulb size={16} className="text-yellow-400" />
              )}
            </button>
          )}
        </div>
        
        <div className="bg-white/5 border border-white/10 px-3 py-1 rounded-lg text-xs font-semibold text-emerald-400 text-right">
          <span className="text-gray-400 block text-[10px] uppercase tracking-wider mb-0.5">{kpiLabel}</span>
          {getTopKpi()}
        </div>
      </div>

      {!hideAI && (insight || loadingInsight) && (
        <div className="mb-4 p-3 bg-emerald-900/20 border border-emerald-500/30 rounded-xl text-sm text-emerald-100 animate-fade-in relative z-10">
          <div className="flex gap-2 items-start">
            <Activity size={16} className={`text-emerald-400 shrink-0 mt-0.5 ${loadingInsight ? 'animate-pulse' : ''}`} />
            <div className="leading-relaxed">
              {loadingInsight ? (
                <span className="animate-pulse text-emerald-400/80 font-medium">AI is analyzing the data, please wait...</span>
              ) : (
                insight
              )}
            </div>
          </div>
        </div>
      )}

      <div className="w-full h-[300px] relative z-0 mt-2">
        {children}
      </div>
    </div>
  );
};

const Dashboard = () => {
  const [stats, setStats] = useState({ work_models: [], experiences: [], locations: [], domains: [], timeline: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      const data = await getDashboardStats();
      setStats(data);
      setLoading(false);
    };
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32 text-emerald-400 animate-pulse">
        <Activity size={48} className="mb-4" />
        <h2 className="text-xl font-bold">Gathering Market Intelligence...</h2>
      </div>
    );
  }

  return (
    <div className="pb-12">
      <div className="mb-8 flex items-center gap-3">
        <div className="bg-emerald-500/20 p-3 rounded-xl border border-emerald-500/30">
          <Activity size={24} className="text-emerald-400" />
        </div>
        <div>
          <h2 className="text-3xl font-bold text-white drop-shadow-md">Market Intelligence</h2>
          <p className="text-gray-400">Real-time AI-powered analytics of the IT job market.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
       
        <div className="lg:col-span-2">
          <ChartCard title="Daily Job Postings Trend" data={stats.timeline} kpiLabel="Peak Day" hideAI={true}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={stats.timeline} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#fff', borderRadius: '8px' }} />
                <Line type="linear" dataKey="value" stroke="#10b981" strokeWidth={3} dot={{ fill: '#10b981', strokeWidth: 2, r: 4 }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        <ChartCard title="Work Model Distribution" data={stats.work_models} kpiLabel="Dominant Model">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={stats.work_models} cx="50%" cy="50%" labelLine={false} label={renderCustomizedLabel} outerRadius={100} dataKey="value">
                {stats.work_models.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#fff', borderRadius: '8px' }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex justify-center gap-4 mt-2 text-xs text-gray-400 absolute bottom-0 w-full pb-4">
             {stats.work_models.map((entry, index) => (
                <div key={index} className="flex items-center gap-1.5">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }}></div>
                  {entry.name}
                </div>
             ))}
          </div>
        </ChartCard>

        <ChartCard title="Experience Level Demand" data={stats.experiences} kpiLabel="Highest Demand">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={stats.experiences} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
              <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
              <Tooltip cursor={{fill: '#1e293b'}} contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#fff', borderRadius: '8px' }} />
              <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} maxBarSize={50} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Top Domains Map" data={stats.domains} kpiLabel="Trending Domain">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart cx="50%" cy="50%" outerRadius="65%" data={stats.domains}>
              <PolarGrid stroke="#334155" />
              <PolarAngleAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
              <PolarRadiusAxis angle={30} domain={[0, 'auto']} tick={false} axisLine={false} />
              <Radar name="Jobs" dataKey="value" stroke="#f43f5e" fill="#f43f5e" fillOpacity={0.4} />
              <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#fff', borderRadius: '8px' }} />
            </RadarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Location Density (Top 10)" data={stats.locations} kpiLabel="Top Tech Hub">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart layout="vertical" data={stats.locations} margin={{ top: 0, right: 10, left: 10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
              <XAxis type="number" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis dataKey="name" type="category" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} width={85} interval={0} />
              <Tooltip cursor={{fill: '#1e293b'}} contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#fff', borderRadius: '8px' }} />
              <Bar dataKey="value" fill="#f59e0b" radius={[0, 4, 4, 0]} maxBarSize={25} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

      </div>
    </div>
  );
};

export default Dashboard;