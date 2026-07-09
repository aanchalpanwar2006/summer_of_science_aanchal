import { useEffect, useRef, useState } from 'react'
import UrlBar from './components/UrlBar.jsx'
import ActivityLog from './components/ActivityLog.jsx'
import FormPreview from './components/FormPreview.jsx'
import ProfilePage from './components/ProfilePage.jsx'

const TERMINAL_STATUSES = ['done', 'error', 'rejected']

export default function App() {
  const [tab, setTab] = useState('form')
  const [runId, setRunId] = useState(null)
  const [runState, setRunState] = useState(null)
  const [steps, setSteps] = useState([])
  const wsRef = useRef(null)

  function handleUrlSubmit(url) {
    setSteps([])
    setRunState(null)

    fetch('/api/runs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    })
      .then((res) => res.json())
      .then(({ run_id }) => setRunId(run_id))
      .catch((err) => setSteps([`Failed to start scan: ${err.message}`]))
  }

  // WebSocket: live scan/fill progress
  useEffect(() => {
    if (!runId) return undefined

    const ws = new WebSocket(`ws://${window.location.host}/ws/runs/${runId}`)
    wsRef.current = ws

    ws.onmessage = (e) => {
      if (e.data === '__DONE__') {
        ws.close()
      } else {
        setSteps((prev) => [...prev, e.data])
      }
    }

    ws.onerror = () => {
      setSteps((prev) => [...prev, 'WebSocket connection failed.'])
    }

    return () => ws.close()
  }, [runId])

  // Poll run state until a terminal status is reached
  useEffect(() => {
    if (!runId) return undefined

    let cancelled = false

    function poll() {
      fetch(`/api/runs/${runId}`)
        .then((r) => r.json())
        .then((data) => {
          if (cancelled) return
          setRunState(data)
          if (!TERMINAL_STATUSES.includes(data.status)) {
            timeoutId = setTimeout(poll, 1200)
          }
        })
        .catch(() => {
          if (!cancelled) timeoutId = setTimeout(poll, 1200)
        })
    }

    let timeoutId = setTimeout(poll, 300)
    return () => {
      cancelled = true
      clearTimeout(timeoutId)
    }
  }, [runId])

  function handleAnswer(fieldId, value) {
    return fetch(`/api/runs/${runId}/answer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ field_id: fieldId, value }),
    })
      .then((r) => r.json())
      .then((updatedField) => {
        setRunState((prev) => ({
          ...prev,
          fields: prev.fields.map((f) => (f.field_id === updatedField.field_id ? updatedField : f)),
        }))
      })
  }

  function handleReview(action, fields) {
    return fetch(`/api/runs/${runId}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, fields }),
    })
      .then((r) => r.json())
      .then(setRunState)
  }

  const status = runState ? runState.status : runId ? 'scanning' : 'idle'
  const showPreview = runState && ['awaiting_review', 'submitting', 'done', 'error', 'rejected'].includes(runState.status)

  return (
    <div className="app">
      <header className="header">
        <h1>Intelligent Form Filler</h1>
        <nav className="tabs">
          <button className={tab === 'form' ? 'tab active' : 'tab'} onClick={() => setTab('form')}>
            Form Fill
          </button>
          <button className={tab === 'profile' ? 'tab active' : 'tab'} onClick={() => setTab('profile')}>
            Profile
          </button>
        </nav>
      </header>

      <main className="main">
        {tab === 'form' ? (
          <>
            <UrlBar onSubmit={handleUrlSubmit} disabled={status === 'scanning' || status === 'submitting'} />
            <ActivityLog steps={steps} status={status} />
            {showPreview && <FormPreview runState={runState} onAnswer={handleAnswer} onReview={handleReview} />}
          </>
        ) : (
          <ProfilePage />
        )}
      </main>
    </div>
  )
}
