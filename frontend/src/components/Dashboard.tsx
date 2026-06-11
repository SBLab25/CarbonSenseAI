import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Leaf, ArrowDownRight, ArrowUpRight, Award, Flame, Zap, Navigation, ShoppingBag } from 'lucide-react';
import { api } from '../lib/api';
import { useCarbon, useCarbonTrends, useProgress } from '../hooks/useCarbon';
import { FootprintPieChart } from './FootprintPieChart';
import { TrendLineChart } from './TrendLineChart';
import { GoalProgressBar } from './GoalProgressBar';
import EcoPointsBadge from './EcoPointsBadge';
import { formatKg } from '../lib/utils';

interface DashboardProps {
  userId: string;
}

export const Dashboard: React.FC<DashboardProps> = ({ userId }) => {
  const navigate = useNavigate();
  const [selectedDays, setSelectedDays] = useState(30);

  // Queries
  const { data: summary, isLoading: isSummaryLoading } = useCarbon(userId);
  const { data: trends, isLoading: isTrendsLoading } = useCarbonTrends(userId, selectedDays);
  const { data: progress, isLoading: isProgressLoading } = useProgress(userId);
  
  const { data: userProfile, isLoading: isProfileLoading } = useQuery({
    queryKey: ['userProfile', userId],
    queryFn: () => api.users.get(userId),
    enabled: !!userId,
  });

  const { data: insights, isLoading: isInsightsLoading } = useQuery({
    queryKey: ['insights', userId],
    queryFn: () => api.agents.insights(userId),
    enabled: !!userId,
  });

  const isLoading = isSummaryLoading || isTrendsLoading || isProgressLoading || isProfileLoading || isInsightsLoading;

  const handleAnalyzeClick = () => {
    // Navigate to ChatPage with query state
    navigate('/chat?analyze=true');
  };

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        {/* Row 1 skeleton */}
        <div className="h-32 bg-slate-900/40 rounded-2xl border border-slate-800 p-6"></div>
        {/* Row 2 skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="h-[320px] bg-slate-900/40 rounded-2xl border border-slate-800 p-6"></div>
          <div className="h-[320px] bg-slate-900/40 rounded-2xl border border-slate-800 p-6"></div>
        </div>
        {/* Row 3 skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="h-40 bg-slate-900/40 rounded-2xl border border-slate-800 p-6"></div>
          <div className="h-40 bg-slate-900/40 rounded-2xl border border-slate-800 p-6"></div>
        </div>
      </div>
    );
  }

  // Get primary hotspot icon/styling
  const getHotspotIcon = (category: string) => {
    switch (category.toLowerCase().trim()) {
      case 'transport':
        return <Navigation className="text-blue-400" size={24} />;
      case 'energy':
        return <Zap className="text-amber-500" size={24} />;
      case 'food':
        return <Leaf className="text-emerald-500" size={24} />;
      case 'shopping':
        return <ShoppingBag className="text-purple-400" size={24} />;
      default:
        return <Flame className="text-rose-400" size={24} />;
    }
  };

  const hasActivities = summary && summary.total_kg > 0;
  const reduction = summary ? summary.reduction_pct : 0;
  const isReduced = reduction >= 0;

  // AI tip from insights or fallback
  const aiTip = insights?.planner?.strategies?.[0]?.action 
    ? `Tip: ${insights.planner.strategies[0].action}`
    : "Track more daily habits and tap 'Analyze with AI' to unlock custom coaching recommendations.";

  const primaryHotspot = insights?.analyst?.primary_hotspot || (summary?.breakdown ? Object.entries(summary.breakdown).sort((a,b) => b[1].kg - a[1].kg)[0]?.[0] : null);
  const primaryHotspotKg = (primaryHotspot && summary?.breakdown?.[primaryHotspot]?.kg) || 0;

  return (
    <div className="space-y-6">
      {/* Row 1: Monthly footprint metric card */}
      <div className="relative overflow-hidden bg-slate-900/60 rounded-2xl border border-slate-800 p-6 shadow-xl backdrop-blur-md">
        <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/5 rounded-full blur-3xl transform translate-x-20 -translate-y-20"></div>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div>
            <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">This Month's Footprint</h2>
            <div className="flex items-baseline gap-3 mt-1.5">
              <span className="text-4xl font-extrabold text-white tracking-tight">
                {formatKg(summary?.total_kg || 0)}
              </span>
              {summary && summary.baseline_kg > 0 && (
                <div className={`flex items-center gap-0.5 text-sm font-bold px-2 py-0.5 rounded-full ${
                  isReduced ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                }`}>
                  {isReduced ? <ArrowDownRight size={16} /> : <ArrowUpRight size={16} />}
                  <span>{Math.abs(reduction).toFixed(1)}% vs baseline</span>
                </div>
              )}
            </div>
            {summary && (
              <p className="text-xs text-slate-500 mt-2">
                Equivalent to <span className="font-semibold text-slate-300">{summary.vs_india_average_pct.toFixed(0)}%</span> of the Indian national average monthly footprint (158 kg CO₂).
              </p>
            )}
          </div>
          
          <div className="flex items-center gap-4 bg-slate-800/40 p-4 rounded-xl border border-slate-800">
            <div className="p-3 bg-emerald-600/20 text-emerald-400 rounded-lg">
              <Leaf size={24} />
            </div>
            <div>
              <p className="text-xs text-slate-400">Baseline Carbon</p>
              <p className="text-lg font-bold text-white mt-0.5">
                {formatKg(summary?.baseline_kg || userProfile?.baseline_footprint_kg || 0)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Row 2: Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-5 bg-slate-900/60 rounded-2xl border border-slate-800 p-6 shadow-xl backdrop-blur-md flex flex-col justify-between">
          <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">Carbon Breakdown</h3>
          <div className="flex-1 flex items-center justify-center">
            <FootprintPieChart breakdown={summary?.breakdown || {}} totalKg={summary?.total_kg || 0} />
          </div>
        </div>
        
        <div className="lg:col-span-7 bg-slate-900/60 rounded-2xl border border-slate-800 p-6 shadow-xl backdrop-blur-md flex flex-col justify-between">
          <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2">Emissions Over Time</h3>
          <div className="flex-1">
            <TrendLineChart trends={trends || []} selectedDays={selectedDays} setSelectedDays={setSelectedDays} />
          </div>
        </div>
      </div>

      {/* Row 3: Goal Tracker & Hotspot */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <GoalProgressBar 
          reductionPct={progress?.reduction_pct || 0} 
          targetPct={userProfile?.monthly_target_reduction_pct || 15.0} 
        />
        
        <div className="flex flex-col bg-slate-900/60 rounded-2xl border border-slate-800 p-5 shadow-lg relative overflow-hidden group">
          <div className="flex justify-between items-start mb-3">
            <div>
              <span className="text-sm font-semibold text-slate-400">Highest Carbon Hotspot</span>
              {primaryHotspot ? (
                <h4 className="text-xl font-bold text-white mt-1 capitalize flex items-center gap-2">
                  {getHotspotIcon(primaryHotspot)}
                  <span>{primaryHotspot}</span>
                </h4>
              ) : (
                <h4 className="text-xl font-bold text-white mt-1">No hotspots yet</h4>
              )}
            </div>
            {primaryHotspot && (
              <span className="text-xs font-semibold px-2 py-0.5 bg-slate-800 text-slate-300 rounded-full">
                {formatKg(primaryHotspotKg)}
              </span>
            )}
          </div>
          
          <div className="flex-1 flex items-center mt-2 p-3.5 bg-emerald-950/20 border border-emerald-900/20 rounded-xl">
            <p className="text-xs text-emerald-300/90 leading-relaxed font-medium">
              {aiTip}
            </p>
          </div>
        </div>
      </div>

      {/* Row 4: Full Eco Points Card */}
      <div className="grid grid-cols-1 gap-6">
        <EcoPointsBadge />
      </div>

      {/* Action CTA Button */}
      <div className="flex justify-center pt-4">
        <button
          onClick={handleAnalyzeClick}
          className="flex items-center gap-2.5 px-8 py-3.5 bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white font-bold rounded-xl shadow-xl shadow-emerald-950/20 hover:scale-[1.02] active:scale-[0.98] transition-all duration-300"
        >
          <Leaf size={18} className="animate-pulse" />
          <span>Analyze with AI Coach</span>
        </button>
      </div>
    </div>
  );
};
