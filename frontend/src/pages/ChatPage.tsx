import React from 'react';
import { getUserId } from '../lib/user-session';
import { ChatInterface } from '../components/ChatInterface';
import { Navigate } from 'react-router-dom';

export default function ChatPage() {
  const userId = getUserId();

  if (!userId) {
    return <Navigate to="/onboarding" replace />;
  }

  return (
    <div className="max-w-4xl mx-auto py-2 px-2 sm:px-4">
      <div className="mb-6 flex flex-col gap-2">
        <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl bg-gradient-to-r from-emerald-400 to-teal-300 bg-clip-text text-transparent">
          AI coaching desk
        </h1>
        <p className="text-slate-400 text-sm">
          Discuss your habits, get immediate tips, or run a full multi-agent footprint audit.
        </p>
      </div>

      <ChatInterface userId={userId} />
    </div>
  );
}
