import { Activity, Radio, Map, Zap, Brain, ChevronRight } from 'lucide-react'

const NAV = [
  { id: 'overview', label: 'Vue Générale', icon: Activity },
  { id: 'live', label: 'Flux en Direct', icon: Zap },
  { id: 'map', label: 'Carte des Tours', icon: Map },
  { id: 'predict', label: 'Prédiction Live', icon: Radio },
  { id: 'model', label: 'Modèle IA', icon: Brain },
]

export default function Sidebar({ current, onChange }) {
  return (
    <aside className="w-64 flex-shrink-0 bg-dark-800 border-r border-dark-600 flex flex-col">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-dark-600">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-brand-blue/20 border border-brand-blue/40 flex items-center justify-center">
            <Radio className="w-5 h-5 text-brand-blue" />
          </div>
          <div>
            <div className="text-white font-bold text-sm leading-tight">Promobile</div>
            <div className="text-slate-400 text-xs">Anomaly Detection</div>
          </div>
        </div>
      </div>

      {/* API status */}
      <div className="px-4 py-3 border-b border-dark-600">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span className="w-2 h-2 rounded-full bg-brand-green animate-pulse-slow" />
          API connectée · localhost:8000
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV.map(({ id, label, icon: Icon }) => {
          const active = current === id
          return (
            <button
              key={id}
              onClick={() => onChange(id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group ${
                active
                  ? 'bg-brand-blue/15 text-brand-blue border border-brand-blue/30'
                  : 'text-slate-400 hover:text-white hover:bg-dark-700'
              }`}
            >
              <Icon className={`w-4 h-4 flex-shrink-0 ${active ? 'text-brand-blue' : 'text-slate-500 group-hover:text-slate-300'}`} />
              <span className="flex-1 text-left">{label}</span>
              {active && <ChevronRight className="w-3 h-3 opacity-60" />}
            </button>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-dark-600">
        <div className="text-xs text-slate-500 leading-relaxed">
          <div className="font-medium text-slate-400 mb-1">Sénégal · 50 tours</div>
          <div>8 000 000 enregistrements</div>
          <div>RF F1 Score: <span className="text-brand-green font-semibold">97.85%</span></div>
        </div>
      </div>
    </aside>
  )
}
