import { useState } from 'react'
import { Send, Zap, AlertTriangle, CheckCircle, TrendingUp } from 'lucide-react'
import { api } from '../api'
import PageHeader from '../components/PageHeader'
import SeverityBadge from '../components/SeverityBadge'

const DEFAULT_INPUT = {
  tower_id: 'TW-001',
  latency_ms: 25.0,
  packet_loss_pct: 0.5,
  signal_strength_dbm: -70.0,
  call_drop_rate: 0.02,
  throughput_mbps: 80.0,
  active_users: 200,
  interference_ratio: 0.1,
  availability_pct: 99.5,
  hour: 12,
  is_peak: 1,
}

const ANOMALY_PRESETS = {
  'Pic de latence critique': { ...DEFAULT_INPUT, latency_ms: 2800, packet_loss_pct: 15, call_drop_rate: 0.45, is_peak: 1 },
  'Dégradation signal': { ...DEFAULT_INPUT, signal_strength_dbm: -115, interference_ratio: 0.85, availability_pct: 91 },
  'Effondrement débit': { ...DEFAULT_INPUT, throughput_mbps: 3, active_users: 4800, interference_ratio: 0.7 },
  'Réseau sain': { ...DEFAULT_INPUT },
}

const FIELDS = [
  { key: 'tower_id', label: 'ID Tour', type: 'text', unit: '' },
  { key: 'latency_ms', label: 'Latence', type: 'number', unit: 'ms', min: 0, max: 5000, step: 1 },
  { key: 'packet_loss_pct', label: 'Perte paquets', type: 'number', unit: '%', min: 0, max: 100, step: 0.1 },
  { key: 'signal_strength_dbm', label: 'Force signal', type: 'number', unit: 'dBm', min: -130, max: -20, step: 1 },
  { key: 'call_drop_rate', label: 'Taux coupures', type: 'number', unit: '', min: 0, max: 1, step: 0.01 },
  { key: 'throughput_mbps', label: 'Débit', type: 'number', unit: 'Mbps', min: 0, max: 1000, step: 1 },
  { key: 'active_users', label: 'Utilisateurs actifs', type: 'number', unit: '', min: 0, max: 10000, step: 1 },
  { key: 'interference_ratio', label: 'Ratio interférence', type: 'number', unit: '', min: 0, max: 1, step: 0.01 },
  { key: 'availability_pct', label: 'Disponibilité', type: 'number', unit: '%', min: 0, max: 100, step: 0.1 },
  { key: 'hour', label: 'Heure', type: 'number', unit: 'h', min: 0, max: 23, step: 1 },
  { key: 'is_peak', label: 'Heure de pointe', type: 'number', unit: '', min: 0, max: 1, step: 1 },
]

function ProbGauge({ prob }) {
  const pct = (prob * 100).toFixed(1)
  const color = prob >= 0.85 ? '#E24B4A' : prob >= 0.6 ? '#E8593C' : prob >= 0.3 ? '#EF9F27' : '#1D9E75'
  const angle = prob * 180

  return (
    <div className="flex flex-col items-center gap-2">
      <svg viewBox="0 0 120 70" className="w-48">
        {/* Track */}
        <path d="M 10 60 A 50 50 0 0 1 110 60" fill="none" stroke="#1C3357" strokeWidth="10" strokeLinecap="round" />
        {/* Fill */}
        <path
          d="M 10 60 A 50 50 0 0 1 110 60"
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={`${prob * 157} 157`}
        />
        {/* Needle */}
        <line
          x1="60" y1="60"
          x2={60 + 38 * Math.cos((Math.PI - (angle * Math.PI / 180)))}
          y2={60 - 38 * Math.sin((Math.PI - (angle * Math.PI / 180)))}
          stroke={color} strokeWidth="2.5" strokeLinecap="round"
        />
        <circle cx="60" cy="60" r="4" fill={color} />
        <text x="60" y="50" textAnchor="middle" fill={color} fontSize="14" fontWeight="bold">{pct}%</text>
      </svg>
      <p className="text-slate-400 text-xs">Probabilité d'anomalie</p>
    </div>
  )
}

export default function Predict() {
  const [form, setForm] = useState(DEFAULT_INPUT)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const payload = { ...form, latency_ms: +form.latency_ms, packet_loss_pct: +form.packet_loss_pct, signal_strength_dbm: +form.signal_strength_dbm, call_drop_rate: +form.call_drop_rate, throughput_mbps: +form.throughput_mbps, active_users: +form.active_users, interference_ratio: +form.interference_ratio, availability_pct: +form.availability_pct, hour: +form.hour, is_peak: +form.is_peak }
      const res = await api.predict(payload)
      setResult(res)
    } catch {
      setError('API hors ligne. Lancez: uvicorn api.main:app --reload')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <PageHeader title="Prédiction Live" subtitle="Soumettez des KPIs réseau pour détecter les anomalies en temps réel" />

      <div className="p-6 grid grid-cols-5 gap-6">
        {/* Form */}
        <div className="col-span-3 space-y-4">
          {/* Presets */}
          <div className="card">
            <p className="text-xs text-slate-400 font-medium uppercase tracking-wider mb-3">Scénarios prédéfinis</p>
            <div className="flex gap-2 flex-wrap">
              {Object.entries(ANOMALY_PRESETS).map(([label, vals]) => (
                <button key={label} onClick={() => setForm(vals)}
                  className="px-3 py-1.5 text-xs bg-dark-700 hover:bg-brand-blue/20 border border-dark-500 hover:border-brand-blue/50 text-slate-300 hover:text-brand-blue rounded-lg transition-all">
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Inputs */}
          <form onSubmit={handleSubmit} className="card space-y-4">
            <div className="grid grid-cols-2 gap-3">
              {FIELDS.map(({ key, label, type, unit, min, max, step }) => (
                <div key={key}>
                  <label className="text-xs text-slate-400 block mb-1">{label} {unit && <span className="text-slate-600">({unit})</span>}</label>
                  <input
                    type={type}
                    value={form[key]}
                    min={min} max={max} step={step}
                    onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                    className="w-full bg-dark-700 border border-dark-500 focus:border-brand-blue text-slate-200 text-sm rounded-lg px-3 py-2 outline-none transition-colors"
                  />
                </div>
              ))}
            </div>

            {error && <p className="text-brand-amber text-xs flex items-center gap-2"><AlertTriangle className="w-4 h-4" />{error}</p>}

            <button type="submit" disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-2.5 bg-brand-blue hover:bg-brand-blue/80 disabled:opacity-50 text-white text-sm font-semibold rounded-lg transition-colors">
              <Send className="w-4 h-4" />
              {loading ? 'Analyse en cours...' : 'Analyser les KPIs'}
            </button>
          </form>
        </div>

        {/* Result panel */}
        <div className="col-span-2 space-y-4">
          {result ? (
            <>
              <div className="card text-center">
                <ProbGauge prob={result.anomaly_probability} />
                <div className="mt-3 flex items-center justify-center gap-3">
                  {result.is_anomaly
                    ? <AlertTriangle className="w-5 h-5 text-brand-red" />
                    : <CheckCircle className="w-5 h-5 text-brand-green" />}
                  <span className={`text-lg font-bold ${result.is_anomaly ? 'text-brand-red' : 'text-brand-green'}`}>
                    {result.is_anomaly ? 'ANOMALIE DÉTECTÉE' : 'RÉSEAU NORMAL'}
                  </span>
                </div>
                <div className="mt-3"><SeverityBadge severity={result.severity} /></div>
              </div>

              <div className="card space-y-3">
                <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Détails</h4>
                {[
                  { label: 'Tour analysée', val: result.tower_id },
                  { label: 'KPI dominant', val: result.dominant_kpi?.replace(/_/g, ' ') },
                  { label: 'Score Isolation Forest', val: result.isolation_forest_score?.toFixed(4) },
                  { label: 'Horodatage', val: result.predicted_at?.slice(0, 19) },
                ].map(({ label, val }) => (
                  <div key={label} className="flex items-start justify-between gap-2">
                    <span className="text-slate-500 text-xs">{label}</span>
                    <span className="text-slate-200 text-xs font-medium text-right max-w-[55%]">{val}</span>
                  </div>
                ))}
              </div>

              {result.recommendation && (
                <div className="card border-brand-blue/30 bg-brand-blue/5">
                  <div className="flex items-start gap-2">
                    <TrendingUp className="w-4 h-4 text-brand-blue flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-brand-blue text-xs font-semibold mb-1">Recommandation</p>
                      <p className="text-slate-300 text-xs leading-relaxed">{result.recommendation}</p>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="card flex flex-col items-center justify-center h-64 text-center gap-3">
              <Zap className="w-10 h-10 text-dark-500" />
              <p className="text-slate-500 text-sm">Soumettez des KPIs pour obtenir<br />une prédiction en temps réel</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
