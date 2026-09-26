const CLASS_LABELS = {
  industrial_fire: "Industrial Fire",
  gas_flare: "Gas Flare",
  mining_activity: "Mining Activity",
  agricultural_burn: "Agricultural Burn",
  wildfire: "Wildfire",
  uncertain: "Uncertain",
};

const CLASS_COLORS = {
  industrial_fire: "#dc2626",
  gas_flare: "#ea580c",
  mining_activity: "#92400e",
  agricultural_burn: "#ca8a04",
  wildfire: "#16a34a",
  uncertain: "#6b7280",
};

function formatDistance(meters) {
  if (meters == null) return 'N/A'
  if (meters < 1000) return `${Math.round(meters)} m`
  return `${(meters / 1000).toFixed(2)} km`
}

function formatDateTime(isoString) {
  if (!isoString) return 'N/A'
  const date = new Date(isoString)
  return date.toLocaleString('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

function getDirectionsUrl(hotspot) {
  const [lon, lat] = hotspot.geometry?.coordinates || []
  return `https://www.google.com/maps/dir/?api=1&destination=${lat},${lon}`
}

export default function HotspotDetailPanel({ hotspot, onClose }) {
  if (!hotspot) return null

  const classColor = CLASS_COLORS[hotspot.predicted_class] || 'bg-white'
  const classLabel = CLASS_LABELS[hotspot.predicted_class] || 'Unknown'
  const confidencePct = hotspot.prediction_confidence
    ? Math.round(hotspot.prediction_confidence * 100)
    : null

  return (
    <div className="absolute top-4 right-4 w-80 bg-slate-800 text-white rounded-lg shadow-2xl border border-slate-700 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700">
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full" style={{ backgroundColor: classColor }} />
          <h2 className="font-semibold text-sm">{classLabel}</h2>
        </div>

        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white text-lg leading-none"
          aria-label="Close"
        >
          ×
        </button>
      </div>

      <div className="p-4 space-y-3 text-sm">
        <img
          src={getSatelliteImageUrl(
            hotspot.latitude,
            hotspot.longitude,
            hotspot.acquired_at
          )}
          alt="Satellite view"
          style={{
            width: '100%',
            borderRadius: 8,
            marginBottom: 12,
          }}
          onError={(e) => {
            e.target.style.display = 'none'
          }}
        />

        {confidencePct !== null && (
          <div>
            <div className="flex justify-between text-slate-400 mb-1">
              <span>Confidence</span>
              <span>{confidencePct}%</span>
            </div>

            <div className="w-full h-1.5 bg-slate-700 rounded-full overflow-hidden">
              <div
                className="h-full"
                style={{ width: `${confidencePct}%`, backgroundColor: classColor }}
              />
            </div>
          </div>
        )}

        <DetailRow
          label="Nearest Asset"
          value={hotspot.nearest_asset_name || 'Unnamed'}
        />

        <DetailRow
          label="Asset Type"
          value={hotspot.nearest_asset_type || 'N/A'}
        />

        <DetailRow
          label="Distance"
          value={formatDistance(hotspot.distance_to_asset_m)}
        />

        <DetailRow
          label="Radiative Power"
          value={hotspot.frp != null ? `${hotspot.frp} MW` : 'N/A'}
        />

        <DetailRow
          label="Source"
          value={hotspot.source}
        />

        <DetailRow
          label="Detected"
          value={formatDateTime(hotspot.acquired_at)}
        />

        <DetailRow
          label="Cluster ID"
          value={hotspot.cluster_id ?? 'N/A'}
        />

        <a
          href={getDirectionsUrl(hotspot)}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center gap-2 mt-2 px-4 py-2 rounded-md bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition-colors"
        >
          📍 Get Directions
        </a>
      </div>
    </div>
  )
}

function getSatelliteImageUrl(lat, lon, acquiredAt) {
  const buffer = 0.05 // ~5.5km box around the hotspot
  const bbox = `${lat - buffer},${lon - buffer},${lat + buffer},${lon + buffer}`
  const date = acquiredAt.slice(0, 10) // YYYY-MM-DD

  return `https://wvs.earthdata.nasa.gov/api/v1/snapshot?REQUEST=GetSnapshot&LAYERS=VIIRS_SNPP_CorrectedReflectance_TrueColor&CRS=EPSG:4326&TIME=${date}&BBOX=${bbox}&FORMAT=image/jpeg&WIDTH=400&HEIGHT=400`
}

function DetailRow({ label, value }) {
  return (
    <div className="flex justify-between gap-2">
      <span className="text-slate-400">{label}</span>
      <span className="text-right font-medium">{value}</span>
    </div>
  )
}