"""
Netlify serverless function handler for FastAPI app
Uses Mangum to adapt FastAPI (ASGI) to AWS Lambda/Netlify Functions
"""
import sys
import os

# Add parent directories to path to import chat_interface
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.insert(0, project_root)

# Import after path is set
from mangum import Mangum
from chat_interface import app

# Create handler for Netlify Functions
# lifespan="off" because Netlify Functions don't support lifespan events
handler = Mangum(app, lifespan="off")
