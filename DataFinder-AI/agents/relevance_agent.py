# agents/relevance_agent.py

from groq import Groq  # make sure you installed `groq` SDK
import os
from dotenv import load_dotenv

load_dotenv()

class RelevanceAgent:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama3-70b-8192"

    def evaluate(self, user_query, dataset_info):
        system_prompt = """
You are a helpful AI assistant that judges whether a given dataset is relevant to the user's machine learning problem.
Give a score between 0 and 10, with reasoning, and a yes/no recommendation.
        """

        user_input = f"""
ML Problem: {user_query}

Dataset Metadata:
Title: {dataset_info.get("title")}
Source: {dataset_info.get("source")}
Description: {dataset_info.get("description")}
File Formats: {dataset_info.get("file_formats")}
License Note: {dataset_info.get("license_note")}
        """

        try:
            chat_completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ]
            )

            response = chat_completion.choices[0].message.content.strip()
            return {
                "relevance_judgement": response
            }

        except Exception as e:
            return {"error": f"LLM Evaluation failed: {str(e)}"}
