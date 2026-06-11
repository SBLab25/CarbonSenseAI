import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Leaf, ArrowRight, ShieldCheck, TrendingDown, Target, HelpCircle } from 'lucide-react';
import { hasSession } from '../lib/user-session';

export default function Landing() {
  const navigate = useNavigate();
  const sessionActive = hasSession();

  const handleStart = () => {
    if (sessionActive) {
      navigate('/dashboard');
    } else {
      navigate('/onboarding');
    }
  };

  const agents = [
    {
      name: 'Baseline Estimator',
      desc: 'Creates a custom carbon budget based on your unique lifestyle profile and country average.',
      icon: Target,
      color: 'text-blue-500 bg-blue-50 dark:bg-blue-950/20'
    },
    {
      name: 'Hotspot Analyst',
      desc: 'Scans your activities to pinpoint exactly where your emissions are concentrated.',
      icon: HelpCircle,
      color: 'text-amber-500 bg-amber-50 dark:bg-amber-950/20'
    },
    {
      name: 'Sustainability Planner',
      desc: 'Generates specific, difficulty-ranked reduction actions tailored to your hotspots.',
      icon: TrendingDown,
      color: 'text-purple-500 bg-purple-50 dark:bg-purple-950/20'
    },
    {
      name: 'Behavioral Coach',
      desc: 'Streams real-time advice and helps you complete missions to lower your footprint.',
      icon: Leaf,
      color: 'text-emerald-500 bg-emerald-50 dark:bg-emerald-950/20'
    }
  ];

  return (
    <div className="flex flex-col items-center justify-center py-10 md:py-16">
      {/* Hero Section */}
      <div className="text-center max-w-3xl mx-auto space-y-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-300 rounded-full font-medium text-xs border border-emerald-100 dark:border-emerald-900/50 shadow-sm">
          <Leaf size={12} className="animate-pulse" />
          <span>Powered by Gemini 1.5 Flash</span>
        </div>
        
        <h1 className="text-4xl md:text-6xl font-black tracking-tight text-slate-900 dark:text-slate-50 leading-tight">
          Track, Reduce, and Coach Your Way to{' '}
          <span className="bg-gradient-to-r from-emerald-600 to-teal-500 bg-clip-text text-transparent">
            Net Zero
          </span>
        </h1>
        
        <p className="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
          CarbonSense AI is a full-stack, multi-agent coaching platform designed to guide you step-by-step toward a low-carbon lifestyle through personalized metrics and gamified challenges.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
          <button
            onClick={handleStart}
            className="flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-8 py-4 rounded-2xl shadow-lg shadow-emerald-600/20 hover:scale-[1.02] active:scale-[0.98] transition-all duration-200"
          >
            <span>{sessionActive ? 'Go to Dashboard' : 'Get Started'}</span>
            <ArrowRight size={18} />
          </button>
        </div>
      </div>

      {/* Pipeline Agents Section */}
      <div className="mt-24 w-full max-w-6xl">
        <div className="text-center space-y-3 mb-16">
          <h2 className="text-3xl font-extrabold tracking-tight">The 4-Agent Pipeline</h2>
          <p className="text-slate-500 dark:text-slate-400 max-w-lg mx-auto">
            Our autonomous AI agents collaborate in sequence to assess, analyze, plan, and coach your progress.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {agents.map((agent, index) => (
            <div
              key={agent.name}
              className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow relative flex flex-col justify-between"
            >
              <div className="space-y-4">
                <div className={`p-3 rounded-xl inline-block ${agent.color}`}>
                  <agent.icon size={22} />
                </div>
                <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                  {index + 1}. {agent.name}
                </h3>
                <p className="text-slate-500 dark:text-slate-400 text-sm leading-relaxed">
                  {agent.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
