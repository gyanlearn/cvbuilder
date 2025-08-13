from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import os
import tempfile
import json
from typing import Dict, List, Optional, Any
import re
from datetime import datetime
import fitz  # PyMuPDF
import pdfplumber
from docx import Document
import google.generativeai as genai
from supabase import create_client, Client
from uuid import uuid4
from dotenv import load_dotenv
from pydantic import BaseModel
import email_validator
from dateutil import parser as date_parser
import logging
import time

# ATS advanced scorer
from backend.ats.config_loader import (
    load_language_quality_config,
    load_professional_language_config,
    load_industry_keywords,
)
from backend.ats.scorer import ats_score as advanced_ats_score
from backend.ats.cv_improver import CVImprover

# Pydantic models for CV improvement
class CVImprovementRequest(BaseModel):
    original_cv_text: str
    ats_feedback: Dict[str, Any]
    industry: str
    original_score: int
    template_id: str = "modern_professional"  # Default template

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add startup logging
logger.info("Starting CV Parser & ATS Scorer API...")
logger.info(f"Environment: {'production' if os.getenv('RENDER') else 'development'}")
logger.info(f"Python version: {os.sys.version}")
logger.info(f"Working directory: {os.getcwd()}")

# Load environment variables
load_dotenv()

app = FastAPI(
    title="CV Parser & ATS Scorer", 
    version="1.0.0",
    description="Production-ready CV parsing and ATS scoring API",
    docs_url="/docs",
    redoc_url="/redoc"
)
# Preload ATS configs at startup (read-only)
ATS_BASE_DIR = os.path.join(os.path.dirname(__file__), 'ats')
try:
    ATS_LANG_CFG = load_language_quality_config(ATS_BASE_DIR)
    ATS_PROF_CFG = load_professional_language_config(ATS_BASE_DIR)
except Exception:
    ATS_LANG_CFG, ATS_PROF_CFG = {}, {}

# Global exception handlers to ensure CORS headers are added
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return add_cors_headers(JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    ))

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return add_cors_headers(JSONResponse(
        status_code=422,
        content={"detail": "Validation error", "errors": exc.errors()}
    ))

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return add_cors_headers(JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    ))

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"]  # In production, specify your domain
)

# CORS middleware with production settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://cv-parser-frontend-qgx0.onrender.com",
        "http://localhost:3000",  # For development
        "https://localhost:3000"
    ],
    allow_credentials=False,  # Set to False for security
    allow_methods=["GET", "POST", "OPTIONS"],  # Added OPTIONS for preflight
    allow_headers=["*"],
    expose_headers=["*"],  # Expose all headers
    max_age=86400,  # Cache preflight for 24 hours
)

# Helper function to add CORS headers
def add_cors_headers(response):
    """Add CORS headers to response"""
    response.headers["Access-Control-Allow-Origin"] = "https://cv-parser-frontend-qgx0.onrender.com"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    # Let FastAPI CORS middleware handle CORS headers
    return response

# Initialize Supabase with error handling
try:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    
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
    mobile_country_code: Optional[str] = None
    mobile_national_number: Optional[str] = None
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
    # Primary: PyMuPDF
    try:
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text() or ""
        doc.close()
    except Exception as e:
        logger.warning(f"PyMuPDF failed, falling back to pdfplumber: {e}")
    # Secondary: pdfplumber (also capture tables)
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += "\n" + page_text
                tables = page.extract_tables()
                for table in tables or []:
                    row_text = " ".join([" ".join([c or '' for c in row]) for row in table])
                    text += "\n" + row_text
    except Exception as e:
        logger.error(f"pdfplumber also failed to extract text: {e}")
    return text.strip()

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file"""
    doc = Document(file_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def extract_text_from_txt(file_path: str) -> str:
    """Extract text from TXT file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read()
        except Exception:
            with open(file_path, 'r', errors='ignore') as file:
                return file.read()

def _extract_phone(text: str) -> Dict[str, Optional[str]]:
    """Extract phone with country code and national number. Prefers patterns like +CC XXXXX..."""
    # Normalize whitespace
    cleaned = re.sub(r"[\t\r]", " ", text)
    # Common patterns: +91 9876543210, +44-7700-900123, +1 (555) 123-4567
    patterns = [
        r"\+(?P<cc>\d{1,3})[\s\-()]*?(?P<num>(?:\d[\s\-()]*){7,15})",
        r"(?P<num>\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4})"  # fallback US pattern
    ]
    for pat in patterns:
        m = re.search(pat, cleaned)
        if m:
            cc = m.groupdict().get("cc")
            raw_num = m.groupdict().get("num") or m.group(0)
            national = re.sub(r"[^\d]", "", raw_num)
            if cc and national.startswith(cc):
                # Remove repeated cc if present
                national = national[len(cc):]
            return {
                "mobile": f"+{cc}{national}" if cc else national,
                "mobile_country_code": f"+{cc}" if cc else None,
                "mobile_national_number": national if national else None,
            }
    return {"mobile": None, "mobile_country_code": None, "mobile_national_number": None}


def _extract_skills(text: str) -> List[str]:
    """Extract skills from explicit skills sections and via keyword matching."""
    skills_found: set[str] = set()
    tl = text.lower()

    # 1) Parse Skills section blocks
    section_patterns = [
        r"(?:^|\n)\s*(skills|technical skills|core competencies|competencies|areas of expertise)\s*[:\n]\s*(?P<body>(?:.+\n?){1,6})",
    ]
    for sp in section_patterns:
        for sm in re.finditer(sp, text, re.IGNORECASE):
            body = sm.group("body")
            # split by commas, bullets, pipes
            tokens = re.split(r"[,•\u2022\-|\n]", body)
            for tok in tokens:
                tok_norm = re.sub(r"\s+", " ", tok.strip().lower())
                if 2 <= len(tok_norm) <= 60:
                    skills_found.add(tok_norm)

    # 2) Keyword dictionary (expandable)
    keywords = [
        # Engineering
        'python','javascript','java','c++','c#','php','ruby','go','rust','react','angular','vue','node.js','django','flask','spring',
        'docker','kubernetes','aws','azure','gcp','sql','mongodb','redis','git','jenkins','agile','scrum','machine learning','ai','data science',
        'tableau','power bi','excel','word','powerpoint','graphql','rest','microservices','spark','hadoop',
        # Product & growth
        'product management','product strategy','product leadership','product roadmap','roadmapping','user research','user interviews',
        'a/b testing','ab testing','split testing','experiment design','experimentation','growth hacking','growth strategy','activation',
        'retention','monetization','pricing','segmentation','okrs','kpis','analytics','mixpanel','amplitude','google analytics',
        'agile methodology','stakeholder management','feature prioritization','impact mapping','jobs to be done','jtbd',
        # Common product synonyms
        'product mgmt','product ops','growth product','product discovery','roadmap planning','experimentation platform',
    ]
    for kw in keywords:
        if kw in tl:
            skills_found.add(kw)

    # Normalize capitalization
    def cap(s: str) -> str:
        if s.upper() in {"OKRS","KPIS","SQL","AI"}:
            return s.upper()
        # title case for multi-words while preserving slashes and hyphens
        return " ".join(w.capitalize() if not w.isupper() else w for w in re.split(r"(\b)", s))

    # Map common variants
    mapped = set()
    mapping = {
        'ab testing':'A/B Testing',
        'a/b testing':'A/B Testing',
        'jtbd':'Jobs To Be Done',
        'okrs':'OKRs',
        'kpis':'KPIs',
        'ai':'AI',
        'product mgmt':'Product Management',
        'product ops':'Product Operations',
        'growth product':'Growth Product',
        'roadmap planning':'Product Roadmap',
    }
    for s in skills_found:
        # normalize extra whitespace and dashes
        s_norm = re.sub(r"\s+", " ", s.strip())
        s2 = mapping.get(s_norm, cap(s_norm))
        mapped.add(s2)
    # Deduplicate by case-insensitive key
    final = sorted({x.lower(): x for x in mapped}.values())
    return final


def _extract_experience(text: str) -> Dict[str, Optional[int]]:
    """Compute experience only from Professional/Work Experience sections.
    Sums all detected job date ranges in those sections: Σ(end - start) in months -> years (floor).
    """
    # Identify experience section blocks by heading and slice until next section heading
    heading_exp = r"^(?:work experience|professional experience|experience|employment history|career history|work history|professional background)\b"
    heading_other = r"^(?:education|academics|projects|skills|certifications|awards|publications|summary|profile|objective|interests|references|contact|personal)\b"

    total_months = 0
    has_section = False

    # Use multiline matching to find headings at line starts
    for m in re.finditer(heading_exp, text, flags=re.IGNORECASE | re.MULTILINE):
        has_section = True
        start_idx = m.start()
        # Find the next heading (any section) after this one
        next_m = re.search(heading_other, text[m.end():], flags=re.IGNORECASE | re.MULTILINE)
        end_idx = m.end() + next_m.start() if next_m else len(text)
        block = text[start_idx:end_idx]

        # Date patterns inside the block
        month_names = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)"
        patterns = [
            rf"(?P<from>{month_names}\s+\d{{4}})\s*(?:[-–to]+|to)\s*(?P<to>{month_names}\s+\d{{4}}|present|current)",
            r"(?P<from>\d{4})\s*(?:[-–to]+|to)\s*(?P<to>\d{4}|present|current)",
            r"(?P<from>\d{1,2}/\d{4})\s*(?:[-–to]+|to)\s*(?P<to>\d{1,2}/\d{4}|present|current)",
        ]

        def parse_dt(s: str) -> Optional[datetime]:
            try:
                return date_parser.parse(s, default=datetime(2000, 1, 1))
            except Exception:
                return None

        for pat in patterns:
            for dm in re.finditer(pat, block, flags=re.IGNORECASE):
                f = dm.group('from')
                t = dm.group('to')
                df = parse_dt(f)
                dt_ = parse_dt(t if t.lower() not in {"present", "current"} else datetime.utcnow().strftime("%b %Y"))
                if df and dt_ and dt_ > df:
                    total_months += max(0, (dt_.year - df.year) * 12 + (dt_.month - df.month))

    years_from_dates = total_months // 12 if total_months > 0 else None

    # If no explicit ranges found but a section exists, optionally fall back to phrase-based estimate
    years = years_from_dates
    if years is None and has_section:
        m = re.search(r"(\d{1,2})\+?\s+years?\s+of\s+experience", text, flags=re.IGNORECASE)
        if m:
            years = int(m.group(1))

    return {"years": years, "has_section": has_section}


def parse_resume_text(text: str) -> ResumeData:
    """Parse resume text and extract structured data"""
    data = ResumeData()
    text_lower = text.lower()
    
    # Email extraction
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    if emails:
        data.email = emails[0]

    # Phone number extraction (country code + national number)
    phone = _extract_phone(text)
    data.mobile = phone["mobile"]
    data.mobile_country_code = phone["mobile_country_code"]
    data.mobile_national_number = phone["mobile_national_number"]
    
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
    
    # Skills extraction
    data.skills = _extract_skills(text)
    
    # Experience extraction
    exp = _extract_experience(text)
    if exp["years"]:
        data.no_of_years_experience = int(exp["years"])

    # Address extraction (simple heuristics)
    def _extract_address_block(t: str) -> Optional[str]:
        lines = [ln.strip() for ln in t.splitlines() if ln.strip()]
        # Try after an Address heading
        for i, ln in enumerate(lines):
            if re.match(r"^address\b[:]?", ln, re.IGNORECASE):
                # take next 1-2 lines as address
                chunk = ", ".join([x for x in lines[i+1:i+3] if x])
                if len(chunk) >= 10:
                    return chunk
        # Otherwise, find first line that looks like a location (contains comma and letters)
        for ln in lines[:12]:  # usually contact block is near top
            if ("," in ln and len(ln) <= 120 and not re.search(r"(linkedin|github|@|http)", ln, re.I)):
                return ln
        return None

    data.address = _extract_address_block(text)

    # Summary extraction
    def _extract_summary(t: str) -> Optional[str]:
        m = re.search(r"(?:^|\n)\s*(professional\s+summary|summary|profile|about\s+me)\s*[:\n]+(?P<body>(?:.+\n?){1,6})", t, re.IGNORECASE)
        if m:
            body = m.group("body")
            # stop at next all-caps heading or blank gap
            body = re.split(r"\n\s*\n|\n[A-Z][A-Z\s]{2,}\n", body)[0]
            return re.sub(r"\s+", " ", body).strip()
        return None

    data.summary = _extract_summary(text)
    
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
    
    # 2. Keywords & Skills Relevance (25 pts) – stricter: 1 point per unique skill, cap 20; +5 bonus if both product and engineering skills present
    product_flags = any(s.lower().startswith("product ") or s.lower() in {"a/b testing","jobs to be done","growth hacking","okrs","kpis"} for s in resume_data.skills)
    engineering_flags = any(s.lower() in {"python","javascript","java","sql","docker","kubernetes","aws","react","node.js"} for s in resume_data.skills)
    base_skills = min(len(resume_data.skills), 20)
    skills_score = base_skills + (5 if product_flags and engineering_flags else 0)
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
    experience_score = min((resume_data.no_of_years_experience or 0) * 4, 20)
    breakdown["experience"] = experience_score
    score += experience_score
    
    if not resume_data.no_of_years_experience:
        # Only flag if we truly cannot detect an experience section
        if not _extract_experience(original_text)["has_section"]:
            issues.append({"priority": "high", "category": "experience", "message": "Missing work experience"})
    
    # 5. Structure & Formatting (15 pts) – stricter baseline
    structure_score = 10
    breakdown["structure"] = structure_score
    score += structure_score
    
    # 6. Readability & Grammar (15 pts) – stricter baseline
    readability_score = 10
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
        # Use word boundaries to avoid matching in place names like Gurugram
        if re.search(rf"\\b{re.escape(title)}\\b", original_text.lower()):
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

@app.options("/upload-resume")
async def upload_resume_options():
    """Handle CORS preflight request for upload endpoint"""
    return JSONResponse(
        content={"message": "CORS preflight"},
        headers={
            "Access-Control-Allow-Origin": "https://cv-parser-frontend-qgx0.onrender.com",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400"
        }
    )

@app.post("/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    industry: str = Query(default="technology", description="Target industry for ATS scoring")
):
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
    
    # Save uploaded file temporarily and process
    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name

        # Upload original file to Supabase Storage (if configured)
        cv_file_url = None
        cv_storage_path = None
        if supabase:
            try:
                bucket_name = os.getenv("SUPABASE_BUCKET", "resumes")
                # Build storage path (assumes bucket already exists and is public)
                ext = os.path.splitext(file.filename)[1].lower() or ".bin"
                storage_key = f"{datetime.utcnow().strftime('%Y/%m/%d')}/{uuid4().hex}{ext}"

                # Read bytes and upload
                with open(temp_file_path, "rb") as fbin:
                    file_bytes = fbin.read()
                supabase.storage.from_(bucket_name).upload(
                    path=storage_key,
                    file=file_bytes,
                    file_options={"content-type": file.content_type or "application/octet-stream"}
                )
                # Get public URL
                cv_file_url = supabase.storage.from_(bucket_name).get_public_url(storage_key)
                cv_storage_path = f"{bucket_name}/{storage_key}"
                logger.info("Uploaded CV to Supabase Storage: %s", cv_storage_path)
            except Exception as e:
                logger.error(f"Failed to upload CV to Supabase Storage: {e}")

        # Extract text based on file type
        if file.content_type == 'application/pdf':
            text = extract_text_from_pdf(temp_file_path)
        elif file.content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            text = extract_text_from_docx(temp_file_path)
        else:  # text/plain
            text = extract_text_from_txt(temp_file_path)
        
        # Parse resume data
        resume_data = parse_resume_text(text)
        
        # Calculate ATS score (basic)
        ats_result = calculate_ats_score(resume_data, text)

        # Advanced ATS report (config-driven)
        try:
            ind_cfg = load_industry_keywords(ATS_BASE_DIR, industry)
            logger.info(f"Starting advanced ATS scoring with LLM for industry: {industry}")
            advanced_report = advanced_ats_score(text, industry, ATS_LANG_CFG, ATS_PROF_CFG, ind_cfg, model)
            logger.info(f"Advanced ATS scoring completed successfully")
        except Exception as e:
            logger.error(f"Advanced ATS scoring failed: {e}")
            advanced_report = None
        
        # Save to Supabase
        try:
            if supabase:
                supabase_data = {
                    "email": resume_data.email,
                    "mobile": resume_data.mobile,
                    "mobile_country_code": resume_data.mobile_country_code,
                    "mobile_national_number": resume_data.mobile_national_number,
                    "address": resume_data.address,
                    "skills": resume_data.skills,
                    "experience": resume_data.experience,
                    "education": resume_data.education,
                    "no_of_years_experience": resume_data.no_of_years_experience,
                    "linkedin": resume_data.linkedin,
                    "github": resume_data.github,
                    "summary": resume_data.summary,
                    "certifications": resume_data.certifications,
                    "cv_file_url": cv_file_url,
                    "cv_storage_path": cv_storage_path,
                    "cv_mime_type": file.content_type,
                    "cv_file_size": len(content),
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
            "parsed_data": {
                **resume_data.dict(),
                "original_text": text  # Include original CV text for improvement
            },
            "ats_score": ats_result.total_score,
            "score_breakdown": ats_result.breakdown,
            "issues": ats_result.issues,
            "recommendations": ats_result.recommendations,
            "advanced_report": advanced_report,
            "processing_time": processing_time
        }, headers={
            "Access-Control-Allow-Origin": "https://cv-parser-frontend-qgx0.onrender.com",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*"
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

@app.options("/improve-cv")
async def improve_cv_options():
    """Handle CORS preflight request for CV improvement endpoint"""
    return JSONResponse(
        content={"message": "CORS preflight"},
        headers={
            "Access-Control-Allow-Origin": "https://cv-parser-frontend-qgx0.onrender.com",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400"
        }
    )

@app.post("/improve-cv")
async def improve_cv(request: CVImprovementRequest):
    """
    Improve CV based on ATS feedback using Gemini Flash 2.0 and generate improved PDF
    """
    if not model:
        raise HTTPException(status_code=503, detail="AI model not available")
    
    cv_improver = None
    
    try:
        # Get ATS feedback and original CV text from request
        ats_feedback = request.ats_feedback
        original_cv_text = request.original_cv_text
        industry = request.industry
        original_score = request.original_score
        template_id = request.template_id
        
        logger.info(f"Starting CV improvement for industry: {industry}, score: {original_score}, template: {template_id}")
        
        # Initialize CV improver
        cv_improver = CVImprover(model)
        
        # Improve CV with selected template
        improvement_result = cv_improver.improve_cv(
            original_cv_text=original_cv_text,
            ats_feedback=ats_feedback,
            industry=industry,
            original_score=original_score,
            template_id=template_id
        )
        
        if not improvement_result.get('success'):
            raise HTTPException(status_code=500, detail=improvement_result.get('error', 'CV improvement failed'))
        
        # Check if PDF was generated
        if not improvement_result.get('pdf_path'):
            logger.error("CV improvement succeeded but no PDF path returned")
            raise HTTPException(status_code=500, detail="PDF generation failed during CV improvement")
        
        # Verify PDF file exists and has content
        pdf_path = improvement_result['pdf_path']
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found at path: {pdf_path}")
            raise HTTPException(status_code=500, detail="Generated PDF file not found")
        
        file_size = os.path.getsize(pdf_path)
        if file_size == 0:
            logger.error(f"PDF file is empty: {pdf_path}")
            raise HTTPException(status_code=500, detail="Generated PDF file is empty")
        
        logger.info(f"PDF generated successfully: {pdf_path} (size: {file_size} bytes)")
        
        # Upload improved PDF to Supabase Storage
        improved_pdf_url = None
        pdf_data_base64 = None
        
        if supabase:
            try:
                bucket_name = os.getenv("SUPABASE_BUCKET", "resumes")
                pdf_filename = os.path.basename(improvement_result['pdf_path'])
                storage_key = f"improved/{datetime.utcnow().strftime('%Y/%m/%d')}/{pdf_filename}"
                
                logger.info(f"Uploading PDF to Supabase: bucket={bucket_name}, key={storage_key}")
                
                with open(improvement_result['pdf_path'], "rb") as fbin:
                    pdf_bytes = fbin.read()
                
                logger.info(f"PDF file read successfully: {len(pdf_bytes)} bytes")
                
                # Upload to Supabase
                upload_result = supabase.storage.from_(bucket_name).upload(
                    path=storage_key,
                    file=pdf_bytes,
                    file_options={"content-type": "application/pdf"}
                )
                
                logger.info(f"Supabase upload result: {upload_result}")
                
                # Get public URL
                improved_pdf_url = supabase.storage.from_(bucket_name).get_public_url(storage_key)
                logger.info(f"Uploaded improved PDF to Supabase: {storage_key}")
                logger.info(f"Public URL: {improved_pdf_url}")
                
            except Exception as e:
                logger.error(f"Failed to upload improved PDF to Supabase: {e}")
                logger.error(f"Supabase error details: {type(e).__name__}: {str(e)}")
                import traceback
                logger.error(f"Supabase traceback: {traceback.format_exc()}")
                # Fallback: provide PDF data directly
                try:
                    with open(improvement_result['pdf_path'], "rb") as fbin:
                        pdf_bytes = fbin.read()
                    import base64
                    pdf_data_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
                    logger.info(f"Fallback: PDF data encoded as base64 ({len(pdf_data_base64)} characters)")
                except Exception as fallback_error:
                    logger.error(f"Fallback PDF encoding also failed: {fallback_error}")
        else:
            logger.warning("Supabase not configured, providing PDF data directly")
            try:
                with open(improvement_result['pdf_path'], "rb") as fbin:
                    pdf_bytes = fbin.read()
                import base64
                pdf_data_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
                logger.info(f"Direct PDF encoding: {len(pdf_data_base64)} characters")
            except Exception as direct_error:
                logger.error(f"Direct PDF encoding failed: {direct_error}")
        
        return JSONResponse(content={
            "success": True,
            "original_score": original_score,
            "new_score": improvement_result['new_score'],
            "improvement_strategy": improvement_result['improvement_strategy'],
            "improved_cv_text": improvement_result['improved_cv_text'],
            "pdf_download_url": improved_pdf_url,
            "pdf_data_base64": pdf_data_base64,  # Fallback for direct download
            "changes_made": improvement_result['changes_made'],
            "template_used": improvement_result.get('template_used', template_id),
            "ats_feedback_summary": {
                "issues_count": len(ats_feedback.get('issues', [])),
                "missing_keywords": len(ats_feedback.get('keyword_matches', {}).get('missing', [])),
                "grammar_issues": len([i for i in ats_feedback.get('issues', []) if i.get('type') == 'grammar']),
                "spelling_issues": len([i for i in ats_feedback.get('issues', []) if i.get('type') == 'spelling'])
            },
            "timestamp": datetime.utcnow().isoformat()
        }, headers={
            "Access-Control-Allow-Origin": "https://cv-parser-frontend-qgx0.onrender.com",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        })
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error improving CV: {e}")
        raise HTTPException(status_code=500, detail="Internal server error occurred while improving the CV")
    finally:
        if cv_improver:
            cv_improver.cleanup()

@app.get("/cv-templates")
async def get_cv_templates():
    """Get available CV templates"""
    try:
        if not model:
            raise HTTPException(status_code=503, detail="AI model not available")
        
        cv_improver = CVImprover(model)
        templates = cv_improver.get_available_templates()
        
        return JSONResponse(content={
            "success": True,
            "templates": templates,
            "timestamp": datetime.utcnow().isoformat()
        }, headers={
            "Access-Control-Allow-Origin": "https://cv-parser-frontend-qgx0.onrender.com",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        })
        
    except Exception as e:
        logger.error(f"Error getting CV templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to get CV templates")

@app.options("/cv-templates")
async def cv_templates_options():
    """Handle CORS preflight request for CV templates endpoint"""
    return JSONResponse(
        content={"message": "CORS preflight"},
        headers={
            "Access-Control-Allow-Origin": "https://cv-parser-frontend-qgx0.onrender.com",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400"
        }
    )

@app.options("/test-cors")
async def test_cors_options():
    """Handle CORS preflight request for test endpoint"""
    return JSONResponse(
        content={"message": "CORS preflight"},
        headers={
            "Access-Control-Allow-Origin": "https://cv-parser-frontend-qgx0.onrender.com",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400"
        }
    )

@app.get("/test-cors")
async def test_cors():
    """Test endpoint to verify CORS is working"""
    return JSONResponse(
        content={"message": "CORS test successful", "timestamp": datetime.utcnow().isoformat()},
        headers={
            "Access-Control-Allow-Origin": "https://cv-parser-frontend-qgx0.onrender.com",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )

@app.options("/")
async def root_options():
    """Handle CORS preflight request for root endpoint"""
    return JSONResponse(
        content={"message": "CORS preflight"},
        headers={
            "Access-Control-Allow-Origin": "https://cv-parser-frontend-qgx0.onrender.com",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400"
        }
    )

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "CV Parser & ATS Scorer API",
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.options("/health")
async def health_options():
    """Handle CORS preflight request for health endpoint"""
    return JSONResponse(
        content={"message": "CORS preflight"},
        headers={
            "Access-Control-Allow-Origin": "https://cv-parser-frontend-qgx0.onrender.com",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400"
        }
    )

@app.get("/health")
async def health_check():
    """Detailed health check for production monitoring"""
    import platform
    import psutil
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": "production" if os.getenv('RENDER') else "development",
        "system": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "memory_usage": f"{psutil.virtual_memory().percent}%",
            "cpu_usage": f"{psutil.cpu_percent()}%"
        },
        "services": {
            "supabase": "connected" if supabase else "disconnected",
            "gemini_ai": "connected" if model else "disconnected"
        },
        "cors": {
            "allowed_origins": ["https://cv-parser-frontend-qgx0.onrender.com"],
            "middleware_active": True
        }
    }
    
    # Check if any critical services are down
    if not supabase or not model:
        health_status["status"] = "degraded"
    
    # Check system resources
    if psutil.virtual_memory().percent > 90:
        health_status["status"] = "degraded"
        health_status["warnings"] = ["High memory usage"]
    
    return health_status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
