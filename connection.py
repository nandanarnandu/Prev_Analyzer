import os
from groq import Groq
from dotenv import load_dotenv

# ✅ Load variables from .env
load_dotenv()

# ✅ Get API key securely
api_key = os.getenv("GROQ_API_KEY")

# ✅ Check if API key exists
if not api_key:
    raise ValueError("❌ GROQ_API_KEY not found in .env file. Please add it and restart.")

# ✅ Initialize client
groq_client = Groq(api_key=api_key)

# Example function to run a test query
def test_connection():
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful data privacy assistant for Prevanalyzer."
                },
                {
                    "role": "user",
                    "content": "Give me a one-line privacy tip."
                }
            ],
            model="llama-3.3-70b-versatile",
            stream=False,
        )
        print("✅ Groq connection successful!")
        print("💡 AI Response:", chat_completion.choices[0].message.content)

    except Exception as e:
        print(f"❌ Groq API error: {e}")

if __name__ == "__main__":
    test_connection()
