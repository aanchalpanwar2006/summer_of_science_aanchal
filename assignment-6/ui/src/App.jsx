import { useState } from 'react'
import CommandBar from './components/CommandBar.jsx'
import ActivityLog from './components/ActivityLog.jsx'
import ProfilePage from './components/ProfilePage.jsx'

export default function App() {
  const [tab, setTab] = useState('command')
  const [steps, setSteps] = useState([])
  const [status, setStatus] = useState('idle') // idle | running | done | error

  function handleCommandSubmit(command) {
    setSteps([])
    setStatus('running')

    fetch('/api/command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command }),
    })
      .then((res) => res.json())
      .then(({ task_id }) => {
        const ws = new WebSocket(`ws://${window.location.host}/ws/${task_id}`)

        ws.onmessage = (e) => {
          if (e.data === '__DONE__') {
            setStatus('done')
            ws.close()
          } else if (e.data.startsWith('ERROR:')) {
            setStatus('error')
            setSteps((prev) => [...prev, e.data])
            ws.close()
          } else {
            setSteps((prev) => [...prev, e.data])
          }
        }

        ws.onerror = () => {
          setStatus('error')
          setSteps((prev) => [...prev, 'WebSocket connection failed.'])
        }
      })
      .catch((err) => {
        setStatus('error')
        setSteps([`Failed to submit command: ${err.message}`])
      })
  }

  return (
    <div className="app">
      <header className="header">
        <h1>SOC Browser Agent</h1>
        <nav className="tabs">
          <button
            className={tab === 'command' ? 'tab active' : 'tab'}
            onClick={() => setTab('command')}
          >
            Agent
          </button>
          <button
            className={tab === 'profile' ? 'tab active' : 'tab'}
            onClick={() => setTab('profile')}
          >
            Profile
          </button>
        </nav>
      </header>

      <main className="main">
        {tab === 'command' ? (
          <>
            <CommandBar onSubmit={handleCommandSubmit} disabled={status === 'running'} />
            <ActivityLog steps={steps} status={status} />
          </>
        ) : (
          <ProfilePage />
        )}
      </main>
    </div>
  )
}
