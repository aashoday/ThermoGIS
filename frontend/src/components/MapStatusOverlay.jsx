export function LoadingOverlay() {
  return (
    <div className="absolute inset-0 flex items-center justify-center bg-slate-900/60 z-10">
      <div className="flex flex-col items-center gap-3">
        <div className="w-8 h-8 border-2 border-slate-600 border-t-red-500 rounded-full animate-spin" />
        <span className="text-slate-300 text-sm">Loading hotspot data...</span>
      </div>
    </div>
  )
}

export function ErrorOverlay({ message, onRetry }) {
  return (
    <div className="absolute inset-0 flex items-center justify-center bg-slate-900/80 z-10">
      <div className="flex flex-col items-center gap-3 text-center px-6">
        <span className="text-4xl">⚠️</span>
        <p className="text-slate-200 text-sm max-w-sm">{message}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-4 py-2 rounded-md bg-red-600 hover:bg-red-700 text-white text-sm font-medium transition-colors"
          >
            Retry
          </button>
        )}
      </div>
    </div>
  )
}

export function EmptyStateOverlay() {
  return (
    <div className="absolute top-20 left-1/2 -translate-x-1/2 px-4 py-2 rounded-lg bg-slate-800/90 border border-slate-700 text-slate-300 text-sm z-10">
      No hotspots match the current filter.
    </div>
  )
}