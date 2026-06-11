import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { hasSession } from '../lib/user-session';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const navigate = useNavigate();
  const sessionActive = hasSession();

  useEffect(() => {
    if (!sessionActive) {
      navigate('/onboarding', { replace: true });
    }
  }, [sessionActive, navigate]);

  if (!sessionActive) {
    return null;
  }

  return <>{children}</>;
}
