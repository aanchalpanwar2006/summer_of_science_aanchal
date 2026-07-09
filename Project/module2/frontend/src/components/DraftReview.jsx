import { useEffect, useState } from 'react'

const STATUS_LABELS = {
  drafting: 'Drafting…',
  awaiting_review: 'Awaiting your review',
  sending: 'Sending…',
  sent: 'Sent',
  error: 'Error',
}

export default function DraftReview({ draftState, onSend, onStartOver }) {
  const [to, setTo] = useState(draftState.to)
  const [subject, setSubject] = useState(draftState.subject)
  const [body, setBody] = useState(draftState.body)
  const [sending, setSending] = useState(false)

  useEffect(() => {
    setTo(draftState.to)
    setSubject(draftState.subject)
    setBody(draftState.body)
  }, [draftState.draft_id])

  const editable = draftState.status === 'awaiting_review'
  const isDrafting = draftState.status === 'drafting'

  async function handleSend() {
    setSending(true)
    try {
      await onSend({ to, subject, body })
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="draft-review">
      <div className="log-header">
        <span className={`status-dot ${draftState.status}`} />
        <span>{STATUS_LABELS[draftState.status] || draftState.status}</span>
      </div>

      {isDrafting ? (
        <p className="log-empty">The LLM is drafting your email…</p>
      ) : (
        <>
          <div className="field-group">
            <label htmlFor="draft-to">To</label>
            <input
              id="draft-to"
              value={to}
              onChange={(e) => setTo(e.target.value)}
              disabled={!editable}
            />
          </div>
          <div className="field-group">
            <label htmlFor="draft-subject">Subject</label>
            <input
              id="draft-subject"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              disabled={!editable}
            />
          </div>
          <div className="field-group">
            <label htmlFor="draft-body">Body</label>
            <textarea
              id="draft-body"
              rows={10}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              disabled={!editable}
            />
          </div>

          {editable && (
            <div className="review-actions">
              <button className="approve-btn" disabled={sending} onClick={handleSend}>
                {sending ? 'Sending…' : 'Send'}
              </button>
            </div>
          )}

          {draftState.status === 'sent' && (
            <p className="save-feedback">Sent successfully.</p>
          )}
          {draftState.status === 'error' && draftState.error && (
            <p className="save-feedback error-feedback">{draftState.error}</p>
          )}
          {(draftState.status === 'sent' || draftState.status === 'error') && (
            <button className="add-field-btn" onClick={onStartOver}>
              Start a new draft
            </button>
          )}
        </>
      )}
    </div>
  )
}
