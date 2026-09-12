import { useQuery } from '@tanstack/react-query'
import { fetchAssets } from '../api/hotspots'

export function useAssets() {
  return useQuery({
    queryKey: ['assets'],
    queryFn: fetchAssets,
    staleTime: 5 * 60 * 1000, // assets barely change — refetch far less often than hotspots
  })
}