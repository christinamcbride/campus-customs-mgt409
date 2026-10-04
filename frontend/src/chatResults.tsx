import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import type { Product } from './types'

/**
 * The products the assistant most recently looked up.
 *
 * The chat panel publishes here; the page reads from here. Keeping this in one
 * place is what lets a conversation update the catalogue area of the page
 * without the chat widget knowing anything about page layout.
 */
interface ChatResultsState {
  products: Product[]
  /** The phrase that produced them, for labelling. */
  matchedFor: string | null
  publish: (products: Product[], matchedFor: string | null) => void
  clear: () => void
}

const ChatResultsContext = createContext<ChatResultsState | null>(null)

export function ChatResultsProvider({ children }: { children: React.ReactNode }) {
  const [products, setProducts] = useState<Product[]>([])
  const [matchedFor, setMatchedFor] = useState<string | null>(null)

  const publish = useCallback((next: Product[], label: string | null) => {
    // An answer that retrieved nothing leaves the previous results alone
    // rather than blanking the page mid-conversation.
    if (next.length === 0) return
    setProducts(next)
    setMatchedFor(label)
  }, [])

  const clear = useCallback(() => {
    setProducts([])
    setMatchedFor(null)
  }, [])

  const value = useMemo(
    () => ({ products, matchedFor, publish, clear }),
    [products, matchedFor, publish, clear],
  )

  return (
    <ChatResultsContext.Provider value={value}>{children}</ChatResultsContext.Provider>
  )
}

export function useChatResults(): ChatResultsState {
  const ctx = useContext(ChatResultsContext)
  if (!ctx) throw new Error('useChatResults must be used inside <ChatResultsProvider>')
  return ctx
}
