import React from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import { CategoryBreakdown } from '../types/api';
import { getCategoryColor, formatKg } from '../lib/utils';

interface FootprintPieChartProps {
  breakdown: Record<string, CategoryBreakdown>;
  totalKg: number;
}

export const FootprintPieChart: React.FC<FootprintPieChartProps> = ({ breakdown, totalKg }) => {
  const data = Object.entries(breakdown)
    .map(([category, details]) => ({
      name: category.charAt(0).toUpperCase() + category.slice(1),
      value: details.kg,
      percentage: details.pct,
      color: getCategoryColor(category),
    }))
    .filter((item) => item.value > 0);

  if (data.length === 0) {
    return (
      <div className="flex h-[260px] flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 p-6 text-center text-slate-500 dark:text-slate-400">
        <p className="text-sm font-medium">No activity data yet</p>
        <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">Log your first activity to generate a carbon breakdown.</p>
      </div>
    );
  }

  return (
    <div className="relative flex h-[260px] w-full items-center justify-center">
      {/* Center Label Overlay */}
      <div className="absolute flex flex-col items-center justify-center text-center pointer-events-none select-none">
        <span className="text-xs font-semibold tracking-wider text-slate-500 dark:text-slate-400 uppercase">Total CO₂</span>
        <span className="text-xl font-bold text-slate-800 dark:text-white mt-0.5">{formatKg(totalKg)}</span>
      </div>

      <div className="w-full h-full" role="img" aria-label="Carbon footprint breakdown by category">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <title>Carbon footprint breakdown by category</title>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={65}
              outerRadius={85}
              paddingAngle={4}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} stroke="#0f172a" strokeWidth={2} />
              ))}
            </Pie>
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const entry = payload[0].payload;
                  return (
                    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white/90 dark:bg-slate-900/90 p-3 shadow-xl backdrop-blur-sm">
                      <div className="flex items-center gap-2">
                        <span
                          className="h-3.5 w-3.5 rounded-full"
                          style={{ backgroundColor: entry.color }}
                        />
                        <span className="text-sm font-bold text-slate-800 dark:text-white">{entry.name}</span>
                      </div>
                      <div className="mt-1.5 flex flex-col text-xs text-slate-600 dark:text-slate-300">
                        <span>Carbon: {formatKg(entry.value)}</span>
                        <span>Percentage: {entry.percentage.toFixed(1)}%</span>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
