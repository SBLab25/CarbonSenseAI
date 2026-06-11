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
    <div className="max-w-7xl mx-auto py-2 px-2 sm:px-4 lg:px-6">
      <div className="mb-6 flex flex-col gap-2">
        <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl bg-gradient-to-r from-emerald-400 to-teal-300 bg-clip-text text-transparent">
          Sustainability Dashboard
        </h1>
        <p className="text-slate-400 text-sm">
          Track your real-time carbon offsets, log activities, and check AI-coached sustainability insights.
        </p>
      </div>

      <Dashboard userId={userId} />
    </div>
  );
}
