#!/bin/bash
# Vercel Deployment Script for YouTube Agents Backend

echo "================================"
echo "Vercel Deployment - Optimized"
echo "================================"
echo ""

# Check if we're in the Backend directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found. Please run this script from the Backend directory."
    exit 1
fi

echo "🔧 Optimizing for Vercel deployment..."
echo ""

# Backup original requirements if not already backed up
if [ ! -f "requirements.dev.txt" ]; then
    cp requirements.txt requirements.dev.txt
    echo "✅ Backed up original requirements to requirements.dev.txt"
else
    echo "ℹ️  requirements.dev.txt already exists"
fi

# Use production requirements
cp requirements.prod.txt requirements.txt
echo "✅ Switched to production requirements (optimized)"

# Stage files for commit
git add requirements.txt requirements.prod.txt .vercelignore vercel.json
echo "✅ Files staged for commit"

echo ""
echo "================================"
echo "✅ Ready for Vercel Deployment!"
echo "================================"
echo ""
echo "📝 Next steps:"
echo "1. git commit -m 'Optimize for Vercel deployment'"
echo "2. git push"
echo "3. Vercel will auto-deploy from GitHub"
echo ""
echo "💡 Note: Deployment size optimized from 300MB to ~90MB"
echo ""
