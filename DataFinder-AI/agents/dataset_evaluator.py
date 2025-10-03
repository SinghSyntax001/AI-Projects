

import os
import json
from groq import Groq

class DatasetEvaluatorAgent:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def evaluate(self, user_query: str, metadata: dict) -> dict:
        prompt = f"""
            You are an expert ML research assistant.  
            Your task is to evaluate if a dataset is suitable and robust for training a machine learning or deep learning model.  

            Problem Statement: {user_query}  

            Dataset Info:  
            - Title: {metadata.get('title', 'N/A')}  
            - Description: {metadata.get('description', 'N/A')}  
            - Source: {metadata.get('source', 'N/A')}  
            - URL: {metadata.get('url', 'N/A')}  

            Please analyze based on:  
            1. Relevance to the problem statement  
            2. Dataset size/diversity (if mentioned)  
            3. Popularity / credibility (if known)  
            4. Freshness (if last updated info is present)  

            Return output in JSON with fields:  
            - "robustness_score": 1-5  
            - "reason": short explanation
        """

        response = self.client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        try:
            result = json.loads(response.choices[0].message.content)
        except Exception:
            result = {
                "robustness_score": 0,
                "reason": "Could not parse LLM response"
            }

        return result
