from llm_config import get_groq_completion

def answer_query(file_text, user_question):
    prompt = f"""
You are an assistant that answers questions based on the uploaded document.

Document content:
{file_text[:4000]}  # limit for safety (you can chunk later)

User question: {user_question}

Please answer in a concise and clear way.
"""
    return get_groq_completion(prompt)
