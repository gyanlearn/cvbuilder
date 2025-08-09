-- Create the resumes table for storing parsed CV data
CREATE TABLE IF NOT EXISTS resumes (
    id SERIAL PRIMARY KEY,
    email TEXT,
    mobile TEXT,
    mobile_country_code TEXT,
    mobile_national_number TEXT,
    address TEXT,
    skills TEXT[],
    experience JSONB,
    education JSONB,
    no_of_years_experience INTEGER,
    linkedin TEXT,
    github TEXT,
    summary TEXT,
    certifications TEXT[],
    cv_file_url TEXT,
    cv_storage_path TEXT,
    cv_mime_type TEXT,
    cv_file_size BIGINT,
    ats_score INTEGER,
    score_breakdown JSONB,
    issues JSONB,
    recommendations TEXT[],
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_resumes_email ON resumes(email);
CREATE INDEX IF NOT EXISTS idx_resumes_ats_score ON resumes(ats_score);
CREATE INDEX IF NOT EXISTS idx_resumes_uploaded_at ON resumes(uploaded_at);

-- Enable Row Level Security (RLS) for future authentication
ALTER TABLE resumes ENABLE ROW LEVEL SECURITY;

-- Create a policy that allows all operations (for now, since no auth is required)
CREATE POLICY "Allow all operations" ON resumes FOR ALL USING (true);

-- Create a view for analytics (optional)
CREATE OR REPLACE VIEW resume_analytics AS
SELECT 
    COUNT(*) as total_resumes,
    AVG(ats_score) as average_score,
    MIN(ats_score) as min_score,
    MAX(ats_score) as max_score,
    COUNT(CASE WHEN ats_score >= 80 THEN 1 END) as excellent_resumes,
    COUNT(CASE WHEN ats_score >= 60 AND ats_score < 80 THEN 1 END) as good_resumes,
    COUNT(CASE WHEN ats_score >= 40 AND ats_score < 60 THEN 1 END) as fair_resumes,
    COUNT(CASE WHEN ats_score < 40 THEN 1 END) as poor_resumes
FROM resumes;

-- Create a function to get common skills (optional)
CREATE OR REPLACE FUNCTION get_common_skills()
RETURNS TABLE(skill TEXT, count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT unnest(skills) as skill, COUNT(*) as count
    FROM resumes
    WHERE skills IS NOT NULL
    GROUP BY unnest(skills)
    ORDER BY count DESC
    LIMIT 20;
END;
$$ LANGUAGE plpgsql;
