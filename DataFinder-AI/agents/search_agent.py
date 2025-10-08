from connectors.duckduckgo_conn import ddg_search
from connectors.hf_datasets_conn import hf_search
from connectors.kaggle_conn import kaggle_search

class SearchAgent:
    def search(self, query: str):
        print("[SearchAgent] Searching sources...")

        # Prioritize dedicated dataset platforms
        results = []
        results.extend(hf_search([query], limit=5))
        results.extend(kaggle_search(query, max_results=5))

        # Refine the web search to be more specific
        web_search_query = f"{query} dataset"
        results.extend(ddg_search(web_search_query, max_results=5))

        return results