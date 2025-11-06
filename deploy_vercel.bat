@echo off
REM Vercel Deployment Script for YouTube Agents Backend (Windows)

echo ================================
echo Vercel Deployment - Optimized
echo ================================
echo.

REM Check if we're in the Backend directory
if not exist "main.py" (
    echo Error: main.py not found. Please run this script from the Backend directory.
    exit /b 1
)

echo Optimizing for Vercel deployment...
echo.

REM Backup original requirements if not already backed up
if not exist "requirements.dev.txt" (
    copy requirements.txt requirements.dev.txt >nul
    echo [OK] Backed up original requirements to requirements.dev.txt
) else (
    echo [INFO] requirements.dev.txt already exists
)

REM Use production requirements
copy requirements.prod.txt requirements.txt >nul
echo [OK] Switched to production requirements (optimized)

REM Stage files for commit
git add requirements.txt requirements.prod.txt .vercelignore vercel.json
echo [OK] Files staged for commit

echo.
echo ================================
echo Ready for Vercel Deployment!
echo ================================
echo.
echo Next steps:
echo 1. git commit -m "Optimize for Vercel deployment"
echo 2. git push
echo 3. Vercel will auto-deploy from GitHub
echo.
echo Note: Deployment size optimized from 300MB to ~90MB
echo.

pause
