from duckduckgo_search import DDGS
from typing import List

def ddg_search(query: str, max_results: int = 5) -> List[dict]:
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append({
                "title": r.get("title", "").replace("\n", " ").strip(),
                "url": r.get("href", "").strip(),
                "snippet": r.get("body", "").replace("\n", " ").strip(),
                "source": "duckduckgo"
            })
    return results
