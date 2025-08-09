# CV Parser & ATS Scorer

A production-ready web application that allows users to upload their resumes (PDF, DOCX, TXT) and get instant ATS (Applicant Tracking System) scoring with AI-powered analysis and optimization suggestions.

## 🚀 Features

- **Multi-format Support**: Upload PDF, DOCX, and TXT files
- **Drag & Drop Interface**: Modern, mobile-first responsive design
- **Advanced Parsing**: Uses PyMuPDF, pdfplumber, and python-docx for accurate text extraction
- **ATS Scoring System**: 100-point scoring with detailed breakdown
- **AI Enhancement**: Gemini 1.5 Flash integration for grammar and content analysis
- **Issue Detection**: Priority-based issue identification with actionable recommendations
- **Database Storage**: Supabase integration for parsed data persistence
- **No Authentication Required**: Anyone can upload and get results instantly

## 🏗️ Architecture

### Backend (FastAPI + Python)
- **File Processing**: Multi-format resume parsing
- **Text Extraction**: PyMuPDF + pdfplumber for PDFs, python-docx for DOCX
- **Data Parsing**: Regex + heuristics for structured data extraction
- **ATS Scoring**: Rule-based system with LLM enhancement
- **Database**: Supabase for data persistence
- **API**: RESTful endpoints with CORS support

### Frontend (Vanilla JS + Tailwind CSS)
- **Mobile-First Design**: Responsive interface optimized for all devices
- **Drag & Drop**: Intuitive file upload experience
- **Real-time Progress**: Upload progress indication
- **Dynamic Results**: Interactive score visualization and issue display
- **Modern UI**: Clean, professional design with Tailwind CSS

## 📊 ATS Scoring System (100 points total)

### 1. Contact & Professional Info (15 pts)
- Valid email format
- Professional phone number
- LinkedIn profile presence

### 2. Keywords & Skills Relevance (25 pts)
- Industry-specific skill matching
- Balance between soft & hard skills

### 3. Education & Certifications (10 pts)
- Degree and institution detection
- Completion year validation

### 4. Work Experience (20 pts)
- Job title recognition
- Chronological order validation

### 5. Structure & Formatting (15 pts)
- Clear section headings
- Consistent formatting

### 6. Readability & Grammar (15 pts)
- AI-powered grammar analysis
- Content quality assessment

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js (for development)
- Supabase account
- Google Gemini API key

### 1. Clone the Repository
```bash
git clone <repository-url>
cd cvbuilder
```

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r ../requirements.txt

# Copy environment variables
cp ../env.example .env

# Edit .env with your API keys
nano .env
```

### 3. Supabase Setup
1. Create a new Supabase project
2. Create the `resumes` table with the following schema:

```sql
CREATE TABLE resumes (
    id SERIAL PRIMARY KEY,
    email TEXT,
    mobile TEXT,
    address TEXT,
    skills TEXT[],
    experience JSONB,
    education JSONB,
    no_of_years_experience INTEGER,
    linkedin TEXT,
    github TEXT,
    summary TEXT,
    certifications TEXT[],
    ats_score INTEGER,
    score_breakdown JSONB,
    issues JSONB,
    recommendations TEXT[],
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 4. Environment Variables
Update your `.env` file with:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
GEMINI_API_KEY=your_gemini_api_key
PORT=8000
HOST=0.0.0.0
```

### 5. Run the Backend
```bash
# Development
python main.py

# Production
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 6. Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Serve the frontend (using Python's built-in server)
python -m http.server 3000

# Or use any static file server
npx serve .
```

## 🚀 Deployment

### Backend Deployment (Render.com)
1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**: Add all variables from `.env`

### Frontend Deployment (Render.com)
1. Create a new Static Site
2. Configure:
   - **Build Command**: `echo "No build required"`
   - **Publish Directory**: `frontend`
   - **Environment Variables**: Update `API_BASE_URL` in `script.js`

### Alternative Deployment Options
- **Vercel**: Deploy frontend as static site
- **Railway**: Deploy backend as Python service
- **Heroku**: Deploy both using buildpacks

## 📁 Project Structure

```
cvbuilder/
├── backend/
│   └── main.py              # FastAPI application
├── frontend/
│   ├── index.html           # Main HTML file
│   └── script.js            # JavaScript functionality
├── requirements.txt         # Python dependencies
├── env.example             # Environment variables template
└── README.md               # This file
```

## 🔧 API Endpoints

### POST /upload-resume
Upload and parse a resume file.

**Request:**
- Content-Type: multipart/form-data
- Body: file (PDF, DOCX, or TXT)

**Response:**
```json
{
  "success": true,
  "parsed_data": {
    "email": "user@example.com",
    "mobile": "+1234567890",
    "skills": ["Python", "JavaScript"],
    "experience": [...],
    "education": [...],
    "linkedin": "https://linkedin.com/in/user",
    "github": "https://github.com/user"
  },
  "ats_score": 85,
  "score_breakdown": {
    "contact": 15,
    "skills": 20,
    "education": 10,
    "experience": 15,
    "structure": 15,
    "readability": 10
  },
  "issues": [
    {
      "priority": "high",
      "category": "contact",
      "message": "Missing phone number"
    }
  ],
  "recommendations": [
    "Add a professional summary section",
    "Include more specific skills"
  ]
}
```

## 🎯 Usage

1. **Upload Resume**: Drag and drop or click to upload your resume
2. **Processing**: Wait for AI analysis and parsing
3. **View Results**: See your ATS score and detailed breakdown
4. **Review Issues**: Check prioritized issues and recommendations
5. **Optimize**: Use the "Fix My Resume with AI" feature (coming soon)

## 🔒 Security Considerations

- File size limits (10MB)
- File type validation
- CORS configuration
- Environment variable protection
- No sensitive data storage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the code comments

## 🚀 Roadmap

- [ ] AI-powered resume optimization
- [ ] Job-specific keyword analysis
- [ ] Resume comparison tools
- [ ] Export functionality
- [ ] User accounts and history
- [ ] Advanced analytics dashboard
