import { useEffect, useState } from 'react'

const EMPTY = { name: '', email: '', phone: '', address: '', resume_text: '' }

export default function ProfilePage() {
  const [form, setForm] = useState(EMPTY)
  const [saving, setSaving] = useState(false)
  const [feedback, setFeedback] = useState('')

  useEffect(() => {
    fetch('/api/user/profile')
      .then((r) => r.json())
      .then((data) => setForm({ ...EMPTY, ...data }))
      .catch(() => {})
  }, [])

  function handleChange(e) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }))
    setFeedback('')
  }

  function handleSave(e) {
    e.preventDefault()
    setSaving(true)
    setFeedback('')

    const payload = Object.fromEntries(
      Object.entries(form).filter(([, v]) => v !== '')
    )

    fetch('/api/user/profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then((r) => r.json())
      .then((data) => {
        setForm({ ...EMPTY, ...data })
        setFeedback('Profile saved.')
      })
      .catch(() => setFeedback('Failed to save profile.'))
      .finally(() => setSaving(false))
  }

  return (
    <div className="profile-page">
      <h2>User Profile</h2>
      <form className="profile-form" onSubmit={handleSave}>
        {[
          { name: 'name', label: 'Name', type: 'input' },
          { name: 'email', label: 'Email', type: 'input' },
          { name: 'phone', label: 'Phone', type: 'input' },
          { name: 'address', label: 'Address', type: 'input' },
          { name: 'resume_text', label: 'Resume Text', type: 'textarea' },
        ].map(({ name, label, type }) => (
          <div className="field-group" key={name}>
            <label htmlFor={name}>{label}</label>
            {type === 'textarea' ? (
              <textarea
                id={name}
                name={name}
                value={form[name]}
                onChange={handleChange}
                placeholder={`Enter ${label.toLowerCase()}…`}
              />
            ) : (
              <input
                id={name}
                name={name}
                type="text"
                value={form[name]}
                onChange={handleChange}
                placeholder={`Enter ${label.toLowerCase()}…`}
              />
            )}
          </div>
        ))}
        <button className="save-btn" type="submit" disabled={saving}>
          {saving ? 'Saving…' : 'Save Profile'}
        </button>
        {feedback && <p className="save-feedback">{feedback}</p>}
      </form>
    </div>
  )
}
