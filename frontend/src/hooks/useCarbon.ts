import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';

export function useCarbon(userId: string) {
  return useQuery({
    queryKey: ['carbon', 'summary', userId],
    queryFn: () => api.carbon.summary(userId),
    enabled: !!userId,
  });
}

export function useCarbonTrends(userId: string, days = 30) {
  return useQuery({
    queryKey: ['carbon', 'trends', userId, days],
    queryFn: () => api.carbon.trends(userId, days),
    enabled: !!userId,
  });
}

export function useProgress(userId: string) {
  return useQuery({
    queryKey: ['carbon', 'progress', userId],
    queryFn: () => api.carbon.progress(userId),
    enabled: !!userId,
  });
}
