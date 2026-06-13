import React from 'react';

interface GoalProgressBarProps {
  reductionPct: number;
  targetPct: number;
}

export const GoalProgressBar: React.FC<GoalProgressBarProps> = ({
  reductionPct,
  targetPct,
}) => {
  const target = targetPct || 15.0; // default to 15%
  const current = reductionPct || 0.0;
  
  // Calculate percentage of target achieved
  const progressRatio = target > 0 ? (current / target) * 100 : 0;
  const clampedProgress = Math.min(100, Math.max(0, progressRatio));

  const isAchieved = current >= target;

  return (
    <div className="flex flex-col w-full bg-white dark:bg-slate-900/60 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm dark:shadow-lg">
      <div className="flex justify-between items-center mb-3">
        <span className="text-sm font-semibold text-slate-500 dark:text-slate-400">Monthly Reduction Goal</span>
        <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
          isAchieved ? 'bg-emerald-100 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400' : 'bg-amber-100 dark:bg-amber-500/20 text-amber-600 dark:text-amber-400'
        }`}>
          {isAchieved ? 'Goal Achieved! 🎉' : 'Keep going!'}
        </span>
      </div>

      {/* Progress Track */}
      <div className="relative w-full h-4 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden mb-2">
        <div
          className="h-full bg-gradient-to-r from-emerald-600 to-teal-400 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${clampedProgress}%` }}
        />
      </div>

      <div className="flex justify-between items-center text-xs text-slate-500 dark:text-slate-400 mt-1">
        <span>{current.toFixed(1)}% reduction achieved</span>
        <span className="font-semibold text-slate-800 dark:text-white">Target: {target.toFixed(1)}%</span>
      </div>
      
      {current < 0 && (
        <div className="mt-3 text-xs text-rose-600 dark:text-red-400 bg-rose-50 dark:bg-red-950/20 border border-rose-200 dark:border-red-900/30 px-3 py-2 rounded-xl">
          ⚠️ Your emissions are currently higher than your baseline. Track more green habits!
        </div>
      )}
    </div>
  );
};
