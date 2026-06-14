import React, { useState } from 'react';
import { Link, NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Menu, X, Leaf, Home, MessageSquare, PlusCircle, Trophy, LogOut, Settings, Users, Medal } from 'lucide-react';
import { clearUserId, hasSession } from '../lib/user-session';
import { useAuth } from '../context/AuthContext';
import EcoPointsBadge from './EcoPointsBadge';
import SettingsModal from './SettingsModal';

export default function Layout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  
  // Theme state
  const [theme, setTheme] = useState<'light' | 'dark' | 'system'>('system');

  React.useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | 'system';
    if (savedTheme) setTheme(savedTheme);
  }, []);

  React.useEffect(() => {
    localStorage.setItem('theme', theme);
    const root = window.document.documentElement;
    if (theme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      root.classList.remove('light', 'dark');
      root.classList.add(systemTheme);
    } else {
      root.classList.remove('light', 'dark');
      root.classList.add(theme);
    }
  }, [theme]);

  const { user, signOut, isLoading } = useAuth();
  // We still check hasSession to ensure onboarding was finished
  const onboardingCompleted = hasSession();

  const handleLogout = async () => {
    await signOut();
    clearUserId(); // Also clear the local onboarding marker
    navigate('/auth');
  };

  const navItems = [
    { name: 'Dashboard', to: '/dashboard', icon: Home },
    { name: 'Log Activity', to: '/log', icon: PlusCircle },
    { name: 'Missions', to: '/missions', icon: Trophy },
    { name: 'Coaching Chat', to: '/chat', icon: MessageSquare },
    { name: 'Community', to: '#community', icon: Users, phase2: true },
    { name: 'Leaderboard', to: '#leaderboard', icon: Medal, phase2: true },
  ];

  if (isLoading) {
    return <div className="min-h-screen bg-slate-950 flex items-center justify-center text-emerald-500">Loading...</div>;
  }

  if (!user || !onboardingCompleted) {
    return (
      <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
        <header className="w-full border-b border-slate-200/80 dark:border-slate-800/80 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md transition-colors duration-300">
          <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2 group">
              <div className="p-2 bg-emerald-600 text-white rounded-xl shadow-md group-hover:scale-105 transition-transform duration-200">
                <Leaf size={20} className="fill-emerald-100/20" />
              </div>
              <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-emerald-600 to-teal-500 bg-clip-text text-transparent">
                CarbonSense <span className="font-light text-slate-500 dark:text-slate-400">AI</span>
              </span>
            </Link>
            
            {!user ? (
              <Link to="/auth" className="px-4 py-2 bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-sm font-bold rounded-xl hover:scale-105 transition-transform">
                Sign In
              </Link>
            ) : (
              <button onClick={handleLogout} className="px-4 py-2 bg-rose-500/10 text-rose-500 text-sm font-bold rounded-xl hover:bg-rose-500/20 transition-colors">
                Sign Out
              </button>
            )}
          </div>
        </header>
        <main className="flex-1 w-full mx-auto">
          <Outlet />
        </main>
      </div>
    );
  }

  const getPageTitle = () => {
    const path = location.pathname;
    if (path.includes('dashboard')) return 'Dashboard';
    if (path.includes('log')) return 'Log Activity';
    if (path.includes('missions')) return 'Missions';
    if (path.includes('chat')) return 'Coaching Chat';
    return 'CarbonSense AI';
  };

  return (
    <div className="min-h-screen flex bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      {/* Mobile Top Bar */}
      <div className="md:hidden fixed top-0 left-0 right-0 h-16 border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md flex items-center justify-between px-4 z-40">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-emerald-600 text-white rounded-lg">
            <Leaf size={18} />
          </div>
          <span className="font-bold text-slate-800 dark:text-slate-200">{getPageTitle()}</span>
        </div>
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-2 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl"
        >
          {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Sidebar */}
      <aside
        className={`fixed md:sticky top-0 left-0 z-30 h-screen w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 transform transition-transform duration-300 ease-in-out ${
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        } flex flex-col`}
      >
        {/* Logo Area */}
        <div className="h-20 flex items-center px-6 border-b border-slate-100 dark:border-slate-800">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="p-2 bg-emerald-500 dark:bg-emerald-600 text-white rounded-xl shadow-sm group-hover:scale-105 transition-transform">
              <Leaf size={22} className="fill-emerald-100/20" />
            </div>
            <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-emerald-600 to-teal-500 bg-clip-text text-transparent">
              CarbonSense
            </span>
          </Link>
        </div>

        {/* Navigation */}
        <div className="flex-1 overflow-y-auto py-6 px-4 space-y-1.5">
          {navItems.map((item) => (
            item.phase2 ? (
              <div
                key={item.name}
                className="flex items-center justify-between px-4 py-3 rounded-xl text-sm font-medium text-slate-400 dark:text-slate-600 cursor-not-allowed"
                title="Coming in Phase 2"
              >
                <div className="flex items-center gap-3">
                  <item.icon size={18} />
                  <span>{item.name}</span>
                </div>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500">
                  Phase 2
                </span>
              </div>
            ) : (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => setMobileMenuOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 border border-emerald-100 dark:border-emerald-800/50 shadow-sm'
                      : 'text-slate-600 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 hover:bg-slate-50 dark:hover:bg-slate-800/50'
                  }`
                }
              >
                <item.icon size={18} />
                <span>{item.name}</span>
              </NavLink>
            )
          ))}
        </div>

        {/* User Profile Area (Bottom) */}
        <div className="p-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
          <div className="flex flex-col gap-3">
            <EcoPointsBadge compact={false} />
            <div className="flex items-center justify-between mt-2">
              <button onClick={() => setSettingsOpen(true)} className="flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-emerald-600 dark:text-slate-400 dark:hover:text-emerald-400 transition-colors">
                <Settings size={16} />
                <span>Settings</span>
              </button>
              <button
                onClick={handleLogout}
                className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/30 rounded-lg transition-colors"
                title="Logout"
              >
                <LogOut size={16} />
              </button>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 w-full min-h-screen pt-16 md:pt-0 overflow-x-hidden">
        {/* Desktop Header */}
        <header className="hidden md:flex h-20 items-center px-8 border-b border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm sticky top-0 z-20">
          <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">
            {getPageTitle()}
          </h1>
        </header>
        
        <div className="p-4 md:p-8 max-w-7xl mx-auto">
          <Outlet />
        </div>
      </main>
      
      {/* Mobile Overlay */}
      {mobileMenuOpen && (
        <div 
          className="md:hidden fixed inset-0 z-20 bg-slate-900/20 backdrop-blur-sm"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      <SettingsModal 
        isOpen={settingsOpen} 
        onClose={() => setSettingsOpen(false)} 
        theme={theme}
        setTheme={setTheme}
      />
    </div>
  );
}
