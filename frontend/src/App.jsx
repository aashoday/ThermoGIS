import { useState } from 'react'
import FireMap from './components/FireMap'
import HotspotDetailPanel from './components/HotspotDetailPanel'
import Legend from './components/Legend'

function App() {
  const [selectedHotspot, setSelectedHotspot] = useState(null)
  const [activeFilter, setActiveFilter] = useState(null)

  return (
    <div className="w-screen h-screen bg-slate-900 relative">
      <FireMap
        onHotspotClick={setSelectedHotspot}
        predictedClass={activeFilter}
      />
      <HotspotDetailPanel
        hotspot={selectedHotspot}
        onClose={() => setSelectedHotspot(null)}
      />
      <Legend activeFilter={activeFilter} onFilterChange={setActiveFilter} />
    </div>
  )
}

export default App