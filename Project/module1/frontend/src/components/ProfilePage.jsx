import { useEffect, useState } from 'react'

export default function ProfilePage() {
  const [profile, setProfile] = useState({})
  const [newKey, setNewKey] = useState('')
  const [newValue, setNewValue] = useState('')
  const [saving, setSaving] = useState(false)
  const [feedback, setFeedback] = useState('')
  const [resumeFile, setResumeFile] = useState(null)
  const [uploadingResume, setUploadingResume] = useState(false)

  function loadProfile() {
    fetch('/api/user/profile')
      .then((r) => r.json())
      .then(setProfile)
      .catch(() => {})
  }

  useEffect(loadProfile, [])

  function handleChange(key, value) {
    setProfile((prev) => ({ ...prev, [key]: value }))
    setFeedback('')
  }

  function handleAddField(e) {
    e.preventDefault()
    const key = newKey.trim()
    if (!key) return
    setProfile((prev) => ({ ...prev, [key]: newValue }))
    setNewKey('')
    setNewValue('')
  }

  function handleSave(e) {
    e.preventDefault()
    setSaving(true)
    setFeedback('')

    const payload = Object.fromEntries(Object.entries(profile).filter(([, v]) => v !== ''))

    fetch('/api/user/profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then((r) => r.json())
      .then((data) => {
        setProfile(data)
        setFeedback('Profile saved.')
      })
      .catch(() => setFeedback('Failed to save profile.'))
      .finally(() => setSaving(false))
  }

  function handleUploadResume(e) {
    e.preventDefault()
    if (!resumeFile) return
    setUploadingResume(true)
    setFeedback('')

    const formData = new FormData()
    formData.append('file', resumeFile)

    fetch('/api/user/resume', { method: 'POST', body: formData })
      .then((r) => r.json())
      .then(() => {
        setFeedback('Resume uploaded.')
        setResumeFile(null)
        loadProfile()
      })
      .catch(() => setFeedback('Failed to upload resume.'))
      .finally(() => setUploadingResume(false))
  }

  const entries = Object.entries(profile).filter(([key]) => key !== 'resume_path')
  const resumePath = profile.resume_path || ''

  return (
    <div className="profile-page">
      <h2>User Profile</h2>
      <form className="profile-form" onSubmit={handleSave}>
        {entries.map(([key, value]) => (
          <div className="field-group" key={key}>
            <label htmlFor={key}>{key}</label>
            <input
              id={key}
              value={value}
              onChange={(e) => handleChange(key, e.target.value)}
              placeholder={`Enter ${key}…`}
            />
          </div>
        ))}

        <div className="add-field-row">
          <input
            type="text"
            placeholder="New field key (e.g. linkedin_url)"
            value={newKey}
            onChange={(e) => setNewKey(e.target.value)}
          />
          <input
            type="text"
            placeholder="Value"
            value={newValue}
            onChange={(e) => setNewValue(e.target.value)}
          />
          <button type="button" className="add-field-btn" onClick={handleAddField}>
            + Add field
          </button>
        </div>

        <button className="save-btn" type="submit" disabled={saving}>
          {saving ? 'Saving…' : 'Save Profile'}
        </button>
        {feedback && <p className="save-feedback">{feedback}</p>}
      </form>

      <h2 className="resume-heading">Resume</h2>
      <form className="resume-form" onSubmit={handleUploadResume}>
        {resumePath && <p className="current-resume">Current: {resumePath.split('/').pop()}</p>}
        <input type="file" accept=".pdf" onChange={(e) => setResumeFile(e.target.files[0] || null)} />
        <button className="save-btn" type="submit" disabled={!resumeFile || uploadingResume}>
          {uploadingResume ? 'Uploading…' : 'Upload Resume'}
        </button>
      </form>
    </div>
  )
}
