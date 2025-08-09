import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY
)

def get_groq_completion(prompt, model="llama-3.3-70b-versatile", temperature=0.7):
    """
    Get a completion from the Groq API
    
    Args:
        prompt (str): The prompt to send to the model
        model (str): The model to use (default: mixtral-8x7b-32768)
        temperature (float): Controls randomness (0.0 to 1.0)
        
    Returns:
        str: The generated response
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error getting completion: {str(e)}"
