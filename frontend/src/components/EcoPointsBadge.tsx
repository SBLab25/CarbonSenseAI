import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getUserId } from '../lib/user-session';
import { api } from '../lib/api';
import { getEcoTier } from '../lib/utils';

interface EcoPointsBadgeProps {
  compact?: boolean;
}

export default function EcoPointsBadge({ compact = false }: EcoPointsBadgeProps) {
  const userId = getUserId();
  
  const { data: userProfile, isLoading } = useQuery({
    queryKey: ['userProfile', userId],
    queryFn: () => (userId ? api.users.get(userId) : null),
    enabled: !!userId,
  });

  if (!userId || isLoading || !userProfile) {
    return null;
  }

  const points = userProfile.eco_points || 0;
  const tier = getEcoTier(points);

  const getTierIcon = (tierName: string) => {
    switch (tierName) {
      case 'Forest': return '🌲';
      case 'Tree': return '🌳';
      case 'Sapling': return '🌿';
      default: return '🌱';
    }
  };

  if (compact) {
    return (
      <div className="flex items-center gap-1.5 px-3 py-1 bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-300 rounded-full font-medium text-sm border border-emerald-100 dark:border-emerald-900/50 shadow-sm transition-all hover:scale-105 duration-200">
        <span>{getTierIcon(tier)}</span>
        <span>{points} pts</span>
      </div>
    );
  }

  let nextTier = '';
  let nextTierPoints = 0;
  let progressPct = 100;
  
  if (tier === 'Seedling') {
    nextTier = 'Sapling';
    nextTierPoints = 200;
    progressPct = (points / 200) * 100;
  } else if (tier === 'Sapling') {
    nextTier = 'Tree';
    nextTierPoints = 500;
    progressPct = ((points - 200) / 300) * 100;
  } else if (tier === 'Tree') {
    nextTier = 'Forest';
    nextTierPoints = 1000;
    progressPct = ((points - 500) / 500) * 100;
  }

  return (
    <div className="bg-gradient-to-br from-emerald-500 to-teal-600 text-white rounded-2xl p-6 shadow-lg border border-emerald-400/20 relative overflow-hidden group">
      <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full blur-2xl transform translate-x-12 -translate-y-12 transition-transform duration-500 group-hover:scale-110"></div>
      
      <div className="flex items-start justify-between relative z-10">
        <div>
          <p className="text-emerald-100 text-xs font-semibold uppercase tracking-wider">CarbonSense Tier</p>
          <h3 className="text-2xl font-bold mt-1 flex items-center gap-2">
            <span>{getTierIcon(tier)}</span>
            <span>{tier}</span>
          </h3>
        </div>
        <div className="text-right">
          <p className="text-emerald-100 text-xs font-semibold uppercase tracking-wider">Eco Points</p>
          <p className="text-3xl font-extrabold mt-0.5 tracking-tight">{points}</p>
        </div>
      </div>

      {tier !== 'Forest' && (
        <div className="mt-6 relative z-10">
          <div className="flex justify-between text-xs text-emerald-100 font-medium mb-2">
            <span>Progress to {nextTier}</span>
            <span>{points} / {nextTierPoints} pts</span>
          </div>
          <div className="w-full bg-emerald-700/40 rounded-full h-2.5 overflow-hidden backdrop-blur-sm">
            <div 
              className="bg-white rounded-full h-full shadow-inner transition-all duration-1000 ease-out"
              style={{ width: `${Math.min(Math.max(progressPct, 0), 100)}%` }}
            ></div>
          </div>
        </div>
      )}
      
      {tier === 'Forest' && (
        <p className="mt-4 text-xs text-emerald-100 font-medium relative z-10">
          🎉 Maximum Eco Tier reached! You are a true Carbon Champion.
        </p>
      )}
    </div>
  );
}
