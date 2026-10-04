import { useEffect, useRef, useState } from 'react'
import './ChatWidget.css'

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
}

const GREETING: Message = {
  id: 0,
  role: 'assistant',
  content:
    "Hi! I'm the Campus Customs shopping assistant. Ask me about our Yale gear — " +
    'styles, prices, or what sizes are in stock.',
}

/**
 * Floating shop assistant.
 *
 * Placeholder for now: it echoes a holding reply instead of calling the agent.
 * Problem 5 replaces `sendMessage` with a POST to the backend agent endpoint;
 * the surrounding state, history and accessibility behaviour stay as they are.
 */
export default function ChatWidget() {
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState('')
  const [messages, setMessages] = useState<Message[]>([GREETING])
  const [pending, setPending] = useState(false)

  const panelRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const launcherRef = useRef<HTMLButtonElement>(null)
  const logRef = useRef<HTMLDivElement>(null)

  // Move focus into the panel when it opens.
  useEffect(() => {
    if (open) inputRef.current?.focus()
  }, [open])

  // Keep the newest message in view.
  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight })
  }, [messages, pending])

  // Escape closes the panel and restores focus to the launcher.
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setOpen(false)
        launcherRef.current?.focus()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open])

  function sendMessage(e: React.FormEvent) {
    e.preventDefault()
    const text = draft.trim()
    if (!text || pending) return

    setMessages((m) => [...m, { id: Date.now(), role: 'user', content: text }])
    setDraft('')
    setPending(true)

    // TODO (Problem 5): POST to the agent endpoint and render the real reply
    // plus any matching products.
    window.setTimeout(() => {
      setMessages((m) => [
        ...m,
        {
          id: Date.now() + 1,
          role: 'assistant',
          content:
            "I'm not connected to the shop's catalogue yet — that arrives in the " +
            'next build. Once I am, I\'ll answer this from our live inventory.',
        },
      ])
      setPending(false)
    }, 600)
  }

  return (
    <>
      <button
        ref={launcherRef}
        className="chat-launcher"
        aria-expanded={open}
        aria-controls="chat-panel"
        onClick={() => setOpen((v) => !v)}
      >
        <span aria-hidden="true">{open ? '✕' : '💬'}</span>
        <span className="sr-only">
          {open ? 'Close shopping assistant' : 'Open shopping assistant'}
        </span>
      </button>

      <div
        id="chat-panel"
        ref={panelRef}
        className={open ? 'chat-panel open' : 'chat-panel'}
        role="dialog"
        aria-label="Campus Customs shopping assistant"
        aria-hidden={!open}
        inert={!open}
      >
        <div className="chat-header">
          <div>
            <strong>Shopping Assistant</strong>
            <span className="chat-status">Preview — not yet connected</span>
          </div>
          <button
            className="chat-close"
            onClick={() => {
              setOpen(false)
              launcherRef.current?.focus()
            }}
          >
            <span aria-hidden="true">✕</span>
            <span className="sr-only">Close shopping assistant</span>
          </button>
        </div>

        <div className="chat-log" ref={logRef} role="log" aria-live="polite">
          {messages.map((m) => (
            <div key={m.id} className={`bubble bubble-${m.role}`}>
              {m.content}
            </div>
          ))}
          {pending && (
            <div className="bubble bubble-assistant typing" aria-label="Assistant is typing">
              <span /><span /><span />
            </div>
          )}
        </div>

        <form className="chat-form" onSubmit={sendMessage}>
          <label htmlFor="chat-input" className="sr-only">
            Ask the shopping assistant a question
          </label>
          <input
            id="chat-input"
            ref={inputRef}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Ask about sizes, prices, or styles…"
            autoComplete="off"
            maxLength={500}
          />
          <button className="btn btn-primary" type="submit" disabled={!draft.trim() || pending}>
            Send
          </button>
        </form>
      </div>
    </>
  )
}
