import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { agenticApi } from './api';

const ACTIVE_STATUSES = ['running', 'reviewing', 'awaiting_confirmation'];

export function useAgentRun(runId) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ['agent-run', runId],
    queryFn: () => agenticApi.getRun(runId),
    enabled: !!runId,
    refetchInterval: (query) => {
      const data = query?.state?.data;
      if (data && ACTIVE_STATUSES.includes(data.status)) {
        return 750;
      }
      return false;
    },
  });

  const cancelMutation = useMutation({
    mutationFn: () => agenticApi.cancelRun(runId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-run', runId] });
    },
  });

  return {
    status: query.data?.status || 'idle',
    artifact: query.data?.artifact || null,
    error: query.error || cancelMutation.error,
    cancel: cancelMutation.mutate,
    refresh: query.refetch,
    isLoading: query.isLoading,
  };
}
