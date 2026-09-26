const FILTERS = [
    { value: null, label: 'All', color: null },
    { value: 'industrial_fire', label: 'Industrial Fire', color: 'bg-red-600' },
    { value: 'gas_flare', label: 'Gas Flare', color: 'bg-orange-600' },
    { value: 'mining_activity', label: 'Mining Activity', color: 'bg-amber-800' },
    { value: 'agricultural_burn', label: 'Agricultural Burn', color: 'bg-yellow-600' },
    { value: 'wildfire', label: 'Wildfire', color: 'bg-green-600' },
    { value: 'uncertain', label: 'Uncertain', color: 'bg-gray-500' },
]

export default function Legend({ activeFilter, onFilterChange }) {
  return (
    <div className="absolute bottom-6 left-4 bg-slate-800 text-white rounded-lg shadow-2xl border border-slate-700 p-3">
      <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-2">
        Classification
      </h3>
      <div className="flex flex-col gap-1">
        {FILTERS.map((filter) => (
          <button
            key={filter.label}
            onClick={() => onFilterChange(filter.value)}
            className={`flex items-center gap-2 px-2 py-1.5 rounded text-sm text-left transition-colors ${
              activeFilter === filter.value
                ? 'bg-slate-700'
                : 'hover:bg-slate-700/50'
            }`}
          >
            {filter.color ? (
              <span className={`w-2.5 h-2.5 rounded-full ${filter.color} flex-shrink-0`} />
            ) : (
              <span className="w-2.5 h-2.5 rounded-full border border-slate-400 flex-shrink-0" />
            )}
            {filter.label}
          </button>
        ))}
      </div>
      <div className="mt-2 pt-2 border-t border-slate-700 flex items-center gap-2 text-xs text-slate-400">
        <span className="w-2 h-2 rounded-full bg-blue-500" />
        Industrial Asset
      </div>
    </div>
  )
}