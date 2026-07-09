import { useEffect, useState } from 'react'

export default function ThreadReplyPanel({ threadId, onBack, onDraftReply, disabled }) {
  const [messages, setMessages] = useState(null)
  const [error, setError] = useState('')
  const [intent, setIntent] = useState('')

  useEffect(() => {
    setMessages(null)
    fetch(`/api/inbox/thread/${threadId}`)
      .then((r) => r.json())
      .then((data) => setMessages(data.messages))
      .catch((err) => setError(`Failed to load thread: ${err.message}`))
  }, [threadId])

  function handleSubmit(e) {
    e.preventDefault()
    if (!intent.trim()) return
    onDraftReply(threadId, intent.trim())
  }

  return (
    <div className="thread-reply-panel">
      <button className="add-field-btn" onClick={onBack}>
        ← Back to inbox
      </button>

      {error && <p className="save-feedback error-feedback">{error}</p>}
      {messages === null && !error && <p className="log-empty">Loading thread…</p>}

      {messages && (
        <div className="thread-context">
          {messages.map((m, i) => (
            <div key={i} className="thread-message">
              <div className="thread-message-header">
                <span>{m.sender}</span>
                <span className="log-time">{m.date}</span>
              </div>
              <p className="thread-message-body">{m.body}</p>
            </div>
          ))}
        </div>
      )}

      <form className="compose-form" onSubmit={handleSubmit}>
        <div className="field-group">
          <label htmlFor="reply-intent">What should the reply say?</label>
          <input
            id="reply-intent"
            type="text"
            value={intent}
            onChange={(e) => setIntent(e.target.value)}
            placeholder='e.g. "tell them I will get back by Friday"'
            disabled={disabled}
          />
        </div>
        <button className="submit-btn" type="submit" disabled={disabled || !intent.trim()}>
          {disabled ? 'Drafting…' : 'Draft Reply'}
        </button>
      </form>
    </div>
  )
}
