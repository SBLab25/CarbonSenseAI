import React from 'react';
import { getUserId } from '../lib/user-session';
import { MissionCenter } from '../components/MissionCenter';
import { Navigate } from 'react-router-dom';

export default function MissionsPage() {
  const userId = getUserId();

  if (!userId) {
    return <Navigate to="/onboarding" replace />;
  }

  return (
    <div className="max-w-7xl mx-auto py-2 px-2 sm:px-4 lg:px-6">
      <div className="mb-6 flex flex-col gap-2">
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-800 dark:text-white sm:text-4xl bg-gradient-to-r from-emerald-600 to-teal-500 dark:from-emerald-400 dark:to-teal-300 bg-clip-text text-transparent">
          Mission Center
        </h1>
        <p className="text-slate-600 dark:text-slate-400 text-sm">
          Complete tasks tailored to your carbon emission hotspots, earn Eco Points, and level up your tier.
        </p>
      </div>

      <MissionCenter userId={userId} />
    </div>
  );
}
