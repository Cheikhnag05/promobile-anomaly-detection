import { useEffect, useState, useCallback } from 'react'
import { RefreshCw, Filter, AlertTriangle } from 'lucide-react'
import { api } from '../api'
import PageHeader from '../components/PageHeader'
import SeverityBadge from '../components/SeverityBadge'
import Loader from '../components/Loader'

const SEV_ROW = {
  critical: 'bg-brand-red/8 border-l-2 border-brand-red',
  high: 'bg-brand-orange/8 border-l-2 border-brand-orange',
  medium: 'bg-brand-amber/8 border-l-2 border-brand-amber',
  low: 'bg-brand-green/8 border-l-2 border-brand-green',
  none: '',
}

const SEVERITIES = ['critical', 'high', 'medium', 'low']
const TYPES = ['latency_spike', 'packet_loss_burst', 'signal_degradation', 'call_drop_surge', 'throughput_collapse', 'interference_event']

export default function LiveFeed() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [filters, setFilters] = useState({ severity: 'critical', limit: 100 })

  const load = useCallback(async (isRefresh = false) => {
    isRefresh ? setRefreshing(true) : setLoading(true)
    try {
      const params = { limit: filters.limit }
      if (filters.severity) params.severity = filters.severity
      const res = await api.anomalies(params)
      setData(res)
    } catch {
      setData(null)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [filters])

  useEffect(() => { load() }, [load])

  const results = data?.results || []
  const critCount = results.filter(r => r.severity === 'critical').length
  const highCount = results.filter(r => r.severity === 'high').length
  const avgProb = results.length ? (results.reduce((s, r) => s + (r.rf_prob || 0), 0) / results.length).toFixed(3) : '–'

  return (
    <div>
      <PageHeader title="Flux en Direct" subtitle="Anomalies détectées en temps réel">
        <button
          onClick={() => load(true)}
          disabled={refreshing}
          className="flex items-center gap-2 px-3 py-1.5 text-xs bg-dark-700 hover:bg-dark-600 border border-dark-500 text-slate-300 rounded-lg transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          Actualiser
        </button>
      </PageHeader>

      <div className="p-6 space-y-5">
        {/* Filters */}
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <span className="text-slate-400 text-xs font-medium">Filtres:</span>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-slate-500 text-xs">Sévérité</label>
            <select
              value={filters.severity}
              onChange={e => setFilters(f => ({ ...f, severity: e.target.value }))}
              className="bg-dark-700 border border-dark-500 text-slate-300 text-xs rounded-lg px-2 py-1.5 focus:outline-none focus:border-brand-blue"
            >
              <option value="">Toutes</option>
              {SEVERITIES.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-slate-500 text-xs">Limite</label>
            <select
              value={filters.limit}
              onChange={e => setFilters(f => ({ ...f, limit: +e.target.value }))}
              className="bg-dark-700 border border-dark-500 text-slate-300 text-xs rounded-lg px-2 py-1.5 focus:outline-none focus:border-brand-blue"
            >
              {[50, 100, 200, 500].map(n => <option key={n} value={n}>{n}</option>)}
            </select>
          </div>
        </div>

        {/* Summary pills */}
        {data && (
          <div className="flex items-center gap-3 flex-wrap">
            <span className="text-slate-400 text-xs">Total: <strong className="text-white">{data.total?.toLocaleString()}</strong></span>
            <span className="w-px h-4 bg-dark-500" />
            <span className="text-xs text-brand-red">⬤ Critiques: <strong>{critCount}</strong></span>
            <span className="text-xs text-brand-orange">⬤ Élevées: <strong>{highCount}</strong></span>
            <span className="text-xs text-slate-400">Prob. moy: <strong className="text-white">{avgProb}</strong></span>
          </div>
        )}

        {loading ? <Loader text="Chargement du flux..." /> : !results.length ? (
          <div className="card text-center text-slate-500 py-12">
            <AlertTriangle className="w-8 h-8 mx-auto mb-2 opacity-40" />
            Aucune anomalie trouvée pour ces filtres.
          </div>
        ) : (
          <div className="card p-0 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-dark-600 bg-dark-700">
                    {['Timestamp', 'Tour', 'Type', 'Sévérité', 'Prob. RF', 'Score IF'].map(h => (
                      <th key={h} className="px-4 py-3 text-left text-slate-400 font-medium uppercase tracking-wider text-[10px]">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {results.map((row, i) => (
                    <tr key={i} className={`border-b border-dark-600/50 hover:bg-dark-700/50 transition-colors ${SEV_ROW[row.severity] || ''}`}>
                      <td className="px-4 py-2.5 text-slate-400 font-mono whitespace-nowrap">{row.timestamp?.replace('T', ' ').slice(0, 19)}</td>
                      <td className="px-4 py-2.5 text-brand-blue font-semibold">{row.tower_id}</td>
                      <td className="px-4 py-2.5 text-slate-300">{row.anomaly_type?.replace(/_/g, ' ')}</td>
                      <td className="px-4 py-2.5"><SeverityBadge severity={row.severity} /></td>
                      <td className="px-4 py-2.5">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 bg-dark-600 rounded-full overflow-hidden">
                            <div className="h-full bg-brand-blue rounded-full" style={{ width: `${(row.rf_prob || 0) * 100}%` }} />
                          </div>
                          <span className="text-slate-300 font-mono">{row.rf_prob?.toFixed(3)}</span>
                        </div>
                      </td>
                      <td className="px-4 py-2.5 text-slate-400 font-mono">{row.if_score?.toFixed(4)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
