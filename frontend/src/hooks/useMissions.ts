import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';

export function useMissions(userId: string) {
  const queryClient = useQueryClient();

  const missionsQuery = useQuery({
    queryKey: ['missions', userId],
    queryFn: () => api.missions.get(userId),
    enabled: !!userId,
  });

  const generateMissionsMutation = useMutation({
    mutationFn: () => api.missions.generate({ user_id: userId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['missions', userId] });
    },
  });

  const acceptMissionMutation = useMutation({
    mutationFn: (missionId: number) => api.missions.accept(missionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['missions', userId] });
    },
  });

  const completeMissionMutation = useMutation({
    mutationFn: (missionId: number) => api.missions.complete(missionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['missions', userId] });
      queryClient.invalidateQueries({ queryKey: ['carbon', userId] });
      queryClient.invalidateQueries({ queryKey: ['userProfile', userId] });
    },
  });

  return {
    pendingMissions: missionsQuery.data?.pending || [],
    activeMissions: missionsQuery.data?.active || [],
    completedMissions: missionsQuery.data?.completed || [],
    isLoading: missionsQuery.isLoading,
    isError: missionsQuery.isError,
    generateMissions: generateMissionsMutation.mutateAsync,
    isGenerating: generateMissionsMutation.isPending,
    acceptMission: acceptMissionMutation.mutateAsync,
    isAccepting: acceptMissionMutation.isPending,
    completeMission: completeMissionMutation.mutateAsync,
    isCompleting: completeMissionMutation.isPending,
  };
}
