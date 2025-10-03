
from connectors.duckduckgo_conn import ddg_search
from connectors.hf_datasets_conn import hf_search
from connectors.kaggle_conn import kaggle_search

class SearchAgent:
    def search(self, query: str):
        print("[SearchAgent] Searching sources...")

        results = []
        results.extend(ddg_search(query, max_results=5))
        results.extend(hf_search([query], limit=5))
        results.extend(kaggle_search(query, max_results=5))

        return results
