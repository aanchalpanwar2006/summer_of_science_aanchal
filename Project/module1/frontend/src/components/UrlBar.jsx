import { useState } from 'react'

export default function UrlBar({ onSubmit, disabled }) {
  const [url, setUrl] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    const trimmed = url.trim()
    if (!trimmed) return
    onSubmit(trimmed)
  }

  return (
    <form className="command-bar" onSubmit={handleSubmit}>
      <input
        className="command-input"
        type="text"
        placeholder="e.g. https://demoqa.com/automation-practice-form"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        disabled={disabled}
        autoFocus
      />
      <button className="submit-btn" type="submit" disabled={disabled || !url.trim()}>
        {disabled ? 'Scanning…' : 'Scan'}
      </button>
    </form>
  )
}
