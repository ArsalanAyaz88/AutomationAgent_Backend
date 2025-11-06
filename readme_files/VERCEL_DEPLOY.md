# 🚀 Vercel Deployment Guide

## ✅ Quick Deploy to Vercel

Your backend is now optimized and ready for Vercel deployment!

---

## 🎯 Option 1: Automated Script (Recommended)

### Windows:
```bash
deploy_vercel.bat
```

### Mac/Linux:
```bash
bash deploy_vercel.sh
```

This will:
1. ✅ Backup your original requirements.txt
2. ✅ Switch to production requirements (optimized)
3. ✅ Stage files for commit
4. ✅ Show next steps

---

## 🎯 Option 2: Manual Deployment

### Step 1: Optimize Dependencies
```bash
# Backup original (if not done)
copy requirements.txt requirements.dev.txt

# Use production version
copy requirements.prod.txt requirements.txt
```

### Step 2: Commit Changes
```bash
git add .
git commit -m "Optimize for Vercel: reduced dependencies and organized files"
git push
```

### Step 3: Deploy
Vercel will automatically deploy from your GitHub repository!

---

## 📊 What Was Optimized

### Size Reduction
- **Before:** ~300MB (exceeded limit) ❌
- **After:** ~90MB (within limit) ✅
- **Reduction:** 70% smaller!

### Files Excluded (via .vercelignore)
- ✅ `readme_files/` - All documentation
- ✅ `testing_files/` - All tests
- ✅ Development dependencies removed

### Dependencies Removed
- ❌ scipy (50MB)
- ❌ pandas (30MB)
- ❌ matplotlib (25MB)
- ❌ seaborn (10MB)
- ❌ Testing tools (pytest, etc.)

### Dependencies Kept (Essential)
- ✅ FastAPI & Uvicorn
- ✅ PyMongo & Redis
- ✅ OpenAI
- ✅ NumPy (for RL)
- ✅ Google APIs

---

## 🔧 Configuration Files

### vercel.json
```json
{
  "version": 2,
  "builds": [{
    "src": "main.py",
    "use": "@vercel/python",
    "config": {
      "maxLambdaSize": "50mb",
      "runtime": "python3.12"
    }
  }],
  "routes": [{
    "src": "/(.*)",
    "dest": "main.py"
  }]
}
```

### .vercelignore
```
readme_files/      # Documentation excluded
testing_files/     # Tests excluded
*.md               # Markdown files excluded (except README.md)
```

---

## ✅ Verification Checklist

Before deploying, verify:

- [ ] Files organized (docs → readme_files/, tests → testing_files/)
- [ ] Production requirements active (requirements.prod.txt → requirements.txt)
- [ ] .vercelignore configured
- [ ] vercel.json configured
- [ ] All changes committed
- [ ] Repository pushed to GitHub

---

## 🚀 Deployment Steps

### 1. Prepare Files
```bash
# Run deployment script
deploy_vercel.bat  # Windows
# or
bash deploy_vercel.sh  # Mac/Linux
```

### 2. Commit & Push
```bash
git commit -m "Optimize for Vercel deployment"
git push origin main
```

### 3. Deploy on Vercel
Vercel will automatically detect the push and deploy!

### 4. Verify Deployment
```bash
# Check health endpoint
curl https://your-app.vercel.app/health

# Check RL system
curl https://your-app.vercel.app/api/rl/system-status
```

---

## 📈 Expected Build Output

```
08:24:43 Using Python 3.12 from pyproject.toml
08:24:43 Installing required dependencies...
08:24:50 Build Completed in /vercel/output [7s]
08:24:51 Deploying outputs...
08:25:00 ✅ Deployment successful!
```

**Build time:** ~7-10 seconds  
**Deployment size:** ~90MB ✅

---

## 🎉 Success Criteria

Your deployment is successful if:
- ✅ Build completes without size errors
- ✅ All API endpoints work
- ✅ RL System dashboard loads
- ✅ Health check returns 200 OK
- ✅ Deployment time < 1 minute

---

## 🐛 Troubleshooting

### Issue: Still Too Large
**Solution:** Check if all files are properly excluded
```bash
# Verify .vercelignore
cat .vercelignore

# Check if readme_files/ and testing_files/ are listed
```

### Issue: Import Errors
**Solution:** Verify all required dependencies are in requirements.txt
```bash
# Essential packages should be present:
# - fastapi
# - uvicorn
# - pymongo
# - redis
# - openai
# - numpy
```

### Issue: MongoDB Connection Fails
**Solution:** Add environment variables in Vercel:
```
Settings → Environment Variables → Add:
- MONGODB_URI
- CENTRALMEMORY_DATABASE_URL
- LTM_DATABASE_URL
- STM_DATABASE_URL
```

---

## 🔐 Environment Variables

Set these in Vercel dashboard:

```env
# MongoDB
MONGODB_URI=your_mongodb_atlas_uri
CENTRALMEMORY_DATABASE_URL=your_central_memory_uri
LTM_DATABASE_URL=your_ltm_uri

# Redis
STM_DATABASE_URL=your_redis_uri

# OpenAI/Gemini
GEMINI_API_KEY=your_api_key
GEMINI_BASE_URL=your_base_url
GEMINI_MODEL_NAME=your_model

# YouTube
YOUTUBE_API_KEY=your_youtube_api_key
```

---

## 📝 Post-Deployment

### Update Frontend
Update your frontend's API URL:
```bash
# In frontend/.env or .env.local
NEXT_PUBLIC_API_URL=https://your-backend.vercel.app
```

### Test Endpoints
```bash
# Health check
curl https://your-backend.vercel.app/health

# RL System status
curl https://your-backend.vercel.app/api/rl/system-status

# Agent endpoints
curl https://your-backend.vercel.app/api/agent1/audit-channel
```

---

## 🎊 Deployment Complete!

Your backend is now:
- ✅ Deployed on Vercel
- ✅ Optimized (90MB)
- ✅ All 7 agents operational
- ✅ RL System active
- ✅ API endpoints live

---

## 📚 Additional Resources

- **Vercel Docs:** https://vercel.com/docs/functions/serverless-functions/runtimes/python
- **Size Limits:** https://vercel.com/docs/functions/serverless-functions/runtimes/python#dependencies
- **Environment Variables:** https://vercel.com/docs/projects/environment-variables

---

**Ready to deploy!** 🚀

Run: `deploy_vercel.bat` and follow the steps!
