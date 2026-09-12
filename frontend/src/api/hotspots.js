const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

export async function fetchHotspots({ predictedClass, minConfidence } = {}) {
  const params = new URLSearchParams()
  if (predictedClass) params.set('predicted_class', predictedClass)
  if (minConfidence !== undefined) params.set('min_confidence', minConfidence)

  const url = `${API_BASE_URL}/api/hotspots${params.toString() ? `?${params}` : ''}`
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Failed to fetch hotspots: ${response.status}`)
  }
  return response.json()
}

export async function fetchAssets() {
  const response = await fetch(`${API_BASE_URL}/api/assets`)
  if (!response.ok) {
    throw new Error(`Failed to fetch assets: ${response.status}`)
  }
  return response.json()
}