import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell, Legend } from 'recharts'
import { Brain, Target, TrendingUp, BarChart2 } from 'lucide-react'
import PageHeader from '../components/PageHeader'

const RF_METRICS = { precision: 0.9951, recall: 0.9623, f1: 0.9785, roc_auc: 0.9906 }
const IF_METRICS = { precision: 1.0, recall: 0.0182, f1: 0.0358 }

const RADAR_DATA = [
  { metric: 'Précision', rf: RF_METRICS.precision, if: IF_METRICS.precision },
  { metric: 'Rappel', rf: RF_METRICS.recall, if: IF_METRICS.recall },
  { metric: 'F1 Score', rf: RF_METRICS.f1, if: IF_METRICS.f1 },
]

const FEATURE_IMPORTANCE = [
  { feature: 'rf_anomaly_prob', importance: 0.3241 },
  { feature: 'latency_ms_zscore', importance: 0.1823 },
  { feature: 'packet_loss_pct_zscore', importance: 0.1456 },
  { feature: 'call_drop_rate_zscore', importance: 0.1123 },
  { feature: 'interference_ratio_zscore', importance: 0.0934 },
  { feature: 'signal_strength_dbm_zscore', importance: 0.0712 },
  { feature: 'throughput_mbps_zscore', importance: 0.0534 },
  { feature: 'latency_ms_roll_mean_12', importance: 0.0421 },
  { feature: 'packet_loss_pct_roll_std_12', importance: 0.0387 },
  { feature: 'network_health_score', importance: 0.0312 },
  { feature: 'latency_ms_delta', importance: 0.0287 },
  { feature: 'call_drop_rate_delta', importance: 0.0234 },
].slice(0, 10)

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-dark-700 border border-dark-500 rounded-lg px-3 py-2 text-xs shadow-xl">
      <p className="text-slate-300 font-medium mb-1">{label}</p>
      {payload.map(p => (
        <p key={p.name} style={{ color: p.color }}>{p.name}: <strong>{typeof p.value === 'number' ? (p.value * 100).toFixed(1) + '%' : p.value}</strong></p>
      ))}
    </div>
  )
}

export default function ModelInsights() {
  return (
    <div>
      <PageHeader title="Modèle IA" subtitle="Performance et analyse des modèles de détection d'anomalies" />

      <div className="p-6 space-y-6">
        {/* Metrics cards */}
        <div className="grid grid-cols-4 gap-4">
          {[
            { label: 'Précision RF', val: RF_METRICS.precision, icon: Target, color: 'brand-green', desc: 'Peu de faux positifs' },
            { label: 'Rappel RF', val: RF_METRICS.recall, icon: TrendingUp, color: 'brand-blue', desc: 'Anomalies capturées' },
            { label: 'F1 Score RF', val: RF_METRICS.f1, icon: BarChart2, color: 'brand-amber', desc: 'Équilibre précision/rappel' },
            { label: 'ROC-AUC RF', val: RF_METRICS.roc_auc, icon: Brain, color: 'brand-orange', desc: 'Pouvoir discriminant' },
          ].map(({ label, val, icon: Icon, color, desc }) => (
            <div key={label} className="card">
              <div className="flex items-center gap-2 mb-3">
                <Icon className={`w-4 h-4 text-${color}`} />
                <span className="text-slate-400 text-xs font-medium">{label}</span>
              </div>
              <p className={`text-3xl font-bold text-${color} mb-1`}>{(val * 100).toFixed(1)}%</p>
              <p className="text-slate-600 text-xs">{desc}</p>
              <div className="mt-3 h-1.5 bg-dark-600 rounded-full overflow-hidden">
                <div className={`h-full bg-${color} rounded-full transition-all`} style={{ width: `${val * 100}%` }} />
              </div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-6">
          {/* Radar */}
          <div className="card">
            <h3 className="text-sm font-semibold text-white mb-4">Comparaison RF vs Isolation Forest</h3>
            <ResponsiveContainer width="100%" height={280}>
              <RadarChart data={RADAR_DATA}>
                <PolarGrid stroke="#1C3357" />
                <PolarAngleAxis dataKey="metric" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <PolarRadiusAxis angle={30} domain={[0, 1]} tick={{ fill: '#64748b', fontSize: 9 }} />
                <Radar name="Random Forest" dataKey="rf" stroke="#378ADD" fill="#378ADD" fillOpacity={0.35} />
                <Radar name="Isolation Forest" dataKey="if" stroke="#EF9F27" fill="#EF9F27" fillOpacity={0.2} />
                <Legend iconType="circle" iconSize={8} formatter={v => <span className="text-slate-400 text-xs">{v}</span>} />
                <Tooltip content={<CustomTooltip />} />
              </RadarChart>
            </ResponsiveContainer>
            <div className="mt-2 p-3 bg-dark-700 rounded-lg text-xs text-slate-400">
              <strong className="text-brand-blue">Random Forest</strong> domine grâce à la supervision. L'<strong className="text-brand-amber">Isolation Forest</strong> (non supervisé) a un rappel très faible mais une précision parfaite.
            </div>
          </div>

          {/* Feature importance */}
          <div className="card">
            <h3 className="text-sm font-semibold text-white mb-4">Importance des features (Top 10)</h3>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={FEATURE_IMPORTANCE} layout="vertical" margin={{ left: 10, right: 20 }}>
                <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 9 }} axisLine={false} tickLine={false} tickFormatter={v => (v * 100).toFixed(0) + '%'} />
                <YAxis type="category" dataKey="feature" tick={{ fill: '#94a3b8', fontSize: 9 }} width={130} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="importance" radius={[0, 4, 4, 0]} name="Importance">
                  {FEATURE_IMPORTANCE.map((_, i) => (
                    <Cell key={i} fill={`rgba(55, 138, 221, ${1 - i * 0.07})`} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Model cards */}
        <div className="grid grid-cols-2 gap-6">
          {[
            {
              name: 'Random Forest',
              icon: '🌲',
              color: 'border-brand-blue/30 bg-brand-blue/5',
              badge: 'text-brand-blue bg-brand-blue/10',
              status: 'Production',
              metrics: [
                ['Arbres', '200'],
                ['Précision', '99.51%'],
                ['Rappel', '96.23%'],
                ['F1 Score', '97.85%'],
                ['ROC-AUC', '99.06%'],
                ['Balancement classes', 'balanced'],
              ],
              note: 'Modèle supervisé principal. Utilise 45 features ingénierées dont rolling stats, z-scores et features cycliques.',
            },
            {
              name: 'Isolation Forest',
              icon: '🔍',
              color: 'border-brand-amber/30 bg-brand-amber/5',
              badge: 'text-brand-amber bg-brand-amber/10',
              status: 'Baseline',
              metrics: [
                ['Arbres', '200'],
                ['Précision', '100%'],
                ['Rappel', '1.82%'],
                ['F1 Score', '3.58%'],
                ['Contamination', '1.5%'],
                ['Supervision', 'Non supervisé'],
              ],
              note: 'Modèle de référence non supervisé. Précision parfaite mais rappel très faible — ne capture que les anomalies extrêmes.',
            },
          ].map(({ name, icon, color, badge, status, metrics, note }) => (
            <div key={name} className={`card border ${color}`}>
              <div className="flex items-center gap-3 mb-4">
                <span className="text-2xl">{icon}</span>
                <div>
                  <h4 className="text-white font-semibold">{name}</h4>
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${badge}`}>{status}</span>
                </div>
              </div>
              <div className="space-y-2 mb-3">
                {metrics.map(([k, v]) => (
                  <div key={k} className="flex justify-between text-xs">
                    <span className="text-slate-500">{k}</span>
                    <span className="text-slate-200 font-medium">{v}</span>
                  </div>
                ))}
              </div>
              <p className="text-slate-500 text-xs leading-relaxed border-t border-dark-600 pt-3">{note}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
