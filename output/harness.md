# Campus Customs — Build Harness

Living specification for the Campus Customs shopping site. Started at Problem 2
(database analysis) and extended in later problems with models, tools, safety rules,
and specifications.

Source of truth: `data/campus_customs.db` (SQLite). This file is not committed to
GitHub; it ships with the assignment.

---

## 1. Database Overview

| Table | Rows | Purpose |
|---|---:|---|
| `catalogue` | 102 | One row per product — the shop's merchandise |
| `inventory` | 612 | Stock count per product per size (102 × 6) |
| `users` | 3 | Shopper accounts and password hashes |
| `chat_messages` | 22 | Saved chat history, including worked example answers |

No table is empty. There are **no indexes** beyond the automatic ones on the primary
keys and unique constraints, which is fine at 102 products but worth knowing if
queries ever get slower.

---

## 2. `catalogue` — the products

One row per product. This is the only authority on what the shop sells and what it
costs; the chatbot may never state a product or price that did not come from here.

| Field | Type | Constraints | Why it matters |
|---|---|---|---|
| `product_id` | TEXT | **PK** | Stable slug (e.g. `morse-1-4-zip`) used to join inventory, build image URLs, and let the chatbot refer to an exact item without ambiguity. |
| `name` | TEXT | NOT NULL | The human-readable title shown on cards and spoken by the chatbot. |
| `garment_type` | TEXT | NOT NULL | Free-text garment description that drives category filtering — but it is inconsistent, so it must be normalized (see §6.1). |
| `description` | TEXT | NOT NULL | Full sentence describing colour, cut and graphic; the chatbot's richest grounding text for "what does this look like" questions. |
| `colors` | TEXT | NOT NULL | JSON array of colour names; lets the shop filter by colour and lets the chatbot answer "do you have this in pink?" honestly. |
| `search_tags` | TEXT | NOT NULL | JSON array of 4–12 keywords (team, school, theme); the main hook for matching a shopper's natural phrasing to products. |
| `image_file_path` | TEXT | NOT NULL | Relative path like `products/<id>.jpg` pointing into `data/products/`; the backend turns this into a served image URL. |
| `price` | REAL | NOT NULL | Price in USD; must be read from here every time rather than remembered, so the chatbot never quotes a stale number. |

**Price tiers** (7 distinct values, no nulls, no zeroes):

| Price | Products | Typical garment |
|---:|---:|---|
| $32 | 25 | T-shirts |
| $45 | 5 | Performance long-sleeve / lighter sweatshirts |
| $58 | 28 | Crewneck sweatshirts |
| $68 | 23 | Hoodies |
| $72 | 11 | Quarter-zips |
| $88 | 2 | Full-zip hooded sweatshirts |
| $98 | 8 | Fleece and bomber jackets |

---

## 3. `inventory` — stock by size

Exactly 6 rows per product (XS, S, M, L, XL, XXL) for all 102 products. This is the
only authority on availability.

| Field | Type | Constraints | Why it matters |
|---|---|---|---|
| `id` | INTEGER | **PK**, autoincrement | Internal row identifier; not shown to shoppers. |
| `product_id` | TEXT | NOT NULL, FK → `catalogue` | Links stock to its product; every row resolves (no orphans). |
| `size` | TEXT | NOT NULL, UNIQUE with `product_id` | The size label; the unique pair guarantees one stock row per product-size, so a size question has exactly one answer. |
| `quantity` | INTEGER | NOT NULL | Units on hand; **0 means that size is sold out**, which the chatbot must say plainly instead of glossing over. |

**Stock shape — this is the heart of the honesty requirement:**

- Quantities run **0 to 25**, averaging 9.7. No negatives.
- **145 of 612 size rows are zero** (23.7%).
- **77 of 102 products have at least one sold-out size.**
- **No product is sold out entirely** — so "is this available?" is almost always
  "yes, in these sizes but not those." A yes/no answer is usually the wrong shape.
- 58 rows are low stock (1–3 units).

Worked example — Morse ¼ Zip: XS 15, S 2, M 8, **L 0 (sold out)**, XL 25, XXL 2.

---

## 4. `users` — accounts

| Field | Type | Constraints | Why it matters |
|---|---|---|---|
| `id` | INTEGER | **PK**, autoincrement | Identifies the shopper; ties chat history to an account. |
| `name` | TEXT | NOT NULL | Full display name; the chatbot greets the shopper by name when logged in. |
| `email` | TEXT | NOT NULL, **UNIQUE** | The login identifier; uniqueness is enforced by the database, so duplicate registration must be caught and reported as a clean error. |
| `password_hash` | TEXT | NOT NULL | Salted PBKDF2 hash — never a plaintext password, never returned by any endpoint. |
| `created_at` | TEXT | NOT NULL, default `datetime('now')` | Account creation timestamp as `YYYY-MM-DD HH:MM:SS` UTC; the default means inserts can omit it. |
| `first_name` | TEXT | nullable | Added after the original schema; used for a friendly first-name greeting. |
| `last_name` | TEXT | nullable | Added after the original schema; completes the display name. |

**Password hash format** — three `$`-separated segments:

```
pbkdf2_sha256$<salt>$<64-hex-char digest>
```

The digest is 64 hex characters, i.e. SHA-256. **The iteration count is not stored in
the hash**, unlike Django's 4-segment format. Verifying the seeded accounts therefore
depends on knowing the iteration count out of band; new accounts this app creates will
record it explicitly. Resolved when auth is built.

The three seeded accounts are Test User, Ada Lovelace, and Tauhid Zaman. The brief
mentioned one test user; there are three. `name` always equals
`first_name + ' ' + last_name`.

---

## 5. `chat_messages` — saved conversations

Not mentioned in the brief, but present and **already populated with 22 real messages**
(11 user, 11 assistant) across two accounts. These are effectively worked examples of
the expected chatbot behaviour.

| Field | Type | Constraints | Why it matters |
|---|---|---|---|
| `id` | INTEGER | **PK**, autoincrement | Orders messages within a conversation. |
| `user_id` | INTEGER | NOT NULL, FK → `users` | Scopes history to one account, so a shopper only ever sees their own chat. |
| `role` | TEXT | NOT NULL | Either `user` or `assistant`; drives both message styling and replay into the model. |
| `content` | TEXT | NOT NULL | The message text, Markdown-formatted for assistant turns. |
| `products_json` | TEXT | nullable | JSON array of the products shown alongside an assistant reply — this is the mechanism for "matching products appear on the page based on the conversation". Always null on user turns. |
| `created_at` | TEXT | NOT NULL, default `datetime('now')` | Timestamp for chronological ordering. |

`products_json` entries carry: `product_id`, `name`, `garment_type`, `description`,
`colors`, `search_tags`, `image_file_path`, `image_url`, `price`, `inventory`,
`total_stock`. Assistant turns attach either 0, 1, or 8 products — so the product panel
must handle an empty result, a single focused item, and a multi-product grid.

### What the stored examples establish

- **Honest refusal is expected.** "I couldn't find any products matching 'gym shorts'"
  and "I searched the current collection but couldn't find any items featuring
  Handsome Dan" — no invented products, with a suggested alternative offered.
- **Colour claims are checked.** "No—this Baseball Left Chest Crewneck is only
  available in navy and white, not pink."
- **Stock is reported by size.** "currently in stock in sizes S, M, L, and XXL."
- **The shopper is addressed by name** when logged in.
- **Tone is warm and brief**, Markdown-formatted, prices bolded (`**$68**`).

---

## 6. Data quirks the code must handle

### 6.1 `garment_type` is inconsistent
22 distinct raw values with overlapping and case-variant spellings — `short-sleeve
T-shirt` vs `short-sleeve t-shirt`, and `hoodie` / `pullover hoodie` / `hooded
sweatshirt` / `full-zip hooded sweatshirt`. Filtering on the raw column splits
identical garments across buckets. **Decision:** normalize at query time into six
categories — Quarter-Zips, Jackets, Hoodies, Crewnecks, Long Sleeve, T-Shirts — leaving
the database untouched, since graders run their own copy.

### 6.2 Colour names are inconsistent
Across 22 distinct colour values, the same colour appears under several names:
`navy blue` (62) and `navy` (18) coexist, and grey splits six ways — `heather gray`
(41), `charcoal gray` (3), `gray` (3), `dark heather gray` (2), `heather charcoal gray`
(1), `light gray` (1). A shopper asking for "grey" must match all six, so colour
matching has to be substring- and case-insensitive or it will miss most of them.

### 6.3 JSON is stored as TEXT
`colors`, `search_tags` and `products_json` are TEXT holding JSON. All 102 rows parse
cleanly, but parsing must still be defensive rather than assuming well-formed input.

### 6.4 Image paths are uniform
All 102 rows follow `products/<product_id>.jpg` exactly, and all 102 files exist. The
path still has to be resolved safely — a filename from a request must never escape
`data/products/`.

### 6.5 Prices are `REAL`
Floating point, so money should be rounded for display rather than printed raw.

---

## 7. Rules carried forward

1. **The database is the only source of truth** for products, prices and stock. No
   product, price, colour or size may be stated unless a query returned it.
2. **Size questions get a per-size answer** — list what is available *and* what is
   sold out, never a bare "yes".
3. **"I don't know" is a correct answer.** If a search returns nothing, say so and
   offer an alternative; never substitute a plausible-sounding product.
4. **Never expose `password_hash`** or any secret through the API.
5. **Never commit** `data/campus_customs.db`, `data/products/`, or `.env`.

---

---

## 8. Application Shape (Problem 3)

### Services

| Service | Port | Entry point |
|---|---:|---|
| FastAPI backend | 8787 | `backend/main.py` (re-exports `backend/app/main.py`) |
| Vite + React frontend | 5174 | `frontend/` |

Ports 8000 and 5173 are occupied by another project on the development machine,
hence 8787/5174. Vite proxies `/api` to the backend, so the frontend stays
origin-relative and image URLs returned by the API work unchanged.

### API surface so far

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | Reports whether the database, images and AI key are present |
| `GET /api/products` | List with `search`, `category`, `min_price`, `max_price`, `in_stock_only`, `limit`, `offset` |
| `GET /api/products/{product_id}` | One product plus per-size stock |
| `GET /api/categories` | Normalized categories and the real price range |
| `GET /api/images/{filename}` | Serves `data/products/`, path-traversal guarded |

### Routes

`/` home · `/products` catalogue · `/products/:productId` single item ·
`/about` · `/login` · `/create-account` · `*` not found.

### Design system

Original palette, not copied from the reference site: deep navy (`--navy-900`
`#0b1f3a`) for chrome, paper cream (`--cream-50` `#fbf9f4`) for page ground, and a
brass accent (`--brass-500` `#b08d35`) for rules, active states, and the primary
call to action. Display type is an old-style serif for collegiate feel; body text is
the system sans stack. No webfont is loaded, so the site renders identically offline.

### Decisions worth carrying forward

- **Product cards link to detail pages by `product_id`**, the same key the chatbot
  uses, so an assistant reply can deep-link to a product with no extra mapping.
- **Sold-out sizes render disabled and struck through**, with screen-reader text
  spelling out "sold out" — the visual honesty requirement has a text equivalent.
- **The chat widget is a placeholder** that states it is not connected. Its message
  state, history and accessibility behaviour are already in place; Problem 5 swaps
  the fake reply for a call to the agent endpoint.
- **Auth forms validate locally only** and say so. Wired up in a later problem.

### Bugs found and fixed during Problem 3

1. **SQLite cross-thread error.** FastAPI runs sync endpoints in a threadpool and
   could close a connection on a different thread than the one that opened it,
   producing intermittent 500s under concurrent requests. Sequential `curl` tests
   never triggered it; the browser loading several endpoints at once did. Fixed with
   `check_same_thread=False`; each request still gets its own connection.
2. **Aborted requests clobbering good state.** React StrictMode runs effects twice;
   the first run's abort landed in `.catch` and overwrote data the second run had
   already fetched, so the category filters rendered empty. Aborts are now ignored.
3. **`inert=""`** on the closed chat panel — React 19 wants a real boolean.

---

---

## 9. Authentication (Problem 4)

### What is stored for a user

The `users` table holds exactly six things per account, and nothing else:

| Column | Example | Notes |
|---|---|---|
| `id` | `4` | Primary key, used as the session subject |
| `name` | `Nora Whitfield` | Derived as `first_name + ' ' + last_name` |
| `email` | `nora@yale.edu` | Stored lowercased; UNIQUE in the schema |
| `password_hash` | `pbkdf2_sha256$240000$<salt>$<digest>` | Never the password itself |
| `created_at` | `2026-10-04 18:02:55` | Set by the column default |
| `first_name` / `last_name` | `Nora` / `Whitfield` | Collected at registration |

No plaintext password, no security questions, no password hints, and no
recovery copy of the password exists anywhere in the project.

### How passwords are protected

Passwords are hashed with **PBKDF2-HMAC-SHA256**, which is deliberately slow and
salted:

- **Salted.** Every account gets a fresh 16-byte random salt. Two users who pick
  the same password still get different stored values, so a stolen database
  cannot be attacked with a single precomputed rainbow table.
- **Slow by design.** New accounts use **240,000 iterations**. A correct login
  pays that cost once; an attacker guessing offline pays it for every guess.
- **One-way.** The stored value is a digest. There is no key, no decrypt
  function, and no code path in this project that can reverse it. Verifying a
  login recomputes the digest from the submitted password and compares. A person
  reading the database, or an AI system reading this repository, sees only the
  digest and learns nothing about the password.
- **Constant-time comparison.** `hmac.compare_digest` is used so that comparison
  timing does not leak how much of a digest was guessed correctly.
- **Never returned, never logged.** The `User` response model has no password
  field of any kind, and `password_hash` is read only inside the login check.
  Verified by searching API responses, the server log, and the database for a
  known test password: zero hits.
- **Length bounds.** Minimum 8 characters; maximum 200, so a huge input cannot be
  used to force unbounded hashing work.

### The seeded hash format

The three accounts shipped in the database use a **three-segment** format with no
iteration count recorded:

```
pbkdf2_sha256$<salt>$<digest>
```

The iteration count was not documented, so it was recovered by testing the known
test-user password against common values: **120,000 iterations, salt treated as
UTF-8 text**. Verification treats any three-segment hash as using that count.

New accounts are written in a **four-segment** format that records the cost, so
it can be raised later without locking anyone out:

```
pbkdf2_sha256$<iterations>$<salt>$<digest>
```

On a successful login with a weaker stored hash, the hash is transparently
upgraded to the current parameters — the one moment the plaintext is legitimately
in memory. This rewrites the seeded row in the local database on first login.

### Sessions

Login returns a signed token in an **HttpOnly cookie** named `cc_session`:

- **HttpOnly**, so page JavaScript cannot read it and an XSS bug cannot steal the
  session. Confirmed in the browser: `document.cookie` does not contain it.
- **SameSite=Lax**, so it is not sent on cross-site POSTs.
- **Secure** flag available via `COOKIE_SECURE=true` for HTTPS deployment.
- The token is `base64url(payload).base64url(HMAC-SHA256)` over `{sub, exp}`. The
  signature covers the exact payload bytes, so a client cannot change the user id
  or the expiry. A forged or tampered token is rejected.
- Expiry is 7 days by default (`JWT_TTL_SECONDS`).
- If `JWT_SECRET` is unset the app still starts, using a key generated for that
  process, and logs a warning. Sessions then end when the server restarts. This
  keeps the app runnable by a grader who configures nothing.

### Leak-resistant behaviour

- **Login errors are identical** for an unknown email and a wrong password:
  `"Incorrect email or password."` Neither the message nor the status code
  reveals whether an address has an account.
- **Timing is equalised.** When the email is unknown, a dummy hash is verified so
  the response takes comparable time, closing the timing side channel.
- **Email comparison is case-insensitive** for both login and the duplicate
  check, so `TEST@…` cannot be used to register a second account.

### Endpoints

| Endpoint | Behaviour |
|---|---|
| `POST /api/auth/register` | 201 + session on success; 409 duplicate email; 422 validation |
| `POST /api/auth/login` | 200 + session; 401 on any credential failure |
| `POST /api/auth/logout` | 204 and clears the cookie |
| `GET /api/auth/me` | 200 with the current user; 401 when signed out |

### Bug found and fixed during Problem 4

`logout` cleared the cookie on the injected `Response` but returned a newly
constructed one, so the `Set-Cookie` header was silently dropped and the session
survived logout. Caught by asserting that `/me` returns 401 after logging out,
rather than by trusting the 204.

---

*Last updated: Problem 4 — authentication.*
