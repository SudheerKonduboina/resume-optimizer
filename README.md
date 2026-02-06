# Free ATS Resume Checker (Resume Optimizer)

A free ats resume checker tool that analyzes resumes for ATS compatibility and suggests keyword + formatting improvements.

## Tech
- Frontend: Next.js + Tailwind
- Backend: FastAPI
- AI/ML (open-source only): KeyBERT + SentenceTransformers (MiniLM)

## Run
### Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

### Frontend
cd frontend
npm i
npm run dev

## Features
- Upload PDF/DOCX (<=10MB)
- ATS score breakdown (keywords/formatting/content)
- Keyword gap + semantic matching vs JD (optional)
- Suggestions + downloadable HTML report
- 5/day per IP rate limit (in-memory demo)
