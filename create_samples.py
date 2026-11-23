"""
Create sample resume PDF/DOCX files for demonstration purposes.
Run this script to generate sample files in the sample_data/ folder.

Usage: python create_samples.py
"""

import os
import sys

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), 'sample_data')
os.makedirs(SAMPLE_DIR, exist_ok=True)

# ── Sample Resume Content ─────────────────────────────────────────────────────

RESUME_1 = """Priya Sharma
priya.sharma@email.com | +91-9876543210 | LinkedIn: /in/priyasharma | GitHub: github.com/priyasharma

OBJECTIVE
Motivated Computer Science student with strong programming skills seeking a Full Stack Developer position.

EDUCATION
Bachelor of Technology in Computer Science Engineering
ABC University, Hyderabad | 2021–2025 | CGPA: 8.6/10

TECHNICAL SKILLS
Programming Languages: Python, JavaScript, Java, C++
Web Technologies: React.js, Node.js, HTML5, CSS3, Bootstrap, Tailwind CSS
Backend Frameworks: Flask, Django, Express.js
Databases: MySQL, MongoDB, SQLite, PostgreSQL
Cloud & DevOps: Git, GitHub, Docker (basic), AWS (basic)
AI/ML: Machine Learning, scikit-learn, pandas, numpy, TensorFlow (basic)
Other: REST API, Agile, Scrum, Jira

EXPERIENCE
Software Development Intern | TechSolutions Pvt. Ltd., Hyderabad | June 2024 – Aug 2024 (3 months)
- Developed a React.js dashboard for real-time sales analytics, reducing report generation time by 40%
- Built RESTful APIs using Flask and Python, integrated with PostgreSQL database
- Implemented user authentication using JWT tokens
- Collaborated with a 5-member team using Agile/Scrum methodology

Web Development Intern | StartupXYZ | Jan 2024 – March 2024 (2 months)
- Created responsive web pages using HTML, CSS, JavaScript and Bootstrap
- Integrated REST APIs and handled AJAX requests

PROJECTS
1. AI-Based Resume Screening System (Python, Flask, React.js, NLP)
   - Built a full-stack web app to screen resumes using TF-IDF and cosine similarity
   - Achieved 85% accuracy in matching candidates to job descriptions

2. E-Commerce Platform (React.js, Node.js, MongoDB)
   - Developed a full-stack e-commerce website with cart, payment, and admin panel
   - Deployed on AWS EC2 with CI/CD pipeline using GitHub Actions

3. COVID-19 Data Dashboard (Python, Tableau, pandas)
   - Visualized global COVID data with interactive charts using Tableau

CERTIFICATIONS
- AWS Cloud Practitioner (2024)
- Python for Data Science – Coursera (2023)
- Full Stack Web Development – Udemy (2023)

ACHIEVEMENTS
- Winner – National Level Hackathon 2024 (Team of 4)
- Google Developer Student Club Lead – 2023-24
- Published research paper on NLP in IEEE conference

LANGUAGES
English (Fluent), Telugu (Native), Hindi (Conversational)
"""

RESUME_2 = """Rahul Verma
rahul.verma@email.com | +91-9123456789 | Portfolio: rahulverma.dev

PROFILE
A data science enthusiast with hands-on experience in machine learning, deep learning, and data analysis.
Looking for a Data Scientist / ML Engineer role to apply my skills.

EDUCATION
Bachelor of Science in Computer Science
XYZ College of Engineering, Pune | 2022–2026 | GPA: 7.8/10

SKILLS
Languages: Python, R, SQL, MATLAB
ML/AI: Machine Learning, Deep Learning, Neural Networks, NLP, Computer Vision
Libraries: pandas, numpy, scikit-learn, TensorFlow, PyTorch, Keras, matplotlib, seaborn, OpenCV
Data Tools: Jupyter Notebook, Google Colab, Tableau, Power BI
Database: MySQL, MongoDB
Version Control: Git, GitHub
Cloud: Google Cloud (basic), AWS (basic)

INTERNSHIP
Data Science Intern | Analytics Corp., Mumbai | May 2024 – July 2024
- Built a customer churn prediction model using Random Forest achieving 89% accuracy
- Performed EDA on 500,000+ records using pandas and matplotlib
- Created interactive dashboards in Tableau for business stakeholders
- Used SQL to extract and transform data from MySQL database

PROJECTS
1. Sentiment Analysis System (Python, NLP, NLTK, scikit-learn)
   - Analyzed 50,000 Twitter reviews using VADER and TextBlob
   - Achieved 91% accuracy using BERT fine-tuning

2. Object Detection for Autonomous Vehicles (Python, OpenCV, YOLOv5)
   - Real-time object detection achieving 30 FPS on video streams
   - Trained on custom dataset of 10,000 annotated images

3. Stock Price Prediction (Python, LSTM, TensorFlow)
   - Used LSTM neural networks to predict next-day closing prices
   - RMSE of 2.3 on test data

4. Customer Segmentation (Python, K-Means, pandas)
   - Segmented 100,000 customers using K-Means clustering
   - Identified 5 distinct customer personas for marketing

CERTIFICATIONS
- Deep Learning Specialization – Coursera (Andrew Ng) 2024
- Google Data Analytics Professional Certificate 2023
- Kaggle Machine Learning Certificate 2023

ACHIEVEMENTS
- Kaggle Expert (top 10% globally)
- 2nd Place – State Level Data Science Competition 2024
- Published ML research paper in Springer journal

LANGUAGES: English, Hindi, Marathi
"""

RESUME_3 = """Ananya Singh
ananya.singh@gmail.com | 9988776655

CAREER OBJECTIVE
Recent graduate seeking a software development opportunity. Good knowledge of Java and web technologies.

EDUCATION
B.Tech Computer Science | DEF Institute of Technology | 2020–2024
Percentage: 72%

12th Standard | Government Higher Secondary School | 2020
Percentage: 78%

SKILLS
- Java
- C language  
- HTML and CSS
- Basic JavaScript
- MySQL
- MS Office, Excel

MINI PROJECTS
Library Management System (Java, MySQL)
- Simple console application for adding and searching books

Student Result Portal (HTML, CSS, PHP, MySQL)
- Web form to store and display student marks

Personal Portfolio Website (HTML, CSS, JavaScript)
- Static website to showcase my skills and projects

INTERNSHIP
No formal internship experience.
Completed a 1-week online web development workshop.

HOBBIES
Reading books, Playing cricket, Listening to music

LANGUAGES
English, Hindi

REFERENCES
Available on request.
"""

def create_pdf_resumes():
    """Create sample resume PDFs using reportlab."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.units import cm

        resumes = [
            ('sample_resume_priya_sharma.pdf', RESUME_1, 'Priya Sharma – Full Stack Developer'),
            ('sample_resume_rahul_verma.pdf', RESUME_2, 'Rahul Verma – Data Scientist'),
            ('sample_resume_ananya_singh.pdf', RESUME_3, 'Ananya Singh – Junior Developer'),
        ]

        for filename, content, title in resumes:
            filepath = os.path.join(SAMPLE_DIR, filename)
            doc = SimpleDocTemplate(filepath, pagesize=A4,
                                    rightMargin=2*cm, leftMargin=2*cm,
                                    topMargin=2*cm, bottomMargin=2*cm)
            styles = getSampleStyleSheet()
            story = []

            # Simple monospace text paragraphs
            body_style = ParagraphStyle(
                'Body', parent=styles['Normal'],
                fontSize=9, fontName='Courier',
                spaceAfter=4, leading=12
            )

            for line in content.strip().split('\n'):
                if line.strip():
                    # Escape special XML characters
                    safe_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    story.append(Paragraph(safe_line, body_style))
                else:
                    story.append(Spacer(1, 6))

            doc.build(story)
            print(f"  ✅ Created: {filename}")

        return True
    except ImportError:
        print("  ⚠️  reportlab not found, creating text files instead...")
        return False

def create_text_resumes():
    """Fallback: create .txt files if reportlab unavailable."""
    resumes = [
        ('sample_resume_priya_sharma.txt', RESUME_1),
        ('sample_resume_rahul_verma.txt', RESUME_2),
        ('sample_resume_ananya_singh.txt', RESUME_3),
    ]
    for filename, content in resumes:
        filepath = os.path.join(SAMPLE_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ Created: {filename}")

def create_docx_resumes():
    """Create sample DOCX resume files."""
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor

        resumes = [
            ('sample_resume_priya_sharma.docx', RESUME_1, 'Priya Sharma'),
            ('sample_resume_rahul_verma.docx', RESUME_2, 'Rahul Verma'),
        ]

        for filename, content, name in resumes:
            filepath = os.path.join(SAMPLE_DIR, filename)
            doc = Document()

            # Add paragraphs
            for line in content.strip().split('\n'):
                p = doc.add_paragraph()
                run = p.add_run(line)
                run.font.size = Pt(10)
                # Bold the first line (name)
                if line == content.strip().split('\n')[0]:
                    run.font.bold = True
                    run.font.size = Pt(14)

            doc.save(filepath)
            print(f"  ✅ Created: {filename}")

        return True
    except ImportError:
        print("  ⚠️  python-docx not available for DOCX creation")
        return False

def create_sample_jds():
    """Create sample job description text files."""
    jds = {
        'sample_jd_full_stack.txt': """FULL STACK DEVELOPER – Job Description

We are looking for a skilled Full Stack Developer with 1-2 years of experience.

Required Skills:
- Python, JavaScript, React.js, Node.js
- Databases: SQL, MongoDB, PostgreSQL
- REST API design and development
- Docker, Git, CI/CD pipelines
- Agile/Scrum methodology
- Strong communication and teamwork

Nice to Have:
- AWS or Azure cloud experience
- TypeScript
- GraphQL

Education: Bachelor's degree in Computer Science or related field
Experience: 1-2 years (internships count)""",

        'sample_jd_data_scientist.txt': """DATA SCIENTIST – Job Description

We are hiring a Data Scientist to join our AI team.

Required:
- Python programming (pandas, numpy, scikit-learn)
- Machine learning algorithms
- Deep learning (TensorFlow or PyTorch)
- SQL for data querying
- Statistical analysis and visualization (matplotlib, seaborn)
- Experience with NLP or Computer Vision

Preferred:
- MLOps experience
- Cloud (GCP, AWS)
- Tableau or Power BI

Education: B.Tech/M.Tech Computer Science, Statistics, or Data Science
Experience: 0-2 years (freshers with strong projects welcome)"""
    }

    for filename, content in jds.items():
        filepath = os.path.join(SAMPLE_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ Created: {filename}")


if __name__ == '__main__':
    print("=" * 55)
    print("  Creating Sample Demo Data")
    print("=" * 55)

    print("\n📄 Creating PDF Resumes...")
    if not create_pdf_resumes():
        create_text_resumes()

    print("\n📝 Creating DOCX Resumes...")
    create_docx_resumes()

    print("\n📋 Creating Sample Job Descriptions...")
    create_sample_jds()

    print("\n" + "=" * 55)
    print(f"  ✅ All sample files saved to: {SAMPLE_DIR}")
    print("=" * 55)
    print("\nYou can now upload these files to test the application!")
