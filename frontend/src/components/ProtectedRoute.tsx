import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { hasSession } from '../lib/user-session';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const navigate = useNavigate();
  const { user, isLoading } = useAuth();
  // Also check hasSession to ensure onboarding was completed, 
  // since the backend only creates the user profile after onboarding.
  const onboardingCompleted = hasSession(); 

  useEffect(() => {
    if (!isLoading) {
      if (!user) {
        navigate('/auth', { replace: true });
      } else if (!onboardingCompleted) {
        navigate('/onboarding', { replace: true });
      }
    }
  }, [user, isLoading, onboardingCompleted, navigate]);

  if (isLoading) {
    return <div className="min-h-screen bg-slate-950 flex items-center justify-center text-emerald-500">Loading...</div>;
  }

  if (!user || !onboardingCompleted) {
    return null;
  }

  return <>{children}</>;
}
