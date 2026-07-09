import { useEffect, useState } from 'react'

const SOURCE_LABELS = {
  profile: 'From profile',
  answered: 'Answered',
  missing: 'Missing',
}

function fileName(path) {
  if (!path) return ''
  return path.split('/').pop()
}

export default function FormPreview({ runState, onAnswer, onReview }) {
  const [values, setValues] = useState({})
  const [savingField, setSavingField] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    const initial = {}
    for (const field of runState.fields) {
      initial[field.field_id] = field.proposed_value
    }
    setValues(initial)
  }, [runState.run_id])

  const editable = runState.status === 'awaiting_review'

  function setValue(fieldId, value) {
    setValues((prev) => ({ ...prev, [fieldId]: value }))
  }

  async function handleSaveAnswer(field) {
    setSavingField(field.field_id)
    try {
      await onAnswer(field.field_id, values[field.field_id] || '')
    } finally {
      setSavingField(null)
    }
  }

  async function handleReview(action) {
    setSubmitting(true)
    try {
      const fields = runState.fields.map((f) => ({ field_id: f.field_id, value: values[f.field_id] || '' }))
      await onReview(action, fields)
    } finally {
      setSubmitting(false)
    }
  }

  function renderValueEditor(field) {
    const value = values[field.field_id] ?? ''

    if (field.element_type === 'file') {
      return value ? (
        <span className="file-value">{fileName(value)}</span>
      ) : (
        <span className="file-missing">No resume on file — upload one in the Profile tab.</span>
      )
    }

    if (field.element_type === 'select') {
      return (
        <select value={value} onChange={(e) => setValue(field.field_id, e.target.value)} disabled={!editable}>
          <option value="">— choose —</option>
          {field.options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      )
    }

    if (field.element_type === 'radio') {
      return (
        <div className="radio-group">
          {field.options.map((opt) => (
            <label key={opt.value} className="radio-option">
              <input
                type="radio"
                name={field.field_id}
                value={opt.value}
                checked={value === opt.value}
                onChange={() => setValue(field.field_id, opt.value)}
                disabled={!editable}
              />
              {opt.label}
            </label>
          ))}
        </div>
      )
    }

    if (field.element_type === 'checkbox' && field.options.length > 0) {
      const selected = new Set(value ? value.split(',').filter(Boolean) : [])
      function toggle(optValue) {
        const next = new Set(selected)
        if (next.has(optValue)) next.delete(optValue)
        else next.add(optValue)
        setValue(field.field_id, Array.from(next).join(','))
      }
      return (
        <div className="checkbox-group">
          {field.options.map((opt) => (
            <label key={opt.value} className="checkbox-option">
              <input
                type="checkbox"
                checked={selected.has(opt.value)}
                onChange={() => toggle(opt.value)}
                disabled={!editable}
              />
              {opt.label}
            </label>
          ))}
        </div>
      )
    }

    if (field.element_type === 'checkbox') {
      return (
        <label className="checkbox-option">
          <input
            type="checkbox"
            checked={value === 'true'}
            onChange={(e) => setValue(field.field_id, e.target.checked ? 'true' : 'false')}
            disabled={!editable}
          />
          Yes
        </label>
      )
    }

    if (field.element_type === 'textarea') {
      return (
        <textarea
          value={value}
          onChange={(e) => setValue(field.field_id, e.target.value)}
          disabled={!editable}
        />
      )
    }

    return (
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(field.field_id, e.target.value)}
        disabled={!editable}
      />
    )
  }

  return (
    <div className="form-preview">
      <h2>Review before submitting</h2>
      {runState.fields.length === 0 ? (
        <p className="log-empty">No fillable fields were detected on this page.</p>
      ) : (
        <table className="field-table">
          <thead>
            <tr>
              <th>Field</th>
              <th>Value</th>
              <th>Status</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {runState.fields.map((field) => (
              <tr key={field.field_id} className={field.source === 'missing' ? 'row-missing' : ''}>
                <td>
                  {field.label}
                  {field.required && <span className="required-mark">*</span>}
                </td>
                <td>{renderValueEditor(field)}</td>
                <td>
                  <span className={`field-badge badge-${field.source}`}>{SOURCE_LABELS[field.source]}</span>
                </td>
                <td>
                  {field.source === 'missing' && field.element_type !== 'file' && editable && (
                    <button
                      className="answer-btn"
                      type="button"
                      disabled={savingField === field.field_id}
                      onClick={() => handleSaveAnswer(field)}
                    >
                      {savingField === field.field_id ? 'Saving…' : 'Save answer'}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {editable && (
        <div className="review-actions">
          <button className="approve-btn" disabled={submitting} onClick={() => handleReview('approve')}>
            {submitting ? 'Submitting…' : 'Approve & Submit'}
          </button>
          <button className="reject-btn" disabled={submitting} onClick={() => handleReview('reject')}>
            Reject
          </button>
        </div>
      )}

      {runState.status === 'error' && runState.error && <p className="save-feedback error-feedback">{runState.error}</p>}
    </div>
  )
}
