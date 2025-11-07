#!/usr/bin/env python3
"""
Professional Chat Interface for Sage Agent - r.Potential.ai Brand
IMPROVED: Logging, caching, rate limiting, error handling, timeouts
"""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, validator
import os
import json
import hashlib
import asyncio
from functools import lru_cache
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from cachetools import TTLCache
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from loguru import logger
import traceback
from dotenv import load_dotenv

# Load environment variables from .env file FIRST, before any other imports
load_dotenv()

# Now import SageAgent after .env is loaded
from sage_agent_simple import SageAgent

# Storage for conversations
CONVERSATIONS_FILE = "conversations.json"

def load_conversations():
    """Load all conversations from file"""
    if os.path.exists(CONVERSATIONS_FILE):
        try:
            with open(CONVERSATIONS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_conversations(conversations):
    """Save conversations to file"""
    try:
        with open(CONVERSATIONS_FILE, 'w') as f:
            json.dump(conversations, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving conversations: {str(e)}")

# Configure logging
logger.add(
    "logs/chat_interface.log",
    rotation="100 MB",
    retention="10 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    backtrace=True,
    diagnose=True
)

app = FastAPI(
    title="Sage Strategic Intelligence Agent",
    description="AI-powered strategic intelligence chat interface",
    version="2.0.0"
)

# Mount static files for logo
import os
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware (optional, for production)
if os.getenv("TRUSTED_HOSTS"):
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=os.getenv("TRUSTED_HOSTS").split(",")
    )

# Cache for answers (TTL: 1 hour)
answer_cache: TTLCache = TTLCache(maxsize=1000, ttl=3600)

# Initialize agent
data_path = os.getenv("DATA_PATH", "results/rpotential_filtered_focused_data.csv")
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    logger.error("OPENAI_API_KEY environment variable not set")
    raise ValueError("OPENAI_API_KEY environment variable required")

# Check if data file exists, try multiple locations
if not os.path.exists(data_path):
    logger.warning(f"⚠️ Data file not found at {data_path}, checking alternative locations...")
    alt_paths = [
        f"/app/{data_path}",
        f"./{data_path}",
        "results/rpotential_filtered_focused_data.csv",
        "/app/results/rpotential_filtered_focused_data.csv",
        os.path.join(os.path.dirname(__file__), data_path),
        os.path.join(os.path.dirname(__file__), "results", "rpotential_filtered_focused_data.csv")
    ]
    found = False
    for alt_path in alt_paths:
        if os.path.exists(alt_path):
            data_path = alt_path
            logger.info(f"✅ Found data file at {data_path}")
            found = True
            break
    if not found:
        logger.error(f"❌ Data file not found in any location. Checked: {[data_path] + alt_paths}")
        logger.error("Current working directory: " + os.getcwd())
        logger.error("Files in current dir: " + str(os.listdir('.')))
        if os.path.exists('results'):
            logger.error("Files in results/: " + str(os.listdir('results')))
        raise FileNotFoundError(f"Data file not found. Please ensure results/rpotential_filtered_focused_data.csv exists or set DATA_PATH environment variable.")

try:
    agent = SageAgent(data_path=data_path, api_key=api_key)
    logger.info(f"✅ Agent initialized with {len(agent.df)} posts from {data_path}")
except Exception as e:
    logger.error(f"❌ Failed to initialize agent: {str(e)}")
    logger.error(traceback.format_exc())
    raise

# CEO Questions - Full list of 50 questions from CEO_QUESTIONS_FULL_LIST.md
SUGGESTED_QUESTIONS = [
    "How do our human-agent configurations compare to industry leaders?",
    "Do I have the right talents and tools to execute our strategy?",
    "How do global conditions impact our current workforce-AI configurations?",
    "What roles are at risk of skill obsolescence and how can we help affected employees understand their full potential?",
    "How do we identify potential top performers in the AI era?",
    "Beyond the PR noise - Which enterprise vendors are shipping meaningful product to win the AI + workforce platform war— BigTech or upstarts?",
    "Which managers are talent multipliers and which are talent drainers?",
    "Which high-performing individuals are being suffocated by process or culture?",
    "Which critical teams are one resignation away from operational collapse?",
    "Which core skills we depend on will be obsolete in 3 years and how are we pivoting?",
    "Which competitors are attracting our talent and what are they offering differently?",
    "Where is AI adoption improving output by >20% and where is it adding noise?",
    "Where do we have untapped leadership potential we're not promoting?",
    "Where could we trade multiple mediocre performers for one all-star financially?",
    "Where are we overpaying or underpaying relative to market in ways that affect retention?",
    "What's the cheapest lever to double talent productivity without adding headcount?",
    "What unconventional talent pools could we tap for competitive advantage?",
    "What operational issues cause the most employee frustration and attrition risk?",
    "What percentage of our hires deliver outsized returns and who are underperforming?",
    "What is the ROI of our current workforce in hard financial terms vs market?",
    "What is our hidden attrition rate of people mentally quitting but staying?",
    "What black swan talent risks could gut our execution and how resilient are we?",
    "How much time do our top performers waste on low-value tasks weekly?",
    "How much of our productivity depends on informal power nodes in the org chart and hidden work?",
    "How many high-value employees are at risk of burnout or leaving?",
    "How is our employer brand ranked vs competitors among top talent pools for AI?",
    "How are employees adapting to AI tools and what productivity impacts are we seeing?",
    "How can I increase productivity and optimize SG&A without layoffs?",
    "How can I automate work without dehumanizing my workers?",
    "What KPIs should we monitor to ensure maximum synergy between human potential and AI capabilities?",
    "How is X project or strategy going for Y?",
    "Are there biases in job assignments that could be mitigated by better understanding employee potential?",
    "How can we ensure AI integration enhances employee satisfaction rather than creating resistance?",
    "What would our company look like in 5 years if we fully leveraged AI across all business units?",
    "Which processes are underperforming and how can AI address inefficiencies?",
    "Simulate a cyberattack disrupting AI systems: What human redundancies are necessary?",
    "How can we align AI adoption with career growth to retain top talent?",
    "What personalized development plans would prepare high-potential employees for future leadership in an AI-native world?",
    "How can we dynamically reallocate resources using real-time data?",
    "What's the ROI of automating workflows versus upskilling employees?",
    "Can you audit our AI deployment plans for bias or compliance risks?",
    "What are the operational risks of over-relying on AI and how do we ensure human oversight?",
    "Which departments have the highest potential for AI-driven innovation?",
    "Where do intersections between untapped employee skills and agent capabilities suggest new opportunities?",
    "If a competitor launches a disruptive AI product how can we respond?",
    "How do we qualify and select the right agents that best match our brand and processes?",
    "Simulate a 30% demand surge: What mix of human workforce scaling and AI tools would be required?",
    "Run simulations for 20% operational efficiency: What human-agent ratio is needed in specific functions?",
    "Which roles are most critical for future growth and how can we upskill employees or deploy AI to fill gaps?",
    "How do current job roles and employee skills align with our 5-year strategic goals and where are the gaps?"
]

class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="The question to ask")
    estimates_ok: bool = Field(default=False, description="Allow estimates in the answer")
    
    @validator('question')
    def validate_question(cls, v):
        if not v or not v.strip():
            raise ValueError("Question cannot be empty")
        if len(v.strip()) < 3:
            raise ValueError("Question must be at least 3 characters long")
        return v.strip()

def get_cache_key(question: str, estimates_ok: bool) -> str:
    """Generate cache key for a question"""
    key_string = f"{question.lower().strip()}:{estimates_ok}"
    return hashlib.md5(key_string.encode()).hexdigest()

@app.get("/", response_class=HTMLResponse)
async def chat_interface():
    """Serve the main chat interface"""
    questions_json = json.dumps(SUGGESTED_QUESTIONS)
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>r.Potential - Strategic Intelligence</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=EB+Garamond:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Helvetica Neue', sans-serif;
            background: #000000;
            color: #ffffff;
            height: 100vh;
            overflow: hidden;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            min-height: 100vh;
        }}
        
        .header-left {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .logo {{
            width: 43px;
            height: 43px;
            background: transparent;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow: visible;
        }}
        
        .logo svg {{
            width: 22px;
            height: 22px;
        }}
        
        .brand-name {{
            font-size: 16px;
            font-weight: 600;
            letter-spacing: -0.3px;
            font-family: 'EB Garamond', serif;
        }}
        
        .nav {{
            display: flex;
            gap: 8px;
            align-items: center;
        }}
        
        .nav-item {{
            padding: 8px 16px;
            font-size: 14px;
            font-weight: 500;
            color: rgba(26,26,26,0.7);
            cursor: pointer;
            border-radius: 20px;
            transition: all 0.2s;
            border: none;
            background: none;
        }}
        
        .nav-item:hover {{
            color: rgba(26,26,26,0.9);
            background: rgba(0,0,0,0.05);
        }}
        
        .nav-item.active {{
            background: rgba(233, 88, 11, 0.1);
            color: #E9580B;
        }}
        
        .header-date {{
            font-size: 14px;
            color: rgba(26,26,26,0.7);
            font-weight: 400;
        }}
        
        .app-container {{
            display: flex;
            flex-direction: column;
            height: 100vh;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #0f0f0f 100%);
        }}
        
        .content {{
            display: flex;
            flex: 1;
            overflow: hidden;
        }}
        
        .sidebar {{
            width: 320px;
            background: rgba(20, 20, 20, 0.8);
            color: #ffffff;
            display: flex;
            flex-direction: column;
            border-right: 1px solid rgba(255,255,255,0.08);
            overflow-y: auto;
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
        }}
        
        .sidebar-header {{
            padding: 32px 24px 24px;
            border-bottom: 1px solid rgba(255,255,255,0.08);
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .sidebar-logo {{
            width: 64px;
            height: 64px;
            border-radius: 16px;
            overflow: hidden;
            flex-shrink: 0;
            box-shadow: 0 8px 24px rgba(0,0,0,0.3);
            background: rgba(255,255,255,0.05);
            padding: 8px;
        }}
        
        .sidebar-logo img {{
            width: 100%;
            height: 100%;
            object-fit: contain;
        }}
        
        .sidebar-brand {{
            font-family: 'EB Garamond', serif;
            font-size: 24px;
            font-weight: 600;
            color: #ffffff;
            letter-spacing: -0.5px;
        }}
        
        .new-chat-btn {{
            margin: 20px 24px;
            padding: 14px 20px;
            background: linear-gradient(135deg, #E9580B 0%, #d14a09 100%);
            color: white;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            font-weight: 600;
            font-size: 14px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            box-shadow: 0 4px 16px rgba(233, 88, 11, 0.3);
        }}
        
        .new-chat-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(233, 88, 11, 0.4);
            background: linear-gradient(135deg, #f56a1c 0%, #e55b0a 100%);
        }}
        
        .new-chat-btn:active {{
            transform: translateY(0);
        }}
        
        .conversations-list {{
            flex: 1;
            padding: 12px;
            overflow-y: auto;
        }}
        
        .conversation-item {{
            padding: 14px 16px;
            margin-bottom: 6px;
            background: rgba(255,255,255,0.03);
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            border-left: 3px solid transparent;
            font-size: 13px;
            word-break: break-word;
            color: rgba(255,255,255,0.8);
            margin-left: 12px;
            margin-right: 12px;
        }}
        
        .conversation-item:hover {{
            background: rgba(255,255,255,0.06);
            transform: translateX(4px);
        }}
        
        .conversation-item.active {{
            background: rgba(233, 88, 11, 0.15);
            border-left-color: #E9580B;
            color: #ffffff;
        }}
        
        .conversation-timestamp {{
            font-size: 11px;
            color: rgba(255,255,255,0.4);
            margin-top: 6px;
        }}
        
        .main {{
            flex: 1;
            display: flex;
            flex-direction: column;
        }}
        
        .chat-area {{
            flex: 1;
            overflow-y: auto;
            padding: 60px 120px;
            background: transparent;
            scroll-behavior: smooth;
            position: relative;
        }}
        
        .chat-area::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: 
                radial-gradient(circle at 20% 30%, rgba(233, 88, 11, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 70%, rgba(233, 88, 11, 0.05) 0%, transparent 50%);
            pointer-events: none;
        }}
        
        .chat-area::-webkit-scrollbar {{
            width: 8px;
        }}
        
        .chat-area::-webkit-scrollbar-thumb {{
            background: rgba(255,255,255,0.2);
            border-radius: 4px;
        }}
        
        .chat-area::-webkit-scrollbar-thumb:hover {{
            background: rgba(255,255,255,0.3);
        }}
        
        .message {{
            display: flex;
            gap: 20px;
            margin-bottom: 40px;
            animation: fadeIn 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            z-index: 1;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .avatar {{
            width: 56px;
            height: 56px;
            border-radius: 18px;
            flex-shrink: 0;
            background: rgba(255,255,255,0.05);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            font-weight: 600;
            color: white;
            box-shadow: 
                0 8px 32px rgba(0,0,0,0.3),
                0 0 0 1px rgba(255,255,255,0.1) inset;
            overflow: hidden;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }}
        
        .avatar img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            border-radius: 18px;
        }}
        
        .message-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 8px;
        }}
        
        .message-author {{
            font-size: 14px;
            font-weight: 600;
            color: rgba(255,255,255,0.9);
            letter-spacing: -0.2px;
        }}
        
        .message-content {{
            flex: 1;
            max-width: 900px;
        }}
        
        .message-text {{
            font-size: 16px;
            line-height: 1.75;
            color: rgba(255,255,255,0.9);
            margin-bottom: 12px;
            white-space: pre-wrap;
            word-wrap: break-word;
            background: rgba(255, 255, 255, 0.03);
            padding: 24px 28px;
            border-radius: 20px;
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: 
                0 8px 32px rgba(0,0,0,0.2),
                0 0 0 1px rgba(255,255,255,0.05) inset;
        }}
        
        .message-text p {{
            margin: 16px 0;
            line-height: 1.75;
            color: rgba(255,255,255,0.9);
        }}
        
        .message-text blockquote.luxury-citation {{
            background: linear-gradient(135deg, rgba(233, 88, 11, 0.12) 0%, rgba(233, 88, 11, 0.06) 100%) !important;
            border-left: 4px solid #E9580B !important;
            color: rgba(255,255,255,0.95) !important;
            padding: 20px 24px !important;
            border-radius: 12px !important;
            margin: 24px 0 !important;
            box-shadow: 0 4px 16px rgba(0,0,0,0.1) !important;
            backdrop-filter: blur(10px) !important;
            -webkit-backdrop-filter: blur(10px) !important;
            transition: all 0.3s ease !important;
        }}
        
        .message-text blockquote.luxury-citation:hover {{
            transform: translateX(4px) !important;
            box-shadow: 0 6px 24px rgba(233, 88, 11, 0.2) !important;
            border-left-width: 6px !important;
        }}
        
        .message-text blockquote.luxury-citation a {{
            color: #E9580B !important;
            text-decoration: none !important;
            font-weight: 600 !important;
            transition: all 0.2s !important;
        }}
        
        .message-text blockquote.luxury-citation a:hover {{
            background: rgba(233, 88, 11, 0.25) !important;
            transform: translateX(2px) !important;
        }}
        
        .message-text .luxury-section-header {{
            margin-top: 40px !important;
            margin-bottom: 24px !important;
            padding-bottom: 16px !important;
            border-bottom: 2px solid rgba(233, 88, 11, 0.3) !important;
        }}
        
        .message-text .luxury-section-header h1,
        .message-text .luxury-section-header h2 {{
            font-family: 'EB Garamond', serif !important;
            font-weight: 700 !important;
            letter-spacing: -1px !important;
            color: #ffffff !important;
        }}
        
        .message-text li {{
            margin: 16px 0 !important;
            padding-left: 24px !important;
            position: relative !important;
            line-height: 1.8 !important;
            color: rgba(255,255,255,0.9) !important;
        }}
        
        .message-text li::before {{
            content: '•' !important;
            position: absolute !important;
            left: 0 !important;
            color: #E9580B !important;
            font-size: 24px !important;
            font-weight: 700 !important;
            line-height: 1 !important;
        }}
        
        .message-text strong {{
            color: #ffffff;
            font-weight: 600;
        }}
        
        .message-text h2, .message-text h3 {{
            color: #ffffff;
            margin-top: 32px;
            margin-bottom: 16px;
        }}
        
        .message-text .cursor {{
            display: inline-block;
            width: 2px;
            height: 18px;
            background: #1a1a1a;
            margin-left: 2px;
            animation: blink 1s infinite;
            vertical-align: baseline;
        }}
        
        @keyframes blink {{
            0%, 50% {{ opacity: 1; }}
            51%, 100% {{ opacity: 0; }}
        }}
        
        .message-meta {{
            font-size: 12px;
            color: rgba(255,255,255,0.5);
            margin-top: 16px;
            display: flex;
            gap: 16px;
            align-items: center;
        }}
        
        .confidence-badge {{
            display: inline-flex;
            align-items: center;
            padding: 6px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }}
        
        .confidence-high {{
            background: rgba(16, 185, 129, 0.2);
            color: #10b981;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }}
        
        .confidence-medium {{
            background: rgba(245, 158, 11, 0.2);
            color: #f59e0b;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }}
        
        .confidence-low {{
            background: rgba(239, 68, 68, 0.2);
            color: #ef4444;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }}
        
        .welcome {{
            max-width: 900px;
            margin: 0 auto;
            padding: 80px 0;
            display: block !important;
            visibility: visible !important;
            text-align: center;
        }}
        
        .welcome-logo {{
            width: 160px;
            height: 160px;
            margin: 0 auto 40px;
            border-radius: 32px;
            overflow: hidden;
            box-shadow: 
                0 20px 60px rgba(0,0,0,0.5),
                0 0 0 1px rgba(255,255,255,0.1) inset;
            background: rgba(255,255,255,0.05);
            padding: 16px;
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
        }}
        
        .welcome-logo img {{
            width: 100%;
            height: 100%;
            object-fit: contain;
        }}
        
        .welcome h1 {{
            font-size: 48px;
            font-weight: 700;
            margin-bottom: 24px;
            color: #ffffff;
            letter-spacing: -1px;
            font-family: 'EB Garamond', serif;
        }}
        
        .welcome p {{
            font-size: 18px;
            color: rgba(255,255,255,0.7);
            line-height: 1.7;
            margin-bottom: 60px;
            font-weight: 400;
        }}
        
        .suggestions {{
            display: flex !important;
            flex-direction: column;
            gap: 8px;
            margin-top: 40px;
            visibility: visible !important;
            opacity: 1 !important;
            max-height: 600px;
            overflow-y: auto;
            border: none;
            border-radius: 0;
            background: transparent;
        }}
        
        .suggestions::-webkit-scrollbar {{
            width: 6px;
        }}
        
        .suggestions::-webkit-scrollbar-thumb {{
            background: rgba(255,255,255,0.2);
            border-radius: 3px;
        }}
        
        .suggestion-item {{
            padding: 20px 24px;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid rgba(255,255,255,0.1);
            text-align: left;
            font-size: 15px;
            color: rgba(255,255,255,0.8);
            line-height: 1.6;
            background: rgba(255,255,255,0.03);
            display: block !important;
            visibility: visible !important;
            border-radius: 16px;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }}
        
        .suggestion-item:first-child {{
            border-top: 1px solid rgba(255,255,255,0.1);
        }}
        
        .suggestion-item:last-child {{
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        
        .suggestion-item:hover {{
            background: rgba(233, 88, 11, 0.15);
            border-color: rgba(233, 88, 11, 0.3);
            transform: translateX(8px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        }}
        
        .input-area {{
            background: rgba(10, 10, 10, 0.8);
            padding: 32px 120px;
            border-top: 1px solid rgba(255,255,255,0.08);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            box-shadow: 0 -4px 24px rgba(0,0,0,0.3);
        }}
        
        .input-wrapper {{
            max-width: 900px;
            margin: 0 auto;
            display: flex;
            gap: 12px;
            align-items: center;
        }}
        
        .input-field {{
            flex: 1;
            padding: 18px 24px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            font-size: 16px;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            outline: none;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            color: rgba(255,255,255,0.9);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }}
        
        .input-field::placeholder {{
            color: rgba(255,255,255,0.4);
        }}
        
        .input-field:focus {{
            border-color: rgba(233, 88, 11, 0.5);
            box-shadow: 
                0 0 0 4px rgba(233, 88, 11, 0.1),
                0 8px 32px rgba(0,0,0,0.2);
            background: rgba(255,255,255,0.08);
        }}
        
        .send-button {{
            padding: 18px 36px;
            background: linear-gradient(135deg, #E9580B 0%, #d14a09 100%);
            color: white;
            border: none;
            border-radius: 16px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            box-shadow: 0 8px 24px rgba(233, 88, 11, 0.3);
            letter-spacing: -0.2px;
        }}
        
        .send-button:hover:not(:disabled) {{
            background: linear-gradient(135deg, #f56a1c 0%, #e55b0a 100%);
            transform: translateY(-2px);
            box-shadow: 0 12px 32px rgba(233, 88, 11, 0.4);
        }}
        
        .send-button:active:not(:disabled) {{
            transform: translateY(0);
        }}
        
        .send-button:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}
        
        .error-message {{
            background: rgba(239, 68, 68, 0.15);
            color: #ef4444;
            padding: 16px 20px;
            border-radius: 12px;
            margin-bottom: 16px;
            font-size: 14px;
            border: 1px solid rgba(239, 68, 68, 0.3);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }}
        
        .loading-indicator {{
            display: inline-flex;
            gap: 4px;
            align-items: center;
            color: rgba(255,255,255,0.6);
            font-size: 14px;
        }}
        
        .loading-dot {{
            width: 6px;
            height: 6px;
            background: rgba(255,255,255,0.6);
            border-radius: 50%;
            animation: bounce 1.4s infinite;
        }}
        
        .loading-dot:nth-child(2) {{ animation-delay: 0.2s; }}
        .loading-dot:nth-child(3) {{ animation-delay: 0.4s; }}
        
        @keyframes bounce {{
            0%, 80%, 100% {{ transform: translateY(0); opacity: 0.5; }}
            40% {{ transform: translateY(-8px); opacity: 1; }}
        }}
        
        .cache-badge {{
            display: inline-flex;
            align-items: center;
            padding: 6px 12px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: 600;
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
            margin-left: 8px;
            border: 1px solid rgba(59, 130, 246, 0.3);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }}
    </style>
</head>
<body>
    <div class="app-container">
        <div class="content">
            <div class="sidebar">
                <div class="sidebar-header">
                    <div class="sidebar-logo">
                        <img src="/static/logo.png" alt="r.Potential Logo" />
            </div>
                    <div class="sidebar-brand">r.Potential</div>
        </div>
                <button class="new-chat-btn" onclick="newChat()">+ New Chat</button>
                <div class="conversations-list" id="conversationsList"></div>
    </div>
    
            <div class="main">
        <div class="chat-area" id="chatArea">
            <div class="welcome" id="welcome">
                        <div class="welcome-logo">
                            <img src="/static/logo.png" alt="r.Potential Logo" />
                        </div>
                <h1>Strategic Intelligence</h1>
                <p>Ask questions about AI workforce optimization, talent intelligence, and competitive analysis</p>
                
                <div class="suggestions" id="suggestions">
                    <!-- Suggestions loaded by JavaScript -->
                </div>
            </div>
        </div>
        
        <div class="input-area">
            <div class="input-wrapper">
                <input type="text" 
                       class="input-field" 
                       id="questionInput" 
                               placeholder="Ask a strategic question..." 
                               autocomplete="off" 
                               maxlength="2000" />
                <button class="send-button" id="sendButton">Send</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        console.log('JavaScript is being parsed and executed.');
        let suggestedQuestions = {questions_json};
        let currentConversationId = null;
        let conversations = {{}};
        
        console.log('[INIT] Total questions loaded:', suggestedQuestions ? suggestedQuestions.length : 0);
        
        async function loadConversations() {{
            try {{
                const res = await fetch('/api/conversations');
                conversations = await res.json();
                renderConversationsList();
            }} catch (e) {{
                console.error('Error loading conversations:', e);
                conversations = {{}};
            }}
        }}
        
        function renderConversationsList() {{
            const list = document.getElementById('conversationsList');
            if (!list) return;
            
            list.innerHTML = '';
            
            const sortedConversations = Object.entries(conversations).sort((a, b) => {{
                const timeA = new Date(a[1].timestamp || 0).getTime();
                const timeB = new Date(b[1].timestamp || 0).getTime();
                return timeB - timeA;
            }});
            
            for (const [id, conv] of sortedConversations) {{
                const div = document.createElement('div');
                div.className = 'conversation-item' + (id === currentConversationId ? ' active' : '');
                div.onclick = () => loadConversation(id);
                
                const firstMsg = conv.messages && conv.messages[0] ? conv.messages[0].content.substring(0, 40) : 'New chat';
                const timestamp = new Date(conv.timestamp).toLocaleString();
                
                const msgDiv = document.createElement('div');
                msgDiv.textContent = escapeHtml(firstMsg) + '...';
                const timeDiv = document.createElement('div');
                timeDiv.className = 'conversation-timestamp';
                timeDiv.textContent = timestamp;
                div.appendChild(msgDiv);
                div.appendChild(timeDiv);
                list.appendChild(div);
            }}
        }}
        
        function newChat() {{
            currentConversationId = null;
            const chatArea = document.getElementById('chatArea');
            chatArea.innerHTML = '';
            
            const welcomeDiv = document.createElement('div');
            welcomeDiv.className = 'welcome';
            welcomeDiv.id = 'welcome';
            
            const logoDiv = document.createElement('div');
            logoDiv.className = 'welcome-logo';
            const logoImg = document.createElement('img');
            logoImg.src = '/static/logo.png';
            logoImg.alt = 'r.Potential Logo';
            logoDiv.appendChild(logoImg);
            
            const h1 = document.createElement('h1');
            h1.textContent = 'Strategic Intelligence';
            
            const p = document.createElement('p');
            p.textContent = 'Ask questions about AI workforce optimization, talent intelligence, and competitive analysis';
            
            const suggestionsDiv = document.createElement('div');
            suggestionsDiv.className = 'suggestions';
            suggestionsDiv.id = 'suggestions';
            
            welcomeDiv.appendChild(logoDiv);
            welcomeDiv.appendChild(h1);
            welcomeDiv.appendChild(p);
            welcomeDiv.appendChild(suggestionsDiv);
            
            chatArea.appendChild(welcomeDiv);
            renderSuggestions();
            renderConversationsList();
        }}
        
        async function loadConversation(convId) {{
            currentConversationId = convId;
            const conv = conversations[convId];
            const chatArea = document.getElementById('chatArea');
            
            chatArea.innerHTML = '';
            
            for (const msg of conv.messages || []) {{
                const div = document.createElement('div');
                div.className = 'message';
                
                const avatar = document.createElement('div');
                avatar.className = 'avatar';
                const avatarImg = document.createElement('img');
                avatarImg.src = msg.role === 'user' ? '/static/user_avatar.jpeg' : '/static/assistant_avatar.jpeg';
                avatarImg.alt = msg.role === 'user' ? 'User' : 'Assistant';
                avatar.appendChild(avatarImg);
                
                const contentDiv = document.createElement('div');
                contentDiv.className = 'message-content';
                
                const textDiv = document.createElement('div');
                textDiv.className = 'message-text';
                if (msg.role === 'assistant' && msg.content.includes('<blockquote>')) {{
                    textDiv.innerHTML = msg.content;
                }} else {{
                    textDiv.textContent = msg.content || '';
                }}
                
                const metaDiv = document.createElement('div');
                metaDiv.className = 'message-meta';
                const timeSpan = document.createElement('span');
                timeSpan.textContent = new Date(msg.timestamp).toLocaleTimeString();
                metaDiv.appendChild(timeSpan);
                
                contentDiv.appendChild(textDiv);
                contentDiv.appendChild(metaDiv);
                
                div.appendChild(avatar);
                div.appendChild(contentDiv);
                chatArea.appendChild(div);
            }}
            
            renderConversationsList();
            chatArea.scrollTop = chatArea.scrollHeight;
        }}
        
        function renderSuggestions() {{
            const container = document.getElementById('suggestions');
            if (!container) {{
                console.error('[ERROR] Suggestions container NOT FOUND');
                return;
            }}
            
            container.style.display = 'flex';
            container.style.visibility = 'visible';
            container.style.opacity = '1';
            
            if (!Array.isArray(suggestedQuestions)) {{
                console.error('[ERROR] suggestedQuestions is not an array:', suggestedQuestions);
                container.innerHTML = '<div class="suggestion-item" style="color: red;">Error: Questions not loaded properly</div>';
                return;
            }}
            
            if (suggestedQuestions.length === 0) {{
                console.warn('[WARN] No questions to display');
                container.innerHTML = '<div class="suggestion-item">No questions available</div>';
                return;
            }}
            
            container.innerHTML = '';
            
            suggestedQuestions.forEach((q, index) => {{
                if (!q || typeof q !== 'string') {{
                    console.warn('[WARN] Invalid question at index', index, ':', q);
                    return;
                }}
                
                const div = document.createElement('div');
                div.className = 'suggestion-item';
                div.textContent = q;
                div.style.display = 'block';
                div.style.visibility = 'visible';
                div.style.opacity = '1';
                div.onclick = function() {{ 
                    askQuestion(q); 
                }};
                container.appendChild(div);
            }});
        }}
        
        function askQuestion(question) {{
            const input = document.getElementById('questionInput');
            if (input) {{
                input.value = question;
                sendQuestion();
            }}
        }}
        
        function typewriterEffect(element, text, speed = 8, callback) {{
            // For HTML content, show all at once (typewriter doesn't work well with HTML)
            if (text.includes('<blockquote>') || text.includes('<strong>') || text.includes('<h')) {{
                element.innerHTML = text;
                if (callback) setTimeout(callback, 100);
                return;
            }}
            
            // Regular text typewriter effect
            let i = 0;
            element.innerHTML = '';
            
            function type() {{
                if (i < text.length) {{
                    element.innerHTML = escapeHtml(text.substring(0, i + 1)) + '<span class="cursor"></span>';
                    i++;
                    setTimeout(type, speed);
                }} else {{
                    element.innerHTML = escapeHtml(text);
                    if (callback) callback();
                }}
            }}
            
            type();
        }}
        
        function typewriterLuxury(element, htmlContent, callback) {{
            // LUXURY typewriter effect that handles HTML gracefully
            // Extract text content and HTML tags separately
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = htmlContent;
            const textContent = tempDiv.textContent || tempDiv.innerText || '';
            
            // If content is too short or simple, show immediately
            if (textContent.length < 50) {{
                element.innerHTML = htmlContent;
                if (callback) setTimeout(callback, 100);
                return;
            }}
            
            // Parse HTML structure to preserve tags while typing
            let currentIndex = 0;
            let displayedContent = '';
            const htmlString = htmlContent;
            
            // Speed varies by character type for luxury feel
            function getSpeed(char) {{
                if (char === ' ') return 15;  // Faster for spaces
                if (char === '.' || char === '!' || char === '?') return 80;  // Pause at sentence end
                if (char === ',' || char === ';') return 40;  // Pause at commas
                if (char === '\\n') return 20;  // Line breaks
                return 12;  // Normal speed
            }}
            
            function type() {{
                if (currentIndex >= htmlString.length) {{
                    element.innerHTML = htmlString;
                    if (callback) callback();
                    return;
                }}
                
                // Find next safe point to display (after closing tags)
                let nextIndex = currentIndex + 1;
                let safeToDisplay = htmlString.substring(0, nextIndex);
                
                // Check if we're in the middle of an HTML tag
                const beforeCurrent = htmlString.substring(0, currentIndex);
                const openTags = (beforeCurrent.match(/<[^>]+>/g) || []).length;
                const closeTags = (beforeCurrent.match(/<\\/[^>]+>/g) || []).length;
                const inTag = htmlString.substring(currentIndex).match(/^<[^>]*>/);
                
                // If we're starting a tag, skip to end of tag
                // Special handling for <a> tags - render them completely to preserve links
                if (inTag) {{
                    const tagEnd = htmlString.indexOf('>', currentIndex);
                    if (tagEnd !== -1) {{
                        nextIndex = tagEnd + 1;
                        safeToDisplay = htmlString.substring(0, nextIndex);
                        // For <a> tags, also find the closing </a> tag to render complete links
                        const tagMatch = htmlString.substring(currentIndex, tagEnd + 1);
                        if (tagMatch.startsWith('<a')) {{
                            const closingTagIndex = htmlString.indexOf('</a>', tagEnd);
                            if (closingTagIndex !== -1) {{
                                nextIndex = closingTagIndex + 4; // Include </a>
                                safeToDisplay = htmlString.substring(0, nextIndex);
                            }}
                        }}
                    }}
                }}
                
                // Display up to safe point
                element.innerHTML = safeToDisplay;
                
                // NO AUTO-SCROLL during typewriter - let user scroll freely
                // User can scroll up to read previous content while AI is typing
                
                currentIndex = nextIndex;
                
                // Get next character for speed calculation
                const nextChar = htmlString[currentIndex] || '';
                const speed = getSpeed(nextChar);
                
                setTimeout(type, speed);
            }}
            
            // Start typing
            element.innerHTML = '';
            type();
        }}
        
        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}
        
        async function sendQuestion() {{
            const input = document.getElementById('questionInput');
            const button = document.getElementById('sendButton');
            const welcome = document.getElementById('welcome');
            const question = input?.value.trim();
            
            if (!question || !input || !button) return;
            
            if (question.length < 3) {{
                alert('Please enter a question with at least 3 characters');
                return;
            }}
            
            // Create new conversation if needed
            if (!currentConversationId) {{
                currentConversationId = new Date().getTime().toString();
                conversations[currentConversationId] = {{
                    timestamp: new Date().toISOString(),
                    messages: []
                }};
            }}
            
            input.value = '';
            button.disabled = true;
            button.innerHTML = 'Sending...';
            
            if (welcome) welcome.style.display = 'none';
            
            // Add user message
            const userMsg = {{
                role: 'user',
                content: question,
                timestamp: new Date().toISOString()
            }};
            conversations[currentConversationId].messages.push(userMsg);
            
            // Display user message
            const chatArea = document.getElementById('chatArea');
            const userDiv = document.createElement('div');
            userDiv.className = 'message';
            
            const userAvatar = document.createElement('div');
            userAvatar.className = 'avatar';
            const userAvatarImg = document.createElement('img');
            userAvatarImg.src = '/static/user_avatar.jpeg';
            userAvatarImg.alt = 'User';
            userAvatar.appendChild(userAvatarImg);
            
            const userContent = document.createElement('div');
            userContent.className = 'message-content';
            
            const userHeader = document.createElement('div');
            userHeader.className = 'message-header';
            const userName = document.createElement('div');
            userName.className = 'message-author';
            userName.textContent = 'Tobias Yergin';
            userHeader.appendChild(userName);
            
            const userText = document.createElement('div');
            userText.className = 'message-text';
            userText.style.color = 'rgba(255,255,255,0.9)';
            userText.style.fontSize = '16px';
            userText.style.lineHeight = '1.75';
            userText.style.padding = '16px 20px';
            userText.style.marginTop = '8px';
            userText.textContent = question;
            
            userContent.appendChild(userHeader);
            userContent.appendChild(userText);
            userDiv.appendChild(userAvatar);
            userDiv.appendChild(userContent);
            chatArea.appendChild(userDiv);
            chatArea.scrollTop = chatArea.scrollHeight;
            
            const loadingId = addMessage('assistant', '<div class="loading-indicator"><div class="loading-dot"></div><div class="loading-dot"></div><div class="loading-dot"></div> <span style="margin-left: 8px;">Analyzing...</span></div>');
            
            try {{
                const startTime = Date.now();
                const response = await fetch('/api/answer', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ question: question }})
                }});
                
                if (!response.ok) {{
                    const errorData = await response.json().catch(() => ({{}}));
                    const errorMsg = errorData.detail || 'HTTP ' + response.status + ': ' + response.statusText;
                    throw new Error(errorMsg);
                }}
                
                const data = await response.json();
                const duration = ((Date.now() - startTime) / 1000).toFixed(1);
                
                const loadingEl = document.getElementById(loadingId);
                if (loadingEl) loadingEl.remove();
                
                if (data.error) {{
                    const errorMsg = escapeHtml(data.error);
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'message';
                    
                    const errorAvatar = document.createElement('div');
                    errorAvatar.className = 'avatar';
                    const errorAvatarImg = document.createElement('img');
                    errorAvatarImg.src = '/static/assistant_avatar.jpeg';
                    errorAvatarImg.alt = 'Assistant';
                    errorAvatar.appendChild(errorAvatarImg);
                    
                    const errorContent = document.createElement('div');
                    errorContent.className = 'message-content';
                    
                    const errorHeader = document.createElement('div');
                    errorHeader.className = 'message-header';
                    const errorAuthor = document.createElement('div');
                    errorAuthor.className = 'message-author';
                    errorAuthor.textContent = 'Paul Joly';
                    errorHeader.appendChild(errorAuthor);
                    
                    const errorWrapper = document.createElement('div');
                    const errorDivInner = document.createElement('div');
                    errorDivInner.className = 'error-message';
                    errorDivInner.textContent = 'Error: ' + errorMsg;
                    errorWrapper.appendChild(errorDivInner);
                    
                    errorContent.appendChild(errorHeader);
                    errorContent.appendChild(errorWrapper);
                    
                    errorDiv.appendChild(errorAvatar);
                    errorDiv.appendChild(errorContent);
                    document.getElementById('chatArea').appendChild(errorDiv);
                    
                    if (data.answer && data.answer.suggested_followups && data.answer.suggested_followups.length > 0) {{
                        const followupsDiv = errorDiv.querySelector('.message-content');
                        const fqSection = document.createElement('div');
                        fqSection.className = 'followup-questions';
                        fqSection.style.marginTop = '24px';
                        fqSection.style.paddingTop = '20px';
                        fqSection.style.borderTop = '1px solid #e5e5e5';
                        
                        const fqTitle = document.createElement('div');
                        fqTitle.style.fontSize = '13px';
                        fqTitle.style.fontWeight = '600';
                        fqTitle.style.color = '#666';
                        fqTitle.style.marginBottom = '12px';
                        fqTitle.textContent = 'Suggested follow-up questions:';
                        fqSection.appendChild(fqTitle);
                        
                        data.answer.suggested_followups.forEach(fq => {{
                            const fqItem = document.createElement('div');
                            fqItem.className = 'suggestion-item';
                            fqItem.style.cursor = 'pointer';
                            fqItem.style.marginBottom = '8px';
                            fqItem.textContent = fq;
                            fqItem.onclick = () => askQuestion(fq);
                            fqSection.appendChild(fqItem);
                        }});
                        
                        followupsDiv.appendChild(fqSection);
                    }}
                }} else {{
                    // Debug: Log the response structure
                    try {{
                        const responseStr = JSON.stringify(data);
                        console.log('[DEBUG] Full API response:', responseStr);
                    }} catch(e) {{
                        console.log('[DEBUG] Full API response: [unable to stringify]');
                    }}
                    try {{
                        const answerStr = JSON.stringify(data.answer);
                        console.log('[DEBUG] Answer object:', answerStr);
                    }} catch(e) {{
                        console.log('[DEBUG] Answer object: [unable to stringify]');
                    }}
                    
                    // Check if we actually have a valid answer
                    if (!data.answer || (!data.answer.full_answer && !data.answer.executive_summary && !data.answer.answer)) {{
                        console.error('[ERROR] No valid answer found in response');
                        const errorDiv = document.createElement('div');
                        errorDiv.className = 'message';
                        
                        const errorAvatar = document.createElement('div');
                        errorAvatar.className = 'avatar';
                        const errorAvatarImg = document.createElement('img');
                        errorAvatarImg.src = '/static/assistant_avatar.jpeg';
                        errorAvatarImg.alt = 'Assistant';
                        errorAvatar.appendChild(errorAvatarImg);
                        
                        const errorContent = document.createElement('div');
                        errorContent.className = 'message-content';
                        
                        const errorHeader = document.createElement('div');
                        errorHeader.className = 'message-header';
                        const errorAuthor = document.createElement('div');
                        errorAuthor.className = 'message-author';
                        errorAuthor.textContent = 'Paul Joly';
                        errorHeader.appendChild(errorAuthor);
                        
                        const errorWrapper = document.createElement('div');
                        errorWrapper.innerHTML = '<div class="error-message">No answer was generated. The question may be too complex or the dataset may not contain relevant information. Please try rephrasing your question.</div>';
                        
                        errorContent.appendChild(errorHeader);
                        errorContent.appendChild(errorWrapper);
                        
                        errorDiv.appendChild(errorAvatar);
                        errorDiv.appendChild(errorContent);
                        document.getElementById('chatArea').appendChild(errorDiv);
                        return;
                    }}
                    
                    const answer = formatAnswer(data.answer);
                    if (data.answer && data.answer.suggested_followups) {{
                        answer.followups = data.answer.suggested_followups;
                    }} else {{
                        answer.followups = generateFallbackFollowups(question);
                    }}
                    if (data.cached) {{
                        answer.cached = true;
                    }}
                    addMessageWithTypewriter('assistant', answer, data.answer.confidence || 'HIGH');
                    
                    // Save assistant message to conversation
                    conversations[currentConversationId].messages.push({{
                        role: 'assistant',
                        content: answer.text,
                        timestamp: new Date().toISOString()
                    }});
                    
                    // Save conversation
                    try {{
                        await fetch('/api/save-conversation', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{
                                conversationId: currentConversationId,
                                conversation: conversations[currentConversationId]
                            }})
                        }});
                    }} catch (e) {{
                        console.error('Error saving conversation:', e);
                    }}
                    
                    renderConversationsList();
                    console.log('[PERF] Response time: ' + duration + 's, Cached: ' + (data.cached || false));
                }}
            }} catch (error) {{
                const loadingEl = document.getElementById(loadingId);
                if (loadingEl) loadingEl.remove();
                const errorMsg2 = escapeHtml(error.message || 'Unknown error occurred');
                const errorMsgHtml = '<div class="error-message">Error: ' + errorMsg2 + '</div>';
                addMessage('assistant', errorMsgHtml, null);
                console.error('[ERROR]', error);
            }} finally {{
                button.disabled = false;
                button.innerHTML = 'Send';
                input.focus();
            }}
        }}
        
        function generateFallbackFollowups(question) {{
            const q = question.toLowerCase();
            const followups = [];
            
            if (q.includes('human-agent') || q.includes('configuration') || q.includes('workforce')) {{
                followups.push('What optimal human-AI configurations are Reddit users discussing?');
                followups.push('Which teams or roles are most impacted by AI adoption?');
            }}
            if (q.includes('competitor') || q.includes('compare') || q.includes('industry')) {{
                followups.push('Which AI tools are Reddit users comparing and what are key differentiators?');
                followups.push('What do Reddit discussions reveal about competitive positioning?');
            }}
            if (q.includes('frustration') || q.includes('attrition') || q.includes('employee')) {{
                followups.push('What operational issues are Reddit users identifying as primary causes?');
                followups.push('How are organizations addressing employee concerns?');
            }}
            if (q.includes('productivity') || q.includes('efficiency')) {{
                followups.push('Where are Reddit users reporting AI adoption showing productivity improvements?');
                followups.push('What low-cost productivity levers are Reddit discussions highlighting?');
            }}
            
            if (followups.length < 3) {{
                followups.push('What are the most common AI tool implementation challenges Reddit users report?');
                followups.push('Which critical teams are Reddit discussions identifying as at risk?');
                followups.push('What productivity optimization strategies are Reddit users sharing?');
            }}
            
            return followups.slice(0, 5);
        }}
        
        function validateAndEscapeUrl(url) {{
            if (!url || typeof url !== 'string') return '#';
            // Remove any whitespace
            url = url.trim();
            // If URL doesn't start with http:// or https://, try to fix it
            if (!url.match(/^https?:\\/\\//i)) {{
                // If it looks like a Reddit URL without protocol, add https://
                if (url.startsWith('reddit.com') || url.startsWith('www.reddit.com')) {{
                    url = 'https://' + url;
                }} else {{
                    // If it's a relative path or malformed, return #
                    return '#';
                }}
            }}
            // Validate URL format
            try {{
                const urlObj = new URL(url);
                // Only allow http and https protocols
                if (!['http:', 'https:'].includes(urlObj.protocol)) {{
                    return '#';
                }}
                // Return properly encoded URL
                return url;
            }} catch (e) {{
                // Invalid URL, return safe fallback
                return '#';
            }}
        }}
        
        function formatAnswer(answer) {{
            // Try multiple possible fields for the answer
            let text = answer.full_answer || answer.executive_summary || answer.answer || answer.text || '';
            
            // If still empty, check if it's an object with nested content
            if (!text && typeof answer === 'object') {{
                text = answer.content || answer.response || answer.summary || '';
            }}
            
            // Clean up the text
            if (text && typeof text === 'string') {{
                text = text.trim();
            }} else {{
                text = '';
            }}
            
            // If still empty or too short, show error message
            if (!text || text.length < 10) {{
                text = 'Unable to generate a complete answer from the available data. The question may be too specific or the dataset may not contain relevant information. Please try rephrasing your question or asking about a different topic.';
            }}
            
            // Format citations with luxury design - FLAGGED and prominent
            // Improved regex to capture URLs with special characters and parentheses
            // Pattern: "quote" - r/subreddit by u/username on Date (Link: URL)
            text = text.replace(/"([^"]+)" - r\/([^\\s]+) by u\/([^\\s]+) on ([^\\s]+ [^\\s]+ [^\\s]+) \\(Link: ([^\\)]+)\\)/g, function(match, quote, subreddit, username, date, url) {{
                const safeUrl = validateAndEscapeUrl(url);
                return '<blockquote class="luxury-citation" style="margin: 24px 0; padding: 20px 24px; background: linear-gradient(135deg, rgba(233, 88, 11, 0.12) 0%, rgba(233, 88, 11, 0.06) 100%); border-left: 4px solid #E9580B; border-radius: 12px; font-style: italic; position: relative; box-shadow: 0 4px 16px rgba(0,0,0,0.1); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);">' +
                '<div style="font-size: 16px; line-height: 1.7; color: rgba(255,255,255,0.95); margin-bottom: 12px;">"' + escapeHtml(quote) + '"</div>' +
                '<div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(233, 88, 11, 0.2);">' +
                '<span style="font-size: 12px; font-weight: 600; color: #E9580B; text-transform: uppercase; letter-spacing: 0.5px;">CITATION</span>' +
                '<span style="font-size: 13px; color: rgba(255,255,255,0.7); font-style: normal;">r/' + escapeHtml(subreddit) + '</span>' +
                '<span style="font-size: 13px; color: rgba(255,255,255,0.7); font-style: normal;">•</span>' +
                '<span style="font-size: 13px; color: rgba(255,255,255,0.7); font-style: normal;">u/' + escapeHtml(username) + '</span>' +
                '<span style="font-size: 13px; color: rgba(255,255,255,0.7); font-style: normal;">•</span>' +
                '<span style="font-size: 13px; color: rgba(255,255,255,0.7); font-style: normal;">' + escapeHtml(date) + '</span>' +
                '<a href="' + safeUrl + '" target="_blank" rel="noopener noreferrer" style="margin-left: auto; font-size: 13px; color: #E9580B; text-decoration: none; font-weight: 600; padding: 4px 12px; background: rgba(233, 88, 11, 0.15); border-radius: 6px; transition: all 0.2s; border: 1px solid rgba(233, 88, 11, 0.3); cursor: pointer;">View Source →</a>' +
                '</div></blockquote>';
            }});
            
            // Handle citations without date (backward compatibility)
            text = text.replace(/"([^"]+)" - r\/([^\\s]+) by u\/([^\\s]+) \\(Link: ([^\\)]+)\\)/g, function(match, quote, subreddit, username, url) {{
                const safeUrl = validateAndEscapeUrl(url);
                return '<blockquote class="luxury-citation" style="margin: 24px 0; padding: 20px 24px; background: linear-gradient(135deg, rgba(233, 88, 11, 0.12) 0%, rgba(233, 88, 11, 0.06) 100%); border-left: 4px solid #E9580B; border-radius: 12px; font-style: italic; position: relative; box-shadow: 0 4px 16px rgba(0,0,0,0.1); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);">' +
                '<div style="font-size: 16px; line-height: 1.7; color: rgba(255,255,255,0.95); margin-bottom: 12px;">"' + escapeHtml(quote) + '"</div>' +
                '<div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(233, 88, 11, 0.2);">' +
                '<span style="font-size: 12px; font-weight: 600; color: #E9580B; text-transform: uppercase; letter-spacing: 0.5px;">CITATION</span>' +
                '<span style="font-size: 13px; color: rgba(255,255,255,0.7); font-style: normal;">r/' + escapeHtml(subreddit) + '</span>' +
                '<span style="font-size: 13px; color: rgba(255,255,255,0.7); font-style: normal;">•</span>' +
                '<span style="font-size: 13px; color: rgba(255,255,255,0.7); font-style: normal;">u/' + escapeHtml(username) + '</span>' +
                '<a href="' + safeUrl + '" target="_blank" rel="noopener noreferrer" style="margin-left: auto; font-size: 13px; color: #E9580B; text-decoration: none; font-weight: 600; padding: 4px 12px; background: rgba(233, 88, 11, 0.15); border-radius: 6px; transition: all 0.2s; border: 1px solid rgba(233, 88, 11, 0.3); cursor: pointer;">View Source →</a>' +
                '</div></blockquote>';
            }});
            
            
            // Handle comment citations
            text = text.replace(/"([^"]+)" - r\/([^\\s]+) \\(comment\\) by u\/([^\\s]+) on ([^\\s]+ [^\\s]+ [^\\s]+) \\(Comment in: ([^\\)]+)\\)/g,
                '<blockquote class="luxury-citation luxury-comment" style="margin: 24px 0; padding: 20px 24px; background: linear-gradient(135deg, rgba(233, 88, 11, 0.12) 0%, rgba(233, 88, 11, 0.06) 100%); border-left: 4px solid #E9580B; border-radius: 12px; font-style: italic; position: relative; box-shadow: 0 4px 16px rgba(0,0,0,0.1); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);">' +
                '<div style="font-size: 16px; line-height: 1.7; color: rgba(255,255,255,0.95); margin-bottom: 12px;">"$1"</div>' +
                '<div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(233, 88, 11, 0.2);">' +
                '<span style="font-size: 12px; font-weight: 600; color: #E9580B; text-transform: uppercase; letter-spacing: 0.5px;">COMMENT</span>' +
                '<span style="font-size: 13px; color: rgba(255,255,255,0.7); font-style: normal;">r/$2</span>' +
                '<span style="font-size: 13px; color: rgba(255,255,255,0.7); font-style: normal;">•</span>' +
                '<span style="font-size: 13px; color: rgba(255,255,255,0.7); font-style: normal;">u/$3</span>' +
                '<span style="font-size: 13px; color: rgba(255,255,255,0.7); font-style: normal;">•</span>' +
                '<span style="font-size: 13px; color: rgba(255,255,255,0.7); font-style: normal;">$4</span>' +
                '<span style="font-size: 13px; color: rgba(255,255,255,0.6); font-style: normal;">in: $5</span>' +
                '</div></blockquote>');
            
            // Handle "Date unavailable" citations
            text = text.replace(/"([^"]+)" - r\/([^\\s]+) \\(comment\\) by u\/([^\\s]+) on Date unavailable \\(Comment in: ([^\\)]+)\\)/g,
                '<blockquote class="luxury-citation luxury-comment" style="margin: 24px 0; padding: 20px 24px; background: linear-gradient(135deg, rgba(233, 88, 11, 0.12) 0%, rgba(233, 88, 11, 0.06) 100%); border-left: 4px solid #E9580B; border-radius: 12px; font-style: italic; position: relative; box-shadow: 0 4px 16px rgba(0,0,0,0.1); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);">' +
                '<div style="font-size: 16px; line-height: 1.7; color: rgba(255,255,255,0.95); margin-bottom: 12px;">"$1"</div>' +
                '<div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(233, 88, 11, 0.2);">' +
                '<span style="font-size: 12px; font-weight: 600; color: #E9580B; text-transform: uppercase; letter-spacing: 0.5px;">COMMENT</span>' +
                '<span style="font-size: 13px; color: rgba(255,255,255,0.7); font-style: normal;">r/$2</span>' +
                '<span style="font-size: 13px; color: rgba(255,255,255,0.7); font-style: normal;">•</span>' +
                '<span style="font-size: 13px; color: rgba(255,255,255,0.7); font-style: normal;">u/$3</span>' +
                '<span style="font-size: 13px; color: rgba(255,255,255,0.6); font-style: normal;">in: $4</span>' +
                '</div></blockquote>');
            
            // Clean up markdown with LUXURY formatting
            let cleanText = text
                // Executive Summary - make it a standout headline
                .replace(/Executive Summary\\s*\\n\\s*\\n/g, '<div class="luxury-section-header" style="margin-top: 32px; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 2px solid rgba(233, 88, 11, 0.3);"><h1 style="font-size: 32px; font-weight: 700; color: #ffffff; letter-spacing: -1px; margin: 0; font-family: \\'EB Garamond\\', serif;">Executive Summary</h1></div>')
                // Main section headers - LUXURY headlines
                .replace(/^([A-Z][^\\n]+(?: – |: |CANNOT|CAN Answer|Strategic Signals|Recommended|Data Limitations|Suggested))\\s*\\n/gm, '<div class="luxury-section-header" style="margin-top: 40px; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid rgba(233, 88, 11, 0.2);"><h2 style="font-size: 24px; font-weight: 700; color: #ffffff; letter-spacing: -0.5px; margin: 0; font-family: \\'EB Garamond\\', serif;">$1</h2></div>')
                // Sub-section headers (with bullet points)
                .replace(/^•\\s*\\*\\*([^*]+)\\*\\*:/gm, '<h3 style="margin-top: 28px; margin-bottom: 16px; font-size: 20px; font-weight: 600; color: #ffffff; letter-spacing: -0.3px;">$1</h3>')
                // Bold text - make it stand out
                .replace(/\\*\\*([^*]+)\\*\\*/g, '<strong style="color: #ffffff; font-weight: 700;">$1</strong>')
                // Headers (H3)
                .replace(/### ([^\\n]+)/g, '<h3 style="margin-top: 32px; margin-bottom: 16px; font-size: 20px; font-weight: 600; color: #ffffff; letter-spacing: -0.3px;">$1</h3>')
                // Headers (H2)
                .replace(/## ([^\\n]+)/g, '<h2 style="margin-top: 40px; margin-bottom: 20px; font-size: 24px; font-weight: 700; color: #ffffff; letter-spacing: -0.5px; font-family: \\'EB Garamond\\', serif;">$1</h2>')
                // Bullet points - luxury styling
                .replace(/^•\\s+/gm, '<li style="margin: 12px 0; padding-left: 8px; position: relative;"><span style="position: absolute; left: -16px; color: #E9580B; font-size: 20px;">•</span>')
                // Paragraph breaks
                .replace(/\\n\\n/g, '</p><p style="margin: 16px 0; line-height: 1.8; color: rgba(255,255,255,0.9); font-size: 16px;">')
                // Single line breaks
                .replace(/\\n/g, '<br>')
                // Multiple spaces
                .replace(/  +/g, ' ')
                // Close list items
                .replace(/(<li[^>]*>)/g, '$1')
                .replace(/(<br>)(?=<li|$)/g, '</li>$1');
            
            // Wrap in paragraph tags with luxury styling
            if (cleanText.length > 50) {{
                // Ensure proper paragraph wrapping
                if (!cleanText.startsWith('<p') && !cleanText.startsWith('<div') && !cleanText.startsWith('<h')) {{
                    cleanText = '<p style="margin: 16px 0; line-height: 1.8; color: rgba(255,255,255,0.9); font-size: 16px;">' + cleanText + '</p>';
                }}
            }}
            
            // Debug logging
            console.log('[DEBUG] formatAnswer - Input text length:', text.length);
            console.log('[DEBUG] formatAnswer - Output cleanText length:', cleanText.length);
            const firstChars = cleanText.length > 300 ? cleanText.substring(0, 300) : cleanText;
            console.log('[DEBUG] formatAnswer - First 300 chars:', firstChars);
            
            return {{
                text: cleanText,
                confidence: answer.confidence || 'HIGH',
                posts: answer.posts_analyzed || 0,
                scope: answer.data_scope || ''
            }};
        }}
        
        function addMessageWithTypewriter(role, answerData, confidence) {{
            const chatArea = document.getElementById('chatArea');
            const messageId = 'msg-' + Date.now();
            
            const messageDiv = document.createElement('div');
            messageDiv.id = messageId;
            messageDiv.className = 'message';
            
            const avatarDiv = document.createElement('div');
            avatarDiv.className = 'avatar';
            const avatarImg = document.createElement('img');
            avatarImg.src = '/static/assistant_avatar.jpeg';
            avatarImg.alt = 'Assistant';
            avatarDiv.appendChild(avatarImg);
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            
            const messageHeader = document.createElement('div');
            messageHeader.className = 'message-header';
            const authorName = document.createElement('div');
            authorName.className = 'message-author';
            authorName.textContent = 'Paul Joly';
            messageHeader.appendChild(authorName);
            
            const textDiv = document.createElement('div');
            textDiv.className = 'message-text';
            
            // Now append elements in correct order (text will be added via typewriter)
            contentDiv.appendChild(messageHeader);
            contentDiv.appendChild(textDiv);
            
            // Verify text was set
            if (!answerData.text || answerData.text.length < 10) {{
                console.error('[ERROR] Answer text is empty or too short:', answerData.text);
                textDiv.innerHTML = '<div class="error-message">Error: Answer text is missing. Please try again.</div>';
                return;
            }}
            
            const metaDiv = document.createElement('div');
            metaDiv.className = 'message-meta';
            const confidenceClass = confidence.toLowerCase();
            const postsCount = answerData.posts;
            let scopeText = '';
            if (answerData.scope) {{
                const scopeSubstr = answerData.scope.length > 80 ? answerData.scope.substring(0, 80) : answerData.scope;
                scopeText = escapeHtml(scopeSubstr) + '...';
            }}
            const badgeEl = document.createElement('span');
            badgeEl.className = 'confidence-badge confidence-' + confidenceClass;
            badgeEl.textContent = confidence;
            metaDiv.appendChild(badgeEl);
            const postsEl = document.createElement('span');
            postsEl.textContent = postsCount + ' posts analyzed';
            metaDiv.appendChild(postsEl);
            if (answerData.cached) {{
                const cacheBadge = document.createElement('span');
                cacheBadge.className = 'cache-badge';
                cacheBadge.textContent = 'CACHED';
                metaDiv.appendChild(cacheBadge);
            }}
            if (scopeText) {{
                const scopeEl = document.createElement('span');
                scopeEl.textContent = scopeText;
                metaDiv.appendChild(scopeEl);
            }}
            contentDiv.appendChild(metaDiv);
            
            if (answerData.followups && answerData.followups.length > 0) {{
                const followupsDiv = document.createElement('div');
                followupsDiv.className = 'followup-questions';
                followupsDiv.style.marginTop = '24px';
                followupsDiv.style.paddingTop = '20px';
                followupsDiv.style.paddingBottom = '12px';
                followupsDiv.style.borderTop = '1px solid rgba(255,255,255,0.1)';
                followupsDiv.style.background = 'rgba(255, 255, 255, 0.05)';
                followupsDiv.style.borderRadius = '16px';
                followupsDiv.style.padding = '20px';
                followupsDiv.style.border = '1px solid rgba(255,255,255,0.1)';
                
                const followupsTitle = document.createElement('div');
                followupsTitle.style.fontSize = '13px';
                followupsTitle.style.fontWeight = '600';
                followupsTitle.style.color = 'rgba(255,255,255,0.9)';
                followupsTitle.style.marginBottom = '16px';
                followupsTitle.style.background = 'rgba(233, 88, 11, 0.15)';
                followupsTitle.style.padding = '10px 16px';
                followupsTitle.style.borderRadius = '10px';
                followupsTitle.style.border = '1px solid rgba(233, 88, 11, 0.3)';
                followupsTitle.textContent = 'Suggested follow-up questions:';
                followupsDiv.appendChild(followupsTitle);
                
                answerData.followups.forEach((fq, index) => {{
                    const fqItem = document.createElement('div');
                    fqItem.className = 'suggestion-item';
                    fqItem.style.cursor = 'pointer';
                    fqItem.style.marginBottom = '8px';
                    fqItem.style.background = 'rgba(255, 255, 255, 0.05)';
                    fqItem.style.padding = '14px 18px';
                    fqItem.style.borderRadius = '12px';
                    fqItem.style.color = 'rgba(255,255,255,0.9)';
                    fqItem.style.border = '1px solid rgba(255,255,255,0.1)';
                    fqItem.textContent = fq;
                    fqItem.onclick = () => askQuestion(fq);
                    followupsDiv.appendChild(fqItem);
                }});
                
                contentDiv.appendChild(followupsDiv);
            }}
            
            messageDiv.appendChild(avatarDiv);
            messageDiv.appendChild(contentDiv);
            
            chatArea.appendChild(messageDiv);
            // Initial scroll to show the message, but then let user scroll freely
            chatArea.scrollTop = chatArea.scrollHeight;
            
            // LUXURY TYPEWRITER EFFECT - letter by letter
            typewriterLuxury(textDiv, answerData.text, () => {{
                console.log('[DEBUG] Typewriter completed');
                // Only scroll to bottom when typing is complete (if user wants to see the end)
                const chatArea = document.getElementById('chatArea');
                if (chatArea) {{
                    const isNearBottom = chatArea.scrollHeight - chatArea.scrollTop - chatArea.clientHeight < 200;
                    if (isNearBottom) {{
                        chatArea.scrollTop = chatArea.scrollHeight;
                    }}
                }}
            }});
        }}
        
        function addMessage(role, content, confidence) {{
            const chatArea = document.getElementById('chatArea');
            const messageId = 'msg-' + Date.now();
            
            const messageDiv = document.createElement('div');
            messageDiv.id = messageId;
            messageDiv.className = 'message';
            
            const avatarEl = document.createElement('div');
            avatarEl.className = 'avatar';
            const avatarImg = document.createElement('img');
            avatarImg.src = '/static/assistant_avatar.jpeg';
            avatarImg.alt = 'Assistant';
            avatarEl.appendChild(avatarImg);
            
            const contentEl = document.createElement('div');
            contentEl.className = 'message-content';
            
            const messageHeader = document.createElement('div');
            messageHeader.className = 'message-header';
            const authorName = document.createElement('div');
            authorName.className = 'message-author';
            authorName.textContent = 'Paul Joly';
            messageHeader.appendChild(authorName);
            
            const contentWrapper = document.createElement('div');
            contentWrapper.innerHTML = content;
            
            contentEl.appendChild(messageHeader);
            contentEl.appendChild(contentWrapper);
            
            messageDiv.appendChild(avatarEl);
            messageDiv.appendChild(contentEl);
            
            chatArea.appendChild(messageDiv);
            chatArea.scrollTop = chatArea.scrollHeight;
            
            return messageId;
        }}
        
        document.addEventListener('DOMContentLoaded', function() {{
            loadConversations();
            
            document.getElementById('questionInput').addEventListener('keypress', function(e) {{
                if (e.key === 'Enter' && !e.shiftKey) {{
                    e.preventDefault();
                    sendQuestion();
                }}
            }});
            
            renderSuggestions();
            
            setTimeout(() => {{
                renderSuggestions();
            }}, 100);
            
            document.getElementById('questionInput').focus();
            document.getElementById('sendButton').addEventListener('click', sendQuestion);
        }});
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)

@app.get("/api/suggestions")
@limiter.limit("30/minute")
async def get_suggestions(request: Request):
    """Get suggested questions"""
    logger.info("Suggestions requested")
    return {"suggestions": SUGGESTED_QUESTIONS}

@app.post("/api/answer")
@limiter.limit("10/minute")
async def answer_question(request: Request, question_request: QuestionRequest):
    """Answer a CEO question with caching and timeout"""
    start_time = datetime.now()
    cache_key = get_cache_key(question_request.question, question_request.estimates_ok)
    
    # Check cache first
    if cache_key in answer_cache:
        logger.info(f"Cache HIT for question: {question_request.question[:50]}...")
        cached_answer = answer_cache[cache_key]
        return {
            "question": question_request.question,
            "answer": cached_answer,
            "cached": True,
            "timestamp": datetime.now().isoformat()
        }
    
    logger.info(f"Processing question: {question_request.question[:100]}...")
    
    try:
        # Set timeout for agent response (60 seconds)
        answer = await asyncio.wait_for(
            asyncio.to_thread(
                agent.answer_ceo_question,
                question=question_request.question,
                estimates_ok=question_request.estimates_ok,
            verbose=False
            ),
            timeout=60.0
        )
        
        # Cache the answer
        answer_cache[cache_key] = answer
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Answer generated in {duration:.2f}s for: {question_request.question[:50]}...")
        
        return {
            "question": question_request.question,
            "answer": answer,
            "cached": False,
            "timestamp": datetime.now().isoformat()
        }
        
    except asyncio.TimeoutError:
        logger.error(f"⏱️ Timeout after 60s for question: {question_request.question[:50]}...")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request timed out. The question is too complex or the service is overloaded. Please try again with a simpler question."
        )
    except ValueError as e:
        logger.error(f"❌ Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Error processing question: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/api/health")
async def health_check():
    """Enhanced health check endpoint"""
    try:
        posts_count = len(agent.df)
        cache_size = len(answer_cache)
        cache_info = answer_cache.currsize if hasattr(answer_cache, 'currsize') else cache_size
        
        return {
            "status": "healthy",
            "posts_loaded": posts_count,
            "cache_size": cache_info,
            "cache_maxsize": answer_cache.maxsize,
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        )

@app.get("/api/stats")
@limiter.limit("30/minute")
async def get_stats(request: Request):
    """Get API statistics"""
    return {
        "cache_size": len(answer_cache),
        "cache_maxsize": answer_cache.maxsize,
        "posts_loaded": len(agent.df),
        "suggested_questions_count": len(SUGGESTED_QUESTIONS),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/conversations")
@limiter.limit("30/minute")
async def get_conversations(request: Request):
    """Get all conversations"""
    return load_conversations()

@app.post("/api/save-conversation")
@limiter.limit("30/minute")
async def save_conversation(request: Request):
    """Save a conversation"""
    try:
        data = await request.json()
        conversation_id = data.get('conversationId')
        conversation = data.get('conversation')
        
        conversations = load_conversations()
        conversations[conversation_id] = conversation
        save_conversations(conversations)
        
        return {"status": "saved"}
    except Exception as e:
        logger.error(f"Error saving conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"🚀 Starting Sage Agent on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )
