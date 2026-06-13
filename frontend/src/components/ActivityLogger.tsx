import React, { useState } from 'react';
import { useActivities } from '../hooks/useActivities';
import { getUserId } from '../lib/user-session';
import ActivityForm from './ActivityForm';
import NLActivityInput from './NLActivityInput';
import { Trash2, Calendar, ClipboardList } from 'lucide-react';
import { formatKg } from '../lib/utils';

export default function ActivityLogger() {
  const userId = getUserId() || '';
  const [activeTab, setActiveTab] = useState<'form' | 'nl'>('form');
  
  const { activities, deleteActivity, isLoading } = useActivities(userId, 1, 10);

  const getCategoryIcon = (category: string) => {
    switch (category.toLowerCase()) {
      case 'transport': return '🚗';
      case 'energy': return '⚡';
      case 'food': return '🥗';
      case 'shopping': return '🛍️';
      default: return '📄';
    }
  };

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString(undefined, { 
      month: 'short', 
      day: 'numeric', 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <div className="lg:col-span-2 space-y-6">
        <div className="flex bg-slate-100 dark:bg-slate-900 p-1 rounded-2xl border border-slate-200/50 dark:border-slate-800/50">
          <button
            onClick={() => setActiveTab('form')}
            className={`flex-1 py-3 text-sm font-semibold rounded-xl transition-all duration-200 ${
              activeTab === 'form'
                ? 'bg-white dark:bg-slate-800 text-emerald-600 dark:text-emerald-400 shadow-sm'
                : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-300'
            }`}
          >
            Form Input
          </button>
          <button
            onClick={() => setActiveTab('nl')}
            className={`flex-1 py-3 text-sm font-semibold rounded-xl transition-all duration-200 ${
              activeTab === 'nl'
                ? 'bg-white dark:bg-slate-800 text-emerald-600 dark:text-emerald-400 shadow-sm'
                : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-300'
            }`}
          >
            AI Natural Language
          </button>
        </div>

        {activeTab === 'form' ? <ActivityForm /> : <NLActivityInput />}
      </div>

      <div className="space-y-4">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <ClipboardList className="text-emerald-600" size={20} />
          <span>Recent Activity History</span>
        </h2>

        {isLoading ? (
          <div className="py-12 text-center text-sm text-slate-400">Loading history...</div>
        ) : activities.length === 0 ? (
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-8 text-center text-slate-400 text-sm">
            <Calendar className="mx-auto mb-3 text-slate-300 dark:text-slate-700" size={32} />
            <p>No activities logged yet.</p>
            <p className="text-xs text-slate-500 mt-1">Start by logging your emissions above!</p>
          </div>
        ) : (
          <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
            {activities.map((act) => (
              <div
                key={act.activity_id}
                className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 flex items-center justify-between shadow-sm group hover:border-emerald-600/30 dark:hover:border-emerald-500/30 transition-all duration-200"
              >
                <div className="flex items-center gap-3">
                  <div className="text-2xl p-2 bg-slate-50 dark:bg-slate-950 rounded-xl">
                    {getCategoryIcon(act.category)}
                  </div>
                  <div>
                    <h4 className="font-bold text-sm capitalize">
                      {act.type.replace('_', ' ')}
                    </h4>
                    <p className="text-xs text-slate-400">
                      {act.amount} {act.unit} • {formatDate(act.logged_at)}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className={`text-sm font-extrabold ${act.co2_kg < 0 ? 'text-emerald-600' : 'text-slate-700 dark:text-slate-300'}`}>
                    {act.co2_kg < 0 ? '-' : ''}{formatKg(Math.abs(act.co2_kg))}
                  </span>
                  <button
                    onClick={() => deleteActivity(act.activity_id)}
                    className="p-1.5 text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 rounded-lg hover:bg-rose-50 dark:hover:bg-rose-950/20 opacity-0 group-hover:opacity-100 focus:opacity-100 transition-all duration-200"
                    title="Delete activity"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
