import { useState } from 'react'
import Sidebar from './components/Sidebar'
import ApiWakeup from './components/ApiWakeup'
import Overview from './pages/Overview'
import LiveFeed from './pages/LiveFeed'
import TowerMap from './pages/TowerMap'
import Predict from './pages/Predict'
import ModelInsights from './pages/ModelInsights'
import About from './pages/About'

const PAGES = {
  overview: Overview,
  live: LiveFeed,
  map: TowerMap,
  predict: Predict,
  model: ModelInsights,
  about: About,
}

export default function App() {
  const [page, setPage] = useState('overview')
  const Page = PAGES[page]

  return (
    <ApiWakeup>
      <div className="flex h-screen bg-dark-900 overflow-hidden">
        <Sidebar current={page} onChange={setPage} />
        <main className="flex-1 overflow-y-auto">
          <div className="animate-fade-in">
            <Page />
          </div>
        </main>
      </div>
    </ApiWakeup>
  )
}
