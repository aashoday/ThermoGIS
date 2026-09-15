import { useState, useMemo } from 'react'
import FireMap from './components/FireMap'
import HotspotDetailPanel from './components/HotspotDetailPanel'
import Legend from './components/Legend'
import Header from './components/Header'
import { LoadingOverlay, ErrorOverlay, EmptyStateOverlay } from './components/MapStatusOverlay'
import { useHotspots } from './hooks/useHotspots'

function App() {
  const [selectedHotspot, setSelectedHotspot] = useState(null)
  const [activeFilter, setActiveFilter] = useState(null)

  // Separate unfiltered fetch just for the header stats, so the counts
  // always reflect the full dataset regardless of the active map filter.
  const { data: allHotspotsData, isLoading, isError, refetch, dataUpdatedAt } =
    useHotspots({ predictedClass: null })

  const stats = useMemo(() => {
    if (!allHotspotsData?.features) return null
    const counts = { industrial: 0, non_industrial: 0, uncertain: 0 }
    for (const feature of allHotspotsData.features) {
      const cls = feature.properties.predicted_class
      if (cls in counts) counts[cls] += 1
    }
    return counts
  }, [allHotspotsData])

  const lastUpdated = dataUpdatedAt
    ? new Date(dataUpdatedAt).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
    : null

  const isEmpty = !isLoading && !isError && allHotspotsData?.features?.length === 0

  return (
    <div className="w-screen h-screen bg-slate-900 relative">
      <FireMap onHotspotClick={setSelectedHotspot} predictedClass={activeFilter} />

      {isLoading && <LoadingOverlay />}
      {isError && (
        <ErrorOverlay
          message="Couldn't reach the ThermoGIS backend. Check that the API is running."
          onRetry={refetch}
        />
      )}
      {isEmpty && <EmptyStateOverlay />}

      <Header stats={stats} isLoading={isLoading} lastUpdated={lastUpdated} />
      <HotspotDetailPanel hotspot={selectedHotspot} onClose={() => setSelectedHotspot(null)} />
      <Legend activeFilter={activeFilter} onFilterChange={setActiveFilter} />
    </div>
  )
}

export default App