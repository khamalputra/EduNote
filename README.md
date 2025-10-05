# EduNote — Learning Notes & Flashcards

EduNote is a full-stack learning companion that combines rich markdown notes with flashcards and SM-2-based spaced repetition. It is built with Streamlit and Supabase, making it cloud-ready for rapid deployment.

## Features
- 🔐 **Secure authentication** via Supabase email/password Auth.
- 📝 **Markdown notes** with taggable organization and fast search.
- 🗂️ **Deck and flashcard management** including CSV import/export and note-to-card conversion.
- 🧠 **SM-2 spaced repetition** delivered through a study workflow powered by a Postgres RPC function.
- 📊 **Analytics dashboard** for daily review counts, deck accuracy, due forecasts, and review streaks.
- 📤 **Data export** across notes, decks, cards, and reviews for backup or analysis.

## Tech Stack
- **Frontend:** Streamlit multipage app
- **Backend:** Supabase Postgres + Auth + Row Level Security
- **Charts:** Streamlit native charts & matplotlib
- **Language:** Python 3.10+
- **Package Manager:** pip (`requirements.txt`)

## Architecture Overview
```
┌─────────────────────────────────────────────┐
│ Streamlit UI (app.py + pages/*)             │
│  ├─ Authentication gateway (app.py)         │
│  ├─ Notes, decks, cards CRUD pages          │
│  ├─ Study session invoking apply_review()   │
│  └─ Analytics & settings pages              │
│                                             │
│ Shared libs (lib/*)                         │
│  ├─ supabase_client.py  → Supabase singleton│
│  ├─ auth.py             → Auth helpers       │
│  ├─ utils.py            → CSV & navigation   │
│  └─ srs.py              → SRS utilities      │
└─────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│ Supabase Postgres                           │
│  ├─ Tables: profiles, notes, decks, cards,  │
│  │          reviews                         │
│  ├─ RLS policies (owner-only access)        │
│  ├─ Trigger: touch_updated_at()             │
│  └─ RPC: apply_review(card_id, grade)       │
└─────────────────────────────────────────────┘
```

## Database Schema
Key tables and relationships (see `supabase/schema.sql` for full DDL):

| Table    | Purpose | Highlights |
|----------|---------|------------|
| `profiles` | Stores user profile metadata linked to `auth.users`. | Users can view/update their own profile. |
| `notes` | Markdown notes with tags per user. | `tags` array, updated timestamps, owned by `auth.uid()`. |
| `decks` | Flashcard decks per user. | Shares `touch_updated_at` trigger for modified timestamps. |
| `cards` | Flashcards linked to decks and optionally notes. | SM-2 scheduling fields (`ease`, `interval_days`, `due_at`, etc.). |
| `reviews` | History of study reviews. | Stores grade, previous/new interval & ease, timestamps. |

Row Level Security policies (see `supabase/policies.sql`) ensure users only access rows where `owner = auth.uid()`.

The `apply_review` RPC function (see `supabase/functions.sql`) encapsulates SM-2 scheduling logic, writes a review record, and returns the updated card.

## Setup

### 1. Supabase Project
1. Create a new Supabase project (free tier is fine).
2. In the SQL editor, run the scripts in order:
   - `supabase/schema.sql`
   - `supabase/policies.sql`
   - `supabase/functions.sql`
3. Grab your project **URL** and **anon key** from `Settings → API`.

### 2. Local Environment
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file from the provided template:
```bash
cp .env.example .env
# then fill in SUPABASE_URL and SUPABASE_ANON_KEY
```

### 3. Run the App
```bash
streamlit run app.py
```

Open the provided local URL. Register an account, then start creating notes, decks, and cards.

## Deployment
EduNote is designed to run on Streamlit Community Cloud or any Python host.

### Deploy to Streamlit Community Cloud
1. Push this repository to GitHub.
2. Create a new Streamlit Cloud app pointing to `app.py`.
3. Add environment variables in the Streamlit app settings:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
4. Deploy. Streamlit will install dependencies from `requirements.txt` automatically.

### Deploy elsewhere (e.g., Render, Fly.io)
- Build a Python service that runs `streamlit run app.py`.
- Ensure environment variables are configured.
- Persist Supabase credentials securely via the hosting provider’s secret store.

## Testing & Quality
- The Supabase RPC `apply_review` can be unit-tested via Supabase SQL or the Python client.
- Use `streamlit run` locally to manually verify UI flows.
- `requirements.txt` pins key dependencies to guarantee reproducible builds.

## AI Assistance
AI was only used during development to scaffold code and documentation. The production application does not depend on AI services at runtime.

## Screenshots
_Add screenshots of key pages here once the app is running._

## License
MIT License (adjust if needed for your organization).
