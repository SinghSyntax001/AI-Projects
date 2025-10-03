from dotenv import load_dotenv
import os

load_dotenv(override=True)
api_key = os.getenv('GROQ_API_KEY')

if not api_key:
    print("No API key found")
elif not api_key.startswith("gsk"):
    print("An API key was found but it doesn't start with gsk")
elif api_key.strip() != api_key:
    print("API key was found but it looks like it might have space or tab characters")
else:
    print("API key found and looks good")

MODEL = "llama-3.1-8b-instant"