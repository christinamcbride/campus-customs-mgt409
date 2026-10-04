# AI Prompts Log — Campus Customs (MGT 409, HW4)

A record of the prompts I typed while building the Campus Customs shopping site.
Prompts are reproduced **word for word**, exactly as I typed them, including
original spelling and punctuation. One section per problem.

---

## Problem 1 — Locating the assignment folder and confirming the data

**Prompt 1 (initial):**

```
We're going to work in the homework 4 folder in MGT 409 today on my desktop can you locate it?
```

**Prompt 2 (follow-up):**

```
Do you see the data folder in HW4 now?
```

*What was lacking after the first prompt:* the HW4 folder was found but completely
empty — no `data/` folder, no database, no product images — so there was nothing to
build against until the assignment data was added and I asked it to look again.

---

## Problem 2 — Project requirements and scope

**Prompt 1 (initial):**

```
Campus Customs Project Instructions
You are helping me build a full-stack Campus Customs shopping website.
Project requirements
Build:

* A React + Vite + TypeScript frontend
* A Python FastAPI backend
* A PydanticAI agent powering the chatbot
* A local SQLite database for products, inventory, and users

Shoppers should be able to:

* Browse products
* Create an account and log in
* Chat with the shopping assistant about merchandise
* See matching products appear on the page based on the conversation
* Get accurate answers about product prices and inventory
* Receive honest responses when information is unavailable

Existing data
The project includes:

* `data/campus_customs.db` — SQLite database
* `data/products/` — product images

The database contains these tables:

* `catalogue`
* `inventory`
* `users`

One test user already exists. Product image paths are stored in the `catalogue` table and correspond to files in `data/products/`.
Do not commit the database or product images to GitHub. Add appropriate entries to `.gitignore`.
Design direction
Research [yalebulldogblue.com](https://yalebulldogblue.com/) for visual inspiration and information about the Campus Customs style. Use that research to inform:

* Colors
* Typography
* Layout
* Branding
* Product presentation
* The chatbot's tone and knowledge prompt

Do not copy the site directly. Create an original design inspired by its visual style.
AI configuration
Use a `PORTKEY_API_KEY` environment variable for the agent's AI calls.
We're not using Portkey or openAI, but the graders for this assignment have their own variable PORTKEY_API_KEY so we want this assignment to be able to open for them with their own key.
How to work
Work on one problem at a time.
Before making changes:

1. Inspect the existing project structure.
2. Identify the current problem or requested feature.
3. Explain briefly what you plan to change.
4. Make the smallest complete change needed.
5. Run appropriate checks or tests.
6. Report what changed and whether verification passed.

If requirements are ambiguous, make a reasonable assumption and state it before proceeding. Do not silently invent major functionality.
Development expectations
Prioritize:

* A polished, responsive customer experience
* Clear separation between frontend and backend
* Secure password handling
* Proper validation of API inputs
* Accurate database queries
* Reliable chatbot behavior
* Useful error and loading states
* Accessible controls and readable text
* Clean, maintainable code

The chatbot must use the local database as its source of truth for prices, products, and stock. It must not invent product information or claim an item is available without checking the database.
When the user asks about inventory by size, query the inventory table and clearly identify available and unavailable sizes.
GitHub submission requirements
At the end:

* Push the project to a public GitHub repository.
* Do not commit `data/campus_customs.db`.
* Do not commit files in `data/products/`.
* Do not commit `.env` files, API keys, or other secrets.
* Provide the public repository URL.

Do not claim that the project is finished until the application has been tested and the repository contents have been reviewed.
```

**Follow-up (clarification I answered):** the assistant flagged a contradiction in my
instructions — I said to use `PORTKEY_API_KEY` but also that we are not using Portkey
or OpenAI — and asked what the agent should actually call at runtime. I selected:

```
Portkey gateway, OpenAI-compatible
```

*What was lacking after the first prompt:* my instructions named the environment
variable but not the actual provider or endpoint behind it, so the agent's model
configuration was ambiguous and could not be written without guessing.

---

## Problem 3 — Backend scaffold and catalogue API

No new prompt was typed for this problem; it was carried out under the standing
instructions in Problem 2 ("work on one problem at a time", smallest complete change,
verify before reporting).

Work completed: `.gitignore` excluding `data/` and secrets, FastAPI application,
SQLite access layer, product listing/search/filter endpoints, per-size inventory
lookup, and an image endpoint with a path-traversal guard.

---

## Problem 4 — Prompt logging

**Prompt 1 (initial):**

```
Create `AI_prompts.md` at the start of the assignment and keep it updated as you work. This file is the log of what i typed. I'll describe each problem to you  in my own words so please keep the phrasing word for word and exact. Put one section for each problem. Each section must include:

* The problem number and title
* At least one prompt you typed, in your own words as much as possible
* One follow-up prompt if you needed it, along with one sentence explaining what was lacking after the first prompt
```

---
