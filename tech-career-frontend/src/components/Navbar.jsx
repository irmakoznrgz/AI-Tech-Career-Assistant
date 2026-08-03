import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Bookmark, Search, TrendingUp, BarChart2 } from 'lucide-react';
import useStore from '../store/useStore';

const Navbar = () => {
  const location = useLocation();
  const savedJobs = useStore((state) => state.savedJobs);
  const savedCount = (savedJobs || []).length;

  return (
    <nav className="flex items-center justify-between px-8 py-5 border-b border-white/10 bg-black/20">
      <Link to="/" className="flex items-center gap-2">
        <TrendingUp className="text-emerald-400" size={28} strokeWidth={2.5} />
        <span className="text-2xl font-bold text-emerald-400 tracking-wide drop-shadow-md">
          TechCareer.ai
        </span>
      </Link>

      <div className="flex gap-8 items-center text-sm font-medium">
        
        <Link to="/" className={`flex items-center gap-2 transition-all duration-300 hover:text-emerald-400 hover:scale-105 ${location.pathname === '/' ? 'text-emerald-400 drop-shadow-md' : 'text-gray-300'}`}>
          <Search size={18} />
          <span>Search</span>
        </Link>

        <Link to="/dashboard" className={`flex items-center gap-2 transition-all duration-300 hover:text-emerald-400 hover:scale-105 ${location.pathname === '/dashboard' ? 'text-emerald-400 drop-shadow-md' : 'text-gray-300'}`}>
          <BarChart2 size={18} />
          <span>Dashboard</span>
        </Link>
        
        <Link to="/saved-jobs" className={`flex items-center gap-2 px-4 py-2 rounded-full transition-all duration-300 border ${location.pathname === '/saved-jobs' ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400' : 'bg-white/5 border-white/10 text-gray-300 hover:bg-white/10 hover:text-emerald-400'}`}>
          <Bookmark size={18} className={savedCount > 0 ? "fill-current" : ""} />
          <span>Saved Jobs ({savedCount})</span>
        </Link>

      </div>
    </nav>
  );
};

export default Navbar;