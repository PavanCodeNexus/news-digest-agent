"""
Central config. All keys are read from environment variables —
never hardcode API keys in source files (standard security practice,
also matters if you ever push this to GitHub).

Set these before running (Linux/Mac):
    export GNEWS_API_KEY="your_key_here"
    export GUARDIAN_API_KEY="your_key_here"

On Windows PowerShell:
    $env:GNEWS_API_KEY="your_key_here"
    $env:GUARDIAN_API_KEY="your_key_here"

Or use a .env file with python-dotenv (see requirements.txt).
"""

import os
from dotenv import load_dotenv

load_dotenv()  # loads variables from a .env file if present

GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")
GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY", "")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Email notifications (sent via Gmail SMTP using an App Password)
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
NOTIFY_TO_EMAIL = os.getenv("NOTIFY_TO_EMAIL", "")  # defaults to GMAIL_ADDRESS if blank

# Groq free tier: 30 requests/minute, 1,000 requests/day per model —
# far more generous and stable than Gemini's free tier has been for us.
# Llama 3.3 70B is a strong, fast, general-purpose open model.
GROQ_MODEL = "llama-3.3-70b-versatile"

# RSS feeds — no API key needed for these
PIB_RSS_URL = "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3"  # PIB English releases
HINDU_RSS_URL = "https://www.thehindu.com/news/national/feeder/default.rss"

# How many articles to pull per source per run
# (Reduced since we now pull from 8 sources instead of 4 — keeps total
# volume manageable for the free-tier AI summarizer.)
MAX_ARTICLES_PER_SOURCE = 6
