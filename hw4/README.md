# Campus Customs

A full-stack storefront for Campus Customs, the family-run shop on Broadway in
New Haven that has printed and stitched Yale apparel since 1973. Shoppers can
browse the catalogue, create an account, and talk to a shopping assistant that
answers from the shop's real inventory — including telling you honestly when
something is sold out or not carried at all.

Built for Yale SOM **MGT 409**.

| | |
|---|---|
| **Frontend** | React 19 · Vite · TypeScript |
| **Backend** | Python · FastAPI |
| **Agent** | PydanticAI, via an OpenAI-compatible gateway |
| **Database** | SQLite |

---

## Quick start

> **Prerequisites:** Python 3.11+ and Node 20+.
>
> **The `data/` folder is required and is not in this repository.** It ships
> with the assignment and contains `campus_customs.db` and `data/products/`
> (102 product images). Place it at `hw4/data/` before starting the
> backend — the app will report `database_present: false` without it.

### 1. Your API key

The agent authenticates with **`PORTKEY_API_KEY`**. Either method works:

**A. Drop in your key file** (what graders will already have). Put your
`PORTKEY_API_KEY.env` in the **`hw4/` folder**, containing:

```
PORTKEY_API_KEY=your-key-here
```

No quotes, no spaces around the `=`. The file is gitignored and is never
committed.

**B. Or export it in your shell** — an exported environment variable takes
precedence over the file:

```bash
export PORTKEY_API_KEY=your-key-here
```

The backend looks for the key in this order, later entries winning:
`.env` → `backend/.env` → `backend/PORTKEY_API_KEY.env` →
`PORTKEY_API_KEY.env` → real environment variables.

**The site runs without a key.** The whole catalogue, accounts and product
pages work; only `/api/chat` returns 503 with a message saying the key is
missing. Nothing else degrades.

### 2. Backend

```bash
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
```

Then, **from the `backend/` folder**:

```bash
cd backend && uvicorn main:app --reload --port 8000
```

Check it came up: <http://127.0.0.1:8000/api/health> should report
`database_present: true` and, with a key set, `agent.configured: true`.
Interactive API docs are at <http://127.0.0.1:8000/docs>.

### 3. Frontend

In a second terminal:

```bash
cd frontend && npm install && npm run dev
```

Open **<http://localhost:5174>**. Vite proxies `/api` to port 8000, so both
servers must be running.

### 4. Sign in

A seeded account is available for testing:

| Email | Password |
|---|---|
| `test@campuscustoms.yale.edu` | `password` |

Or create a new account from the site — it is written to the `users` table with
a salted PBKDF2 hash.

---

## Optional configuration

All optional; sensible defaults apply. See `.env.example`.

| Variable | Default | Purpose |
|---|---|---|
| `PORTKEY_API_KEY` | *(unset)* | Gateway auth for the agent |
| `AI_BASE_URL` | `https://api.portkey.ai/v1` | OpenAI-compatible endpoint |
| `AI_MODEL` | `gpt-4o-mini` | Model name passed through the gateway |
| `JWT_SECRET` | *(generated per run)* | Signs session cookies. Unset means sessions end on restart. |
| `CORS_ORIGINS` | `http://localhost:5174` | Allowed browser origins |
| `COOKIE_SECURE` | `false` | Set `true` when serving over HTTPS |

---

## What it does

**Browse.** 102 products with search, six normalised categories, price bands,
four sort orders, and in-stock filtering. Every product has its own page with a
large image, full description, colours, and stock for each size.

**Accounts.** Registration and login with PBKDF2-HMAC-SHA256 hashing, a fresh
salt per account, and an HttpOnly signed session cookie. No plaintext password
is stored, logged, or returned anywhere.

**The assistant.** A PydanticAI agent with five database-backed tools. It can
search the catalogue, pull full product details, report stock size by size,
summarise stock counts, and list categories.

What makes it trustworthy rather than merely conversational:

- **The database is the only source of truth.** Every product, price and stock
  figure comes from a tool call.
- **Prices are enforced, not just requested.** An output validator checks every
  dollar figure in a reply against prices actually retrieved. An unverified
  number is rejected and the model has to correct itself before the shopper
  sees anything.
- **Honest about gaps.** Ask for gym shorts and it says the shop does not carry
  them, rather than inventing a product.
- **Sizes are reported both ways** — what is available *and* what is sold out.
- **Results appear on the page.** Products the agent looked up render as cards
  beside the conversation, each linking to its detail page. The page shows what
  the agent actually retrieved, not what it mentioned in prose.
- **Memory.** Signed-in shoppers get their conversation saved and replayed when
  they return. Page context travels with each message, so "do you have this in
  pink?" resolves to whatever product you are viewing.

---

## Project layout

```
backend/
  main.py              FastAPI app — products, auth, images, chat
  agent.py             Agent wiring: prompt, model, price guardrail
  tools.py             The five database-backed tools
  models.py            Pydantic types for cards, tools, chat, deps
  prompts/prompt.md    System prompt: voice and safety rules
  db.py                SQLite access
  security.py          Password hashing and session tokens
  config.py            Settings
frontend/
  src/pages/           Home, Products, ProductDetail, About, Login, …
  src/components/      NavBar, ProductCard, ChatWidget, ChatResults, …
  src/theme.css        Design tokens
output/
  harness.md           Build harness: schema, tools, safety rules
  usability.md         Usability improvements and rationale
  design.md            Visual design and rationale
AI_prompts.md          Log of the prompts used to build this
data/                  NOT IN GIT — ships with the assignment
```

---

## Notes

- **Ports.** Backend 8000, frontend 5174.
- **Not committed:** `data/` (database and product images), any `.env` or
  `PORTKEY_API_KEY.env`, `node_modules`, `.venv`, and build output.
- **Checkout is not implemented.** Sizes and stock shown are real, read live
  from the database, but no orders are placed.
- A student project. Not affiliated with Yale University.
