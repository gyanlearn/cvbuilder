from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import os
import tempfile
import json
from typing import Dict, List, Optional
import re
from datetime import datetime
import fitz  # PyMuPDF
import pdfplumber
from docx import Document
import google.generativeai as genai
from supabase import create_client, Client
from dotenv import load_dotenv
from pydantic import BaseModel
import email_validator
from dateutil import parser as date_parser
import logging
import time

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(
    title="CV Parser & ATS Scorer", 
    version="1.0.0",
    description="Production-ready CV parsing and ATS scoring API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"]  # In production, specify your domain
)

# CORS middleware with production settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://cv-parser-frontend.onrender.com",
        "http://localhost:3000",  # For development
        "https://localhost:3000"
    ],
    allow_credentials=False,  # Set to False for security
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    return response

# Initialize Supabase with error handling
try:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("Supabase credentials not found in environment variables")
        raise ValueError("Missing Supabase credentials")
    
    supabase: Client = create_client(supabase_url, supabase_key)
    logger.info("Supabase client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Supabase: {e}")
    supabase = None

# Initialize Gemini AI with error handling
try:
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    if not gemini_api_key:
        logger.error("Gemini API key not found in environment variables")
        raise ValueError("Missing Gemini API key")
    
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    logger.info("Gemini AI initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Gemini AI: {e}")
    model = None

class ResumeData(BaseModel):
    email: Optional[str] = None
    mobile: Optional[str] = None
    address: Optional[str] = None
    skills: List[str] = []
    experience: List[Dict] = []
    education: List[Dict] = []
    no_of_years_experience: Optional[int] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    summary: Optional[str] = None
    certifications: List[str] = []

class ATSResult(BaseModel):
    total_score: int
    breakdown: Dict[str, int]
    issues: List[Dict]
    recommendations: List[str]

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF using PyMuPDF and pdfplumber"""
    text = ""
    
    # Use PyMuPDF for general text extraction
    doc = fitz.open(file_path)
    for page in doc:
        text += page.get_text()
    doc.close()
    
    # Use pdfplumber for table extraction
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if row:
                        text += " " + " ".join([str(cell) if cell else "" for cell in row])
    
    return text

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file"""
    doc = Document(file_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def extract_text_from_txt(file_path: str) -> str:
    """Extract text from TXT file"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def parse_resume_text(text: str) -> ResumeData:
    """Parse resume text and extract structured data"""
    data = ResumeData()
    
    # Email extraction
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    if emails:
        data.email = emails[0]
    
    # Phone number extraction
    phone_pattern = r'(\+?1?[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
    phones = re.findall(phone_pattern, text)
    if phones:
        data.mobile = ''.join(phones[0])
    
    # LinkedIn extraction
    linkedin_pattern = r'linkedin\.com/in/[a-zA-Z0-9-]+'
    linkedin_matches = re.findall(linkedin_pattern, text)
    if linkedin_matches:
        data.linkedin = f"https://www.{linkedin_matches[0]}"
    
    # GitHub extraction
    github_pattern = r'github\.com/[a-zA-Z0-9-]+'
    github_matches = re.findall(github_pattern, text)
    if github_matches:
        data.github = f"https://www.{github_matches[0]}"
    
    # Skills extraction (common programming languages and tools)
    skills_keywords = [
        'python', 'javascript', 'java', 'c++', 'c#', 'php', 'ruby', 'go', 'rust',
        'react', 'angular', 'vue', 'node.js', 'django', 'flask', 'spring',
        'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'sql', 'mongodb',
        'redis', 'git', 'jenkins', 'agile', 'scrum', 'machine learning',
        'ai', 'data science', 'tableau', 'power bi', 'excel', 'word', 'powerpoint'
    ]
    
    text_lower = text.lower()
    for skill in skills_keywords:
        if skill in text_lower:
            data.skills.append(skill.title())
    
    # Experience extraction (basic pattern matching)
    experience_pattern = r'(\d{4})\s*[-–]\s*(\d{4}|present|current)'
    experience_matches = re.findall(experience_pattern, text, re.IGNORECASE)
    
    if experience_matches:
        data.no_of_years_experience = len(experience_matches)
    
    # Education extraction
    education_keywords = ['bachelor', 'master', 'phd', 'degree', 'university', 'college']
    for keyword in education_keywords:
        if keyword in text_lower:
            # Simple education detection
            data.education.append({"degree": keyword.title(), "institution": "Detected"})
            break
    
    return data

def calculate_ats_score(resume_data: ResumeData, original_text: str) -> ATSResult:
    """Calculate ATS score using rule-based system and LLM enhancement"""
    score = 0
    breakdown = {}
    issues = []
    recommendations = []
    
    # 1. Contact & Professional Info (15 pts)
    contact_score = 0
    if resume_data.email:
        try:
            email_validator.validate_email(resume_data.email)
            contact_score += 5
        except:
            issues.append({"priority": "high", "category": "contact", "message": "Invalid email format"})
    
    if resume_data.mobile:
        contact_score += 5
    else:
        issues.append({"priority": "high", "category": "contact", "message": "Missing phone number"})
    
    if resume_data.linkedin:
        contact_score += 5
    else:
        issues.append({"priority": "medium", "category": "contact", "message": "Missing LinkedIn profile"})
    
    breakdown["contact"] = contact_score
    score += contact_score
    
    # 2. Keywords & Skills Relevance (25 pts)
    skills_score = min(len(resume_data.skills) * 2, 25)
    breakdown["skills"] = skills_score
    score += skills_score
    
    if len(resume_data.skills) < 5:
        issues.append({"priority": "high", "category": "skills", "message": "Insufficient skills listed"})
    
    # 3. Education & Certifications (10 pts)
    education_score = min(len(resume_data.education) * 5, 10)
    breakdown["education"] = education_score
    score += education_score
    
    if not resume_data.education:
        issues.append({"priority": "medium", "category": "education", "message": "Missing education information"})
    
    # 4. Work Experience (20 pts)
    experience_score = min(resume_data.no_of_years_experience * 4, 20) if resume_data.no_of_years_experience else 0
    breakdown["experience"] = experience_score
    score += experience_score
    
    if not resume_data.no_of_years_experience:
        issues.append({"priority": "high", "category": "experience", "message": "Missing work experience"})
    
    # 5. Structure & Formatting (15 pts)
    structure_score = 15  # Basic score, can be enhanced with more analysis
    breakdown["structure"] = structure_score
    score += structure_score
    
    # 6. Readability & Grammar (15 pts)
    readability_score = 15  # Basic score, can be enhanced with LLM analysis
    breakdown["readability"] = readability_score
    score += readability_score
    
    # LLM Enhancement for grammar and content analysis
    try:
        if model:
            prompt = f"""
            Analyze this resume text and provide specific feedback on grammar, content quality, and ATS optimization:
            
            {original_text[:2000]}
            
            Provide:
            1. Grammar issues (if any)
            2. Content quality score (1-10)
            3. ATS optimization suggestions
            4. Overall professional impression
            """
            
            response = model.generate_content(prompt)
            llm_feedback = response.text
            
            # Extract issues from LLM feedback
            if "grammar" in llm_feedback.lower() or "spelling" in llm_feedback.lower():
                issues.append({"priority": "medium", "category": "readability", "message": "Grammar/spelling issues detected"})
            
            recommendations.append(f"AI Analysis: {llm_feedback[:200]}...")
        else:
            logger.warning("Gemini AI not available, skipping LLM analysis")
        
    except Exception as e:
        logger.error(f"LLM analysis failed: {e}")
    
    # Penalty deductions
    penalties = []
    
    # Check for creative job titles
    creative_titles = ['ninja', 'guru', 'rockstar', 'wizard', 'hero']
    for title in creative_titles:
        if title in original_text.lower():
            penalties.append(-2)
            issues.append({"priority": "medium", "category": "formatting", "message": f"Avoid creative job titles like '{title}'"})
    
    # Check for missing summary
    if not any(word in original_text.lower() for word in ['summary', 'objective', 'profile']):
        penalties.append(-3)
        issues.append({"priority": "high", "category": "content", "message": "Missing professional summary section"})
    
    # Apply penalties
    total_penalty = sum(penalties)
    score = max(0, score + total_penalty)
    
    # Sort issues by priority
    priority_order = {"high": 1, "medium": 2, "low": 3}
    issues.sort(key=lambda x: priority_order.get(x["priority"], 4))
    
    return ATSResult(
        total_score=score,
        breakdown=breakdown,
        issues=issues,
        recommendations=recommendations
    )

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    """Upload and parse resume file"""
    start_time = time.time()
    logger.info(f"Processing file upload: {file.filename}")
    
    # Validate file type
    allowed_types = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']
    if file.content_type not in allowed_types:
        logger.warning(f"Invalid file type attempted: {file.content_type}")
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, DOCX, and TXT files are allowed.")
    
    # Validate file size (10MB limit)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        logger.warning(f"File too large: {len(content)} bytes")
        raise HTTPException(status_code=400, detail="File size must be less than 10MB")
    
    # Validate filename
    if not file.filename or len(file.filename) > 255:
        logger.warning(f"Invalid filename: {file.filename}")
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    # Save uploaded file temporarily
    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
    
    try:
        # Extract text based on file type
        if file.content_type == 'application/pdf':
            text = extract_text_from_pdf(temp_file_path)
        elif file.content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            text = extract_text_from_docx(temp_file_path)
        else:  # text/plain
            text = extract_text_from_txt(temp_file_path)
        
        # Parse resume data
        resume_data = parse_resume_text(text)
        
        # Calculate ATS score
        ats_result = calculate_ats_score(resume_data, text)
        
        # Save to Supabase
        try:
            if supabase:
                supabase_data = {
                    "email": resume_data.email,
                    "mobile": resume_data.mobile,
                    "address": resume_data.address,
                    "skills": resume_data.skills,
                    "experience": resume_data.experience,
                    "education": resume_data.education,
                    "no_of_years_experience": resume_data.no_of_years_experience,
                    "linkedin": resume_data.linkedin,
                    "github": resume_data.github,
                    "summary": resume_data.summary,
                    "certifications": resume_data.certifications,
                    "ats_score": ats_result.total_score,
                    "score_breakdown": ats_result.breakdown,
                    "issues": ats_result.issues,
                    "recommendations": ats_result.recommendations,
                    "uploaded_at": datetime.utcnow().isoformat()
                }
                
                result = supabase.table("resumes").insert(supabase_data).execute()
                logger.info(f"Resume data saved to database for {resume_data.email}")
            else:
                logger.warning("Supabase not available, skipping database save")
            
        except Exception as e:
            logger.error(f"Supabase save failed: {e}")
            # Continue without saving to database
        
        processing_time = time.time() - start_time
        logger.info(f"Successfully processed resume in {processing_time:.2f}s - Score: {ats_result.total_score}")
        
        return JSONResponse(content={
            "success": True,
            "parsed_data": resume_data.dict(),
            "ats_score": ats_result.total_score,
            "score_breakdown": ats_result.breakdown,
            "issues": ats_result.issues,
            "recommendations": ats_result.recommendations,
            "processing_time": processing_time
        })
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing resume: {e}")
        raise HTTPException(status_code=500, detail="Internal server error occurred while processing the resume")
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.error(f"Failed to cleanup temp file: {e}")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "CV Parser & ATS Scorer API",
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Detailed health check for production monitoring"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "supabase": "connected" if supabase else "disconnected",
            "gemini_ai": "connected" if model else "disconnected"
        }
    }
    
    # Check if any critical services are down
    if not supabase or not model:
        health_status["status"] = "degraded"
    
    return health_status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
