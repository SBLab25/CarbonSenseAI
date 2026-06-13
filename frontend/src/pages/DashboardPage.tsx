import React from 'react';
import { getUserId } from '../lib/user-session';
import { Dashboard } from '../components/Dashboard';
import { Navigate } from 'react-router-dom';

export default function DashboardPage() {
  const userId = getUserId();

  if (!userId) {
    return <Navigate to="/onboarding" replace />;
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h2 className="text-3xl font-extrabold tracking-tight text-slate-800 dark:text-white bg-gradient-to-r from-emerald-600 to-teal-500 dark:from-emerald-400 dark:to-teal-300 bg-clip-text text-transparent">
          Sustainability Dashboard
        </h2>
        <p className="text-slate-600 dark:text-slate-400 text-sm">
          Track your real-time carbon offsets, log activities, and check AI-coached sustainability insights.
        </p>
      </div>

      <Dashboard userId={userId} />
    </div>
  );
}
