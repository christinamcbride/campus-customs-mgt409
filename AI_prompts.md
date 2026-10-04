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

---

## Problem 6 — Tools for Product Information and Stock

**Prompt 1 (initial):**

```
create a PORTKEY_API_KEY.env file for me in the folder and i'll paste in my API key. and then set up problem 6: tools for product information and stock
give the agent tools that look up real information from `campus_customs.db`.
the tools should be able to find:

* product descriptions
* prices
* how many products are in stock
* stock by size when the customer asks

the agent must use the database as its source of truth. it should never invent prices or quantities. if a size is out of stock, it should say so clearly. expand `prompts/prompt.md` so the agent knows to call these tools when answering questions about prices and stock. add or update the return types in `models.py`. in `output/harness.md`, list each tool and explain which model fields you chose for the lookup results and why.please inspect the existing implementation first, make only the changes needed for this problem, test the tools through the chat endpoint, and tell me what you changed.
```

---

## Problem 7 — Chat Search That Updates the Page

**Prompt 1 (initial):**

```
problem 7: chat search that updates the page 
add a feature that lets the chatbot search for products based on what the customer asks.
for example, if a customer asks, "what hoodies do you have?", the agent should search the catalogue and return matching products.
the website should dynamically display the matching products as product cards. each card should include:

* product image
* product name
* price
* short product information

this should work as an api contract: the agent returns structured product matches, and the frontend renders those matches on the page.
make sure the single-item page from problem 3 still works after adding the dynamic product cards. every product card, including cards added to the page through chat, should open the product's detail view when clicked. the detail view should include the large product image and full product information. update `prompts/prompt.md` and `output/harness.md` so it is clear how search results move from the agent to the frontend and appear on the page.
```

---

## Problem 8 — Customer Memory

**Prompt 1 (initial):**

```
problem 8: customer memory when a shopper is logged in, save their chat history in an appropriate database table and reload it when they return.
the agent should know who is chatting, including the customer's name and email. pass this information through the agent dependencies or another clear method, and make it available through tools if needed.
also pass enough page context to the agent so it can understand which product the shopper is viewing. for example, if someone is on a product page and asks, "do you have this in pink?", the agent should know which product they mean. you can add this information to the agent context. guests can still chat, but chat history only needs to be saved for logged-in users.
document the following in `output/harness.md`:

* how user chat history is stored
* which customer fields the agent can see
* how page context is passed to the agent
```

---

## Problem 9 — Usability Improvements

**Prompt 1 (initial):**

```
problem 9: usability improvements now that the core shop works, improve it by choosing and implementing:

* two front-end usability improvements
* two agent or backend usability improvements

front-end improvements should make the site look better or make it easier to use. agent and backend improvements should make the agent's output better, more accurate, or safer. they could include new agent tools or changes that make the agent run faster or cost less.
create `output/usability.md` before or while you build the improvements.
for each improvement, explain:

* what you added
* why it helps a campus customs shopper or the business

make sure all four improvements actually appear in the running app. the graders will read the write-up and look for the features.
```

---

## Problem 10 — Style the Website

**Prompt 1 (initial):**

```
problem 10: style the website. add creative design so the site feels like a real campus customs storefront. focus on things like:

* fonts
* color
* visual hierarchy
* motion
* product presentation
* the chat experience

use an imaginative and innovative design. write `output/design.md` and briefly explain:

* what you changed
* why the changes should encourage customers to stay on the site and buy

keep the explanation concrete and short.
```

---

## Problem 11 — Site Testing (App Check)

**Prompt 1 (initial):**

````
problem 11: site testing (app check) 
test the live site and document the results in `output/app_check.html`. this should be a page that can be opened by double-clicking it.
include clear screenshots and short captions for these checks:

1. chat checking the inventory level of an item, with honest stock and price information from the database;
2. dynamic search-result cards appearing after a category question, such as asking about hoodies;
3. one of the usability features added in problem 9.

make the html easy to grade. for each check, include:

* a heading
* a screenshot
* one or two sentences explaining what the screenshot proves

put the screenshot files in `output/app_check_images/`.
link to the images from `app_check.html` using relative paths. for example:

```text
app_check_images/inventory.png
```
````

**Prompt 2 (follow-up):**

````
continuing on problem 11, make the html easy to grade. include a heading for each check, a screenshot, and one or two sentences explaining what the screenshot proves. put the screenshot image files in `output/app_check_images/`. link to them from `app_check.html` using relative paths. for example:

```text
app_check_images/inventory.png
```
````

*What was lacking after the first prompt:* the page met the letter of the
requirement but buried it — each check opened with an intro paragraph and
closed with a verification table and footnote, so the heading, screenshot and
one-line explanation a grader is looking for were not the first things on the
page. The screenshots were also captured at 800px wide, which made the chat
text small.

