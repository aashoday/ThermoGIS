import { useEffect, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import { useHotspots } from '../hooks/useHotspots'
import { useAssets } from '../hooks/useAssets'

// Gujarat-centered default view
const DEFAULT_CENTER = [71.5, 22.5]
const DEFAULT_ZOOM = 6.5

const CLASS_COLORS = {
  industrial: '#ef4444',      // red
  non_industrial: '#6b7280',  // gray
  uncertain: '#f59e0b',       // amber
}

function colorForClass(predictedClass) {
  return CLASS_COLORS[predictedClass] || '#ffffff'
}

export default function FireMap({ onHotspotClick }) {
  const mapContainerRef = useRef(null)
  const mapRef = useRef(null)
  const [mapLoaded, setMapLoaded] = useState(false)

  const { data: hotspotsData } = useHotspots()
  const { data: assetsData } = useAssets()

  // Init map once
  useEffect(() => {
    if (mapRef.current) return

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
      center: DEFAULT_CENTER,
      zoom: DEFAULT_ZOOM,
    })

    map.addControl(new maplibregl.NavigationControl(), 'top-right')

    map.on('load', () => {
      setMapLoaded(true)
      map.resize() // force re-measure — avoids stale/incorrect size if CSS painted after init
    })

    mapRef.current = map

    // Also handle browser resize events generally
    const handleResize = () => map.resize()
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      map.remove()
      mapRef.current = null
    }
  }, [])

  // Add/update assets layer
  useEffect(() => {
    const map = mapRef.current
    if (!map || !mapLoaded || !assetsData) return

    if (map.getSource('assets')) {
      map.getSource('assets').setData(assetsData)
      return
    }

    map.addSource('assets', { type: 'geojson', data: assetsData })
    map.addLayer({
      id: 'assets-layer',
      type: 'circle',
      source: 'assets',
      paint: {
        'circle-radius': 3,
        'circle-color': '#3b82f6',
        'circle-opacity': 0.5,
      },
    })
  }, [assetsData, mapLoaded])

  // Add/update hotspots layer
  useEffect(() => {
    const map = mapRef.current
    if (!map || !mapLoaded || !hotspotsData) return

    if (map.getSource('hotspots')) {
      map.getSource('hotspots').setData(hotspotsData)
      return
    }

    map.addSource('hotspots', { type: 'geojson', data: hotspotsData })

    map.addLayer({
      id: 'hotspots-layer',
      type: 'circle',
      source: 'hotspots',
      paint: {
        'circle-radius': [
          'interpolate', ['linear'], ['get', 'frp'],
          0, 5,
          20, 14,
        ],
        'circle-color': [
          'match', ['get', 'predicted_class'],
          'industrial', CLASS_COLORS.industrial,
          'non_industrial', CLASS_COLORS.non_industrial,
          'uncertain', CLASS_COLORS.uncertain,
          '#ffffff',
        ],
        'circle-stroke-width': 1.5,
        'circle-stroke-color': '#0f172a',
        'circle-opacity': 0.9,
      },
    })

    map.on('click', 'hotspots-layer', (e) => {
      const feature = e.features[0]
      if (onHotspotClick) {
        onHotspotClick(feature.properties)
      }
    })

    map.on('mouseenter', 'hotspots-layer', () => {
      map.getCanvas().style.cursor = 'pointer'
    })
    map.on('mouseleave', 'hotspots-layer', () => {
      map.getCanvas().style.cursor = ''
    })
  }, [hotspotsData, mapLoaded, onHotspotClick])

    return (
    <div
      ref={mapContainerRef}
      style={{ width: '100%', height: '100%' }}
    />
  )
}