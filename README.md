# 🌐 Multilingual Ticket Translator

AI-powered customer support system that accepts tickets in any language, detects the language, translates to English, analyses with Gemini AI, and translates engineer replies back to the customer's language.

---

## 🚀 Live Demo

 https://saranyadevimurugavel.github.io/multilingual-ticket-translator/
---



ADMIN LOGIN:
Email id : admin@mtt.com
password : admin@123

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript, Bootstrap |
| Backend | Python, Flask, Flask-SQLAlchemy |
| Database | SQLite (dev) |
| AI | Google Gemini API (free tier) |
| Translation | MyMemory API (free, no key) |
| Detection | langdetect (offline) |
| Auth | JWT |

---

## 📁 Project Structure

```
Multilingual ticket translator/
├── index.html                    # Landing page + Login + Register
├── vercel.json                   # Vercel frontend config
├── pages/
│   ├── client/
│   │   ├── login.html
│   │   └── submit-ticket.html
│   └── admin/
│       ├── login.html
│       ├── dashboard.html
│       ├── translation-center.html
│       ├── history.html
│       ├── batch.html
│       └── glossary.html
├── assets/
│   ├── js/
│   │   ├── app.js         # API helpers + auth
│   │   ├── dashboard.js
│   │   ├── translation.js
│   │   └── sidebar.js
│   └── css/
├── sample_tickets/               # 8 mixed-language test tickets
│   ├── ticket_001.txt  (Tamil)
│   ├── ticket_002.txt  (Hindi)
│   ├── ticket_003.txt  (French)
│   ├── ticket_004.txt  (Malayalam)
│   ├── ticket_005.txt  (Telugu)
│   ├── ticket_006.txt  (German)
│   ├── ticket_007.json (Spanish)
│   └── ticket_008.json (English)
└── backend/
    ├── app.py
    ├── wsgi.py               # Gunicorn entry point for Render
    ├── database.py
    ├── middleware.py
    ├── render.yaml
    ├── requirements.txt
    ├── routes/
    │   ├── auth_routes.py
    │   ├── ticket_routes.py
    │   ├── dashboard_routes.py
    │   ├── glossary_routes.py
    │   └── batch_routes.py
    └── services/
        ├── ai_service.py
        ├── auth_service.py
        └── batch_service.py
```

---

## 🔑 Default Login Credentials

| Role | Email | Password |
|---|---|---|
| Admin | admin@mtt.com | admin123 |
| Client | client@mtt.com | client123 |

---

## 💻 Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/multilingual-ticket-translator.git
cd "multilingual-ticket-translator"

# 2. Setup backend
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

# 3. Create .env file
copy .env.example .env
# Add your GEMINI_API_KEY to .env

# 4. Start Flask backend
python app.py
# Runs at http://localhost:5000

# 5. Start frontend (new terminal)
cd ..
python -m http.server 3000
# Open http://localhost:3000
```

---

## ☁️ Deployment

### Step 1 — GitHub

```bash
git init
git add .
git commit -m "Initial commit: Multilingual Ticket Translator"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/multilingual-ticket-translator.git
git push -u origin main
```

### Step 2 — Render (Backend)

1. Go to https://render.com → New → Web Service
2. Connect your GitHub repo
3. Set **Root Directory** to `backend`
4. Build command: `pip install -r requirements.txt`
5. Start command: `gunicorn wsgi:app`
6. Add environment variables:
   - `SECRET_KEY` = any long random string
   - `GEMINI_API_KEY` = your Gemini API key
   - `FLASK_DEBUG` = 0
7. Deploy → copy the URL (e.g. `https://mtt-backend.onrender.com`)

### Step 3 — Update Frontend API URL

In `assets/js/app.js`, replace:
```js
'https://mtt-backend.onrender.com/api'
```
with your actual Render URL.

### Step 4 — Vercel (Frontend)

1. Go to https://vercel.com → New Project
2. Import your GitHub repo
3. **Root Directory**: leave as `/` (repo root)
4. Framework: **Other**
5. Deploy → get your live URL

---

## 🤖 AI Agent Loop

```
Customer Ticket (any language)
    │
    ▼ langdetect (offline)
Language Detection
    │
    ▼ MyMemory API
Translate → English
    │
    ▼ Gemini API
AI Analysis → Category + Priority + Sentiment + Summary + Response
    │
    ▼
Store both versions in SQLite
    │
Engineer writes reply in English
    │
    ▼ MyMemory API
Translate reply → Customer's original language
    │
Store English + translated reply
```

---

## 🧪 Test Cases

Run from the `backend/` folder:
```bash
pip install pytest pytest-flask
pytest tests/ -v
```

---

## 📋 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | /api/auth/login | Login |
| POST | /api/auth/register | Register |
| POST | /api/tickets/submit | Submit + translate ticket |
| GET | /api/tickets/pending | Next pending ticket |
| POST | /api/tickets/:id/approve | Approve translation |
| POST | /api/tickets/:id/reject | Reject translation |
| GET | /api/dashboard/stats | Dashboard statistics |
| GET | /api/glossary | List glossary terms |
| POST | /api/glossary/add | Add glossary term |
| POST | /api/batch/process-folder | Batch process ticket folder |
| POST | /api/batch/reply | Translate engineer reply |

---

## 🌍 Supported Languages

Tamil, Hindi, Malayalam, Telugu, Kannada, Bengali, Marathi, Gujarati, Punjabi, Urdu, Odia, French, German, Spanish, Arabic, Chinese, Japanese, Korean, Portuguese, Russian, Italian, Turkish

---

## ⚠️ Limitations

- SQLite resets on Render free tier (ephemeral storage) — use PostgreSQL for persistent data
- MyMemory free tier: 5,000 words/day
- Gemini free tier: 15 requests/minute

---

## 📄 License

MIT
