import os

# Optional: Use python-dotenv to load variables from a .env file
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME")
APP_SECRET_KEY = os.getenv("APP_SECRET_KEY")

# Check if the essential key is loaded
if not GOOGLE_API_KEY:
    print("Warning: GOOGLE_API_KEY not found in environment variables or .env file.")

if not APP_SECRET_KEY:
    print("CRITICAL WARNING: APP_SECRET_KEY not found in environment variables or .env file. Flask sessions will be insecure.")

# --- Google Gemini Configuration ---
GEMINI_CONFIG_LIST = [
    {
        "model": GEMINI_MODEL_NAME,
        "api_key": GOOGLE_API_KEY,
    }
]
