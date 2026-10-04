import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'

/**
 * The shopping bag.
 *
 * Held in the browser and persisted to localStorage, so it survives a reload
 * without needing an account. Quantities are capped against the stock the
 * product page actually read from the database, and the bag page re-checks
 * stock on load — the shop should never let someone bag more than exists.
 *
 * There is no checkout: the application does not take payment, and the bag
 * says so rather than implying an order can be placed.
 */

export interface BagLine {
  product_id: string
  name: string
  size: string
  price: number
  image_url: string
  quantity: number
}

interface BagState {
  lines: BagLine[]
  /** Total number of garments, for the nav badge. */
  count: number
  subtotal: number
  add: (line: Omit<BagLine, 'quantity'>, quantity?: number, maxQuantity?: number) => void
  setQuantity: (productId: string, size: string, quantity: number) => void
  remove: (productId: string, size: string) => void
  clear: () => void
}

const STORAGE_KEY = 'campus-customs-bag'
const BagContext = createContext<BagState | null>(null)

function load(): BagLine[] {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed: unknown = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    // Only keep entries that still have the shape we expect; a stale or
    // hand-edited value should not crash the shop.
    return parsed.filter(
      (l): l is BagLine =>
        typeof l === 'object' &&
        l !== null &&
        typeof (l as BagLine).product_id === 'string' &&
        typeof (l as BagLine).size === 'string' &&
        typeof (l as BagLine).price === 'number' &&
        Number.isFinite((l as BagLine).quantity) &&
        (l as BagLine).quantity > 0,
    )
  } catch {
    return []
  }
}

export function BagProvider({ children }: { children: React.ReactNode }) {
  const [lines, setLines] = useState<BagLine[]>(load)

  useEffect(() => {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(lines))
    } catch {
      /* Private browsing or a full quota: the bag just won't persist. */
    }
  }, [lines])

  const add = useCallback<BagState['add']>((line, quantity = 1, maxQuantity) => {
    setLines((current) => {
      const i = current.findIndex(
        (l) => l.product_id === line.product_id && l.size === line.size,
      )
      if (i === -1) {
        const capped = maxQuantity ? Math.min(quantity, maxQuantity) : quantity
        return [...current, { ...line, quantity: Math.max(1, capped) }]
      }
      const next = [...current]
      const wanted = next[i].quantity + quantity
      next[i] = {
        ...next[i],
        quantity: maxQuantity ? Math.min(wanted, maxQuantity) : wanted,
      }
      return next
    })
  }, [])

  const setQuantity = useCallback<BagState['setQuantity']>(
    (productId, size, quantity) => {
      setLines((current) =>
        quantity <= 0
          ? current.filter((l) => !(l.product_id === productId && l.size === size))
          : current.map((l) =>
              l.product_id === productId && l.size === size ? { ...l, quantity } : l,
            ),
      )
    },
    [],
  )

  const remove = useCallback<BagState['remove']>((productId, size) => {
    setLines((current) =>
      current.filter((l) => !(l.product_id === productId && l.size === size)),
    )
  }, [])

  const clear = useCallback(() => setLines([]), [])

  const value = useMemo<BagState>(() => {
    const count = lines.reduce((n, l) => n + l.quantity, 0)
    const subtotal = lines.reduce((n, l) => n + l.quantity * l.price, 0)
    return { lines, count, subtotal, add, setQuantity, remove, clear }
  }, [lines, add, setQuantity, remove, clear])

  return <BagContext.Provider value={value}>{children}</BagContext.Provider>
}

export function useBag(): BagState {
  const ctx = useContext(BagContext)
  if (!ctx) throw new Error('useBag must be used inside <BagProvider>')
  return ctx
}
