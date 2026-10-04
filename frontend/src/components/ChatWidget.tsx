import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { ApiError, fetchChatHistory, formatPrice, sendChatMessage } from '../api'
import { useAuth } from '../auth'
import { useChatResults } from '../chatResults'
import type { Product } from '../types'
import './ChatWidget.css'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  products?: Product[]
  failed?: boolean
}

const GREETING: Message = {
  id: 'greeting',
  role: 'assistant',
  content:
    "Hi! I'm the Campus Customs shopping assistant. Ask me about our Yale gear — " +
    'styles, prices, or what sizes are in stock.',
}

let messageSeq = 0
const nextId = () => `m${++messageSeq}`

/**
 * Very small Markdown renderer for assistant replies.
 *
 * The agent is told to answer in Markdown, and only ever uses bold, bullets and
 * paragraphs. Rendering those four cases directly avoids pulling in a parser,
 * and because every segment is placed as a React text node rather than as HTML,
 * model output cannot inject markup into the page.
 */
function RichText({ text }: { text: string }) {
  const blocks = text.trim().split(/\n{2,}/)
  return (
    <>
      {blocks.map((block, bi) => {
        const lines = block.split('\n')
        const isList = lines.every((l) => /^\s*[-*]\s+/.test(l))
        if (isList) {
          return (
            <ul key={bi} className="bubble-list">
              {lines.map((l, li) => (
                <li key={li}>{inline(l.replace(/^\s*[-*]\s+/, ''))}</li>
              ))}
            </ul>
          )
        }
        return (
          <p key={bi} className="bubble-p">
            {lines.map((l, li) => (
              <span key={li}>
                {inline(l)}
                {li < lines.length - 1 && <br />}
              </span>
            ))}
          </p>
        )
      })}
    </>
  )
}

/** Split on **bold** and return React nodes — never HTML. */
function inline(text: string) {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith('**') && part.endsWith('**') && part.length > 4 ? (
      <strong key={i}>{part.slice(2, -2)}</strong>
    ) : (
      <span key={i}>{part}</span>
    ),
  )
}

function ProductStrip({ products }: { products: Product[] }) {
  return (
    <div className="chat-products" aria-label={`${products.length} matching products`}>
      {products.map((p) => (
        <Link key={p.product_id} to={`/products/${p.product_id}`} className="chat-product">
          <img src={p.image_url} alt="" loading="lazy" width={64} height={64} />
          <span className="chat-product-info">
            <span className="chat-product-name">{p.name}</span>
            <span className="chat-product-price">{formatPrice(p.price)}</span>
          </span>
        </Link>
      ))}
    </div>
  )
}

export default function ChatWidget() {
  const { user } = useAuth()
  const { publish } = useChatResults()
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState('')
  const [messages, setMessages] = useState<Message[]>([GREETING])
  const [pending, setPending] = useState(false)
  const [historyLoaded, setHistoryLoaded] = useState(false)

  const inputRef = useRef<HTMLInputElement>(null)
  const launcherRef = useRef<HTMLButtonElement>(null)
  const logRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (open) inputRef.current?.focus()
  }, [open])

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight })
  }, [messages, pending])

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

  // Signing out clears the on-screen conversation so the next shopper on this
  // browser does not see it.
  useEffect(() => {
    if (!user) {
      setMessages([GREETING])
      setHistoryLoaded(false)
    }
  }, [user])

  // Load stored history once, the first time a signed-in shopper opens the panel.
  useEffect(() => {
    if (!open || !user || historyLoaded) return
    const ctrl = new AbortController()
    fetchChatHistory(ctrl.signal)
      .then((rows) => {
        if (rows.length === 0) return
        setMessages([
          GREETING,
          ...rows.map((r) => ({
            id: `h${r.id}`,
            role: r.role,
            content: r.content,
            products: r.products,
          })),
        ])
      })
      .catch(() => {
        /* History is a nicety; a failure should not block chatting. */
      })
      .finally(() => {
        if (!ctrl.signal.aborted) setHistoryLoaded(true)
      })
    return () => ctrl.abort()
  }, [open, user, historyLoaded])

  const send = useCallback(
    async (text: string) => {
      setMessages((m) => [...m, { id: nextId(), role: 'user', content: text }])
      setPending(true)
      try {
        const res = await sendChatMessage(text)
        // Hand the matches to the page so they render as full product cards.
        publish(res.products, res.matched_for)
        setMessages((m) => [
          ...m,
          {
            id: nextId(),
            role: 'assistant',
            content: res.reply,
            products: res.products,
          },
        ])
      } catch (err) {
        setMessages((m) => [
          ...m,
          {
            id: nextId(),
            role: 'assistant',
            failed: true,
            content:
              err instanceof ApiError
                ? err.message
                : 'Something went wrong reaching the assistant.',
          },
        ])
      } finally {
        setPending(false)
      }
    },
    [publish],
  )

  function submit(e: React.FormEvent) {
    e.preventDefault()
    const text = draft.trim()
    if (!text || pending) return
    setDraft('')
    void send(text)
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
        className={open ? 'chat-panel open' : 'chat-panel'}
        role="dialog"
        aria-label="Campus Customs shopping assistant"
        aria-hidden={!open}
        inert={!open}
      >
        <div className="chat-header">
          <div>
            <strong>Shopping Assistant</strong>
            <span className="chat-status">
              {user ? `Signed in as ${user.first_name ?? user.name}` : 'Ask about our Yale gear'}
            </span>
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
            <div key={m.id} className="chat-turn">
              <div
                className={`bubble bubble-${m.role}${m.failed ? ' bubble-failed' : ''}`}
              >
                {m.role === 'assistant' ? <RichText text={m.content} /> : m.content}
              </div>
              {m.products && m.products.length > 0 && (
                <ProductStrip products={m.products} />
              )}
            </div>
          ))}
          {pending && (
            <div className="bubble bubble-assistant typing" aria-label="Assistant is typing">
              <span /><span /><span />
            </div>
          )}
        </div>

        <form className="chat-form" onSubmit={submit}>
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
            maxLength={2000}
            disabled={pending}
          />
          <button className="btn btn-primary" type="submit" disabled={!draft.trim() || pending}>
            Send
          </button>
        </form>
      </div>
    </>
  )
}
