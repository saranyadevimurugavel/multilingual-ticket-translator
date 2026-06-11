# 🌐 AI Multilingual Ticket Translator

An AI-powered full-stack customer support platform that accepts tickets in any language, automatically detects the language, translates to English, analyses with Google Gemini AI, and translates engineer replies back to the customer's original language.

---

## 🚀 Live Demo

**Frontend:** https://saranyadevimurugavel.github.io/multilingual-ticket-translator/

**Backend API:** https://multilingual-ticket-translator.onrender.com/api/health

---

## 🔑 Default Login Credentials

| Role | Email | Password |
|---|---|---|
| Admin | admin@mtt.com | admin123 |
| Client | client@mtt.com | client123 |

> New clients can register directly on the home page — account creation auto-logs in and redirects to the ticket portal.

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Backend | Python 3, Flask, Flask-SQLAlchemy |
| Database | SQLite (dev) / PostgreSQL (prod) |
| AI Model | Google Gemini 1.5 Flash + rule-based fallback |
| Translation | MyMemory API (free, no key required) |
| Language Detection | Unicode script map + langdetect (offline) |
| Auth | JWT (PyJWT) |
| Deployment | GitHub Pages (frontend) + Render (backend) |

---

## 🔄 System Workflow

```
User / Frontend
  └─ Client submits ticket (text or file upload, any language)
        │ sends request
        ▼
Agent Loop / Backend  (Flask — process_ticket())
  └─ Orchestrates: detect → translate → analyse → persist
        │ dispatches to
        ▼
AI Model (LLM)
  └─ Google Gemini 1.5 Flash
     Fallback: rule-based analyser (no API key needed)
        │
        ├── optional ──→ External API
        │                └─ MyMemory API (translation)
        │ processes & returns
        ▼
Data / Processing Layer
  └─ SQLite database — Ticket saved with all AI fields
        │ structured result
        ▼
Response / Output
  └─ JSON: category, priority, sentiment, summary, confidence
        │ renders output
        ▼
UI — show result
  └─ AI Analysis card shown to client
     Admin reviews in Translation Center / History
```

---

## ✨ Features

### Client Side
- **Register & auto-login** — account creation redirects directly to the ticket portal
- **Submit ticket in any language** — no language selection required; detected automatically
- **File attachment** — upload `.txt`, PDF, images; text files auto-fill the message box
- **AI analysis result** — instantly see detected language, category, priority, sentiment, confidence, translation, summary, and suggested response
- **My Tickets dashboard** — view all previously submitted tickets with status badges; click any row for full details in a slide-in drawer

### Admin Side
- **Dashboard** — live stats: Total Tickets, Pending, Translated Today, Approved
- **Translation Center** — review pending tickets one by one; approve/reject; send English replies that are auto-translated back to customer's language
- **History** — filterable, paginated table of all tickets with full detail drawer; approve/reject directly from history
- **Batch Processing** — process an entire folder of `.txt`/`.json` ticket files through the full AI pipeline; send replies per ticket

---

## 📁 Project Structure

```
multilingual-ticket-translator/
├── index.html                    # Landing page — client login + register
├── vercel.json
├── pages/
│   ├── client/
│   │   ├── login.html            # Client login + register (tabs)
│   │   └── submit-ticket.html   # New Ticket + My Tickets tabs
│   └── admin/
│       ├── login.html            # Admin login with backend warm-up ping
│       ├── dashboard.html        # Live stats + recent tickets
│       ├── translation-center.html  # Approve/reject + reply translation
│       ├── history.html          # Filterable ticket history + drawer
│       └── batch.html            # Batch file processing
├── assets/
│   ├── js/
│   │   ├── app.js               # API base URL, apiCall(), auth helpers
│   │   ├── translation.js       # Submit ticket + Translation Center logic
│   │   ├── dashboard.js         # Dashboard stats + recent tickets
│   │   └── sidebar.js           # Mobile hamburger menu
│   └── css/
│       ├── style.css
│       ├── responsive.css
│       └── components/          # buttons, cards, forms, navbar, sidebar, tables
├── sample_tickets/               # 8 mixed-language test tickets
│   ├── ticket_001.txt  (Tamil)
│   ├── ticket_002.txt  (Hindi)
│   ├── ticket_003.txt  (French)
│   ├── ticket_004.txt  (Malayalam)
│   ├── ticket_005.txt  (Telugu)
│   ├── ticket_006.txt  (German)
│   ├── ticket_007.json (Spanish)
│   └── ticket_008.json (English)
├── .kiro/specs/                  # Kiro spec — requirements document
└── backend/
    ├── app.py                   # Flask app factory + CORS + blueprints
    ├── wsgi.py                  # Gunicorn entry point (Render)
    ├── database.py              # SQLAlchemy models: User, Ticket, GlossaryTerm
    ├── middleware.py            # @login_required / @admin_required decorators
    ├── render.yaml              # Render deployment config
    ├── requirements.txt
    ├── .env.example
    ├── routes/
    │   ├── auth_routes.py       # POST /login, POST /register
    │   ├── ticket_routes.py     # submit, pending, history, my, approve, reject
    │   ├── dashboard_routes.py  # GET /stats
    │   ├── glossary_routes.py   # CRUD glossary terms
    │   └── batch_routes.py      # POST /process-folder, POST /reply
    └── services/
        ├── ai_service.py        # Language detection, MyMemory translation, Gemini analysis
        ├── auth_service.py      # JWT create/decode
        └── batch_service.py     # Folder scan, file parse, reply translation
```

---

## 📋 API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | /api/auth/register | — | Register new user (returns token) |
| POST | /api/auth/login | — | Login (returns token) |
| GET | /api/health | — | Health check |
| POST | /api/tickets/submit | Client | Submit + detect + translate + analyse |
| GET | /api/tickets/my | Client | Get current user's own tickets |
| GET | /api/tickets/pending | Admin | Oldest pending ticket for review |
| GET | /api/tickets/history | Admin | All tickets (filterable, paginated) |
| GET | /api/tickets/recent | Admin | Recent tickets for dashboard |
| POST | /api/tickets/:id/approve | Admin | Approve translation |
| POST | /api/tickets/:id/reject | Admin | Reject translation |
| GET | /api/dashboard/stats | Admin | Aggregate statistics |
| GET | /api/glossary | Admin | List glossary terms |
| POST | /api/glossary/add | Admin | Add glossary term |
| DELETE | /api/glossary/:id | Admin | Delete glossary term |
| POST | /api/batch/process-folder | Admin | Batch process ticket folder |
| POST | /api/batch/reply | Admin | Translate engineer reply |

---

## 🌍 Supported Languages

| Region | Languages |
|---|---|
| Indian | Tamil, Hindi, Malayalam, Telugu, Kannada, Bengali, Marathi, Gujarati, Punjabi, Urdu, Odia |
| International | French, German, Spanish, Arabic, Chinese (Simplified), Japanese, Korean, Portuguese, Russian, Italian, Turkish |

Detection uses offline Unicode script mapping for Indian languages — no network call needed.

---

## 💻 Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/saranyadevimurugavel/multilingual-ticket-translator.git
cd "multilingual-ticket-translator"

# 2. Setup backend
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt

# 3. Create .env file
copy .env.example .env
# Edit .env — add your GEMINI_API_KEY (optional, system works without it)

# 4. Start Flask backend
python app.py
# Runs at http://localhost:5000

# 5. Open frontend (new terminal from repo root)
python -m http.server 3000
# Open http://localhost:3000
```

---

## ☁️ Deployment

### Backend — Render

1. Go to https://render.com → New → Web Service
2. Connect your GitHub repo
3. Set **Root Directory** to `backend`
4. Build command: `pip install -r requirements.txt`
5. Start command: `gunicorn wsgi:app`
6. Add environment variables:
   - `SECRET_KEY` = any long random string
   - `GEMINI_API_KEY` = your key from https://aistudio.google.com/app/apikey
   - `FLASK_DEBUG` = 0
7. Deploy — the service auto-reseeds the admin and client accounts on first start

### Frontend — GitHub Pages

1. Push to `main` branch
2. Go to repo Settings → Pages → Source: Deploy from branch → `main` / `root`
3. Site will be live at `https://<username>.github.io/<repo-name>/`

> The frontend auto-detects localhost vs production and switches the API base URL accordingly — no manual changes needed.

---

## ⚠️ Known Limitations

- **SQLite on Render free tier** — ephemeral disk; database resets on restart. Use PostgreSQL (`DATABASE_URL` env var) for persistent storage
- **MyMemory free tier** — 5,000 words/day without email, 10,000 words/day with `MYMEMORY_EMAIL` env var
- **Gemini free tier** — 15 requests/minute; system falls back to rule-based analysis automatically when quota is exceeded or key is missing
- **Render free tier cold start** — backend sleeps after 15 min inactivity; admin login page pings `/api/health` on load to wake it up

---

## 🧪 Running Tests

```bash
cd backend
pip install pytest pytest-flask
pytest tests/ -v
```

---

## 📄 License

MIT
