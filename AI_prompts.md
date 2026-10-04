# AI Prompts Log — Campus Customs (MGT 409, HW4)

A record of the prompts I typed while building the Campus Customs shopping site.
Prompts are reproduced **word for word**, exactly as I typed them, including original
spelling and punctuation. One section per problem (13 problems total).

---

## Problem 1 — Vibe Coder Prompt

**Prompt 1 (initial):**

```
We're going to work in the homework 4 folder in MGT 409 today on my desktop can you locate it?
```

**Prompt 2 — the main vibe coder prompt:**

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

Do not claim that the project is finished until the application has been tested and the repository contents have been reviewed. Do you see the data folder in HW4 now?
```

*What was lacking after the first prompt:* the HW4 folder was located but completely
empty — no `data/` folder, no database, no product images — so there was nothing to
build against. I added the assignment data and sent the full project brief, ending by
asking it to check for the data folder again.

**Prompt 3 (clarification I answered):** the assistant flagged a contradiction in my
brief — I said to use `PORTKEY_API_KEY` but also that we are not using Portkey or
OpenAI — and asked what the agent should actually call at runtime. I selected:

```
Portkey gateway, OpenAI-compatible
```

*What was lacking:* my brief named the environment variable but not the provider or
endpoint behind it, so the agent's model configuration was ambiguous and could not be
written without guessing.

**Prompt 4 (follow-up):**

```
Create `AI_prompts.md` at the start of the assignment and keep it updated as you work. This file is the log of what i typed. I'll describe each problem to you  in my own words so please keep the phrasing word for word and exact. Put one section for each problem. Each section must include:

* The problem number and title
* At least one prompt you typed, in your own words as much as possible
* One follow-up prompt if you needed it, along with one sentence explaining what was lacking after the first prompt
```

*What was lacking:* my original brief did not mention the prompt log at all, which is
a required deliverable for this assignment.

**Prompt 5 (correction):**

```
no this was all for Problem 1: Vibe Coder Prompt, theres 13 problems so we'll move onto problem 2 next
```

*What was lacking:* the assistant had split my prompts into four separate problems of
its own invention, when everything so far belonged to Problem 1 of the assignment's
own 13-problem structure.

### Work completed under Problem 1

- `.gitignore` excluding `data/` (database and product images), `.env` files, virtual
  environments and `node_modules`
- FastAPI backend with settings loaded from `backend/.env`
- SQLite access layer: product listing, search, filtering, and per-size inventory
- Product image endpoint with a path-traversal guard
- Dependencies pinned to releases that publish CPython 3.14 wheels

---

## Problem 2 — Analyze the Database

**Prompt 1 (initial):**

```
# problem 2: analyze the database
look at the database `data/campus_customs.db` and understand the fields in each table. at a minimum, understand the `catalogue`, `inventory`, and `users` tables. start a file called `output/harness.md` and write down each table and its fields. for each field, include one short sentence explaining why it matters for the shop or the chatbot. we will keep adding to this harness file in later problems. it will eventually include models, tools, safety rules, and specifications.
```

---

## Problem 3 — Build the Campus Customs Website

**Prompt 1 (initial):**

```
problem 3: build the campus customs website
build a react + vite + typescript frontend for campus customs.
add a navigation bar at the top with links to these main pages:

* home
* products
* about us
* log in
* create account

use wording inspired by [yalebulldogblue.com](https://yalebulldogblue.com/) for the home and about us pages, but write the content in your own voice. do not copy the original site's text.
on the products page, show product images from the catalogue. use the image paths stored in the database. include basic product information such as the name, price, and a short description. each product should open to its own single-item page. show a large image on one side and the full product information on the other, including the description, price, and sizes or stock when that information is available. clicking a product card on the products page should take the shopper to its individual page.
add a chat interface in the bottom-right corner of the site. a floating chat panel is fine. it does not need to connect to the agent yet. for now, a basic placeholder that will call the backend later is enough.
you will need a small api soon to read the database. it is okay to start a simple fastapi app in `backend/main.py` that serves products and images. this will later grow into the agent backend in problem 5.
```

---

## Problem 4 — Create an Account and Log In

**Prompt 1 (initial):**

```
problem 4: create an account and log in
build a normal create-account and login flow. for the create-account page, include:

* first name
* last name
* email
* password
* password confirmation

for the login page, include:

* email
* password

new accounts should be saved in the `users` table. make sure passwords are stored securely so that neither people nor ai systems can access the original passwords. the seed database already has a test user you can use while building:

* email: `test@campuscustoms.yale.edu`
* password: `password`

confirm that you can log in as this test user and that a brand-new account you create also works.
update `output/harness.md` with an explanation of how authentication works including what information is stored for a user and how passwords are protected.
```

---

## Problem 5 — PydanticAI Agent Backend

**Prompt 1 (initial):**

````
problem 5: pydanticai agent backend
build the shop chatbot as a pydanticai agent behind fastapi, and connect it to the chat widget in the frontend.
put the api app in `backend/main.py`. this is the file you will run with uvicorn. keep the agent code in these files:

* `backend/prompts/prompt.md` — the system prompt. you will expand this file later.
* `backend/agent.py` — the agent entry point and wiring
* `backend/tools.py` — the tools the agent can call
* `backend/models.py` — pydantic and pydanticai structured types

in `main.py`, add a chat route so that a message from the website returns a reply from the agent. also add any other routes you need for products and authentication.
you will need an ai model api key for the agent.
put the campus customs voice and basic safety rules into `prompts/prompt.md`. you will expand the tools and safety rules later. add or update the types in `models.py` for chat replies and product cards as needed.
in `output/harness.md`, explain how the frontend communicates with fastapi and how the agent is loaded, including the prompt file and the model. make sure the backend runs from the `backend/` folder with this command:

```
uvicorn main:app --reload --port 8000
```
````

