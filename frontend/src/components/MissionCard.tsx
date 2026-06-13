import React from 'react';
import { Mission } from '../types/api';
import { Leaf, Award, Calendar, CheckCircle2, Navigation, Zap, ShoppingBag, Clock } from 'lucide-react';
import { formatKg } from '../lib/utils';

interface MissionCardProps {
  mission: Mission;
  onAccept?: (missionId: number) => void;
  onComplete?: (missionId: number) => void;
  isActionLoading?: boolean;
}

export const MissionCard: React.FC<MissionCardProps> = ({
  mission,
  onAccept,
  onComplete,
  isActionLoading = false,
}) => {
  const getCategoryIcon = (category: string) => {
    switch (category.toLowerCase().trim()) {
      case 'transport':
        return <Navigation size={18} className="text-blue-400" />;
      case 'energy':
        return <Zap size={18} className="text-amber-500" />;
      case 'food':
        return <Leaf size={18} className="text-emerald-500" />;
      case 'shopping':
        return <ShoppingBag size={18} className="text-purple-400" />;
      default:
        return <Award size={18} className="text-rose-400" />;
    }
  };

  const getCategoryEmoji = (category: string) => {
    switch (category.toLowerCase().trim()) {
      case 'transport': return '🚗';
      case 'energy': return '⚡';
      case 'food': return '🥗';
      case 'shopping': return '🛍️';
      default: return '⭐';
    }
  };

  // Calculate deadline countdown
  let deadlineLabel = '';
  let isExpired = false;

  if (mission.deadline && mission.status === 'active') {
    const now = new Date();
    const dl = new Date(mission.deadline);
    const diffTime = dl.getTime() - now.getTime();
    if (diffTime <= 0) {
      isExpired = true;
      deadlineLabel = 'Expired';
    } else {
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      if (diffDays === 1) {
        deadlineLabel = 'Expires today';
      } else {
        deadlineLabel = `${diffDays} days left`;
      }
    }
  }

  const isCompleted = mission.status === 'completed';
  const isPending = mission.status === 'pending';
  const isActive = mission.status === 'active' && !isExpired;

  return (
    <div className={`relative overflow-hidden bg-white dark:bg-slate-900/60 rounded-2xl border p-5 shadow-sm dark:shadow-lg backdrop-blur-md transition-all duration-300 ${
      isCompleted 
        ? 'border-emerald-200 dark:border-emerald-500/30 bg-emerald-50 dark:bg-emerald-950/5' 
        : isExpired 
        ? 'border-slate-200 dark:border-slate-800 opacity-60' 
        : 'border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 hover:scale-[1.01]'
    }`}>
      {/* Category Accent Indicator */}
      <div className="absolute top-0 left-0 w-1 h-full bg-slate-200 dark:bg-slate-800"></div>

      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-slate-100 dark:bg-slate-800 rounded-xl">
            {getCategoryIcon(mission.category)}
          </div>
          <span className="text-[10px] font-bold tracking-wider text-slate-500 dark:text-slate-400 uppercase">
            {getCategoryEmoji(mission.category)} {mission.category}
          </span>
        </div>

        {/* Eco points Reward */}
        <div className="flex items-center gap-1 px-2.5 py-1 bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded-lg text-xs font-bold shadow-sm">
          <span>⭐</span>
          <span>+{mission.eco_points_reward} pts</span>
        </div>
      </div>

      <div className="mt-4">
        <h4 className="text-base font-bold text-slate-800 dark:text-white leading-tight">{mission.title}</h4>
        <p className="text-xs text-slate-600 dark:text-slate-400 mt-1.5 leading-relaxed">{mission.description}</p>
      </div>

      {/* Impact stats & deadline */}
      <div className="mt-5 pt-4 border-t border-slate-200 dark:border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500 dark:text-slate-400">
        {mission.target_reduction_kg && (
          <div className="flex items-center gap-1.5">
            <span className="text-emerald-400 font-semibold">
              ≈{formatKg(mission.target_reduction_kg)}
            </span>
            <span>offset impact</span>
          </div>
        )}

        {/* Countdown */}
        {deadlineLabel && (
          <div className={`flex items-center gap-1 ${isExpired ? 'text-rose-600 dark:text-red-400' : 'text-slate-500 dark:text-slate-400'}`}>
            <Clock size={12} />
            <span className="font-medium">{deadlineLabel}</span>
          </div>
        )}

        {isCompleted && mission.completed_at && (
          <div className="flex items-center gap-1 text-emerald-400 font-medium">
            <CheckCircle2 size={12} />
            <span>Completed on {new Date(mission.completed_at).toLocaleDateString()}</span>
          </div>
        )}
      </div>

      {/* Action CTA */}
      <div className="mt-5">
        {isPending && onAccept && (
          <button
            onClick={() => onAccept(mission.id)}
            disabled={isActionLoading}
            className="w-full py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-850 dark:hover:bg-slate-800 text-slate-800 dark:text-white disabled:opacity-50 text-xs font-bold rounded-xl border border-slate-200 dark:border-slate-700 transition-colors shadow-md"
          >
            Accept Challenge
          </button>
        )}

        {isActive && onComplete && (
          <button
            onClick={() => onComplete(mission.id)}
            disabled={isActionLoading}
            className="w-full py-2 bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 disabled:opacity-50 text-white text-xs font-bold rounded-xl shadow-md shadow-emerald-950/20 transition-all duration-200"
          >
            Complete Challenge
          </button>
        )}

        {isExpired && (
          <div className="w-full text-center py-2 bg-slate-50 dark:bg-slate-850 text-slate-400 dark:text-slate-500 text-xs font-semibold rounded-xl border border-slate-200 dark:border-slate-800 select-none">
            Challenge Expired
          </div>
        )}

        {isCompleted && (
          <div className="w-full text-center py-2 bg-emerald-50 dark:bg-emerald-950/10 text-emerald-600 dark:text-emerald-400 border border-emerald-100 dark:border-emerald-900/20 text-xs font-bold rounded-xl select-none flex items-center justify-center gap-1">
            <CheckCircle2 size={12} />
            <span>Challenge Achieved</span>
          </div>
        )}
      </div>
    </div>
  );
};
