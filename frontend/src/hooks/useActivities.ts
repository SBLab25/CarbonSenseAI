import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { ActivityCreate, NLActivityRequest } from '../types/api';

export function useActivities(userId: string, page = 1, pageSize = 20) {
  const queryClient = useQueryClient();

  const activitiesQuery = useQuery({
    queryKey: ['activities', userId, page, pageSize],
    queryFn: () => api.activities.get(userId, page, pageSize),
    enabled: !!userId,
  });

  const logActivityMutation = useMutation({
    mutationFn: (data: ActivityCreate) => api.activities.log(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['activities', userId] });
      queryClient.invalidateQueries({ queryKey: ['carbon', userId] });
      queryClient.invalidateQueries({ queryKey: ['userProfile', userId] });
    },
  });

  const parseNLMutation = useMutation({
    mutationFn: (data: NLActivityRequest) => api.activities.parseNL(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['activities', userId] });
      queryClient.invalidateQueries({ queryKey: ['carbon', userId] });
      queryClient.invalidateQueries({ queryKey: ['userProfile', userId] });
    },
  });

  const deleteActivityMutation = useMutation({
    mutationFn: (activityId: number) => api.activities.delete(activityId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['activities', userId] });
      queryClient.invalidateQueries({ queryKey: ['carbon', userId] });
      queryClient.invalidateQueries({ queryKey: ['userProfile', userId] });
    },
  });

  return {
    activities: activitiesQuery.data?.activities || [],
    totalCount: activitiesQuery.data?.total || 0,
    isLoading: activitiesQuery.isLoading,
    isError: activitiesQuery.isError,
    refetch: activitiesQuery.refetch,
    logActivity: logActivityMutation.mutateAsync,
    isLogging: logActivityMutation.isPending,
    parseNL: parseNLMutation.mutateAsync,
    isParsing: parseNLMutation.isPending,
    deleteActivity: deleteActivityMutation.mutateAsync,
    isDeleting: deleteActivityMutation.isPending,
  };
}
