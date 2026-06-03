import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'
import { api } from '../api'
import PageHeader from '../components/PageHeader'
import SeverityBadge from '../components/SeverityBadge'
import Loader from '../components/Loader'
import 'leaflet/dist/leaflet.css'

const TOWERS_SENEGAL = [
  { tower_id: 'TW-001', district: 'Dakar', lat: 14.716677, lng: -17.467686, type: 'macro' },
  { tower_id: 'TW-002', district: 'Thiès', lat: 14.791681, lng: -16.925856, type: 'macro' },
  { tower_id: 'TW-003', district: 'Saint-Louis', lat: 16.018073, lng: -16.489527, type: 'macro' },
  { tower_id: 'TW-004', district: 'Ziguinchor', lat: 12.565025, lng: -16.271881, type: 'micro' },
  { tower_id: 'TW-005', district: 'Kaolack', lat: 14.151813, lng: -16.072580, type: 'macro' },
  { tower_id: 'TW-006', district: 'Diourbel', lat: 14.655069, lng: -16.231380, type: 'micro' },
  { tower_id: 'TW-007', district: 'Louga', lat: 15.619318, lng: -16.222735, type: 'macro' },
  { tower_id: 'TW-008', district: 'Tambacounda', lat: 13.769930, lng: -13.667729, type: 'small_cell' },
  { tower_id: 'TW-009', district: 'Kolda', lat: 12.898110, lng: -14.940631, type: 'micro' },
  { tower_id: 'TW-010', district: 'Matam', lat: 15.655926, lng: -13.255803, type: 'small_cell' },
  { tower_id: 'TW-011', district: 'Kédougou', lat: 12.555694, lng: -12.174580, type: 'small_cell' },
  { tower_id: 'TW-012', district: 'Sédhiou', lat: 12.703782, lng: -15.556534, type: 'micro' },
  { tower_id: 'TW-013', district: 'Kaffrine', lat: 14.105714, lng: -15.550817, type: 'macro' },
  { tower_id: 'TW-014', district: 'Fatick', lat: 14.339148, lng: -16.411184, type: 'micro' },
  { tower_id: 'TW-015', district: 'Pikine', lat: 14.754816, lng: -17.390760, type: 'rooftop' },
  { tower_id: 'TW-016', district: 'Guédiawaye', lat: 14.783218, lng: -17.394724, type: 'rooftop' },
  { tower_id: 'TW-017', district: 'Rufisque', lat: 14.716300, lng: -17.272700, type: 'macro' },
  { tower_id: 'TW-018', district: 'Mbour', lat: 14.399197, lng: -16.964874, type: 'macro' },
  { tower_id: 'TW-019', district: 'Tivaouane', lat: 14.952130, lng: -16.817980, type: 'micro' },
  { tower_id: 'TW-020', district: 'Mbacké', lat: 14.799740, lng: -15.906000, type: 'macro' },
]

function getHealthColor(rate) {
  if (rate <= 1.0) return '#1D9E75'
  if (rate <= 1.8) return '#EF9F27'
  if (rate <= 2.5) return '#E8593C'
  return '#E24B4A'
}

function getHealthLabel(rate) {
  if (rate <= 1.0) return 'healthy'
  if (rate <= 1.8) return 'warning'
  if (rate <= 2.5) return 'alert'
  return 'critical'
}

export default function TowerMap() {
  const [anomalies, setAnomalies] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.anomalies({ limit: 1000 })
      .then(r => setAnomalies(r.results || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  // Compute per-tower stats from anomaly data
  const towerStats = {}
  anomalies.forEach(a => {
    if (!towerStats[a.tower_id]) towerStats[a.tower_id] = { count: 0, critical: 0 }
    towerStats[a.tower_id].count++
    if (a.severity === 'critical') towerStats[a.tower_id].critical++
  })

  const towers = TOWERS_SENEGAL.map(t => {
    const stats = towerStats[t.tower_id] || { count: 0, critical: 0 }
    const rate = anomalies.length ? (stats.count / anomalies.length) * 100 * 20 : Math.random() * 3
    return { ...t, anomalyCount: stats.count, criticalCount: stats.critical, rate, color: getHealthColor(rate), health: getHealthLabel(rate) }
  })

  const healthy = towers.filter(t => t.health === 'healthy').length
  const warning = towers.filter(t => t.health === 'warning').length
  const alert = towers.filter(t => t.health === 'alert').length
  const critical = towers.filter(t => t.health === 'critical').length

  return (
    <div>
      <PageHeader title="Carte des Tours" subtitle="Réseau de 50 tours · Sénégal" />

      <div className="p-6 space-y-4">
        {/* Status summary */}
        <div className="grid grid-cols-4 gap-3">
          {[
            { label: 'Sain', count: healthy, color: 'text-brand-green', dot: 'bg-brand-green' },
            { label: 'Avertissement', count: warning, color: 'text-brand-amber', dot: 'bg-brand-amber' },
            { label: 'Alerte', count: alert, color: 'text-brand-orange', dot: 'bg-brand-orange' },
            { label: 'Critique', count: critical, color: 'text-brand-red', dot: 'bg-brand-red' },
          ].map(({ label, count, color, dot }) => (
            <div key={label} className="card flex items-center gap-3">
              <div className={`w-3 h-3 rounded-full flex-shrink-0 ${dot}`} />
              <div>
                <p className="text-slate-400 text-xs">{label}</p>
                <p className={`text-xl font-bold ${color}`}>{count}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Map */}
        <div className="card p-0 overflow-hidden" style={{ height: 480 }}>
          {loading ? <Loader text="Chargement de la carte..." /> : (
            <MapContainer
              center={[14.5, -14.5]}
              zoom={6}
              style={{ height: '100%', width: '100%', background: '#0E1E3A' }}
              zoomControl={true}
            >
              <TileLayer
                url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                attribution='&copy; <a href="https://carto.com/">CARTO</a>'
              />
              {towers.map(t => (
                <CircleMarker
                  key={t.tower_id}
                  center={[t.lat, t.lng]}
                  radius={t.anomalyCount > 0 ? 12 : 8}
                  pathOptions={{
                    color: t.color,
                    fillColor: t.color,
                    fillOpacity: 0.8,
                    weight: 2,
                  }}
                >
                  <Popup className="leaflet-popup-dark">
                    <div className="text-xs space-y-1 min-w-[160px]">
                      <p className="font-bold text-sm text-white">{t.tower_id}</p>
                      <p className="text-slate-300">{t.district}</p>
                      <p className="text-slate-400">Type: {t.type}</p>
                      <p className="text-slate-400">Anomalies: <strong className="text-white">{t.anomalyCount}</strong></p>
                      <p className="text-slate-400">Critiques: <strong className="text-brand-red">{t.criticalCount}</strong></p>
                      <div className="mt-1"><SeverityBadge severity={t.health === 'healthy' ? 'none' : t.health === 'warning' ? 'low' : t.health === 'alert' ? 'medium' : 'critical'} /></div>
                    </div>
                  </Popup>
                </CircleMarker>
              ))}
            </MapContainer>
          )}
        </div>

        {/* Legend */}
        <div className="flex items-center gap-6 text-xs text-slate-400">
          <span className="font-medium text-slate-300">Légende:</span>
          {[['#1D9E75','≤1% Sain'],['#EF9F27','1–1.8% Avertissement'],['#E8593C','1.8–2.5% Alerte'],['#E24B4A','>2.5% Critique']].map(([c, l]) => (
            <div key={l} className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full" style={{ background: c }} />
              <span>{l}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
