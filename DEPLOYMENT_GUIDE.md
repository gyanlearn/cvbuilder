# Production Deployment Guide

Deploy your CV Parser & ATS Scorer to production on Render.com in minutes!

## 🚀 Quick Production Setup

### Step 1: Prepare Your Accounts

1. **GitHub Account**: Ensure your code is pushed to a GitHub repository
2. **Render.com Account**: Sign up at [render.com](https://render.com)
3. **Supabase Account**: Sign up at [supabase.com](https://supabase.com)
4. **Google AI Studio**: Get API key at [aistudio.google.com](https://aistudio.google.com)

### Step 2: Set Up Supabase Database

1. **Create New Project**:
   - Go to [supabase.com](https://supabase.com)
   - Click "New Project"
   - Choose organization and set project name: `cv-parser-db`
   - Set a strong database password
   - Choose a region close to your users

2. **Create Database Table**:
   - Go to SQL Editor in your Supabase dashboard
   - Copy and paste the content from `supabase_setup.sql`
   - Click "Run" to create the table and indexes

3. **Get Credentials**:
   - Go to Settings > API
   - Copy your `Project URL` and `anon public` key
   - Save these for later

### Step 3: Get Google Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com)
2. Click "Get API Key" 
3. Create new API key or use existing one
4. Copy the API key (starts with `AIza...`)

### Step 4: Deploy Backend to Render

1. **Connect GitHub**:
   - Go to [render.com](https://render.com)
   - Click "New +" > "Web Service"
   - Connect your GitHub account
   - Select your CV parser repository

2. **Configure Backend Service**:
   ```
   Name: cv-parser-backend
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```

3. **Set Environment Variables**:
   - Click "Environment" tab
   - Add these variables:
     ```
     SUPABASE_URL=https://your-project.supabase.co
     SUPABASE_KEY=your_supabase_anon_key
     GEMINI_API_KEY=your_gemini_api_key
     ```

4. **Deploy**:
   - Click "Create Web Service"
   - Wait for deployment (5-10 minutes)
   - Note your backend URL: `https://cv-parser-backend.onrender.com`

### Step 5: Deploy Frontend to Render

1. **Create Static Site**:
   - Click "New +" > "Static Site"
   - Select same GitHub repository

2. **Configure Frontend**:
   ```
   Name: cv-parser-frontend
   Build Command: echo "No build required"
   Publish Directory: frontend
   ```

3. **Deploy**:
   - Click "Create Static Site"
   - Your frontend will be available at: `https://cv-parser-frontend.onrender.com`

### Step 6: Test Your Production App

1. Visit your frontend URL
2. Upload a test resume (PDF, DOCX, or TXT)
3. Verify ATS scoring works
4. Check Supabase dashboard for stored data

## 🔧 Alternative: One-Click Deploy

Use the `render.yaml` file for one-click deployment:

1. Fork this repository on GitHub
2. Go to [render.com](https://render.com)
3. Click "New +" > "Blueprint"
4. Connect your forked repository
5. Set environment variables in Render dashboard
6. Deploy both services automatically

## 🌐 Production URLs

After deployment, you'll have:
- **Frontend**: `https://cv-parser-frontend.onrender.com`
- **Backend**: `https://cv-parser-backend.onrender.com`
- **API Docs**: `https://cv-parser-backend.onrender.com/docs`

## 🔐 Security Notes

- Environment variables are encrypted on Render
- Supabase uses Row Level Security (RLS)
- API keys are never exposed to frontend
- File uploads are validated and size-limited

## 💰 Cost Estimation

### Free Tier Limits:
- **Render**: 750 hours/month free (sufficient for testing)
- **Supabase**: 500MB database + 2GB bandwidth free
- **Google Gemini**: 15 requests/minute free

### Paid Plans (if needed):
- **Render**: $7/month for always-on service
- **Supabase**: $25/month for Pro plan
- **Google Gemini**: Pay-per-use (very affordable)

## 🚨 Troubleshooting

### Backend Issues:
1. **Build Fails**: Check `requirements.txt` format
2. **Environment Variables**: Ensure all 3 keys are set correctly
3. **Supabase Connection**: Verify URL and key format
4. **Gemini API**: Check API key validity and quotas

### Frontend Issues:
1. **CORS Errors**: Backend will handle CORS automatically
2. **API Connection**: Verify backend URL in `script.js`
3. **File Upload**: Check backend logs for detailed errors

### Database Issues:
1. **Table Not Found**: Run `supabase_setup.sql` in SQL Editor
2. **Permission Denied**: Check RLS policy in Supabase
3. **Connection Error**: Verify Supabase URL and key

## 📊 Monitoring

### Render Dashboard:
- View deployment logs
- Monitor resource usage
- Check service health

### Supabase Dashboard:
- View uploaded resumes
- Monitor database usage
- Check API logs

### Google AI Studio:
- Monitor API usage
- Track quotas and billing

## 🔄 Updates

To update your production app:
1. Push changes to GitHub
2. Render will auto-deploy (if enabled)
3. Or manually trigger deployment in Render dashboard

## 📱 Mobile Testing

Your app is mobile-first and will work perfectly on:
- iOS Safari
- Android Chrome
- All modern mobile browsers

## 🎯 Next Steps

After successful deployment:
1. Share your app URL with users
2. Monitor usage and performance
3. Add custom domain (optional)
4. Implement user analytics (optional)
5. Scale resources as needed

## 🆘 Support

If you encounter issues:
1. Check Render logs for backend errors
2. Use browser dev tools for frontend debugging
3. Verify all environment variables are set
4. Test API endpoints directly using the `/docs` interface

Your production CV Parser & ATS Scorer is now ready to help users optimize their resumes! 🎉
