import React, { useState, useEffect } from 'react';
import Dashboard from './pages/Dashboard';
import UploadResume from './pages/UploadResume';
import CareerGoal from './pages/CareerGoal';
import RoadmapView from './pages/RoadmapView';
import QuizView from './pages/QuizView';
import Learn from './pages/Learn';
import { authAPI } from './services/api';
import { 
  LayoutDashboard, 
  UploadCloud, 
  Target, 
  GitFork, 
  HelpCircle, 
  BookOpen, 
  Cpu, 
  User as UserIcon,
  Award,
  Menu,
  X
} from 'lucide-react';

export default function App() {
  const [activePage, setActivePage] = useState('dashboard');
  const [sharedState, setSharedState] = useState({});
  const [profile, setProfile] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [toasts, setToasts] = useState([]);

  const showToast = (message, type = 'success') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3500);
  };

  // Fetch user profile on startup and when readiness changes
  const fetchProfile = async () => {
    try {
      const res = await authAPI.getProfile();
      if (res.status === 'success') {
        setProfile(res.data);
      }
    } catch (err) {
      console.error("Failed to connect to backend", err);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, [activePage]);

  // Navigate to a page and close sidebar (mobile layout support)
  const navigateTo = (page) => {
    setActivePage(page);
    setSidebarOpen(false);
  };

  const navItems = [
    { id: 'dashboard', name: 'Dashboard', icon: LayoutDashboard },
    { id: 'upload', name: 'Upload Resume', icon: UploadCloud },
    { id: 'goal', name: 'Target Goal', icon: Target },
    { id: 'roadmap', name: 'Roadmap Tracker', icon: GitFork },
    { id: 'quiz', name: 'Quiz Assessment', icon: HelpCircle },
    { id: 'learn', name: 'Learning Center', icon: BookOpen }
  ];

  const renderActivePage = () => {
    switch (activePage) {
      case 'dashboard':
        return <Dashboard setActivePage={navigateTo} setSharedState={setSharedState} showToast={showToast} />;
      case 'upload':
        return <UploadResume setActivePage={navigateTo} showToast={showToast} />;
      case 'goal':
        return <CareerGoal setActivePage={navigateTo} showToast={showToast} />;
      case 'roadmap':
        return <RoadmapView setActivePage={navigateTo} setSharedState={setSharedState} showToast={showToast} />;
      case 'quiz':
        return <QuizView sharedState={sharedState} setActivePage={navigateTo} showToast={showToast} />;
      case 'learn':
        return <Learn sharedState={sharedState} setActivePage={navigateTo} showToast={showToast} />;
      default:
        return <Dashboard setActivePage={navigateTo} setSharedState={setSharedState} showToast={showToast} />;
    }
  };

  return (
    <div className="flex min-h-screen bg-cyber-dark text-slate-100 grid-bg">
      {/* Mobile Top Bar */}
      <div className="md:hidden w-full bg-slate-950/80 backdrop-blur border-b border-slate-900 px-4 py-3 fixed top-0 left-0 flex justify-between items-center z-50">
        <div className="flex items-center space-x-2">
          <Cpu className="w-5 h-5 text-cyber-green animate-pulse-cyber" />
          <span className="font-extrabold text-sm tracking-wider bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
            SKILLGAP.AI
          </span>
        </div>
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-1 rounded bg-slate-900 border border-slate-800 text-gray-400 focus:outline-none"
        >
          {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Sidebar Navigation */}
      <aside className={`fixed inset-y-0 left-0 w-64 bg-slate-950/90 backdrop-blur-md border-r border-slate-900 flex flex-col justify-between p-4 z-40 transform md:transform-none transition-transform duration-300 md:translate-x-0 ${
        sidebarOpen ? 'translate-x-0 pt-16 md:pt-4' : '-translate-x-full'
      }`}>
        <div className="space-y-6">
          {/* Logo */}
          <div className="hidden md:flex items-center space-x-2.5 px-2">
            <div className="p-1.5 rounded-lg bg-cyber-green/10 border border-cyber-green/20">
              <Cpu className="w-6 h-6 text-cyber-green animate-pulse" />
            </div>
            <span className="font-extrabold text-lg tracking-wider bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
              SKILLGAP.AI
            </span>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activePage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => navigateTo(item.id)}
                  className={`w-full flex items-center space-x-3.5 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-gradient-to-r from-indigo-950/50 to-slate-900/50 border-l-2 border-cyber-blue text-white shadow-inner shadow-indigo-500/5'
                      : 'text-gray-400 hover:bg-slate-900/40 hover:text-slate-200'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-cyber-blue' : 'text-gray-400'}`} />
                  <span>{item.name}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Footer Profile Status */}
        {profile && (
          <div className="glass-panel p-3.5 rounded-lg flex items-center justify-between border-slate-900">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center text-cyber-blue">
                <UserIcon className="w-4 h-4" />
              </div>
              <div className="text-left">
                <p className="text-xs font-bold text-gray-300">{profile.username}</p>
                <p className="text-[9px] text-gray-500 font-mono tracking-tight">{profile.email}</p>
              </div>
            </div>
            
            <div className="flex flex-col items-end">
              <div className="flex items-center space-x-0.5 text-cyber-green" title="Career Readiness Score">
                <Award className="w-3.5 h-3.5" />
                <span className="text-xs font-extrabold font-mono">{profile.readiness_score}%</span>
              </div>
              <span className="text-[7px] text-gray-500 font-mono">READINESS</span>
            </div>
          </div>
        )}
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 md:ml-64 p-4 md:p-8 pt-20 md:pt-8 min-h-screen">
        <div className="max-w-5xl mx-auto pb-12">
          {renderActivePage()}
        </div>
      </main>

      {/* Toast Overlay */}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 w-80 max-w-[90vw]">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`p-3.5 rounded-lg glass-panel animate-toast-slide-in shadow-xl flex items-center gap-3 border text-xs font-mono tracking-tight ${
              t.type === 'error'
                ? 'border-red-500/25 bg-red-950/40 text-red-200'
                : t.type === 'info'
                ? 'border-blue-500/25 bg-blue-950/40 text-blue-200'
                : 'border-emerald-500/25 bg-emerald-950/40 text-emerald-200'
            }`}
          >
            <div className={`w-2 h-2 rounded-full shrink-0 animate-pulse ${
              t.type === 'error' ? 'bg-red-400' : t.type === 'info' ? 'bg-blue-400' : 'bg-emerald-400'
            }`}></div>
            <div className="flex-1 leading-snug">{t.message}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
