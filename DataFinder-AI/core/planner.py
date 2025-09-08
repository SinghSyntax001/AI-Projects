from groq import Groq
from pydantic import BaseModel
import os


class Plan(BaseModel):
    domain: list[str]
    tasks: list[str]
    modalities: list[str]
    constraints: dict
    keywords: list[str]


SYS = """You are a data discovery planner. Extract tasks (e.g., classification), modalities (image/text/tabular), domain, constraints (license, region), and 8-12 diverse keywords from the user abstract."""


def make_plan(abstract: str) -> Plan:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    prompt = f"Abstract:\n{abstract}\nReturn JSON with fields: domain, tasks, modalities, constraints, keywords."
    resp = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[
        {"role": "system", "content": SYS},
        {"role": "user", "content": prompt}
    ])
    content = resp.choices[0].message.content
    # parse with pydantic (add try/except & fallback)
    return Plan.model_validate_json(content)