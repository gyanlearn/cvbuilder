#!/usr/bin/env python3
"""
Test script for the CV Parser & ATS Scorer backend
Run this to verify all components are working correctly
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_backend_health():
    """Test if the backend is running and healthy"""
    try:
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            print("✅ Backend is running and healthy")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running. Please start the server first.")
        return False

def test_environment_variables():
    """Test if all required environment variables are set"""
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'GEMINI_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file")
        return False
    else:
        print("✅ All environment variables are set")
        return True

def test_supabase_connection():
    """Test Supabase connection"""
    try:
        from supabase import create_client, Client
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            print("❌ Supabase credentials not found")
            return False
        
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Test connection by trying to query the resumes table
        result = supabase.table("resumes").select("id").limit(1).execute()
        print("✅ Supabase connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {str(e)}")
        return False

def test_gemini_connection():
    """Test Gemini AI connection"""
    try:
        import google.generativeai as genai
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ Gemini API key not found")
            return False
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Test with a simple prompt
        response = model.generate_content("Hello, this is a test.")
        if response.text:
            print("✅ Gemini AI connection successful")
            return True
        else:
            print("❌ Gemini AI response was empty")
            return False
            
    except Exception as e:
        print(f"❌ Gemini AI connection failed: {str(e)}")
        return False

def test_file_upload():
    """Test file upload endpoint with a sample text file"""
    try:
        # Create a sample resume text file
        sample_resume = """
        John Doe
        Software Engineer
        john.doe@email.com
        +1 (555) 123-4567
        
        SUMMARY
        Experienced software engineer with 5 years of experience in Python, JavaScript, and React.
        
        SKILLS
        Python, JavaScript, React, Node.js, SQL, Git, Docker
        
        EXPERIENCE
        Senior Developer - Tech Corp (2020-2023)
        - Developed web applications using React and Node.js
        - Led team of 5 developers
        
        Junior Developer - Startup Inc (2018-2020)
        - Built REST APIs using Python and Flask
        - Collaborated with cross-functional teams
        
        EDUCATION
        Bachelor of Science in Computer Science
        University of Technology (2014-2018)
        
        LinkedIn: linkedin.com/in/johndoe
        GitHub: github.com/johndoe
        """
        
        # Create temporary file
        with open("test_resume.txt", "w") as f:
            f.write(sample_resume)
        
        # Test upload
        with open("test_resume.txt", "rb") as f:
            files = {"file": ("test_resume.txt", f, "text/plain")}
            response = requests.post("http://localhost:8000/upload-resume", files=files)
        
        # Clean up
        os.remove("test_resume.txt")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ File upload test successful")
                print(f"   ATS Score: {result.get('ats_score')}")
                print(f"   Issues found: {len(result.get('issues', []))}")
                return True
            else:
                print("❌ File upload returned success=false")
                return False
        else:
            print(f"❌ File upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ File upload test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing CV Parser & ATS Scorer Backend")
    print("=" * 50)
    
    tests = [
        ("Backend Health", test_backend_health),
        ("Environment Variables", test_environment_variables),
        ("Supabase Connection", test_supabase_connection),
        ("Gemini AI Connection", test_gemini_connection),
        ("File Upload", test_file_upload),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your backend is ready to use.")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    main()
