# Campus Customs — Usability Improvements (Problem 9)

Four improvements: two on the front end, two in the agent/backend. Each was
chosen from a gap hit while building and testing the shop, not picked off a
generic checklist.

**Where to see them in the running app**

| # | Improvement | Where to look |
|---|---|---|
| 1 | Sort and price filtering | `/products` — the filter bar |
| 2 | Conversation starters | Open the chat bubble before typing anything |
| 3 | Price-claim guardrail | `backend/agent.py`; fires on any invented price |
| 4 | Slim tool payloads | `backend/models.py` `ProductSummary`; 51% fewer tokens |

---

## Front-end 1 — Sort and price filtering on the catalogue

### What was added

The catalogue had a search box, category chips and an in-stock toggle, but
**no way to order results and no way to filter by price** — even though the
API had supported `min_price` and `max_price` since Problem 3. The filter bar
now has:

- **A sort control** with four orders: Name (A–Z), Price: low to high, Price:
  high to low, and Best stocked.
- **Three price bands** — Under $40, Under $60, Under $75 — chosen to line up
  with the shop's real price tiers ($32 tees, $58 crewnecks, $68 hoodies,
  $72 quarter-zips, $98 jackets) rather than round numbers that split a tier
  awkwardly.

Backend support was added in `db.list_products` (a `sort` argument) and
`GET /api/products` (a validated `sort` query parameter; an unknown value
returns 422 rather than silently falling back).

Every control writes to the URL, so `?sort=price_desc&max_price=40` is
shareable and survives a refresh or the back button.

Sorting breaks ties by name. Without that, the 28 products that all cost
**$58** could come back in a different order on each request, making the grid
appear to shuffle while paging.

### Why it helps

**For the shopper:** price is the first thing most people filter on, and this
catalogue has 102 items across seven price points. A parent buying for a
first-year and a student spending their own money are looking for opposite
ends of the same list. "Under $40" gets to the 25 tees in one click instead of
scrolling the whole grid.

**For the business:** "Best stocked" quietly surfaces deep inventory, which is
what the shop most wants to sell. Shareable filter URLs also mean a link to
"all jackets, cheapest first" can go in an email or a group chat.

---

## Front-end 2 — Conversation starters in the chat panel

### What was added

Opening the assistant used to show a greeting and an empty box. A shopper who
has never used a store chatbot has no idea whether it can check stock, compare
prices, or only take complaints. The panel now offers **three clickable
starter questions**, and they are **aware of the page you are on**:

- **Anywhere on the site:** "What hoodies do you have?", "Show me something
  under $40", "What fleece jackets are in stock?"
- **On a product page:** "What sizes is this in?", "What colours does this come
  in?", "How many are left?"

Clicking one sends it immediately. They disappear as soon as the conversation
has a real message, and never reappear — including for a returning shopper
whose history was restored, since that is not an empty conversation.

Each starter is phrased as a question that exercises a tool, so the first
exchange demonstrates a genuine capability rather than producing small talk.

### Why it helps

**For the shopper:** it answers "what is this thing for?" without a tutorial.
The product-page variants are the ones that matter most — "What sizes is this
in?" is the single most common question in a clothing shop, and on a product
page it resolves through page context with no typing at all.

**For the business:** the assistant is the differentiating feature of this
site, and an empty text box is the main reason such features go unused. Three
concrete examples turn a blank prompt into an obvious next action.

---

## Backend 1 — Price-claim guardrail on the agent's replies

### What was added

The system prompt tells the agent never to state a price it has not looked up.
That is an instruction, and instructions can be ignored. This **enforces** it
in code.

A PydanticAI `@agent.output_validator` inspects every reply before it is
returned. It extracts each dollar figure and compares it against the prices of
the products the tools actually retrieved during that turn. If a figure cannot
be accounted for, it raises `ModelRetry` with the real prices, and the model
rewrites its answer before the shopper ever sees it.

Sums and differences of retrieved prices are allowed, so legitimate arithmetic
("together that's $156") is not flagged. The check logic lives in
`unverified_prices()` at module level specifically so it can be tested
directly:

| Reply | Prices retrieved | Result |
|---|---|---|
| "The hoodie is **$68**." | $68 | passes |
| "The hoodie is **$45**." | $68 | **blocked** |
| "$68 and $88" | $68, $88 | passes |
| "Together that's $156" | $68, $88 | passes |
| "It's $50" | *nothing retrieved* | **blocked** |
| "We don't carry gym shorts." | none | passes |
| "$68 and also $39" | $68 | **blocked ($39)** |

All eight cases pass, including the ones that must *not* trigger — a guardrail
that blocks correct answers is worse than none.

### Why it helps

**For the shopper:** a wrong price is the single most damaging thing a shop
assistant can say. Someone who is told $45 and charged $68 has been
misinformed, and no apology fixes that.

**For the business:** a quoted price reads like an offer. This closes the gap
between "we told the model not to" and "the model cannot", which matters
because the model's behaviour can change with a provider or version update
while this check keeps holding. It also fails safe: when something is blocked
it is logged with both the invented and the real figures, so the problem is
visible rather than silent.

---

## Backend 2 — Slim tool payloads to cut tokens and latency

### What was added

Tools were handing the model the full `ProductCard` for every result —
including `search_tags` and `image_url`. Neither is any use to the model:
tags are a retrieval mechanism, and the page renders images itself from data
it already has.

Tools now return a compact `ProductSummary` (id, name, category, price,
colours, a trimmed description, in-stock flag). **The page is unaffected**:
full cards still travel to the frontend through `ShopContext.shown_products`,
so images, full descriptions and tags all still render.

Measured on one eight-result search:

| | Before | After |
|---|---:|---:|
| Tool payload | 1,469 tokens | **716 tokens** |
| | | **51% smaller** |

Where the savings came from: `search_tags` 350 tokens, `image_url` 128 tokens,
plus trimming long descriptions to their first sentence for the model's copy.

Verified after the change: the page still receives 8 full cards with
`image_url` and complete descriptions, per-size stock is unchanged, and live
replies still quote correct prices.

### Why it helps

**For the business:** every chat turn pays for its tool output twice — once
when the tool returns and again on each subsequent turn as conversation
history. Halving the largest payload halves that recurring cost, and this
matters more as conversations lengthen.

**For the shopper:** fewer tokens is less for the model to read, so replies
come back faster. It also reduces distraction: the model no longer wades
through ten SEO keywords per product to find the two facts it needs, which
makes it likelier to answer from the fields that actually matter.

---

## Verified in the running app

| Improvement | Evidence |
|---|---|
| Sort control | Four options present; "Price: high to low" put $98 jackets first |
| Price bands | "Under $40" → 25 products, all $32 |
| URL state | `?sort=price_desc&max_price=40` |
| Invalid sort | 422, not a silent fallback |
| Starters (general) | "What hoodies do you have?" / "Show me something under $40" / "What fleece jackets are in stock?" |
| Starters (product page) | "What sizes is this in?" / "What colours does this come in?" / "How many are left?" |
| Starter click | Sent "What sizes is this in?" → "The Morse ¼ Zip is $72 … L is sold out; only 2 remain in S and XXL." Starters then disappeared. |
| Price guardrail | 8/8 unit cases correct; no false positives in live replies |
| Token reduction | 1,469 → 716 tokens, page cards intact |
