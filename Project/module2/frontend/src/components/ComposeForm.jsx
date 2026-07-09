import { useState } from 'react'

export default function ComposeForm({ onSubmit, disabled }) {
  const [to, setTo] = useState('')
  const [intent, setIntent] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    if (!to.trim() || !intent.trim()) return
    onSubmit(to.trim(), intent.trim())
  }

  return (
    <form className="compose-form" onSubmit={handleSubmit}>
      <div className="field-group">
        <label htmlFor="to">To</label>
        <input
          id="to"
          type="email"
          value={to}
          onChange={(e) => setTo(e.target.value)}
          placeholder="recipient@example.com"
          disabled={disabled}
        />
      </div>
      <div className="field-group">
        <label htmlFor="intent">What should this email say?</label>
        <input
          id="intent"
          type="text"
          value={intent}
          onChange={(e) => setIntent(e.target.value)}
          placeholder='e.g. "ask my professor for a deadline extension"'
          disabled={disabled}
        />
      </div>
      <button className="submit-btn" type="submit" disabled={disabled || !to.trim() || !intent.trim()}>
        {disabled ? 'Drafting…' : 'Draft'}
      </button>
    </form>
  )
}
