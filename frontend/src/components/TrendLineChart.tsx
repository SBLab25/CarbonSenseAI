import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import { CarbonTrend } from '../types/api';
import { formatKg } from '../lib/utils';

interface TrendLineChartProps {
  trends: CarbonTrend[];
  selectedDays: number;
  setSelectedDays: (days: number) => void;
}

export const TrendLineChart: React.FC<TrendLineChartProps> = ({
  trends,
  selectedDays,
  setSelectedDays,
}) => {
  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch {
      return dateStr;
    }
  };

  const hasData = trends.some((item) => item.total_kg > 0);

  const ranges = [
    { label: '7d', value: 7 },
    { label: '30d', value: 30 },
    { label: '90d', value: 90 },
  ];

  return (
    <div className="flex flex-col h-full w-full">
      {/* Range Selector */}
      <div className="flex justify-end gap-1.5 mb-4">
        {ranges.map((r) => (
          <button
            key={r.value}
            onClick={() => setSelectedDays(r.value)}
            className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all duration-200 ${
              selectedDays === r.value
                ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-600/20'
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white'
            }`}
          >
            {r.label}
          </button>
        ))}
      </div>

      {/* Chart container */}
      <div className="flex-1 min-h-[200px]" role="img" aria-label="Daily carbon footprint trends">
        {!hasData ? (
          <div className="flex h-full flex-col items-center justify-center rounded-2xl border border-dashed border-slate-700 bg-slate-900/50 p-6 text-center text-slate-400">
            <p className="text-sm font-medium">No trend data yet</p>
            <p className="mt-1 text-xs text-slate-500">
              Start logging activities to see your trend.
            </p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <title>Daily carbon footprint trends</title>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
              <XAxis
                dataKey="date"
                tickFormatter={formatDate}
                stroke="#64748b"
                fontSize={10}
                tickLine={false}
              />
              <YAxis
                stroke="#64748b"
                fontSize={10}
                tickLine={false}
                tickFormatter={(val) => `${val} kg`}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <div className="rounded-xl border border-slate-700 bg-slate-900/90 p-3 shadow-xl backdrop-blur-sm">
                        <p className="text-xs font-semibold text-slate-400">
                          {new Date(data.date).toLocaleDateString('en-US', {
                            weekday: 'long',
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric',
                          })}
                        </p>
                        <p className="text-sm font-bold text-white mt-1">
                          CO₂: {formatKg(data.total_kg)}
                        </p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Line
                type="monotone"
                dataKey="total_kg"
                stroke="#16a34a"
                strokeWidth={3}
                dot={{ r: 4, stroke: '#10b981', strokeWidth: 1, fill: '#0f172a' }}
                activeDot={{ r: 6, stroke: '#34d399', strokeWidth: 2, fill: '#16a34a' }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};
