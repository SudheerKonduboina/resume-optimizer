# ATS Resume Optimizer (Open-Source)

An AI-powered **ATS Resume Analyzer & Optimizer** built using **FastAPI**, **Next.js**, and **open-source NLP models**.  
This tool evaluates resumes against job descriptions to improve **ATS compatibility**, **keyword alignment**, **semantic relevance**, and **formatting quality**.

> Built as a startup-grade project with full backend, frontend, testing, Dockerization, and CI-ready architecture.

---

## 🚀 Features

- Upload resume (**PDF / DOCX**, max 10MB)
- Optional job description comparison
- AI-based keyword gap analysis
- Semantic similarity using embeddings
- Formatting & structure checks
- Score breakdown:
  - Keywords
  - Semantic relevance
  - Formatting
  - Content
- Actionable optimization suggestions
- Downloadable **PDF report**
- Rate limited: **5 analyses/day/IP**
- Mobile-responsive frontend
- Fully open-source stack (no paid APIs)

---

## 🧱 Tech Stack

### Frontend
- Next.js 14
- Tailwind CSS
- Fetch API
- Responsive UI

### Backend
- FastAPI
- Uvicorn
- Pydantic v2
- SlowAPI (rate limiting)

### AI / NLP
- spaCy (tokenization & linguistic processing)
- Sentence-Transformers (semantic similarity)
- KeyBERT (keyword extraction)
- scikit-learn (vector similarity)
- PyMuPDF & python-docx (resume parsing)

### Infrastructure
- Docker
- Docker Compose
- Pytest
- GitHub-ready CI structure

---

## 🗂 Project Structure

```text
resume-optimizer/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core.py
│   │   ├── models.py
│   │   ├── services/
│   │   │   ├── parse.py
│   │   │   ├── keywords.py
│   │   │   ├── scoring.py
│   │   │   ├── report.py
│   │   │   └── report_pdf.py
│   │   └── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── pages/
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml
└── README.md


### ⚙️ Environment Requirements
- Docker Desktop (Windows / Mac / Linux)
- Node.js 18+ (for local frontend development)
- Python 3.11 (for local backend development)
- Internet access (for model downloads)

# 🐳 Docker Setup (Recommended)

## 1️⃣ Build & Run

docker compose up --build

## 2️⃣ Verify Services

- Frontend → http://localhost:3000
- Backend API → http://localhost:8000
- API Docs → http://localhost:8000/docs
- Health Check → http://localhost:8000/health

# 🔌 Backend API Endpoints

 --------------------------------------------------------------------- 
| Method | Endpoint                 | Description                     |
| ------ | ------------------------ | ------------------------------- |
| GET    | `/`                      | Service info                    |
| GET    | `/health`                | Health check                    |
| POST   | `/api/analyze`           | Upload resume + job description |
| GET    | `/api/status/{job_id}`   | Job progress                    |
| GET    | `/api/result/{job_id}`   | Analysis result                 |
| GET    | `/api/download/{job_id}` | Download PDF report             |
 --------------------------------------------------------------------- 

# 🧪 Testing

All backend flows are covered using pytest.

## Run tests

cd backend
pytest -v


cd backend
pytest -v

## Covered Tests

- ✔ Resume analyze flow
- ✔ Status polling
- ✔ Result retrieval
- ✔ PDF download
- ✔ Health endpoint


# 🔒 Rate Limiting

- Production: 5 analyses/day/IP
- Development: Unlimited

# 📦 Deployment Ready

- Dockerized backend & frontend
- Stateless backend design
- No vendor lock-in
- Fully open-source compliant
- CI/CD friendly

#📜 License

- MIT License
- Free to use, modify, and deploy.

# 👤 Author

Sudheer Konduboina