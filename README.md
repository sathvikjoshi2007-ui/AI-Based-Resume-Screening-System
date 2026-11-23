# AI-Based Resume Screening System

> **A 2nd Year CSE AI Project** | Built with React.js, Python Flask, NLTK & scikit-learn

---

## 📋 Project Overview

An AI-powered web application that automatically screens and ranks resumes against a job description using Natural Language Processing (NLP). Recruiters can upload multiple PDF/DOCX resumes, enter job requirements, and instantly receive ranked candidates with detailed match analysis.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📄 Resume Upload | Upload multiple PDF/DOCX files with drag & drop |
| 🧠 AI Analysis | TF-IDF + Cosine Similarity based text matching |
| 📊 Match Score | 0–100% compatibility score per candidate |
| 🏆 Candidate Ranking | Auto-ranked from highest to lowest match |
| 💡 Skill Analysis | Matched skills, missing skills, and gap analysis |
| 💪 Insights | Strengths, weaknesses, and improvement suggestions |
| 📥 PDF Reports | Download professional analysis reports |
| 🗄️ History | SQLite database stores all screening sessions |
| 📱 Responsive | Works on desktop, tablet, and mobile |

---

## 🛠️ Technology Stack

**Frontend:**
- React.js 18 (via CDN — no npm needed!)
- Tailwind CSS (via CDN)
- Chart.js for visualizations

**Backend:**
- Python 3.x + Flask (REST API)
- Flask-CORS (cross-origin support)

**AI / NLP:**
- NLTK (tokenization, stopwords, lemmatization)
- scikit-learn (TF-IDF Vectorizer, Cosine Similarity)

**Resume Parsing:**
- `pdfplumber` (primary PDF parser)
- `PyPDF2` (fallback PDF parser)
- `python-docx` (DOCX parser)

**Database:**
- SQLite (built into Python, no installation needed)

**Report Generation:**
- ReportLab (PDF generation)

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- A modern web browser (Chrome, Firefox, Edge)

### Step 1: Clone / Download the Project
```
# If using git:
git clone <repository-url>
cd "Vise copy (2)"

# Or just download and extract the ZIP
```

### Step 2: Install Python Dependencies
```bash
python -m pip install -r requirements.txt
```

### Step 3: Start the Backend Server
```bash
python backend/app.py
```

You should see:
```
============================================================
  AI Resume Screening System - Backend Server
============================================================
  PDF Library: pdfplumber
  DOCX Support: True
  NLTK Available: True
  Report Generation: True
  Database: .../backend/resume_screening.db
============================================================
  Server running at: http://localhost:5000
  Frontend at:       http://localhost:5000
============================================================
```

### Step 4: Open the Application
Open your web browser and go to:

**→ http://localhost:5000**

That's it! The frontend is served by Flask itself — no separate frontend server needed.

---

## 📂 Project Structure

```
Vise copy (2)/
├── backend/
│   ├── app.py              # Main Flask application (all API endpoints)
│   ├── uploads/            # Temporary storage for uploaded resumes
│   ├── reports/            # Generated PDF reports
│   └── resume_screening.db # SQLite database (auto-created)
├── frontend/
│   └── index.html          # Complete React frontend (single file)
├── sample_data/            # Sample resumes and JDs for demo
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serves the frontend |
| `GET` | `/api/health` | Health check |
| `POST` | `/api/analyze` | Main analysis endpoint |
| `GET` | `/api/report/<id>` | Download PDF report |
| `GET` | `/api/sessions` | Get past sessions |
| `GET` | `/api/sample-data` | Get sample JDs |

### POST /api/analyze
**Request:** `multipart/form-data`
- `files[]` — Resume files (PDF/DOCX)
- `job_description` — Job description text
- `job_title` — Job title (optional)

**Response:**
```json
{
  "success": true,
  "session_id": "abc123",
  "job_title": "Software Engineer",
  "job_skills": ["Python", "React", "SQL"],
  "total_candidates": 3,
  "results": [
    {
      "rank": 1,
      "candidate_name": "John Doe",
      "match_score": 82.5,
      "matched_skills": ["Python", "React"],
      "missing_skills": ["Docker"],
      "strengths": ["..."],
      "weaknesses": ["..."],
      "suggestions": ["..."]
    }
  ]
}
```

---

## 🧮 How the AI Scoring Works

The match score is calculated using a **weighted combination** of four factors:

```
Final Score = (TF-IDF Similarity × 0.40) +
              (Skill Match Rate × 0.40) +
              (Education Match × 0.10) +
              (Experience Match × 0.10)
```

| Component | Weight | Method |
|-----------|--------|--------|
| TF-IDF Cosine Similarity | 40% | Converts text to vectors, measures angle between them |
| Skill Match Rate | 40% | Checks overlap of 80+ skills from curated list |
| Education Level | 10% | Compares detected education level |
| Experience Years | 10% | Compares years of experience |

### Score Interpretation
| Score | Label | Recommendation |
|-------|-------|----------------|
| 85–100% | Excellent Match | Highly recommended for interview |
| 70–84% | Good Match | Strong candidate |
| 55–69% | Fair Match | Worth further evaluation |
| 40–54% | Partial Match | Significant skill gaps |
| 0–39% | Low Match | Does not meet requirements |

---

## 🎯 For Your Presentation

### Key Points to Explain:

1. **Why NLP?** Traditional keyword matching misses context. NLP understands meaning.

2. **Why TF-IDF?** It weights words by importance — common words like "the" count less.

3. **Why Cosine Similarity?** It measures direction (meaning) of text, not just length.

4. **Why weighted scoring?** Different factors have different importance for job matching.

5. **Why SQLite?** Lightweight, serverless database perfect for local projects.

### Demo Flow:
1. Open http://localhost:5000 → Show the home page
2. Click "Get Started" → Upload a sample resume PDF
3. Load a Sample JD or paste your own
4. Click "Analyze" → Show the loading state
5. Navigate to Results → Show the ranked table and score breakdown
6. Click "View" on a candidate → Show the detailed modal with tabs
7. Download a PDF report
8. Show the History page

---

## ⚠️ Important Disclaimer

This system is for **educational purposes only**. The AI scores assist the screening process but should **not** be the sole basis for hiring decisions. Protected personal attributes (gender, age, race, religion, etc.) are **not** used in ranking. All final decisions must be reviewed by qualified human professionals.

---

## 🐛 Troubleshooting

**Q: "Could not connect to backend server"**
- Make sure `python backend/app.py` is running
- Check that port 5000 is not blocked

**Q: "Could not extract text from PDF"**
- The PDF might be image-scanned (not text-based)
- Try a different PDF or convert to DOCX

**Q: "Report download failed"**
- Run: `python -m pip install reportlab`

**Q: NLTK data download fails**
- Run manually: `python -c "import nltk; nltk.download('all')"`

---

*Built as a 2nd Year Computer Science Engineering AI Project*
