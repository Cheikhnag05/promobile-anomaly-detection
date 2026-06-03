export default function StatCard({ title, value, sub, color = 'blue', icon: Icon }) {
  const colorMap = {
    blue: 'text-brand-blue bg-brand-blue/10 border-brand-blue/20',
    green: 'text-brand-green bg-brand-green/10 border-brand-green/20',
    amber: 'text-brand-amber bg-brand-amber/10 border-brand-amber/20',
    red: 'text-brand-red bg-brand-red/10 border-brand-red/20',
    orange: 'text-brand-orange bg-brand-orange/10 border-brand-orange/20',
  }
  const cls = colorMap[color] || colorMap.blue

  return (
    <div className="card flex items-start gap-4 animate-slide-up">
      {Icon && (
        <div className={`w-10 h-10 rounded-lg border flex items-center justify-center flex-shrink-0 ${cls}`}>
          <Icon className="w-5 h-5" />
        </div>
      )}
      <div className="min-w-0">
        <p className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-1">{title}</p>
        <p className="text-2xl font-bold text-white truncate">{value}</p>
        {sub && <p className="text-slate-500 text-xs mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}
