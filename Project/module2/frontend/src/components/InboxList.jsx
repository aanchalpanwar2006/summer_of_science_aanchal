import { useEffect, useState } from 'react'

export default function InboxList({ onReply }) {
  const [items, setItems] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    fetch('/api/inbox/unread')
      .then((r) => r.json())
      .then((data) => setItems(data.items))
      .catch((err) => setError(`Failed to load inbox: ${err.message}`))
  }, [])

  if (error) return <p className="save-feedback error-feedback">{error}</p>
  if (items === null) return <p className="log-empty">Loading unread messages…</p>
  if (items.length === 0) return <p className="log-empty">No unread messages.</p>

  return (
    <ul className="inbox-list">
      {items.map((item) => (
        <li key={item.message_id} className="inbox-item">
          <div className="inbox-item-main">
            <span className="inbox-sender">{item.sender}</span>
            <span className="inbox-subject">{item.subject}</span>
            <span className="inbox-summary">{item.summary}</span>
          </div>
          <button className="answer-btn" onClick={() => onReply(item.thread_id)}>
            Reply
          </button>
        </li>
      ))}
    </ul>
  )
}
