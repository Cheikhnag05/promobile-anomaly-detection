import { useEffect, useState } from 'react'
import { Radio, Wifi } from 'lucide-react'
import { api } from '../api'

export default function ApiWakeup({ children }) {
  const [status, setStatus] = useState('checking') // checking | awake | sleeping | error

  useEffect(() => {
    const timer = setTimeout(() => {
      if (status === 'checking') setStatus('sleeping')
    }, 4000)

    api.health()
      .then(() => { clearTimeout(timer); setStatus('awake') })
      .catch(() => { clearTimeout(timer); setStatus('error') })

    return () => clearTimeout(timer)
  }, [])

  if (status === 'awake') return children

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-dark-900 gap-6 px-4">
      <div className="flex items-center gap-3 mb-2">
        <div className="w-12 h-12 rounded-xl bg-brand-blue/20 border border-brand-blue/40 flex items-center justify-center">
          <Radio className="w-6 h-6 text-brand-blue" />
        </div>
        <div>
          <div className="text-white font-bold text-lg">Promobile</div>
          <div className="text-slate-400 text-sm">Anomaly Detection</div>
        </div>
      </div>

      {(status === 'checking' || status === 'sleeping') && (
        <>
          <div className="w-10 h-10 border-2 border-brand-blue/30 border-t-brand-blue rounded-full animate-spin" />
          <div className="text-center max-w-sm">
            {status === 'sleeping' ? (
              <>
                <p className="text-white font-semibold mb-2">Réveil de l'API en cours…</p>
                <p className="text-slate-400 text-sm leading-relaxed">
                  L'API est hébergée sur le plan gratuit Render et se met en veille après 15 min d'inactivité.
                  <br /><span className="text-brand-amber font-medium">⏳ Environ 30 secondes</span> — merci de patienter.
                </p>
              </>
            ) : (
              <p className="text-slate-400 text-sm">Connexion à l'API…</p>
            )}
          </div>
          <div className="flex gap-1.5 mt-2">
            {[0,1,2].map(i => (
              <div key={i} className="w-2 h-2 rounded-full bg-brand-blue animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
            ))}
          </div>
        </>
      )}

      {status === 'error' && (
        <div className="text-center max-w-sm">
          <Wifi className="w-8 h-8 text-brand-red mx-auto mb-3" />
          <p className="text-white font-semibold mb-2">API inaccessible</p>
          <p className="text-slate-400 text-sm mb-4">Vérifiez que l'API Render est en ligne.</p>
          <button
            onClick={() => { setStatus('checking'); window.location.reload() }}
            className="px-4 py-2 bg-brand-blue hover:bg-brand-blue/80 text-white text-sm rounded-lg transition-colors"
          >
            Réessayer
          </button>
        </div>
      )}
    </div>
  )
}
