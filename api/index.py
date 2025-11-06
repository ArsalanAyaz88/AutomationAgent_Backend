"""
Vercel serverless function entry point.
This file imports the FastAPI app from main.py and exposes it for Vercel.
"""
from main import app

# Vercel will use this app instance
handler = app
