# SkillGap.AI — AI-Powered Skill Gap Analyzer

> An AI-powered career readiness platform that parses your resume, identifies skill gaps, generates interactive learning roadmaps, and tracks your progress — powered by Google Gemini API.

![Tech Stack](https://img.shields.io/badge/stack-React%20%2B%20Flask%20%2B%20Gemini-blueviolet?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)

---

## ✨ Features

- 📄 **Resume Upload** — PDF & DOCX parsing with OCR fallback via Gemini Vision
- 🧠 **AI Skill Extraction** — Extracts tech skills, soft skills, and experience via Gemini
- 🎯 **Career Goal Selection** — Choose from curated career paths
- 📊 **Skill Gap Analysis** — Bar chart visualization of your skill gaps
- 🗺️ **AI Learning Roadmap** — Auto-generated step-by-step learning paths
- 📈 **Progress Tracker** — Mark steps complete, track your readiness score (0–100)
- 🧪 **Quiz System** — AI-generated quizzes per skill
- 🚀 **Demo Mode** — Seed profiles (Frontend, DevOps, Data Science) with one click

---

## 🏗️ Tech Stack

| Layer     | Technology                    |
|-----------|-------------------------------|
| Frontend  | React 19, Vite, Tailwind CSS 4 |
| Backend   | Flask 3, Flask-SQLAlchemy      |
| AI        | Google Gemini API              |
| Charts    | Recharts                       |
| Deploy    | Vercel (frontend), Render (backend) |

---

## 🚀 Local Development

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/skillgapai.git
cd SkillGapAI
```

### 2. Backend setup
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Create .env from example
copy .env.example .env
# Edit .env and set your GEMINI_API_KEY

python run.py
```
Backend runs at **http://localhost:5000**

### 3. Frontend setup
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at **http://localhost:5173**

---

## ☁️ Deployment

### Backend → Render

1. Create a new **Web Service** on [Render](https://render.com)
2. Connect your GitHub repo and set **Root Directory** to `backend`
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn run:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
5. Add **Environment Variables** in the Render dashboard:
   | Key | Value |
   |-----|-------|
   | `GEMINI_API_KEY` | your Gemini API key |
   | `SECRET_KEY` | any random string |
   | `FRONTEND_URL` | your Vercel frontend URL |
   | `FLASK_ENV` | `production` |

### Frontend → Vercel

1. Import your GitHub repo on [Vercel](https://vercel.com)
2. Set **Root Directory** to `frontend`
3. Framework preset: **Vite**
4. Add **Environment Variable** in Vercel dashboard:
   | Key | Value |
   |-----|-------|
   | `VITE_API_URL` | your Render backend URL (e.g. `https://skillgapai-backend.onrender.com`) |
5. Deploy 🚀

---

## 📁 Project Structure

```
SkillGapAI/
├── backend/
│   ├── app/
│   │   ├── routes/       # API blueprints (auth, resume, roadmap, quiz, progress)
│   │   ├── services/     # PDF parsing, Gemini AI service
│   │   ├── models/       # SQLAlchemy models
│   │   ├── config.py
│   │   └── __init__.py
│   ├── requirements.txt
│   ├── Procfile          # Render gunicorn config
│   ├── render.yaml       # Render service definition
│   ├── runtime.txt       # Python version
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── pages/        # Dashboard, UploadResume, Roadmap, Quiz, Progress
│   │   ├── services/     # Axios API client
│   │   ├── App.jsx
│   │   └── index.css
│   ├── vercel.json       # Vercel SPA routing config
│   ├── .env              # Local env (not committed)
│   └── vite.config.js
└── .gitignore
```

---

## 🔑 Environment Variables Reference

### Backend (`.env`)
```env
GEMINI_API_KEY=your_gemini_api_key
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///skillgap.db
FLASK_ENV=production
FRONTEND_URL=https://your-app.vercel.app
```

### Frontend (set in Vercel dashboard)
```env
VITE_API_URL=https://your-backend.onrender.com
```

---

## 📝 License

MIT © 2026 SkillGap.AI
