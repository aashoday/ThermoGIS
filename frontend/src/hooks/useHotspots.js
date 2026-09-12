import { useQuery } from '@tanstack/react-query'
import { fetchHotspots } from '../api/hotspots'

export function useHotspots(filters = {}) {
  return useQuery({
    queryKey: ['hotspots', filters],
    queryFn: () => fetchHotspots(filters),
  })
}
