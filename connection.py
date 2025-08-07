import os
from groq import Groq
from dotenv import load_dotenv

# ✅ Load variables from .env
load_dotenv()

# ✅ Get API key securely
api_key = os.getenv("GROQ_API_KEY")

# ✅ Initialize client
groq_client = Groq(api_key=api_key)
