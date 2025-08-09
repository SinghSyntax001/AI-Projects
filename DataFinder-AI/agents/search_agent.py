# agents/search_agent.py

from ddgs import DDGS


class SearchAgent:
    def __init__(self):
        pass

    def search(self, query):
        print(f"\n🔍 Searching the web for datasets related to:\n\"{query}\"")
        results = set()
        search_terms = [
            f"{query} dataset site:kaggle.com",
            f"{query} dataset site:huggingface.co",
            f"{query} dataset site:zenodo.org",
            f"{query} dataset site:roboflow.com",
            f"{query} dataset download"
        ]
        with DDGS() as ddgs:
            for term in search_terms:
                print(f"  ➤ Searching: {term}")
                try:
                    for r in ddgs.text(term, max_results=5):
                        print(f"[DEBUG] Title: {r.get('title')}")
                        print(f"[DEBUG] Link: {r.get('href')}")
                        if "dataset" in r.get("title", "").lower():
                            results.add(r["href"])
                except Exception as e:
                    print(f"[ERROR] Search failed for term: {term} | {str(e)}")
        return list(results)
