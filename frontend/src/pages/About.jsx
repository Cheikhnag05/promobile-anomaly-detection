import { ExternalLink, Database, Cpu, Globe, Code2, Link } from 'lucide-react'
import PageHeader from '../components/PageHeader'

const STACK = [
  { cat: 'Data', items: ['Python 3.13', 'pandas', 'numpy', 'pyarrow', 'Parquet'] },
  { cat: 'Machine Learning', items: ['scikit-learn', 'Random Forest', 'Isolation Forest', 'joblib', 'SHAP'] },
  { cat: 'Backend', items: ['FastAPI', 'uvicorn', 'Pydantic', 'CORS', 'REST API'] },
  { cat: 'Frontend', items: ['React 18', 'Vite', 'Tailwind CSS', 'Recharts', 'Leaflet'] },
  { cat: 'Déploiement', items: ['GitHub', 'Render (API)', 'Vercel (Frontend)', 'pytest (56 tests)'] },
]

const METRICS = [
  { val: '8 000 000', label: 'Enregistrements KPI', icon: Database, color: 'text-brand-blue' },
  { val: '97.85%', label: 'F1 Score Random Forest', icon: Cpu, color: 'text-brand-green' },
  { val: '50', label: 'Tours au Sénégal', icon: Globe, color: 'text-brand-amber' },
  { val: '56/56', label: 'Tests passés', icon: Code2, color: 'text-brand-orange' },
]

export default function About() {
  return (
    <div>
      <PageHeader title="À propos" subtitle="Projet & Auteur" />
      <div className="p-6 space-y-6 max-w-4xl">

        {/* Hero */}
        <div className="card border-brand-blue/30 bg-gradient-to-br from-brand-blue/10 to-dark-800">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-xl bg-brand-blue/20 border border-brand-blue/40 flex items-center justify-center text-2xl flex-shrink-0">
              📡
            </div>
            <div>
              <h2 className="text-white font-bold text-lg mb-1">Promobile — Network Anomaly Detection</h2>
              <p className="text-slate-300 text-sm leading-relaxed">
                Système end-to-end de détection d'anomalies réseau télécom, inspiré d'une expérience réelle
                chez <strong className="text-brand-blue">Promobile, Dakar, Sénégal</strong>. Traite 8 millions
                d'enregistrements KPI de 50 tours et prédit les anomalies en temps réel avec un modèle
                Random Forest atteignant 97.85% de F1 Score.
              </p>
              <div className="flex gap-3 mt-3">
                <a href="https://github.com/Cheikhnag05/promobile-anomaly-detection" target="_blank"
                  className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors">
                  <Link className="w-3.5 h-3.5" /> Code source
                </a>
                <a href="https://promobile-api.onrender.com/docs" target="_blank"
                  className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors">
                  <ExternalLink className="w-3.5 h-3.5" /> API Docs
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {METRICS.map(({ val, label, icon: Icon, color }) => (
            <div key={label} className="card text-center">
              <Icon className={`w-5 h-5 mx-auto mb-2 ${color}`} />
              <p className={`text-2xl font-bold ${color}`}>{val}</p>
              <p className="text-slate-500 text-xs mt-1">{label}</p>
            </div>
          ))}
        </div>

        {/* Stack */}
        <div className="card">
          <h3 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Stack technique</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {STACK.map(({ cat, items }) => (
              <div key={cat}>
                <p className="text-brand-blue text-xs font-semibold uppercase tracking-wider mb-2">{cat}</p>
                <div className="flex flex-wrap gap-1.5">
                  {items.map(item => (
                    <span key={item} className="px-2 py-1 bg-dark-700 border border-dark-500 text-slate-300 text-xs rounded-md">
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Author */}
        <div className="card border-brand-green/30 bg-brand-green/5">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-full bg-gradient-to-br from-brand-blue to-brand-green flex items-center justify-center text-white font-bold text-xl flex-shrink-0">
              CG
            </div>
            <div className="flex-1">
              <p className="text-white font-bold text-base">Cheikhna Dieng Gueye</p>
              <p className="text-slate-400 text-sm">Data Analyst & ML Engineer · Dakar, Sénégal</p>
              <div className="flex gap-3 mt-2">
                <a href="https://linkedin.com/in/cheikhnagueye" target="_blank"
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-[#0A66C2]/20 hover:bg-[#0A66C2]/40 border border-[#0A66C2]/40 text-[#64B5F6] text-xs rounded-lg transition-colors">
                  <ExternalLink className="w-3.5 h-3.5" /> LinkedIn
                </a>
                <a href="https://github.com/Cheikhnag05" target="_blank"
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-dark-700 hover:bg-dark-600 border border-dark-500 text-slate-300 text-xs rounded-lg transition-colors">
                  <Link className="w-3.5 h-3.5" /> GitHub
                </a>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}
