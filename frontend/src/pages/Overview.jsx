import { useEffect, useState } from 'react'
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { Activity, AlertTriangle, TrendingUp, Database, Cpu } from 'lucide-react'
import { api } from '../api'
import StatCard from '../components/StatCard'
import PageHeader from '../components/PageHeader'
import Loader from '../components/Loader'

const SEV_COLORS = {
  critical: '#E24B4A',
  high: '#E8593C',
  medium: '#EF9F27',
  low: '#1D9E75',
}

const TYPE_COLORS = ['#378ADD','#1D9E75','#EF9F27','#E24B4A','#9B59B6','#E8593C']

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-dark-700 border border-dark-500 rounded-lg px-3 py-2 text-xs shadow-xl">
      <p className="text-slate-300 font-medium mb-1">{label}</p>
      {payload.map(p => (
        <p key={p.name} style={{ color: p.fill || p.color }}>{p.name}: <span className="font-bold">{p.value?.toLocaleString()}</span></p>
      ))}
    </div>
  )
}

export default function Overview() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.stats()
      .then(setStats)
      .catch(() => setError('API hors ligne — lancez: uvicorn api.main:app --reload'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <><PageHeader title="Vue Générale" subtitle="Tableau de bord exécutif" /><Loader text="Chargement des statistiques..." /></>
  if (error) return (
    <><PageHeader title="Vue Générale" subtitle="Tableau de bord exécutif" />
    <div className="p-8">
      <div className="card border-brand-amber/40 bg-brand-amber/5 text-brand-amber text-sm flex items-center gap-3">
        <AlertTriangle className="w-5 h-5 flex-shrink-0" />
        {error}
      </div>
      <p className="text-slate-500 text-xs mt-4">Les données de démonstration s'afficheront quand l'API sera disponible.</p>
    </div></>
  )

  const sevData = Object.entries(stats.by_severity || {}).map(([k, v]) => ({ name: k, value: v }))
  const typeData = Object.entries(stats.by_type || {}).map(([k, v]) => ({ name: k.replace(/_/g, ' '), value: v }))
  const rf = stats.model_performance?.random_forest || {}

  return (
    <div>
      <PageHeader title="Vue Générale" subtitle="Tableau de bord exécutif · Réseau Sénégal 2024" />

      <div className="p-8 space-y-8">
        {/* KPI Cards */}
        <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
          <StatCard title="Enregistrements analysés" value={stats.total_records?.toLocaleString()} sub="Données KPI réseau" icon={Database} color="blue" />
          <StatCard title="Anomalies détectées" value={stats.total_anomalies?.toLocaleString()} sub={`Taux: ${stats.anomaly_rate_pct}%`} icon={AlertTriangle} color="amber" />
          <StatCard title="Alertes critiques" value={stats.by_severity?.critical?.toLocaleString()} sub={`${((stats.by_severity?.critical / stats.total_anomalies) * 100).toFixed(1)}% des anomalies`} icon={Activity} color="red" />
          <StatCard title="F1 Score RF" value={`${((rf.f1 || 0) * 100).toFixed(1)}%`} sub={`ROC-AUC: ${((rf.roc_auc || 0) * 100).toFixed(1)}%`} icon={Cpu} color="green" />
        </div>

        {/* Charts row 1 */}
        <div className="grid grid-cols-2 gap-6">
          {/* Severity bar */}
          <div className="card">
            <h3 className="text-sm font-semibold text-white mb-4">Répartition par sévérité</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={sevData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 10 }} axisLine={false} tickLine={false} tickFormatter={v => (v/1000).toFixed(0)+'k'} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]} name="Anomalies">
                  {sevData.map((entry, i) => (
                    <Cell key={i} fill={SEV_COLORS[entry.name] || '#378ADD'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Type pie */}
          <div className="card">
            <h3 className="text-sm font-semibold text-white mb-4">Types d'anomalies</h3>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={typeData} cx="50%" cy="50%" innerRadius={55} outerRadius={90} paddingAngle={3} dataKey="value">
                  {typeData.map((_, i) => <Cell key={i} fill={TYPE_COLORS[i % TYPE_COLORS.length]} />)}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend iconType="circle" iconSize={8} formatter={v => <span className="text-slate-400 text-xs">{v}</span>} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Model performance */}
        <div className="card">
          <h3 className="text-sm font-semibold text-white mb-4">Performance des modèles</h3>
          <div className="grid grid-cols-4 gap-4">
            {[
              { label: 'Précision RF', val: rf.precision, color: 'brand-green' },
              { label: 'Rappel RF', val: rf.recall, color: 'brand-blue' },
              { label: 'F1 Score RF', val: rf.f1, color: 'brand-amber' },
              { label: 'ROC-AUC RF', val: rf.roc_auc, color: 'brand-orange' },
            ].map(({ label, val, color }) => (
              <div key={label} className="bg-dark-700 rounded-lg p-4">
                <p className="text-slate-400 text-xs mb-2">{label}</p>
                <p className={`text-2xl font-bold text-${color}`}>{((val || 0) * 100).toFixed(1)}%</p>
                <div className="mt-2 h-1.5 bg-dark-600 rounded-full overflow-hidden">
                  <div className={`h-full bg-${color} rounded-full`} style={{ width: `${(val || 0) * 100}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
