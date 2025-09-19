from agents.search_agent import SearchAgent
from agents.scrape_agent import ScrapeAgent
from agents.relevance_agent import RelevanceAgent
from agents.dataset_evaluater import DatasetEvaluatorAgent


def run_pipeline(user_query: str, top_k: int = 5):
    # Search
    search_agent = SearchAgent()
    urls = search_agent.search(user_query)
    urls = urls[:top_k] if top_k else urls

    # Scrape metadata
    scraper = ScrapeAgent()
    all_metadata = []
    for url in urls:
        data = scraper.scrape_metadata(url)
        all_metadata.append(data)

    # Relevance evaluation
    relevance_agent = RelevanceAgent()
    for meta in all_metadata:
        relevance_result = relevance_agent.evaluate(user_query, meta)
        meta.update(relevance_result)

    # Robustness evaluation
    evaluator_agent = DatasetEvaluatorAgent()
    for meta in all_metadata:
        robustness_result = evaluator_agent.evaluate(user_query, meta)
        meta.update(robustness_result)

    return all_metadata


if __name__ == "__main__":
    print("📦 AutoDataFinder.AI – Dataset Discovery Agent")
    user_query = input("\n🧠 Describe your ML problem (e.g., 'object detection for recycling robots'): ")
    results = run_pipeline(user_query, top_k=5)

    print("\n📊 Final Results:\n")
    for entry in results:
        print("\n-----------------------------")
        for k, v in entry.items():
            print(f"{k}: {v}")
