"""
AI-Based Resume Screening System - Backend
==========================================
This is the main Flask application that handles:
- File uploads (PDF/DOCX resumes)
- Text extraction from resumes
- NLP-based resume analysis
- Job description matching using TF-IDF and cosine similarity
- Score calculation and report generation
- SQLite database for storing results

Technology: Python Flask, spaCy, NLTK, scikit-learn, SQLite
"""

import os
import re
import json
import sqlite3
import hashlib
import datetime
import traceback
from io import BytesIO
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

# ─── NLP & ML Libraries ───────────────────────────────────────────────────────
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ─── PDF / DOCX Parsing ───────────────────────────────────────────────────────
try:
    import pdfplumber          # Primary PDF extractor (better than PyPDF2)
    PDF_LIBRARY = "pdfplumber"
except ImportError:
    try:
        import PyPDF2          # Fallback PDF extractor
        PDF_LIBRARY = "PyPDF2"
    except ImportError:
        PDF_LIBRARY = None

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# ─── Report Generation ────────────────────────────────────────────────────────
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# ─── App Configuration ────────────────────────────────────────────────────────
app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app, resources={r"/*": {"origins": "*"}})

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
REPORTS_FOLDER = os.path.join(os.path.dirname(__file__), 'reports')
DATABASE = os.path.join(os.path.dirname(__file__), 'resume_screening.db')

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORTS_FOLDER, exist_ok=True)

# ─── Download NLTK Data ───────────────────────────────────────────────────────
def download_nltk_data():
    """Download required NLTK datasets silently."""
    packages = ['punkt', 'stopwords', 'wordnet', 'averaged_perceptron_tagger', 'punkt_tab']
    for pkg in packages:
        try:
            nltk.download(pkg, quiet=True)
        except Exception:
            pass

download_nltk_data()

try:
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    from nltk.stem import WordNetLemmatizer
    STOP_WORDS = set(stopwords.words('english'))
    LEMMATIZER = WordNetLemmatizer()
    NLTK_AVAILABLE = True
except Exception:
    STOP_WORDS = set()
    LEMMATIZER = None
    NLTK_AVAILABLE = False

# ─── Database Setup ───────────────────────────────────────────────────────────
def init_db():
    """Create the SQLite database tables if they don't exist."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Table to store screening sessions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS screening_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            job_title TEXT,
            job_description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table to store individual candidate results
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidate_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            candidate_name TEXT,
            filename TEXT,
            match_score REAL,
            matched_skills TEXT,       -- JSON array
            missing_skills TEXT,       -- JSON array
            strengths TEXT,            -- JSON array
            weaknesses TEXT,           -- JSON array
            suggestions TEXT,          -- JSON array
            education TEXT,            -- JSON array
            experience_years REAL,
            extracted_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES screening_sessions(session_id)
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# ─── Helper: Allowed File Check ───────────────────────────────────────────────
def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ─── Text Extraction Functions ────────────────────────────────────────────────
def extract_text_from_pdf(filepath):
    """
    Extract plain text from a PDF file.
    Uses pdfplumber (preferred) or PyPDF2 as fallback.
    """
    text = ""
    if PDF_LIBRARY == "pdfplumber":
        try:
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"pdfplumber error: {e}")
    elif PDF_LIBRARY == "PyPDF2":
        try:
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"PyPDF2 error: {e}")
    return text.strip()

def extract_text_from_docx(filepath):
    """Extract plain text from a DOCX file."""
    if not DOCX_AVAILABLE:
        return ""
    try:
        doc = DocxDocument(filepath)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n".join(paragraphs)
    except Exception as e:
        print(f"DOCX extraction error: {e}")
        return ""

def extract_text(filepath):
    """Auto-detect file type and extract text accordingly."""
    ext = filepath.rsplit('.', 1)[1].lower()
    if ext == 'pdf':
        return extract_text_from_pdf(filepath)
    elif ext in ['docx', 'doc']:
        return extract_text_from_docx(filepath)
    return ""

# ─── NLP Analysis Functions ───────────────────────────────────────────────────

# A comprehensive list of technical skills commonly found in resumes
TECH_SKILLS = [
    # Programming Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "c", "ruby", "go",
    "rust", "swift", "kotlin", "php", "scala", "r", "matlab", "perl", "dart",
    # Web Technologies
    "html", "css", "react", "angular", "vue", "node.js", "nodejs", "express",
    "django", "flask", "spring", "bootstrap", "tailwind", "jquery", "next.js",
    "nuxt", "gatsby", "redux", "graphql", "rest api", "restful",
    # Databases
    "sql", "mysql", "postgresql", "sqlite", "mongodb", "redis", "elasticsearch",
    "oracle", "cassandra", "dynamodb", "firebase",
    # Cloud & DevOps
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "jenkins",
    "git", "github", "gitlab", "ci/cd", "terraform", "ansible", "linux", "unix",
    # AI/ML
    "machine learning", "deep learning", "neural networks", "tensorflow", "pytorch",
    "keras", "scikit-learn", "nlp", "computer vision", "data science", "pandas",
    "numpy", "matplotlib", "seaborn", "opencv", "huggingface", "llm",
    # Other Tools
    "agile", "scrum", "jira", "figma", "postman", "excel", "tableau", "power bi",
    "android", "ios", "flutter", "react native", "unity", "blockchain",
    # Soft Skills (also important)
    "leadership", "teamwork", "communication", "problem solving", "critical thinking",
    "project management", "time management", "collaboration"
]

# Education levels for detection
EDUCATION_KEYWORDS = {
    "phd": 5, "doctorate": 5, "ph.d": 5,
    "master": 4, "mtech": 4, "mba": 4, "m.tech": 4, "m.sc": 4, "msc": 4,
    "bachelor": 3, "btech": 3, "b.tech": 3, "b.sc": 3, "bsc": 3, "be": 3,
    "associate": 2, "diploma": 2,
    "high school": 1, "12th": 1, "secondary": 1
}

def preprocess_text(text):
    """
    Clean and normalize text for NLP processing.
    Steps: lowercase → remove special chars → tokenize → remove stopwords → lemmatize
    """
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s\.\+\#]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    if NLTK_AVAILABLE:
        try:
            tokens = word_tokenize(text)
            tokens = [LEMMATIZER.lemmatize(t) for t in tokens if t not in STOP_WORDS and len(t) > 2]
            return ' '.join(tokens)
        except Exception:
            pass
    return text

def extract_candidate_name(text):
    """
    Heuristic to extract the candidate's name from the resume.
    Usually the first line of a resume is the candidate's name.
    """
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    for line in lines[:5]:  # Check first 5 lines
        # A name typically: starts with capital, 2-4 words, no special chars
        words = line.split()
        if 2 <= len(words) <= 4:
            if all(w[0].isupper() for w in words if w):
                # Reject lines that look like headings
                headings = ['resume', 'curriculum', 'vitae', 'profile', 'summary', 'objective']
                if not any(h in line.lower() for h in headings):
                    return line
    return "Unknown Candidate"

def extract_skills(text):
    """
    Extract skills from resume text by matching against our skills list.
    Uses multi-word phrase matching for compound skills like 'machine learning'.
    """
    text_lower = text.lower()
    found_skills = []
    for skill in TECH_SKILLS:
        # Use word boundary matching for single words, substring for phrases
        if ' ' in skill:
            if skill in text_lower:
                found_skills.append(skill.title())
        else:
            # Match whole word (not part of another word)
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.append(skill.upper() if len(skill) <= 4 else skill.title())
    return list(set(found_skills))  # Remove duplicates

def extract_education(text):
    """Extract education qualifications from resume text."""
    text_lower = text.lower()
    found_education = []
    highest_level = 0

    for keyword, level in EDUCATION_KEYWORDS.items():
        if keyword in text_lower:
            if level > highest_level:
                highest_level = level
            # Try to get the full degree name from the line containing the keyword
            for line in text.split('\n'):
                if keyword in line.lower() and len(line.strip()) < 150:
                    if line.strip() not in found_education:
                        found_education.append(line.strip())

    return found_education[:5], highest_level  # Return max 5 entries

def extract_experience_years(text):
    """
    Extract years of experience from resume text using regex patterns.
    Looks for patterns like '3 years', '5+ years', '2-3 years' etc.
    """
    text_lower = text.lower()
    patterns = [
        r'(\d+)\+?\s*years?\s+of\s+experience',
        r'(\d+)\+?\s*years?\s+experience',
        r'experience\s+of\s+(\d+)\+?\s*years?',
        r'(\d+)\+?\s*yrs?\s+of\s+exp',
        r'(\d+)\+?\s*years?\s+in\s+(?:the\s+)?(?:field|industry|domain)',
    ]
    max_years = 0
    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            years = float(match) if isinstance(match, str) else 0
            max_years = max(max_years, years)
    return max_years

def calculate_match_score(resume_text, job_description, resume_skills, job_skills):
    """
    Calculate the overall match score between a resume and job description.
    
    Uses a weighted combination of:
    1. TF-IDF Cosine Similarity (40%) - Overall text similarity
    2. Skill Match Ratio (40%) - Percentage of required skills found
    3. Education Level Match (10%) - Education qualification alignment
    4. Experience Match (10%) - Years of experience alignment
    
    Returns a score between 0 and 100.
    """
    scores = {}

    # ── 1. TF-IDF Cosine Similarity ──────────────────────────────────────────
    try:
        processed_resume = preprocess_text(resume_text)
        processed_jd = preprocess_text(job_description)

        vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform([processed_resume, processed_jd])
        cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        scores['tfidf'] = float(cosine_sim) * 100
    except Exception as e:
        print(f"TF-IDF error: {e}")
        scores['tfidf'] = 0

    # ── 2. Skill Match Score ──────────────────────────────────────────────────
    if job_skills:
        # Normalize skill names for comparison
        resume_skills_lower = {s.lower() for s in resume_skills}
        job_skills_lower = {s.lower() for s in job_skills}
        matched = resume_skills_lower.intersection(job_skills_lower)
        scores['skill_match'] = (len(matched) / len(job_skills_lower)) * 100
    else:
        scores['skill_match'] = scores['tfidf']  # Fallback if no skills extracted

    # ── 3. Education Score ────────────────────────────────────────────────────
    _, resume_edu_level = extract_education(resume_text)
    _, jd_edu_level = extract_education(job_description)

    if jd_edu_level > 0:
        edu_ratio = min(resume_edu_level / jd_edu_level, 1.0)
        scores['education'] = edu_ratio * 100
    else:
        scores['education'] = 70  # Neutral score if JD doesn't mention education

    # ── 4. Experience Score ───────────────────────────────────────────────────
    resume_exp = extract_experience_years(resume_text)
    jd_exp = extract_experience_years(job_description)

    if jd_exp > 0:
        exp_ratio = min(resume_exp / jd_exp, 1.0)
        scores['experience'] = exp_ratio * 100
    else:
        scores['experience'] = 65  # Neutral score if JD doesn't specify years

    # ── Weighted Final Score ──────────────────────────────────────────────────
    final_score = (
        scores['tfidf'] * 0.40 +
        scores['skill_match'] * 0.40 +
        scores['education'] * 0.10 +
        scores['experience'] * 0.10
    )

    return round(min(max(final_score, 0), 100), 1), scores

def generate_strengths_weaknesses(resume_skills, job_skills, match_score, scores):
    """
    Generate human-readable strengths, weaknesses, and improvement suggestions
    based on the analysis results.
    """
    resume_skills_lower = {s.lower() for s in resume_skills}
    job_skills_lower = {s.lower() for s in job_skills}

    matched_skills = [s for s in resume_skills if s.lower() in job_skills_lower]
    missing_skills = [s for s in job_skills if s.lower() not in resume_skills_lower]

    strengths = []
    weaknesses = []
    suggestions = []

    # Strengths based on score components
    if scores.get('tfidf', 0) > 60:
        strengths.append("Strong overall alignment with the job description language and terminology")
    if scores.get('skill_match', 0) > 70:
        strengths.append(f"Excellent skill coverage — matches {len(matched_skills)} of the required skills")
    if scores.get('education', 0) >= 100:
        strengths.append("Meets or exceeds the educational qualification requirements")
    if scores.get('experience', 0) >= 100:
        strengths.append("Meets or exceeds the required years of experience")
    if len(resume_skills) > 10:
        strengths.append("Demonstrates a broad and diverse technical skill set")
    if match_score >= 75:
        strengths.append("High overall compatibility with the role requirements")
    if not strengths:
        strengths.append("Has relevant background that could be applicable to the role")

    # Weaknesses
    if scores.get('skill_match', 0) < 50:
        weaknesses.append(f"Missing {len(missing_skills)} key skills required by the job description")
    if scores.get('tfidf', 0) < 40:
        weaknesses.append("Resume content doesn't closely align with job description language")
    if scores.get('education', 0) < 70:
        weaknesses.append("May not fully meet the educational requirements specified")
    if scores.get('experience', 0) < 50:
        weaknesses.append("Years of experience may fall short of the job requirements")
    if len(resume_skills) < 5:
        weaknesses.append("Limited number of technical skills highlighted in the resume")
    if not weaknesses:
        weaknesses.append("Few significant gaps identified relative to the job requirements")

    # Improvement suggestions
    if missing_skills:
        top_missing = missing_skills[:3]
        suggestions.append(f"Focus on acquiring: {', '.join(top_missing)} to strengthen your candidacy")
    if scores.get('tfidf', 0) < 60:
        suggestions.append("Tailor your resume language to better match the job description keywords")
    if scores.get('experience', 0) < 70:
        suggestions.append("Highlight project experience, internships, or freelance work to demonstrate practical skills")
    suggestions.append("Quantify your achievements with numbers (e.g., 'Improved performance by 30%')")
    suggestions.append("Use action verbs to describe your contributions (e.g., Developed, Led, Implemented)")
    if len(resume_skills) < 8:
        suggestions.append("Consider adding a dedicated 'Skills' section to make your competencies more visible")

    return matched_skills, missing_skills, strengths[:4], weaknesses[:4], suggestions[:5]

# ─── API Routes ───────────────────────────────────────────────────────────────

@app.route('/')
def serve_frontend():
    """Serve the frontend HTML file."""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """API health check endpoint."""
    return jsonify({
        "status": "ok",
        "message": "AI Resume Screening API is running",
        "pdf_library": PDF_LIBRARY,
        "docx_available": DOCX_AVAILABLE,
        "nltk_available": NLTK_AVAILABLE,
        "reportlab_available": REPORTLAB_AVAILABLE
    })

@app.route('/api/analyze', methods=['POST'])
def analyze_resumes():
    """
    Main endpoint: Accept one or more resume files + job description,
    extract text, run NLP analysis, and return ranked results.
    
    Request: multipart/form-data
        - files[]: List of resume files (PDF/DOCX)
        - job_description: Text of the job description
        - job_title: (Optional) Title of the job position
    
    Response: JSON with ranked candidate results
    """
    try:
        # ── Validate input ────────────────────────────────────────────────────
        if 'files' not in request.files:
            return jsonify({"error": "No files uploaded. Please upload at least one resume."}), 400

        files = request.files.getlist('files')
        job_description = request.form.get('job_description', '').strip()
        job_title = request.form.get('job_title', 'Software Engineer').strip()

        if not files or all(f.filename == '' for f in files):
            return jsonify({"error": "No files selected."}), 400

        if not job_description or len(job_description) < 50:
            return jsonify({"error": "Please provide a detailed job description (at least 50 characters)."}), 400

        # ── Extract skills from job description ───────────────────────────────
        job_skills = extract_skills(job_description)

        # ── Create a session ID for this screening batch ──────────────────────
        session_id = hashlib.md5(
            (job_description[:100] + datetime.datetime.now().isoformat()).encode()
        ).hexdigest()[:12]

        # Save the session to database
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO screening_sessions (session_id, job_title, job_description) VALUES (?, ?, ?)',
            (session_id, job_title, job_description)
        )
        conn.commit()

        # ── Process each resume file ──────────────────────────────────────────
        results = []
        errors = []

        for file in files:
            if file.filename == '':
                continue

            if not allowed_file(file.filename):
                errors.append(f"'{file.filename}' is not a supported format (PDF/DOCX only).")
                continue

            try:
                filename = secure_filename(file.filename)
                # Add session prefix to avoid filename collisions
                saved_filename = f"{session_id}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
                file.save(filepath)

                # ── Extract text ──────────────────────────────────────────────
                resume_text = extract_text(filepath)

                if not resume_text or len(resume_text) < 50:
                    errors.append(f"Could not extract text from '{filename}'. File may be image-based or corrupted.")
                    continue

                # ── NLP Analysis ──────────────────────────────────────────────
                candidate_name = extract_candidate_name(resume_text)
                resume_skills = extract_skills(resume_text)
                education_list, _ = extract_education(resume_text)
                experience_years = extract_experience_years(resume_text)

                # ── Calculate Match Score ─────────────────────────────────────
                match_score, score_breakdown = calculate_match_score(
                    resume_text, job_description, resume_skills, job_skills
                )

                # ── Generate Insights ─────────────────────────────────────────
                matched_skills, missing_skills, strengths, weaknesses, suggestions = generate_strengths_weaknesses(
                    resume_skills, job_skills, match_score, score_breakdown
                )

                # ── Save to Database ──────────────────────────────────────────
                cursor.execute('''
                    INSERT INTO candidate_results
                    (session_id, candidate_name, filename, match_score, matched_skills,
                     missing_skills, strengths, weaknesses, suggestions, education,
                     experience_years, extracted_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session_id, candidate_name, filename, match_score,
                    json.dumps(matched_skills), json.dumps(missing_skills),
                    json.dumps(strengths), json.dumps(weaknesses),
                    json.dumps(suggestions), json.dumps(education_list),
                    experience_years, resume_text[:5000]  # Store first 5000 chars
                ))
                conn.commit()
                candidate_id = cursor.lastrowid

                results.append({
                    "id": candidate_id,
                    "candidate_name": candidate_name,
                    "filename": filename,
                    "match_score": match_score,
                    "score_breakdown": score_breakdown,
                    "matched_skills": matched_skills,
                    "missing_skills": missing_skills[:10],
                    "strengths": strengths,
                    "weaknesses": weaknesses,
                    "suggestions": suggestions,
                    "education": education_list,
                    "experience_years": experience_years,
                    "total_skills_found": len(resume_skills),
                    "session_id": session_id
                })

            except Exception as e:
                print(f"Error processing {file.filename}: {traceback.format_exc()}")
                errors.append(f"Error processing '{file.filename}': {str(e)}")

        conn.close()

        if not results:
            return jsonify({
                "error": "Could not process any of the uploaded files.",
                "details": errors
            }), 400

        # ── Sort results by match score (highest first) ───────────────────────
        results.sort(key=lambda x: x['match_score'], reverse=True)

        # Add rank to each result
        for i, r in enumerate(results):
            r['rank'] = i + 1

        return jsonify({
            "success": True,
            "session_id": session_id,
            "job_title": job_title,
            "job_skills": job_skills,
            "total_candidates": len(results),
            "results": results,
            "errors": errors
        })

    except Exception as e:
        print(f"Unexpected error in /api/analyze: {traceback.format_exc()}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route('/api/report/<int:candidate_id>', methods=['GET'])
def download_report(candidate_id):
    """
    Generate and download a PDF report for a specific candidate.
    Uses ReportLab to create a professional PDF.
    """
    if not REPORTLAB_AVAILABLE:
        return jsonify({"error": "Report generation is not available (reportlab not installed)."}), 503

    try:
        # Fetch candidate data from database
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM candidate_results WHERE id = ?', (candidate_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({"error": "Candidate not found."}), 404

        # Build data dict from row
        columns = [desc[0] for desc in cursor.description]
        candidate = dict(zip(columns, row))
        candidate['matched_skills'] = json.loads(candidate.get('matched_skills', '[]'))
        candidate['missing_skills'] = json.loads(candidate.get('missing_skills', '[]'))
        candidate['strengths'] = json.loads(candidate.get('strengths', '[]'))
        candidate['weaknesses'] = json.loads(candidate.get('weaknesses', '[]'))
        candidate['suggestions'] = json.loads(candidate.get('suggestions', '[]'))
        candidate['education'] = json.loads(candidate.get('education', '[]'))

        # ── Generate PDF ──────────────────────────────────────────────────────
        report_filename = f"report_{candidate_id}_{candidate['candidate_name'].replace(' ', '_')}.pdf"
        report_path = os.path.join(REPORTS_FOLDER, report_filename)

        doc = SimpleDocTemplate(
            report_path,
            pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm
        )

        styles = getSampleStyleSheet()
        story = []

        # Title style
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=22,
            textColor=colors.HexColor('#1e3a5f'),
            spaceAfter=6
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1e3a5f'),
            spaceBefore=12,
            spaceAfter=4
        )
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=4
        )

        # Header
        story.append(Paragraph("AI Resume Screening Report", title_style))
        story.append(Paragraph(f"Generated: {datetime.datetime.now().strftime('%B %d, %Y %H:%M')}", body_style))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1e3a5f')))
        story.append(Spacer(1, 12))

        # Candidate Info Table
        score = candidate['match_score']
        score_color = '#27ae60' if score >= 75 else '#f39c12' if score >= 50 else '#e74c3c'

        info_data = [
            ['Candidate Name', candidate['candidate_name']],
            ['Resume File', candidate['filename']],
            ['Match Score', f"{score}%"],
            ['Experience', f"{candidate['experience_years']} years" if candidate['experience_years'] else 'Not specified'],
        ]

        info_table = Table(info_data, colWidths=[5*cm, 12*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f4f8')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 16))

        # Skills sections
        def add_skills_section(title, skills, color):
            story.append(Paragraph(title, heading_style))
            if skills:
                skills_text = " • ".join(skills)
                story.append(Paragraph(skills_text, body_style))
            else:
                story.append(Paragraph("None identified", body_style))
            story.append(Spacer(1, 8))

        add_skills_section("✅ Matched Skills", candidate['matched_skills'], '#27ae60')
        add_skills_section("❌ Missing Skills", candidate['missing_skills'], '#e74c3c')

        # Strengths
        story.append(Paragraph("💪 Strengths", heading_style))
        for s in candidate['strengths']:
            story.append(Paragraph(f"• {s}", body_style))
        story.append(Spacer(1, 8))

        # Weaknesses
        story.append(Paragraph("⚠️ Areas for Improvement", heading_style))
        for w in candidate['weaknesses']:
            story.append(Paragraph(f"• {w}", body_style))
        story.append(Spacer(1, 8))

        # Suggestions
        story.append(Paragraph("💡 Recommendations", heading_style))
        for s in candidate['suggestions']:
            story.append(Paragraph(f"• {s}", body_style))

        # Footer
        story.append(Spacer(1, 20))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        story.append(Paragraph(
            "⚠️ Disclaimer: This report is generated by an AI system and is intended to assist in the screening process only. "
            "Final hiring decisions should be made by qualified human recruiters based on comprehensive evaluation.",
            ParagraphStyle('Disclaimer', parent=styles['Normal'], fontSize=8, textColor=colors.grey)
        ))

        doc.build(story)

        return send_file(
            report_path,
            as_attachment=True,
            download_name=report_filename,
            mimetype='application/pdf'
        )

    except Exception as e:
        print(f"Report generation error: {traceback.format_exc()}")
        return jsonify({"error": f"Could not generate report: {str(e)}"}), 500


@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """Get list of past screening sessions."""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.session_id, s.job_title, s.created_at,
                   COUNT(c.id) as candidate_count,
                   MAX(c.match_score) as top_score
            FROM screening_sessions s
            LEFT JOIN candidate_results c ON s.session_id = c.session_id
            GROUP BY s.session_id
            ORDER BY s.created_at DESC
            LIMIT 20
        ''')
        rows = cursor.fetchall()
        conn.close()

        sessions = []
        for row in rows:
            sessions.append({
                "session_id": row[0],
                "job_title": row[1],
                "created_at": row[2],
                "candidate_count": row[3],
                "top_score": row[4]
            })
        return jsonify({"sessions": sessions})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/sample-data', methods=['GET'])
def get_sample_data():
    """Return sample job descriptions and resume text for demo purposes."""
    samples = {
        "job_descriptions": [
            {
                "title": "Full Stack Developer",
                "description": """We are looking for a skilled Full Stack Developer with 2+ years of experience.

Requirements:
- Proficiency in Python, JavaScript, React.js, Node.js
- Experience with databases: SQL, MongoDB, PostgreSQL
- Knowledge of REST API design and development
- Familiarity with Docker, Git, and CI/CD pipelines
- Understanding of Agile/Scrum methodologies
- Strong problem-solving and communication skills
- Bachelor's degree in Computer Science or related field

Responsibilities:
- Develop and maintain web applications using React and Flask/Django
- Design and implement RESTful APIs
- Write clean, well-documented code
- Collaborate with cross-functional teams
- Participate in code reviews"""
            },
            {
                "title": "Data Scientist / ML Engineer",
                "description": """Seeking a passionate Data Scientist with 1+ years of experience in machine learning.

Required Skills:
- Python programming (pandas, numpy, scikit-learn)
- Machine learning algorithms and deep learning
- TensorFlow or PyTorch experience
- Statistical analysis and data visualization (matplotlib, seaborn)
- SQL for data querying
- Experience with NLP or computer vision is a plus
- Strong mathematical background (statistics, linear algebra)

Education: Bachelor's or Master's degree in Computer Science, Statistics, or related field."""
            },
            {
                "title": "Frontend Developer",
                "description": """Looking for a creative Frontend Developer to join our team.

Skills Required:
- HTML5, CSS3, JavaScript (ES6+)
- React.js or Angular or Vue.js
- Responsive design and Bootstrap / Tailwind CSS
- RESTful API integration
- Git version control
- UI/UX sensibility and attention to detail
- Knowledge of TypeScript is a plus

Experience: 1-3 years in frontend development."""
            }
        ]
    }
    return jsonify(samples)


# ─── Run Application ──────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 60)
    print("  AI Resume Screening System - Backend Server")
    print("=" * 60)
    print(f"  PDF Library: {PDF_LIBRARY}")
    print(f"  DOCX Support: {DOCX_AVAILABLE}")
    print(f"  NLTK Available: {NLTK_AVAILABLE}")
    print(f"  Report Generation: {REPORTLAB_AVAILABLE}")
    print(f"  Database: {DATABASE}")
    print("=" * 60)
    print("  Server running at: http://localhost:5000")
    print("  Frontend at:       http://localhost:5000")
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=5000)
