import { useEffect, useState } from 'react'
import ComposeForm from './components/ComposeForm.jsx'
import DraftReview from './components/DraftReview.jsx'
import InboxList from './components/InboxList.jsx'
import ThreadReplyPanel from './components/ThreadReplyPanel.jsx'

const IN_FLIGHT_STATUSES = ['drafting', 'sending']

export default function App() {
  const [tab, setTab] = useState('compose')
  const [draftId, setDraftId] = useState(null)
  const [draftState, setDraftState] = useState(null)
  const [replyThreadId, setReplyThreadId] = useState(null)

  useEffect(() => {
    if (!draftId) return undefined
    let cancelled = false
    let timeoutId

    function poll() {
      fetch(`/api/drafts/${draftId}`)
        .then((r) => r.json())
        .then((data) => {
          if (cancelled) return
          setDraftState(data)
          if (IN_FLIGHT_STATUSES.includes(data.status)) {
            timeoutId = setTimeout(poll, 800)
          }
        })
        .catch(() => {
          if (!cancelled) timeoutId = setTimeout(poll, 800)
        })
    }

    timeoutId = setTimeout(poll, 300)
    return () => {
      cancelled = true
      clearTimeout(timeoutId)
    }
  }, [draftId])

  function startCompose(to, intent) {
    setDraftState(null)
    fetch('/api/drafts/compose', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ to, intent }),
    })
      .then((r) => r.json())
      .then(({ draft_id }) => setDraftId(draft_id))
  }

  function startReply(threadId, intent) {
    setDraftState(null)
    fetch('/api/drafts/reply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ thread_id: threadId, intent }),
    })
      .then((r) => r.json())
      .then(({ draft_id }) => setDraftId(draft_id))
  }

  function handleSend({ to, subject, body }) {
    return fetch(`/api/drafts/${draftId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ to, subject, body }),
    })
      .then((r) => r.json())
      .then(() => fetch(`/api/drafts/${draftId}/send`, { method: 'POST' }))
      .then((r) => r.json())
      .then(setDraftState)
  }

  function resetDraft() {
    setDraftId(null)
    setDraftState(null)
    setReplyThreadId(null)
  }

  function switchTab(nextTab) {
    setTab(nextTab)
    resetDraft()
  }

  const draftInProgress = draftState && IN_FLIGHT_STATUSES.includes(draftState.status)
  const showReview = draftState !== null

  return (
    <div className="app">
      <header className="header">
        <h1>Email Assistant</h1>
        <nav className="tabs">
          <button className={tab === 'compose' ? 'tab active' : 'tab'} onClick={() => switchTab('compose')}>
            Compose
          </button>
          <button className={tab === 'inbox' ? 'tab active' : 'tab'} onClick={() => switchTab('inbox')}>
            Inbox
          </button>
        </nav>
      </header>

      <main className="main">
        {tab === 'compose' && (
          <>
            {!showReview && <ComposeForm onSubmit={startCompose} disabled={false} />}
            {showReview && (
              <DraftReview draftState={draftState} onSend={handleSend} onStartOver={resetDraft} />
            )}
          </>
        )}

        {tab === 'inbox' && (
          <>
            {!replyThreadId && !showReview && <InboxList onReply={setReplyThreadId} />}
            {replyThreadId && !showReview && (
              <ThreadReplyPanel
                threadId={replyThreadId}
                onBack={() => setReplyThreadId(null)}
                onDraftReply={startReply}
                disabled={draftInProgress}
              />
            )}
            {showReview && (
              <DraftReview draftState={draftState} onSend={handleSend} onStartOver={resetDraft} />
            )}
          </>
        )}
      </main>
    </div>
  )
}
