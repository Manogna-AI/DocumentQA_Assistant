import { useQuery } from '@tanstack/react-query';
import { checkHealth } from '@/services/healthService';

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: checkHealth,
    refetchInterval: 15_000,
  });
}
