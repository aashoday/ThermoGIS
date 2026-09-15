function StatBadge({ label, count, colorClass }) {
  return (
    <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-800/80 border border-slate-700">
      <span className={`w-2 h-2 rounded-full ${colorClass}`} />
      <span className="text-xs text-slate-400">{label}</span>
      <span className="text-xs font-semibold text-white">{count}</span>
    </div>
  )
}

export default function Header({ stats, isLoading, lastUpdated }) {
  return (
    <div className="absolute top-4 left-4 flex items-center gap-3 flex-wrap">
      <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800/90 border border-slate-700 shadow-lg backdrop-blur-sm">
        <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse" />
        <h1 className="font-bold text-white text-sm tracking-wide">ThermoGIS</h1>
      </div>

      {!isLoading && stats && (
        <>
          <StatBadge label="Industrial" count={stats.industrial} colorClass="bg-red-500" />
          <StatBadge label="Non-Industrial" count={stats.non_industrial} colorClass="bg-gray-500" />
          <StatBadge label="Uncertain" count={stats.uncertain} colorClass="bg-amber-500" />
        </>
      )}

      {lastUpdated && (
        <div className="px-2.5 py-1 rounded-md bg-slate-800/80 border border-slate-700 text-xs text-slate-400">
          Updated {lastUpdated}
        </div>
      )}
    </div>
  )
}