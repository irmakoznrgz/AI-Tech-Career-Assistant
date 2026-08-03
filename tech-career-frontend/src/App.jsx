import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import SavedJobs from './pages/SavedJobs';
import ChatWidget from './components/ChatWidget';
import Dashboard from './pages/Dashboard';

function App() {
  return (
    <Router>
      <div 
        className="min-h-screen bg-cover bg-center bg-no-repeat bg-fixed text-white font-sans"
        style={{ backgroundImage: "url('/img/pic.jpg')" }}
      >
        <div className="min-h-screen bg-slate-900/50 flex flex-col relative">
          
          <Navbar />
          
          <main className="flex-grow container mx-auto px-4 py-8">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/saved-jobs" element={<SavedJobs />} />
              <Route path="/dashboard" element={<Dashboard />} />
            </Routes>
          </main>

          <ChatWidget /> 
        </div>
      </div>
    </Router>
  );
}

export default App;