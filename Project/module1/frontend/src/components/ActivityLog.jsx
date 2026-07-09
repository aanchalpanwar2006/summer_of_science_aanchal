import { useEffect, useRef } from 'react'

const STATUS_LABELS = {
  idle: 'Waiting for a URL',
  scanning: 'Scanning page',
  awaiting_review: 'Awaiting your review',
  submitting: 'Submitting form',
  done: 'Done',
  error: 'Error',
  rejected: 'Rejected',
}

function timestamp() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export default function ActivityLog({ steps, status }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [steps])

  return (
    <div className="activity-log">
      <div className="log-header">
        <span className={`status-dot ${status}`} />
        <span>{STATUS_LABELS[status] || status}</span>
      </div>

      {steps.length === 0 ? (
        <p className="log-empty">Scan and fill progress will appear here in real time.</p>
      ) : (
        <ul className="log-list">
          {steps.map((step, i) => (
            <li key={i} className="log-item">
              <span className="log-time">{timestamp()}</span>
              <span className="log-text">{step}</span>
            </li>
          ))}
        </ul>
      )}
      <div ref={bottomRef} />
    </div>
  )
}
