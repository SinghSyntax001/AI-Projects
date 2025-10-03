from groq import Groq
from config import MODEL

client = Groq()

def base_agent(system_prompt, user_prompt, response_format):
    """
    A simple wrapper around the Groq client to send system + user prompts
    and get a structured response.
    """
    return client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format=response_format
    )
