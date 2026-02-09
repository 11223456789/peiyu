# Vercel Serverless Function Entry Point
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.main import app

# Vercel handler
handler = app
