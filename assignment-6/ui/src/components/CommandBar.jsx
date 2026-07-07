import { useState } from 'react'

export default function CommandBar({ onSubmit, disabled }) {
  const [command, setCommand] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    const trimmed = command.trim()
    if (!trimmed) return
    onSubmit(trimmed)
    setCommand('')
  }

  return (
    <form className="command-bar" onSubmit={handleSubmit}>
      <input
        className="command-input"
        type="text"
        placeholder='e.g. "go to google.com and search for AI news"'
        value={command}
        onChange={(e) => setCommand(e.target.value)}
        disabled={disabled}
        autoFocus
      />
      <button className="submit-btn" type="submit" disabled={disabled || !command.trim()}>
        {disabled ? 'Running…' : 'Run'}
      </button>
    </form>
  )
}
