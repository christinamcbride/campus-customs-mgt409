# Campus Customs — Design (Problem 10)

**The idea: the shop prints its own garments, so the site is printed too.**

Campus Customs has run screens on Broadway since 1973. Rather than dress the
site as a generic college store, the whole interface is built as press output —
ink on newsprint stock, halftone screens, registration marks, and type that
looks struck rather than set. Original throughout; inspired by the reference
site's navy-and-cream collegiate feel, not copied from it.

---

## What changed

### Fonts

- **Fraunces** (self-hosted variable) for display. Its `SOFT` and `WONK` axes
  are turned up, which rounds terminals like ink spread and swaps in irregular
  letterforms — it reads as struck metal type, not a web font.
- **Work Sans** for body and UI. Small labels run uppercase at wide tracking,
  the way a printed price list sets its column heads.
- Prices, stock counts and sizes use **tabular figures**, so they line up in
  columns instead of wobbling.

### Colour

Named as a press names its inks, not as a palette:

| Token | Use |
|---|---|
| Press navy `#10203a` | Everything is printed in it |
| Newsprint `#f6f1e6` | The stock the site is printed on |
| Brass `#a8812a` | The second plate — rules, marks, the accent word |
| `--brass-ink` `#7a5a14` | The same plate run heavier, for small text on light stock |

That last token exists because the display brass measured **3.5:1** on white —
below the readable floor at label size. Two inks for one colour, chosen by
surface.

A **paper-grain layer** sits over the entire page, so nothing renders on flat
white. Solid navy areas carry a **halftone dot screen**, because a screen-printed
solid is dots, not a flat fill.

### Visual hierarchy

- The hero is a poster: `We print it **here.**` at up to 7rem, the accent word
  in brass as a second plate. No label above the heading — the heading carries
  itself.
- Section heads sit on a 2px ink rule, like a price list separating columns.
- "Why shop with us" was three identical icon-and-text cards. It is now a
  **ruled press sheet** — a sticky heading beside hairline-separated rows.
  Type does the work; no card chrome.
- The shop's logo is a **printer's registration cross**, which rotates on hover.

### Motion

One authored moment, reused: **ink setting on the sheet**. Content arrives
blurred and lifted, then resolves sharp — the way a print dries. The hero
staggers it across four elements; the chat results band uses the same curve.
Everything shares one easing (`cubic-bezier(0.16, 1, 0.3, 1)`), so the site
settles rather than slides. Product cards lift off the stack on hover, and
their image creeps 3.5%. All of it is disabled under `prefers-reduced-motion`.

### Product presentation

- Each garment sits on a **fresh white sheet** against the cream page.
- Colours show as **ink swatches** — small chips of the actual colour, so
  "heather gray, white, red, black" is visible before you read it.
- Price is set in the display face, large, in tabular figures.
- Sold out is stamped **"OUT OF RUN"**, the printer's term.
- On the detail page, sold-out sizes are **struck through with a dashed
  border** — crossed off the run rather than merely greyed.

### The chat experience

The assistant is now **"The Counter"** — the order desk of a real shop.

- Its replies arrive as **tickets torn off a pad**: a perforated top edge made
  of scalloped notches, on fresh stock with a paper lift.
- Each ticket prints in with a `clip-path` wipe, top to bottom, like a receipt
  feeding out.
- What the shopper says is written in **ink** — a solid navy block.
- Retrieved products list as **line items** on the ticket.
- Starter prompts sit under "Ask the counter" as dashed-outline chips that
  become solid on hover, like options on a form.
- Copy follows: *"Afternoon — you're through to the counter at Campus Customs."*

### Craft details

- **Every emoji icon is gone.** `💬 ☰ ✕ →` are now drawn SVGs in one 24×24
  box at 1.6 stroke, including a registration cross and a squeegee.
- **Browser surfaces are themed**: text selection, caret, scrollbars, focus
  rings and underline offset all come from the palette rather than the browser.

---

## Why this should keep customers on the site and buying

**It looks like a shop that makes things.** Anyone can resell Yale merchandise;
Campus Customs prints it. A site built out of ink, halftones and registration
marks argues that in the first second, before a word is read. That is the
shop's actual competitive claim, made visually.

**Ink swatches answer the first question without a click.** "Does it come in
grey?" is the most common reason a shopper opens and abandons a product page.
Showing the colours on the card means fewer dead-end clicks and more time on
products that can actually be bought.

**Honest stock builds the trust that closes the sale.** "OUT OF RUN" and sizes
struck through tell shoppers the truth early. A shopper who learns their size
is gone *before* committing comes back; one who discovers it at checkout
usually does not.

**Tabular figures make the catalogue scannable.** Prices in aligned columns let
someone compare 24 products at a glance. Faster comparison means more products
seen per visit.

**"The Counter" makes the assistant feel staffed.** A chat labelled *Shopping
Assistant* reads as a bot to be dismissed. One labelled *The Counter*, printing
tickets, reads as asking someone who works there — and this assistant answers
from real inventory, which is worth getting people to use.

**Restraint where it earns money.** The expressive work is in the hero, the
chat and the texture. Filters, forms and the checkout path stay quiet and
conventional, because a shopper mid-purchase needs clarity, not personality.

---

## Verified

- Contrast: every text style meets 4.5:1 (large text 3:1). Three failures found
  by measuring computed values — brass labels at 3.5:1 and the lightest ink at
  2.65:1 — were fixed, not waived.
- The mechanical design detector reports **0 findings**. Four accent-bar
  "side tabs" it flagged were replaced with the perforated ticket edge, ruled
  headings, and a screened panel.
- Desktop (1280) and mobile (375) both inspected: no horizontal overflow,
  hamburger menu intact, chat panel usable.
- Functionality unchanged: sort and price filters, single-product page, auth,
  chat with product cards and starters, and the results band all still work.
  8/8 tool cases pass through the chat endpoint.
